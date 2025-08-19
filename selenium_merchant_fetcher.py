#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selenium을 사용한 kloa.gg 떠상 데이터 실시간 수집 + 디스코드 봇
"""

import json
import time
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Optional
import pytz

# Selenium 관련
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Discord 봇 관련
import discord
from discord.ext import commands, tasks

class SeleniumMerchantFetcher:
    """Selenium을 사용한 실시간 떠돌이 상인 데이터 가져오기"""
    
    def __init__(self):
        self.base_url = "https://kloa.gg/merchant"
    
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 브라우저 창 숨기기
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"Chrome 드라이버 설정 실패: {e}")
            print("ChromeDriver가 설치되어 있는지 확인하세요.")
            return None

    def fetch_merchant_data_selenium(self):
        """Selenium으로 떠상 데이터 가져오기 (div.bg-elevated에서 구조화된 데이터 추출)"""
        driver = self.setup_driver()
        if not driver:
            return None
        
        try:
            print("kloa.gg 페이지 로딩 중...")
            driver.get(self.base_url)
            
            # 페이지 로딩 대기
            wait = WebDriverWait(driver, 15)
            
            # div.bg-elevated 요소들 대기 및 찾기
            print("div.bg-elevated 요소들 로딩 대기 중...")
            bg_elevated_elements = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.bg-elevated"))
            )
            
            if len(bg_elevated_elements) < 2:
                print(f"❌ div.bg-elevated 요소가 충분하지 않습니다. 발견된 요소 수: {len(bg_elevated_elements)}")
                return []
            
            # 두 번째 div.bg-elevated 요소에서 데이터 추출
            print("두 번째 div.bg-elevated 요소에서 상인 데이터 추출 중...")
            second_element = bg_elevated_elements[1]
            
            # 각 상인 정보가 담긴 div 요소들 찾기
            merchant_divs = second_element.find_elements(By.CSS_SELECTOR, "div.px-8.py-3")
            
            merchants = []
            
            for merchant_div in merchant_divs:
                try:
                    # 서버명 확인 (니나브만 처리)
                    server_element = merchant_div.find_element(By.CSS_SELECTOR, "p.text-sm.font-medium.text-bola")
                    server_name = server_element.text.strip()
                    
                    if server_name != "니나브":
                        continue
                    
                    # 지역명과 NPC명 추출
                    location_element = merchant_div.find_element(By.CSS_SELECTOR, "span.text-base.font-medium")
                    region_name = location_element.text.strip()
                    
                    npc_element = merchant_div.find_element(By.CSS_SELECTOR, "span.text-sm.font-medium.text-secondary")
                    npc_name = npc_element.text.strip()
                    
                    # 아이템들 추출
                    items = []
                    item_elements = merchant_div.find_elements(By.CSS_SELECTOR, "p.px-1.rounded.text-lostark-grade")
                    
                    for item_element in item_elements:
                        try:
                            # data-grade 속성에서 등급 추출
                            grade = int(item_element.get_attribute("data-grade") or "3")
                            
                            # 아이템명 추출 (img 태그 다음의 텍스트)
                            item_name = item_element.text.strip()
                            
                            # 아이템 타입 추출 (img의 title 속성에서)
                            img_element = item_element.find_element(By.TAG_NAME, "img")
                            item_type_title = img_element.get_attribute("title")
                            
                            # 타입 매핑
                            if "카드" in item_type_title:
                                item_type = 1
                            elif "호감도" in item_type_title:
                                item_type = 2
                            else:
                                item_type = 3  # 특수 아이템
                            
                            if item_name:  # 빈 이름이 아닌 경우만 추가
                                items.append({
                                    'name': item_name,
                                    'type': item_type,
                                    'grade': grade,
                                    'hidden': False
                                })
                        
                        except Exception as e:
                            print(f"아이템 파싱 오류: {e}")
                            continue
                    
                    if items:  # 아이템이 있는 경우만 상인 추가
                        merchant_info = {
                            'region_name': region_name,
                            'npc_name': npc_name,
                            'group': 1,  # 기본값
                            'items': items
                        }
                        merchants.append(merchant_info)
                        print(f"  ✅ {region_name} - {npc_name}: {len(items)}개 아이템")
                
                except Exception as e:
                    print(f"상인 정보 파싱 오류: {e}")
                    continue
            
            print(f"데이터 수집 완료! 총 {len(merchants)}명의 상인 발견")
            return merchants
            
        except TimeoutException:
            print("페이지 로딩 시간 초과")
            return []
        except NoSuchElementException:
            print("div.bg-elevated 요소를 찾을 수 없음")
            return []
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return []
        finally:
            driver.quit()
    
    def get_current_active_merchants(self) -> List[Dict]:
        """현재 활성화된 상인들 가져오기 (Selenium으로 직접 파싱)"""
        try:
            print("🔄 Selenium으로 실시간 데이터 가져오는 중...")
            
            # Selenium으로 데이터 가져오기 (이미 니나브 서버 상인들만 필터링됨)
            merchants_data = self.fetch_merchant_data_selenium()
            if not merchants_data:
                return []
            
            print(f"✅ 니나브 서버 상인 {len(merchants_data)}명 발견:")
            for merchant in merchants_data:
                print(f"  - {merchant['region_name']} {merchant['npc_name']}: {len(merchant['items'])}개 아이템")
                for item in merchant['items'][:3]:  # 처음 3개 아이템만 표시
                    type_name = "카드" if item['type'] == 1 else "호감도" if item['type'] == 2 else "특수"
                    print(f"    • [{type_name}] {item['name']} (등급 {item['grade']})")
                if len(merchant['items']) > 3:
                    print(f"    ... 외 {len(merchant['items']) - 3}개")
            
            return merchants_data
            
        except Exception as e:
            print(f"❌ 실시간 데이터 가져오기 실패: {e}")
            return []
    
class SeleniumMerchantBot:
    """Selenium 기반 떠상 디스코드 봇"""
    
    def __init__(self, token: str, channel_id: int):
        self.token = token
        self.channel_id = channel_id
        
        # 봇 설정
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        
        # Selenium 데이터 가져오기 초기화
        self.merchant_fetcher = SeleniumMerchantFetcher()
        
        # 상인 데이터 저장
        self.merchant_data = None
        self.last_data_update = None
        self.last_notification = None
        
        self.setup_bot()
    
    def setup_bot(self):
        """봇 이벤트 및 명령어 설정"""
        
        @self.bot.event
        async def on_ready():
            print(f'🤖 {self.bot.user} Selenium 떠상봇이 준비되었습니다!')
            print(f'📢 알림 채널: {self.channel_id}')
            
            # 초기 데이터 로드
            await self.load_merchant_data()
            
            # 주기적 체크 시작
            self.check_merchants.start()
        
        @self.bot.command(name='떠상')
        async def check_current_merchants(ctx):
            """현재 활성 상인 확인"""
            try:
                # 최신 데이터 확인
                await self.refresh_data_if_needed()
                
                if not self.merchant_data:
                    embed = discord.Embed(
                        title="🏪 떠돌이 상인 (Selenium)",
                        description="상인 데이터를 가져올 수 없습니다.",
                        color=0xff0000,
                        timestamp=datetime.now()
                    )
                    await ctx.send(embed=embed)
                    return
                
                if not self.merchant_data:
                    embed = discord.Embed(
                        title="🏪 떠돌이 상인 (Selenium)",
                        description="현재 활성화된 상인이 없습니다.",
                        color=0x808080,
                        timestamp=datetime.now()
                    )
                else:
                    embed = discord.Embed(
                        title="🏪 떠돌이 상인 (Selenium)",
                        description=f"현재 **{len(self.merchant_data)}명**의 상인이 활성화되어 있습니다!",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    for merchant in self.merchant_data:
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
                    embed.set_footer(text=f"Selenium 기반 | 데이터 업데이트: {update_time}")
                else:
                    embed.set_footer(text="Selenium 기반 | 실시간 데이터")
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 오류가 발생했습니다: {e}")
        
        @self.bot.command(name='새로고침')
        async def refresh_data(ctx):
            """데이터 새로고침"""
            try:
                await ctx.send("🔄 Selenium으로 데이터를 새로고침하는 중...")
                
                success = await self.load_merchant_data()
                
                if success and self.merchant_data:
                    embed = discord.Embed(
                        title="✅ 데이터 새로고침 완료",
                        description=f"Selenium으로 상인 데이터를 성공적으로 업데이트했습니다.",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="📊 현재 활성 상인 수",
                        value=f"**{len(self.merchant_data)}명**",
                        inline=True
                    )
                    
                    if self.last_data_update:
                        update_time = self.last_data_update.strftime("%Y-%m-%d %H:%M:%S")
                        embed.add_field(
                            name="🕒 업데이트 시간",
                            value=update_time,
                            inline=True
                        )
                    
                else:
                    embed = discord.Embed(
                        title="❌ 데이터 새로고침 실패",
                        description="Selenium으로 데이터를 가져올 수 없습니다.",
                        color=0xff0000,
                        timestamp=datetime.now()
                    )
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 새로고침 오류: {e}")
        
        @self.bot.command(name='떠상검색', aliases=['검색', 'search'])
        async def search_item(ctx, *, item_name: str):
            """아이템으로 상인 검색"""
            try:
                await self.refresh_data_if_needed()
                
                if not self.merchant_data:
                    await ctx.send("❌ 상인 데이터를 가져올 수 없습니다.")
                    return
                
                found_merchants = []
                
                for merchant in self.merchant_data:
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
                
                embed.set_footer(text="Selenium 기반 | 검색 결과")
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 검색 중 오류: {e}")
        
        @self.bot.command(name='도움말', aliases=['명령어'])
        async def help_command(ctx):
            """봇 도움말 및 명령어 목록"""
            embed = discord.Embed(
                title="🤖 Selenium 떠상봇 도움말",
                description="Selenium을 사용한 떠돌이 상인 알림 봇입니다.",
                color=0x7289da,
                timestamp=datetime.now()
            )
            
            # 기본 명령어
            basic_commands = [
                "`!떠상` - 현재 활성 떠돌이 상인 조회",
                "`!새로고침` - 데이터 수동 새로고침",
                "`!떠상검색 아이템명` - 특정 아이템 검색"
            ]
            embed.add_field(
                name="📋 기본 명령어",
                value='\n'.join(basic_commands),
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
            
            embed.set_footer(text="Selenium 기반 | 떠상 시간: 04:00~09:30, 10:00~15:30, 16:00~21:30, 22:00~03:30")
            await ctx.send(embed=embed)
        
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
            
            embed.set_footer(text="Selenium 기반")
            await ctx.send(embed=embed)
    
    async def load_merchant_data(self) -> bool:
        """Selenium으로 상인 데이터 로드"""
        try:
            print("🔄 Selenium으로 데이터 로드 중...")
            
            # 비동기로 Selenium 실행
            loop = asyncio.get_event_loop()
            merchants = await loop.run_in_executor(None, self.merchant_fetcher.get_current_active_merchants)
            
            if merchants:
                self.merchant_data = merchants
                self.last_data_update = datetime.now()
                print(f"✅ Selenium 데이터 로드 성공: {len(merchants)}명")
                return True
            else:
                print("❌ Selenium 데이터 로드 실패")
                self.merchant_data = []
                return False
                
        except Exception as e:
            print(f"❌ 데이터 로드 오류: {e}")
            return False
    
    async def refresh_data_if_needed(self):
        """필요시 데이터 새로고침 (30분마다)"""
        try:
            now = datetime.now()
            
            # 데이터가 없거나 30분이 지났으면 새로고침
            if (self.merchant_data is None or 
                self.last_data_update is None or 
                (now - self.last_data_update).total_seconds() > 1800):  # 30분
                
                print("🔄 데이터 자동 새로고침...")
                await self.load_merchant_data()
                
        except Exception as e:
            print(f"❌ 자동 새로고침 오류: {e}")
    
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
            
            # 상인이 활성화되어 있고, 마지막 알림으로부터 30분이 지났으면 알림
            now = datetime.now()
            if self.merchant_data and len(self.merchant_data) > 0 and (
                self.last_notification is None or 
                (now - self.last_notification).total_seconds() > 1800  # 30분
            ):
                embed = discord.Embed(
                    title="🚨 떠돌이 상인 알림 (Selenium)",
                    description=f"현재 **{len(self.merchant_data)}명**의 상인이 활성화되어 있습니다!",
                    color=0xff6b35,
                    timestamp=now
                )
                
                for merchant in self.merchant_data:
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
                
                embed.set_footer(text="Selenium 기반 | 다음 알림: 30분 후")
                
                await channel.send(embed=embed)
                self.last_notification = now
                print(f"✅ Selenium 상인 알림 전송: {len(self.merchant_data)}명")
            
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
    print("🚀 Selenium 기반 떠상봇 시작")
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
    print(f"   - 데이터 소스: Selenium (Chrome)")
    print(f"   - 채널 ID: {CHANNEL_ID}")
    print(f"   - 체크 주기: 5분")
    print(f"   - 알림 주기: 30분")
    print(f"   - 데이터 새로고침: 30분")
    
    # 봇 시작
    bot = SeleniumMerchantBot(TOKEN, CHANNEL_ID)
    bot.run()

if __name__ == "__main__":
    main()
