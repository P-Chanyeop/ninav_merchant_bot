# -*- coding: utf-8 -*-
"""
니나브 서버 전용 떠상봇 - 동적 데이터 기반
ninav_server_finder.py에서 가져온 실제 데이터 사용
"""

import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Optional
from real_time_merchant_fetcher import RealTimeMerchantFetcher

class NinavDynamicMerchantBot:
    """니나브 서버 전용 떠상봇 - 동적 데이터"""
    
    def __init__(self, token: str, channel_id: int):
        self.token = token
        self.channel_id = channel_id
        
        # 봇 설정
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        
        # 실시간 데이터 가져오기 초기화
        self.merchant_fetcher = RealTimeMerchantFetcher()
        
        # 동적으로 가져온 상인 데이터 저장
        self.ninav_merchants_data = None
        self.last_data_update = None
        
        # 마지막 알림 시간 추적
        self.last_notification = None
        
        self.setup_bot()
    
    def setup_bot(self):
        """봇 이벤트 및 명령어 설정"""
        
        @self.bot.event
        async def on_ready():
            print(f'🤖 {self.bot.user} 니나브 서버 떠상봇이 준비되었습니다!')
            print(f'📢 알림 채널: {self.channel_id}')
            
            # 초기 데이터 로드
            await self.load_ninav_data()
            
            # 주기적 체크 시작
            self.check_merchants.start()
        
        @self.bot.command(name='떠상')
        async def check_current_merchants(ctx):
            """현재 활성 상인 확인"""
            try:
                # 최신 데이터 확인
                await self.refresh_data_if_needed()
                
                if not self.ninav_merchants_data:
                    embed = discord.Embed(
                        title="🏪 니나브 서버 떠돌이 상인",
                        description="상인 데이터를 가져올 수 없습니다.",
                        color=0xff0000,
                        timestamp=datetime.now()
                    )
                    await ctx.send(embed=embed)
                    return
                
                active_merchants = await self.get_current_active_merchants()
                
                if not active_merchants:
                    embed = discord.Embed(
                        title="🏪 니나브 서버 떠돌이 상인",
                        description="현재 활성화된 상인이 없습니다.",
                        color=0x808080,
                        timestamp=datetime.now()
                    )
                else:
                    embed = discord.Embed(
                        title="🏪 니나브 서버 떠돌이 상인",
                        description=f"현재 **{len(active_merchants)}명**의 상인이 활성화되어 있습니다!",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    for merchant in active_merchants:
                        region = merchant['region_name']
                        npc = merchant['npc_name']
                        items = [item['name'] for item in merchant['items']]
                        
                        # 아이템을 3개씩 나누어 표시
                        item_chunks = [items[i:i+3] for i in range(0, len(items), 3)]
                        item_text = '\n'.join([' • '.join(chunk) for chunk in item_chunks])
                        
                        embed.add_field(
                            name=f"📍 {region} - {npc}",
                            value=f"```{item_text}```",
                            inline=False
                        )
                    
                    # 마감 시간 표시 추가
                    now = datetime.now()
                    current_hour = now.hour
                    current_minute = now.minute
                    
                    # 현재 시간대에 따른 마감 시간 계산
                    if (4 <= current_hour < 9) or (current_hour == 9 and current_minute <= 30):
                        end_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
                        end_time_str = "09:30"
                    elif (10 <= current_hour < 15) or (current_hour == 15 and current_minute <= 30):
                        end_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
                        end_time_str = "15:30"
                    elif (16 <= current_hour < 21) or (current_hour == 21 and current_minute <= 30):
                        end_time = now.replace(hour=21, minute=30, second=0, microsecond=0)
                        end_time_str = "21:30"
                    elif current_hour >= 22 or current_hour < 4 or (current_hour == 3 and current_minute <= 30):
                        if current_hour >= 22:
                            end_time = (now + timedelta(days=1)).replace(hour=3, minute=30, second=0, microsecond=0)
                        else:
                            end_time = now.replace(hour=3, minute=30, second=0, microsecond=0)
                        end_time_str = "03:30"
                    else:
                        end_time = None
                        end_time_str = "비활성"
                    
                    if end_time and now < end_time:
                        remaining = end_time - now
                        hours = remaining.seconds // 3600
                        minutes = (remaining.seconds % 3600) // 60
                        
                        embed.add_field(
                            name="⏰ 마감까지 남은 시간",
                            value=f"```{hours}시간 {minutes}분 남음```",
                            inline=True
                        )
                        
                        embed.add_field(
                            name="🕐 마감 시간",
                            value=f"```{end_time_str}```",
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name="⏰ 상태",
                            value="```마감됨```",
                            inline=True
                        )
                
                # 데이터 업데이트 시간 표시
                if self.last_data_update:
                    update_time = self.last_data_update.strftime("%H:%M:%S")
                    embed.set_footer(text=f"니나브 서버 전용 | 데이터 업데이트: {update_time}")
                else:
                    embed.set_footer(text="니나브 서버 전용 | 실시간 데이터")
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 오류가 발생했습니다: {e}")
        
        @self.bot.command(name='니나브새로고침')
        async def refresh_ninav_data(ctx):
            """니나브 서버 데이터 새로고침"""
            try:
                await ctx.send("🔄 니나브 서버 데이터를 새로고침하는 중...")
                
                success = await self.load_ninav_data()
                
                if success and self.ninav_merchants_data:
                    embed = discord.Embed(
                        title="✅ 데이터 새로고침 완료",
                        description=f"니나브 서버 상인 데이터를 성공적으로 업데이트했습니다.",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="📊 업데이트된 상인 수",
                        value=f"**{len(self.ninav_merchants_data)}명**",
                        inline=True
                    )
                    
                    if self.last_data_update:
                        update_time = self.last_data_update.strftime("%Y-%m-%d %H:%M:%S")
                        embed.add_field(
                            name="🕒 업데이트 시간",
                            value=update_time,
                            inline=True
                        )
                    
                    # 상인 목록 표시
                    merchant_list = []
                    for merchant in self.ninav_merchants_data:
                        region = merchant['region_name']
                        npc = merchant['npc_name']
                        item_count = len(merchant['items'])
                        merchant_list.append(f"• {region} - {npc} ({item_count}개 아이템)")
                    
                    embed.add_field(
                        name="👥 상인 목록",
                        value='\n'.join(merchant_list),
                        inline=False
                    )
                    
                else:
                    embed = discord.Embed(
                        title="❌ 데이터 새로고침 실패",
                        description="니나브 서버 데이터를 가져올 수 없습니다.",
                        color=0xff0000,
                        timestamp=datetime.now()
                    )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 새로고침 오류: {e}")
        
        @self.bot.command(name='니나브상인')
        async def ninav_merchants_info(ctx):
            """니나브 서버 상인 정보"""
            try:
                await self.refresh_data_if_needed()
                
                if not self.ninav_merchants_data:
                    await ctx.send("❌ 상인 데이터를 가져올 수 없습니다.")
                    return
                
                embed = discord.Embed(
                    title="🗺️ 니나브 서버 떠돌이 상인 정보",
                    description="니나브 서버의 모든 떠돌이 상인 위치와 아이템",
                    color=0x0099ff,
                    timestamp=datetime.now()
                )
                
                for merchant in self.ninav_merchants_data:
                    region = merchant['region_name']
                    npc = merchant['npc_name']
                    items = [item['name'] for item in merchant['items']]
                    
                    # 아이템을 3개씩 나누어 표시
                    item_chunks = [items[i:i+3] for i in range(0, len(items), 3)]
                    item_text = '\n'.join([' • '.join(chunk) for chunk in item_chunks])
                    
                    embed.add_field(
                        name=f"📍 {region} - {npc}",
                        value=f"```{item_text}```",
                        inline=False
                    )
                
                embed.set_footer(text=f"니나브 서버 전용 | 총 {len(self.ninav_merchants_data)}명의 상인")
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 오류가 발생했습니다: {e}")
        
        @self.bot.command(name='도움말', aliases=['명령어'])
        async def help_command(ctx):
            """봇 도움말 및 명령어 목록"""
            embed = discord.Embed(
                title="🤖 니나브 서버 떠상봇 도움말",
                description="니나브 서버 전용 떠돌이 상인 알림 봇입니다.",
                color=0x7289da,
                timestamp=datetime.now()
            )
            
            # 기본 명령어
            basic_commands = [
                "`!떠상` - 현재 활성 떠돌이 상인 조회",
                "`!니나브상인` - 모든 상인 정보 보기",
                "`!니나브새로고침` - 데이터 수동 새로고침"
            ]
            embed.add_field(
                name="📋 기본 명령어",
                value='\n'.join(basic_commands),
                inline=False
            )
            
            # 검색 명령어
            search_commands = [
                "`!떠상검색 아이템명` - 특정 아이템 검색",
                "`!상인검색 상인명` - 특정 상인 검색",
                "`!지역검색 지역명` - 특정 지역 검색"
            ]
            embed.add_field(
                name="🔍 검색 명령어",
                value='\n'.join(search_commands),
                inline=False
            )
            
            # 정보 명령어
            info_commands = [
                "`!시간` - 현재 시간 및 마감까지 남은 시간",
                "`!상태` - 봇 상태 및 데이터 정보",
                "`!통계` - 상인 통계 정보"
            ]
            embed.add_field(
                name="📊 정보 명령어",
                value='\n'.join(info_commands),
                inline=False
            )
            
            # 자동 기능
            auto_features = [
                "🚨 새로운 상인 등장시 자동 알림",
                "⚠️ 마감 30분 전 자동 알림",
                "🔄 30분마다 자동 데이터 새로고침",
                "⏰ 실시간 남은 시간 계산"
            ]
            embed.add_field(
                name="🤖 자동 기능",
                value='\n'.join(auto_features),
                inline=False
            )
            
            embed.set_footer(text="니나브 서버 전용 | 떠상 시간: 04:00~09:30, 10:00~15:30, 16:00~21:30, 22:00~03:30")
            await ctx.send(embed=embed)
        
        @self.bot.command(name='떠상검색', aliases=['검색', 'search'])
        async def search_item(ctx, *, item_name: str):
            """아이템으로 상인 검색"""
            try:
                await self.refresh_data_if_needed()
                
                if not self.ninav_merchants_data:
                    await ctx.send("❌ 상인 데이터를 가져올 수 없습니다.")
                    return
                
                active_merchants = await self.get_current_active_merchants()
                found_merchants = []
                
                for merchant in active_merchants:
                    items = [item['name'] for item in merchant['items']]
                    if any(item_name.lower() in item.lower() for item in items):
                        found_merchants.append(merchant)
                
                if not found_merchants:
                    embed = discord.Embed(
                        title=f"🔍 '{item_name}' 검색 결과",
                        description="해당 아이템을 파는 상인을 찾을 수 없습니다.",
                        color=0xff9900,
                        timestamp=datetime.now()
                    )
                else:
                    embed = discord.Embed(
                        title=f"🔍 '{item_name}' 검색 결과",
                        description=f"**{len(found_merchants)}명**의 상인이 해당 아이템을 판매합니다.",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    for merchant in found_merchants:
                        region = merchant['region_name']
                        npc = merchant['npc_name']
                        items = [item['name'] for item in merchant['items']]
                        
                        # 검색된 아이템 하이라이트
                        highlighted_items = []
                        for item in items:
                            if item_name.lower() in item.lower():
                                highlighted_items.append(f"**{item}**")
                            else:
                                highlighted_items.append(item)
                        
                        item_chunks = [highlighted_items[i:i+3] for i in range(0, len(highlighted_items), 3)]
                        item_text = '\n'.join([' • '.join(chunk) for chunk in item_chunks])
                        
                        embed.add_field(
                            name=f"📍 {region} - {npc}",
                            value=item_text,
                            inline=False
                        )
                
                embed.set_footer(text="니나브 서버 전용 | 검색 결과")
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 검색 중 오류: {e}")
        
        @self.bot.command(name='상인검색', aliases=['npc검색'])
        async def search_npc(ctx, *, npc_name: str):
            """상인 이름으로 검색"""
            try:
                await self.refresh_data_if_needed()
                
                if not self.ninav_merchants_data:
                    await ctx.send("❌ 상인 데이터를 가져올 수 없습니다.")
                    return
                
                active_merchants = await self.get_current_active_merchants()
                found_merchants = []
                
                for merchant in active_merchants:
                    if npc_name.lower() in merchant['npc_name'].lower():
                        found_merchants.append(merchant)
                
                if not found_merchants:
                    embed = discord.Embed(
                        title=f"🔍 '{npc_name}' 상인 검색 결과",
                        description="해당 이름의 상인을 찾을 수 없습니다.",
                        color=0xff9900,
                        timestamp=datetime.now()
                    )
                else:
                    embed = discord.Embed(
                        title=f"🔍 '{npc_name}' 상인 검색 결과",
                        description=f"**{len(found_merchants)}명**의 상인을 찾았습니다.",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    for merchant in found_merchants:
                        region = merchant['region_name']
                        npc = merchant['npc_name']
                        items = [item['name'] for item in merchant['items']]
                        
                        item_chunks = [items[i:i+3] for i in range(0, len(items), 3)]
                        item_text = '\n'.join([' • '.join(chunk) for chunk in item_chunks])
                        
                        embed.add_field(
                            name=f"📍 **{region} - {npc}**",
                            value=f"```{item_text}```",
                            inline=False
                        )
                
                embed.set_footer(text="니나브 서버 전용 | 상인 검색")
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 상인 검색 중 오류: {e}")
        
        @self.bot.command(name='지역검색', aliases=['region'])
        async def search_region(ctx, *, region_name: str):
            """지역 이름으로 검색"""
            try:
                await self.refresh_data_if_needed()
                
                if not self.ninav_merchants_data:
                    await ctx.send("❌ 상인 데이터를 가져올 수 없습니다.")
                    return
                
                active_merchants = await self.get_current_active_merchants()
                found_merchants = []
                
                for merchant in active_merchants:
                    if region_name.lower() in merchant['region_name'].lower():
                        found_merchants.append(merchant)
                
                if not found_merchants:
                    embed = discord.Embed(
                        title=f"🔍 '{region_name}' 지역 검색 결과",
                        description="해당 지역의 상인을 찾을 수 없습니다.",
                        color=0xff9900,
                        timestamp=datetime.now()
                    )
                else:
                    embed = discord.Embed(
                        title=f"🔍 '{region_name}' 지역 검색 결과",
                        description=f"**{len(found_merchants)}명**의 상인을 찾았습니다.",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    for merchant in found_merchants:
                        region = merchant['region_name']
                        npc = merchant['npc_name']
                        items = [item['name'] for item in merchant['items']]
                        
                        item_chunks = [items[i:i+3] for i in range(0, len(items), 3)]
                        item_text = '\n'.join([' • '.join(chunk) for chunk in item_chunks])
                        
                        embed.add_field(
                            name=f"📍 **{region} - {npc}**",
                            value=f"```{item_text}```",
                            inline=False
                        )
                
                embed.set_footer(text="니나브 서버 전용 | 지역 검색")
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 지역 검색 중 오류: {e}")
        
        @self.bot.command(name='시간', aliases=['time', '남은시간'])
        async def time_info(ctx):
            """현재 시간 및 마감까지 남은 시간"""
            now = datetime.now()
            
            embed = discord.Embed(
                title="🕐 시간 정보",
                color=0x3498db,
                timestamp=now
            )
            
            embed.add_field(
                name="📅 현재 시간",
                value=f"```{now.strftime('%Y-%m-%d %H:%M:%S')}```",
                inline=False
            )
            
            # 떠상 활성 시간 확인 (04:00~09:30, 10:00~15:30, 16:00~21:30, 22:00~03:30)
            current_hour = now.hour
            current_minute = now.minute
            
            # 현재 활성 시간대 확인 및 다음 마감 시간 계산
            if (4 <= current_hour < 9) or (current_hour == 9 and current_minute <= 30):
                # 04:00 ~ 09:30 시간대
                end_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
                if now > end_time:
                    end_time = end_time.replace(hour=10, minute=0)  # 다음 시작 시간
                remaining = end_time - now
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                
                embed.add_field(
                    name="⏰ 떠상 마감까지",
                    value=f"```{hours}시간 {minutes}분 남음```",
                    inline=True
                )
                embed.add_field(
                    name="🕐 마감 시간",
                    value="```09:30```",
                    inline=True
                )
                embed.color = 0x00ff00
                
            elif (10 <= current_hour < 15) or (current_hour == 15 and current_minute <= 30):
                # 10:00 ~ 15:30 시간대
                end_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
                remaining = end_time - now
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                
                embed.add_field(
                    name="⏰ 떠상 마감까지",
                    value=f"```{hours}시간 {minutes}분 남음```",
                    inline=True
                )
                embed.add_field(
                    name="🕐 마감 시간",
                    value="```15:30```",
                    inline=True
                )
                embed.color = 0x00ff00
                
            elif (16 <= current_hour < 21) or (current_hour == 21 and current_minute <= 30):
                # 16:00 ~ 21:30 시간대
                end_time = now.replace(hour=21, minute=30, second=0, microsecond=0)
                remaining = end_time - now
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                
                embed.add_field(
                    name="⏰ 떠상 마감까지",
                    value=f"```{hours}시간 {minutes}분 남음```",
                    inline=True
                )
                embed.add_field(
                    name="🕐 마감 시간",
                    value="```21:30```",
                    inline=True
                )
                embed.color = 0x00ff00
                
            elif current_hour >= 22 or current_hour < 4 or (current_hour == 3 and current_minute <= 30):
                # 22:00 ~ 03:30 시간대
                if current_hour >= 22:
                    # 22시 이후면 다음날 03:30까지
                    end_time = (now + timedelta(days=1)).replace(hour=3, minute=30, second=0, microsecond=0)
                else:
                    # 03:30 이전이면 오늘 03:30까지
                    end_time = now.replace(hour=3, minute=30, second=0, microsecond=0)
                
                remaining = end_time - now
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                
                embed.add_field(
                    name="⏰ 떠상 마감까지",
                    value=f"```{hours}시간 {minutes}분 남음```",
                    inline=True
                )
                embed.add_field(
                    name="🕐 마감 시간",
                    value="```03:30```",
                    inline=True
                )
                embed.color = 0x00ff00
                
            else:
                # 비활성 시간대 - 다음 시작 시간 계산
                if 9 < current_hour < 10 or (current_hour == 9 and current_minute > 30):
                    # 09:30 ~ 10:00 사이
                    next_start = now.replace(hour=10, minute=0, second=0, microsecond=0)
                    next_time_str = "10:00"
                elif 15 < current_hour < 16 or (current_hour == 15 and current_minute > 30):
                    # 15:30 ~ 16:00 사이
                    next_start = now.replace(hour=16, minute=0, second=0, microsecond=0)
                    next_time_str = "16:00"
                elif 21 < current_hour < 22 or (current_hour == 21 and current_minute > 30):
                    # 21:30 ~ 22:00 사이
                    next_start = now.replace(hour=22, minute=0, second=0, microsecond=0)
                    next_time_str = "22:00"
                else:
                    # 03:30 ~ 04:00 사이
                    next_start = now.replace(hour=4, minute=0, second=0, microsecond=0)
                    next_time_str = "04:00"
                
                remaining = next_start - now
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                
                embed.add_field(
                    name="⏰ 떠상 시작까지",
                    value=f"```{hours}시간 {minutes}분 남음```",
                    inline=True
                )
                embed.add_field(
                    name="🕐 다음 시작",
                    value=f"```{next_time_str}```",
                    inline=True
                )
                embed.color = 0xff9900
            
            embed.set_footer(text="니나브 서버 전용 | 떠상 시간: 04:00~09:30, 10:00~15:30, 16:00~21:30, 22:00~03:30")
            await ctx.send(embed=embed)
        
        @self.bot.command(name='상태', aliases=['status', '정보'])
        async def bot_status(ctx):
            """봇 상태 및 데이터 정보"""
            embed = discord.Embed(
                title="🤖 봇 상태 정보",
                color=0x7289da,
                timestamp=datetime.now()
            )
            
            # 데이터 상태
            if self.ninav_merchants_data:
                embed.add_field(
                    name="📊 데이터 상태",
                    value=f"```✅ 정상 ({len(self.ninav_merchants_data)}명 상인)```",
                    inline=True
                )
            else:
                embed.add_field(
                    name="📊 데이터 상태",
                    value="```❌ 데이터 없음```",
                    inline=True
                )
            
            # 마지막 업데이트
            if self.last_data_update:
                update_time = self.last_data_update.strftime("%H:%M:%S")
                embed.add_field(
                    name="🔄 마지막 업데이트",
                    value=f"```{update_time}```",
                    inline=True
                )
            
            # 현재 활성 상인 수
            active_count = len(await self.get_current_active_merchants())
            embed.add_field(
                name="👥 현재 활성 상인",
                value=f"```{active_count}명```",
                inline=True
            )
            
            embed.set_footer(text="니나브 서버 전용 | 실시간 모니터링")
            await ctx.send(embed=embed)
        
        @self.bot.command(name='통계', aliases=['stats'])
        async def merchant_stats(ctx):
            """상인 통계 정보"""
            try:
                await self.refresh_data_if_needed()
                
                if not self.ninav_merchants_data:
                    await ctx.send("❌ 상인 데이터를 가져올 수 없습니다.")
                    return
                
                embed = discord.Embed(
                    title="📊 니나브 서버 상인 통계",
                    color=0x9b59b6,
                    timestamp=datetime.now()
                )
                
                # 총 상인 수
                total_merchants = len(self.ninav_merchants_data)
                active_merchants = await self.get_current_active_merchants()
                active_count = len(active_merchants)
                
                embed.add_field(
                    name="👥 상인 수",
                    value=f"```총 {total_merchants}명 / 활성 {active_count}명```",
                    inline=False
                )
                
                # 아이템 통계
                if active_merchants:
                    total_items = sum(len(m['items']) for m in active_merchants)
                    avg_items = total_items / len(active_merchants)
                    
                    embed.add_field(
                        name="🎒 아이템 통계",
                        value=f"```총 {total_items}개 / 평균 {avg_items:.1f}개```",
                        inline=True
                    )
                    
                    # 가장 많은 아이템을 가진 상인
                    max_merchant = max(active_merchants, key=lambda m: len(m['items']))
                    embed.add_field(
                        name="🏆 최다 아이템 상인",
                        value=f"```{max_merchant['region_name']} - {max_merchant['npc_name']} ({len(max_merchant['items'])}개)```",
                        inline=True
                    )
                
                embed.set_footer(text="니나브 서버 전용 | 실시간 통계")
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 통계 조회 중 오류: {e}")
        
        @self.bot.command(name='핑', aliases=['ping'])
        async def ping_command(ctx):
            """봇 응답 속도 확인"""
            latency = round(self.bot.latency * 1000)
            
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"응답 속도: **{latency}ms**",
                color=0x00ff00 if latency < 100 else 0xff9900 if latency < 200 else 0xff0000,
                timestamp=datetime.now()
            )
            
            embed.set_footer(text="니나브 서버 전용")
            await ctx.send(embed=embed)
    
    async def load_ninav_data(self) -> bool:
        """실시간 니나브 서버 데이터 로드"""
        try:
            print("🔄 실시간 니나브 서버 데이터 로드 중...")
            
            # 실시간 데이터 가져오기
            result = self.merchant_fetcher.get_current_active_merchants()
            
            if result and len(result) > 0:
                self.ninav_merchants_data = result
                self.last_data_update = datetime.now()
                print(f"✅ 실시간 데이터 로드 성공: {len(result)}명")
                
                # 로드된 데이터 확인
                for merchant in result:
                    region = merchant['region_name']
                    npc = merchant['npc_name']
                    item_count = len(merchant['items'])
                    print(f"  - {region} - {npc}: {item_count}개 아이템")
                
                return True
            else:
                print("❌ 실시간 데이터 로드 실패 또는 활성 상인 없음")
                return False
                
        except Exception as e:
            print(f"❌ 데이터 로드 오류: {e}")
            return False
    
    async def refresh_data_if_needed(self):
        """필요시 데이터 새로고침 (30분마다)"""
        try:
            now = datetime.now()
            
            # 데이터가 없거나 30분이 지났으면 새로고침
            if (self.ninav_merchants_data is None or 
                self.last_data_update is None or 
                (now - self.last_data_update).total_seconds() > 1800):  # 30분
                
                print("🔄 데이터 자동 새로고침...")
                await self.load_ninav_data()
                
        except Exception as e:
            print(f"❌ 자동 새로고침 오류: {e}")
    
    async def get_current_active_merchants(self) -> List[Dict]:
        """현재 활성화된 상인 목록 가져오기 (실시간 데이터 사용)"""
        try:
            # 실시간 데이터가 이미 현재 활성 상인들만 포함하므로 그대로 반환
            if self.ninav_merchants_data:
                return self.ninav_merchants_data
            
            return []
            
        except Exception as e:
            print(f"❌ 활성 상인 확인 오류: {e}")
            return []
    
    @tasks.loop(minutes=5)
    async def check_merchants(self):
        """5분마다 상인 상태 확인"""
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                print(f"❌ 채널을 찾을 수 없습니다: {self.channel_id}")
                return
            
            # 데이터 자동 새로고침
            await self.refresh_data_if_needed()
            
            active_merchants = await self.get_current_active_merchants()
            
            # 상인이 활성화되어 있고, 마지막 알림으로부터 30분이 지났으면 알림
            now = datetime.now()
            if active_merchants and (
                self.last_notification is None or 
                (now - self.last_notification).total_seconds() > 1800  # 30분
            ):
                embed = discord.Embed(
                    title="🚨 니나브 서버 떠돌이 상인 알림",
                    description=f"현재 **{len(active_merchants)}명**의 상인이 활성화되어 있습니다!",
                    color=0xff6b35,
                    timestamp=now
                )
                
                for merchant in active_merchants:
                    region = merchant['region_name']
                    npc = merchant['npc_name']
                    items = [item['name'] for item in merchant['items']]
                    
                    # 아이템을 3개씩 나누어 표시
                    item_chunks = [items[i:i+3] for i in range(0, len(items), 3)]
                    item_text = '\n'.join([' • '.join(chunk) for chunk in item_chunks])
                    
                    embed.add_field(
                        name=f"📍 {region} - {npc}",
                        value=f"```{item_text}```",
                        inline=False
                    )
                
                embed.set_footer(text="니나브 서버 전용 | 다음 알림: 30분 후")
                
                await channel.send(embed=embed)
                self.last_notification = now
                print(f"✅ 니나브 서버 상인 알림 전송: {len(active_merchants)}명")
            
        except Exception as e:
            print(f"❌ 상인 체크 오류: {e}")
    
    def run(self):
        """봇 실행"""
        try:
            self.bot.run(self.token)
        except Exception as e:
            print(f"❌ 봇 실행 오류: {e}")

def main():
    """메인 함수"""
    print("🚀 니나브 서버 전용 떠상봇 시작 (동적 데이터)")
    print("=" * 60)
    
    # 봇 토큰 입력 (보안상 하드코딩 제거)
    TOKEN = input("Discord 봇 토큰을 입력하세요: ").strip()
    if not TOKEN:
        print("❌ 봇 토큰이 필요합니다!")
        return
    
    # 채널 ID 입력
    CHANNEL_ID = input("알림을 보낼 채널 ID를 입력하세요: ").strip()
    if not CHANNEL_ID.isdigit():
        print("❌ 올바른 채널 ID가 필요합니다!")
        return
    
    CHANNEL_ID = int(CHANNEL_ID)
    
    print(f"✅ 설정 완료:")
    print(f"   - 서버: 니나브")
    print(f"   - 채널 ID: {CHANNEL_ID}")
    print(f"   - 데이터 소스: HTML 동적 추출")
    print(f"   - 체크 주기: 5분")
    print(f"   - 알림 주기: 30분")
    print(f"   - 데이터 새로고침: 30분")
    
    # 봇 시작
    bot = NinavDynamicMerchantBot(TOKEN, CHANNEL_ID)
    bot.run()

if __name__ == "__main__":
    main()
