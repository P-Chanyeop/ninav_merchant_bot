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
            
            # 페이지가 완전히 로드될 때까지 대기
            time.sleep(3)
            
            # 니나브 서버 클릭
            try:
                driver.find_elements(By.CSS_SELECTOR, "button.text-secondary.font-medium")[7].click()
                print("니나브 서버 선택 완료")
            except IndexError:
                print("❌ 니나브 서버 버튼을 찾을 수 없습니다. 페이지 구조가 변경되었을 수 있습니다.")
                return []
            
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
                    
                    # if server_name != "니나브":
                    #     continue
                    
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
                            # data-grade 속성에서 등급 추출 및 변환
                            grade_attr = item_element.get_attribute("data-grade")
                            
                            # None이나 빈 문자열이 아닌 경우에만 변환, 그렇지 않으면 기본값 3
                            if grade_attr is not None and grade_attr.strip() != "":
                                try:
                                    grade_num = int(grade_attr)
                                except ValueError:
                                    grade_num = 3  # 숫자로 변환할 수 없으면 기본값
                            else:
                                grade_num = 3  # 기본값
                            
                            # 등급 숫자를 텍스트로 변환
                            grade_map = {
                                4: "전설",
                                3: "영웅", 
                                2: "희귀",
                                1: "고급",
                                0: "일반"
                            }
                            grade = grade_map.get(grade_num, "영웅")  # 기본값은 영웅
                            
                            # 아이템명 추출 (img 태그 다음의 텍스트)
                            item_name = item_element.text.strip()
                            
                            # 디버그: data-grade="0"인 아이템 확인
                            if grade_attr == "0":
                                print(f"DEBUG: data-grade=0 아이템 발견 - {item_name}, grade_num={grade_num}, grade='{grade}'")
                            
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
                    print(f"    • [{type_name}] {item['name']} ({item['grade']})")
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
    
    def format_item_with_color(self, item):
        """아이템을 등급별 색깔로 포맷팅 (디스코드 임베드용)"""
        grade = item['grade']
        name = item['name']
        
        # 등급별 색상 코드 (RGB를 16진수로 변환)
        # 고급(147,188,70), 일반(하얀색), 희귀(42,177,246), 영웅(128,69,221), 전설(249,174,0)
        grade_colors = {
            '일반': 0xFFFFFF,  # 하얀색
            '고급': 0x93BC46,  # RGB(147,188,70) 
            '희귀': 0x2AB1F6,  # RGB(42,177,246)
            '영웅': 0x8045DD,  # RGB(128,69,221)
            '전설': 0xF9AE00   # RGB(249,174,0)
        }
        
        # 아이템 정보와 색상 반환
        return {
            'name': name,
            'grade': grade,
            'color': grade_colors.get(grade, 0xFFFFFF)
        }
    
    def get_grade_color(self, grade):
        """등급별 색상 코드 반환"""
        grade_colors = {
            '일반': 0xFFFFFF,  # 하얀색
            '고급': 0x93BC46,  # RGB(147,188,70) 
            '희귀': 0x2AB1F6,  # RGB(42,177,246)
            '영웅': 0x8045DD,  # RGB(128,69,221)
            '전설': 0xF9AE00   # RGB(249,174,0)
        }
        return grade_colors.get(grade, 0xFFFFFF)
    
    def format_items_for_discord(self, items, highlight_item=None):
        """디스코드용 아이템 목록 포맷팅 (이모지 색상 표시)"""
        formatted_items = []
        
        # 등급별 이모지 설정
        grade_emojis = {
            '일반': '⚪',     # 하얀색 원
            '고급': '🟢',     # 초록색 원 (RGB 147,188,70 근사)
            '희귀': '🔵',     # 파란색 원 (RGB 42,177,246 근사)
            '영웅': '🟣',     # 보라색 원 (RGB 128,69,221 근사)
            '전설': '🟠'      # 주황색 원 (RGB 249,174,0 근사)
        }
        
        for item in items:
            grade = item['grade']
            name = item['name']
            
            # 등급별 이모지 추가
            emoji = grade_emojis.get(grade, '⚪')
            formatted_name = f"{emoji} {name}"
            
            # 검색 결과 하이라이트
            if highlight_item and highlight_item.lower() in name.lower():
                formatted_items.append(f"**{formatted_name}**")
            else:
                formatted_items.append(formatted_name)
        
        return formatted_items
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
                        
                        # 색상이 적용된 아이템 목록 생성
                        colored_items = self.format_items_for_discord(merchant['items'])
                        
                        # 아이템을 2개씩 나누어 표시
                        item_chunks = [colored_items[i:i+2] for i in range(0, len(colored_items), 2)]
                        item_text = '\n'.join([' • '.join(chunk) for chunk in item_chunks])
                        
                        embed.add_field(
                            name=f"📍 {region} - {npc}",
                            value=f"```\n{item_text}```",
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
                        
                        # 검색된 아이템 하이라이트 (색상 포함)
                        colored_items = self.format_items_for_discord(merchant['items'], item_name)
                        
                        item_chunks = [colored_items[i:i+2] for i in range(0, len(colored_items), 2)]
                        item_text = '\n'.join([' • '.join(chunk) for chunk in item_chunks])
                        
                        embed.add_field(
                            name=f"📍 {region} - {npc}",
                            value=f"```\n{item_text}```",
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
                "`!떠상검색 아이템명` - 특정 아이템 검색",
                "`!상인목록` - 활성 상인들의 간단한 목록"
            ]
            embed.add_field(
                name="📋 기본 명령어",
                value='\n'.join(basic_commands),
                inline=False
            )
            
            # 필터링 명령어
            filter_commands = [
                "`!등급별 [등급]` - 특정 등급 아이템만 보기",
                "`!타입별 [타입]` - 특정 타입 아이템만 보기",
                "`!통계` - 상인 및 아이템 통계 정보",
                "`!시간` - 떠상 시간표 및 현재 상태"
            ]
            embed.add_field(
                name="🔍 필터링 & 정보",
                value='\n'.join(filter_commands),
                inline=False
            )
            
            # 유틸리티 명령어
            utility_commands = [
                "`!핑` - 봇 응답 속도 확인"
            ]
            embed.add_field(
                name="🛠️ 유틸리티",
                value='\n'.join(utility_commands),
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
            
            # 사용 예시
            examples = [
                "`!등급별 전설` - 전설 등급만 보기",
                "`!타입별 카드` - 카드 아이템만 보기",
                "`!떠상검색 카드팩` - 카드팩 검색"
            ]
            embed.add_field(
                name="💡 사용 예시",
                value='\n'.join(examples),
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
        
        @self.bot.command(name='등급별', aliases=['등급', 'grade'])
        async def filter_by_grade(ctx, grade_name: str = None):
            """특정 등급의 아이템만 필터링해서 보기"""
            try:
                await self.refresh_data_if_needed()
                
                if not self.merchant_data:
                    await ctx.send("❌ 상인 데이터를 가져올 수 없습니다.")
                    return
                
                # 등급 매핑
                grade_aliases = {
                    '전설': '전설', 'legendary': '전설', '4': '전설',
                    '영웅': '영웅', 'epic': '영웅', '3': '영웅',
                    '희귀': '희귀', 'rare': '희귀', '2': '희귀',
                    '고급': '고급', 'uncommon': '고급', '1': '고급',
                    '일반': '일반', 'common': '일반', '0': '일반'
                }
                
                if not grade_name:
                    embed = discord.Embed(
                        title="📊 등급별 아이템 통계",
                        description="현재 활성 상인들의 등급별 아이템 현황",
                        color=0x7289da,
                        timestamp=datetime.now()
                    )
                    
                    # 등급별 카운트
                    grade_count = {'전설': 0, '영웅': 0, '희귀': 0, '고급': 0, '일반': 0}
                    for merchant in self.merchant_data:
                        for item in merchant['items']:
                            if item['grade'] in grade_count:
                                grade_count[item['grade']] += 1
                    
                    for grade, count in grade_count.items():
                        if count > 0:
                            embed.add_field(
                                name=f"🔸 {grade} 등급",
                                value=f"**{count}개**",
                                inline=True
                            )
                    
                    embed.add_field(
                        name="💡 사용법",
                        value="`!등급별 전설` - 전설 등급만 보기\n`!등급별 영웅` - 영웅 등급만 보기",
                        inline=False
                    )
                    
                    await ctx.send(embed=embed)
                    return
                
                # 등급 정규화
                target_grade = grade_aliases.get(grade_name.lower())
                if not target_grade:
                    await ctx.send(f"❌ 올바른 등급을 입력하세요: 전설, 영웅, 희귀, 고급, 일반")
                    return
                
                # 해당 등급 아이템을 가진 상인들 찾기
                filtered_merchants = []
                for merchant in self.merchant_data:
                    filtered_items = [item for item in merchant['items'] if item['grade'] == target_grade]
                    if filtered_items:
                        filtered_merchant = merchant.copy()
                        filtered_merchant['items'] = filtered_items
                        filtered_merchants.append(filtered_merchant)
                
                if not filtered_merchants:
                    embed = discord.Embed(
                        title=f"🔍 {target_grade} 등급 아이템 검색 결과",
                        description=f"현재 **{target_grade}** 등급 아이템을 파는 상인이 없습니다.",
                        color=0xff9900,
                        timestamp=datetime.now()
                    )
                else:
                    total_items = sum(len(m['items']) for m in filtered_merchants)
                    embed = discord.Embed(
                        title=f"🔍 {target_grade} 등급 아이템 검색 결과",
                        description=f"**{len(filtered_merchants)}명**의 상인이 **{total_items}개**의 {target_grade} 등급 아이템을 판매합니다.",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    for merchant in filtered_merchants:
                        region = merchant['region_name']
                        npc = merchant['npc_name']
                        
                        # 색상이 적용된 아이템 목록 생성
                        colored_items = self.format_items_for_discord(merchant['items'])
                        
                        item_chunks = [colored_items[i:i+2] for i in range(0, len(colored_items), 2)]
                        item_text = '\n'.join([' • '.join(chunk) for chunk in item_chunks])
                        
                        embed.add_field(
                            name=f"📍 {region} - {npc}",
                            value=f"```\n{item_text}```",
                            inline=False
                        )
                
                embed.set_footer(text="Selenium 기반 | 등급별 필터링")
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 등급별 검색 중 오류: {e}")
        
        @self.bot.command(name='타입별', aliases=['타입', 'type'])
        async def filter_by_type(ctx, type_name: str = None):
            """아이템 타입별로 필터링해서 보기"""
            try:
                await self.refresh_data_if_needed()
                
                if not self.merchant_data:
                    await ctx.send("❌ 상인 데이터를 가져올 수 없습니다.")
                    return
                
                # 타입 매핑
                type_aliases = {
                    '카드': 1, 'card': 1, '1': 1,
                    '호감도': 2, 'rapport': 2, '2': 2,
                    '특수': 3, 'special': 3, '3': 3
                }
                
                type_names = {1: '카드', 2: '호감도', 3: '특수'}
                
                if not type_name:
                    embed = discord.Embed(
                        title="📦 타입별 아이템 통계",
                        description="현재 활성 상인들의 타입별 아이템 현황",
                        color=0x7289da,
                        timestamp=datetime.now()
                    )
                    
                    # 타입별 카운트
                    type_count = {1: 0, 2: 0, 3: 0}
                    for merchant in self.merchant_data:
                        for item in merchant['items']:
                            if item['type'] in type_count:
                                type_count[item['type']] += 1
                    
                    for type_id, count in type_count.items():
                        if count > 0:
                            type_emoji = "🃏" if type_id == 1 else "💝" if type_id == 2 else "⭐"
                            embed.add_field(
                                name=f"{type_emoji} {type_names[type_id]}",
                                value=f"**{count}개**",
                                inline=True
                            )
                    
                    embed.add_field(
                        name="💡 사용법",
                        value="`!타입별 카드` - 카드만 보기\n`!타입별 호감도` - 호감도 아이템만 보기\n`!타입별 특수` - 특수 아이템만 보기",
                        inline=False
                    )
                    
                    await ctx.send(embed=embed)
                    return
                
                # 타입 정규화
                target_type = type_aliases.get(type_name.lower())
                if target_type is None:
                    await ctx.send(f"❌ 올바른 타입을 입력하세요: 카드, 호감도, 특수")
                    return
                
                # 해당 타입 아이템을 가진 상인들 찾기
                filtered_merchants = []
                for merchant in self.merchant_data:
                    filtered_items = [item for item in merchant['items'] if item['type'] == target_type]
                    if filtered_items:
                        filtered_merchant = merchant.copy()
                        filtered_merchant['items'] = filtered_items
                        filtered_merchants.append(filtered_merchant)
                
                type_emoji = "🃏" if target_type == 1 else "💝" if target_type == 2 else "⭐"
                target_type_name = type_names[target_type]
                
                if not filtered_merchants:
                    embed = discord.Embed(
                        title=f"🔍 {type_emoji} {target_type_name} 아이템 검색 결과",
                        description=f"현재 **{target_type_name}** 아이템을 파는 상인이 없습니다.",
                        color=0xff9900,
                        timestamp=datetime.now()
                    )
                else:
                    total_items = sum(len(m['items']) for m in filtered_merchants)
                    embed = discord.Embed(
                        title=f"🔍 {type_emoji} {target_type_name} 아이템 검색 결과",
                        description=f"**{len(filtered_merchants)}명**의 상인이 **{total_items}개**의 {target_type_name} 아이템을 판매합니다.",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    for merchant in filtered_merchants:
                        region = merchant['region_name']
                        npc = merchant['npc_name']
                        
                        # 색상이 적용된 아이템 목록 생성
                        colored_items = self.format_items_for_discord(merchant['items'])
                        
                        item_chunks = [colored_items[i:i+2] for i in range(0, len(colored_items), 2)]
                        item_text = '\n'.join([' • '.join(chunk) for chunk in item_chunks])
                        
                        embed.add_field(
                            name=f"📍 {region} - {npc}",
                            value=f"```\n{item_text}```",
                            inline=False
                        )
                
                embed.set_footer(text="Selenium 기반 | 타입별 필터링")
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 타입별 검색 중 오류: {e}")
        
        @self.bot.command(name='통계', aliases=['stats', 'statistics'])
        async def show_statistics(ctx):
            """상인 및 아이템 통계 정보"""
            try:
                await self.refresh_data_if_needed()
                
                if not self.merchant_data:
                    await ctx.send("❌ 상인 데이터를 가져올 수 없습니다.")
                    return
                
                embed = discord.Embed(
                    title="📊 떠돌이 상인 통계",
                    description="현재 활성 상인들의 상세 통계 정보",
                    color=0x7289da,
                    timestamp=datetime.now()
                )
                
                # 기본 통계
                total_merchants = len(self.merchant_data)
                total_items = sum(len(m['items']) for m in self.merchant_data)
                
                embed.add_field(
                    name="🏪 기본 정보",
                    value=f"```활성 상인: {total_merchants}명\n총 아이템: {total_items}개```",
                    inline=False
                )
                
                # 등급별 통계
                grade_count = {'전설': 0, '영웅': 0, '희귀': 0, '고급': 0, '일반': 0}
                for merchant in self.merchant_data:
                    for item in merchant['items']:
                        if item['grade'] in grade_count:
                            grade_count[item['grade']] += 1
                
                grade_stats = []
                for grade, count in grade_count.items():
                    if count > 0:
                        percentage = (count / total_items * 100) if total_items > 0 else 0
                        grade_stats.append(f"{grade}: {count}개 ({percentage:.1f}%)")
                
                if grade_stats:
                    embed.add_field(
                        name="🔸 등급별 분포",
                        value="```" + "\n".join(grade_stats) + "```",
                        inline=True
                    )
                
                # 타입별 통계
                type_count = {1: 0, 2: 0, 3: 0}
                type_names = {1: '카드', 2: '호감도', 3: '특수'}
                
                for merchant in self.merchant_data:
                    for item in merchant['items']:
                        if item['type'] in type_count:
                            type_count[item['type']] += 1
                
                type_stats = []
                for type_id, count in type_count.items():
                    if count > 0:
                        percentage = (count / total_items * 100) if total_items > 0 else 0
                        type_stats.append(f"{type_names[type_id]}: {count}개 ({percentage:.1f}%)")
                
                if type_stats:
                    embed.add_field(
                        name="📦 타입별 분포",
                        value="```" + "\n".join(type_stats) + "```",
                        inline=True
                    )
                
                # 지역별 통계
                region_count = {}
                for merchant in self.merchant_data:
                    region = merchant['region_name']
                    if region in region_count:
                        region_count[region] += 1
                    else:
                        region_count[region] = 1
                
                if region_count:
                    region_stats = [f"{region}: {count}명" for region, count in sorted(region_count.items())]
                    embed.add_field(
                        name="🗺️ 지역별 상인 수",
                        value="```" + "\n".join(region_stats) + "```",
                        inline=False
                    )
                
                # 업데이트 정보
                if self.last_data_update:
                    update_time = self.last_data_update.strftime("%H:%M:%S")
                    embed.set_footer(text=f"Selenium 기반 | 마지막 업데이트: {update_time}")
                else:
                    embed.set_footer(text="Selenium 기반 | 실시간 데이터")
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 통계 조회 중 오류: {e}")
        
        @self.bot.command(name='시간', aliases=['time', 'schedule'])
        async def show_schedule(ctx):
            """떠상 시간표 및 현재 상태"""
            try:
                now = datetime.now()
                current_hour = now.hour
                current_minute = now.minute
                
                embed = discord.Embed(
                    title="⏰ 떠돌이 상인 시간표",
                    description="떠돌이 상인 활성화 시간 및 현재 상태",
                    color=0x7289da,
                    timestamp=now
                )
                
                # 시간표
                schedules = [
                    ("🌅 새벽", "04:00 ~ 09:30"),
                    ("🌞 오전", "10:00 ~ 15:30"),
                    ("🌆 오후", "16:00 ~ 21:30"),
                    ("🌙 밤", "22:00 ~ 03:30")
                ]
                
                schedule_text = []
                for period, time_range in schedules:
                    schedule_text.append(f"{period} {time_range}")
                
                embed.add_field(
                    name="📅 활성화 시간표",
                    value="```" + "\n".join(schedule_text) + "```",
                    inline=False
                )
                
                # 현재 상태 확인
                current_status = "❌ 비활성"
                next_start = None
                current_end = None
                
                if (4 <= current_hour < 9) or (current_hour == 9 and current_minute <= 30):
                    current_status = "✅ 활성 (새벽 시간대)"
                    current_end = now.replace(hour=9, minute=30, second=0, microsecond=0)
                elif (10 <= current_hour < 15) or (current_hour == 15 and current_minute <= 30):
                    current_status = "✅ 활성 (오전 시간대)"
                    current_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
                elif (16 <= current_hour < 21) or (current_hour == 21 and current_minute <= 30):
                    current_status = "✅ 활성 (오후 시간대)"
                    current_end = now.replace(hour=21, minute=30, second=0, microsecond=0)
                elif current_hour >= 22 or current_hour < 4 or (current_hour == 3 and current_minute <= 30):
                    current_status = "✅ 활성 (밤 시간대)"
                    if current_hour >= 22:
                        current_end = (now + timedelta(days=1)).replace(hour=3, minute=30, second=0, microsecond=0)
                    else:
                        current_end = now.replace(hour=3, minute=30, second=0, microsecond=0)
                
                # 다음 시작 시간 계산
                if current_status == "❌ 비활성":
                    if current_hour < 4:
                        next_start = now.replace(hour=4, minute=0, second=0, microsecond=0)
                    elif current_hour < 10:
                        next_start = now.replace(hour=10, minute=0, second=0, microsecond=0)
                    elif current_hour < 16:
                        next_start = now.replace(hour=16, minute=0, second=0, microsecond=0)
                    elif current_hour < 22:
                        next_start = now.replace(hour=22, minute=0, second=0, microsecond=0)
                    else:
                        next_start = (now + timedelta(days=1)).replace(hour=4, minute=0, second=0, microsecond=0)
                
                embed.add_field(
                    name="🔄 현재 상태",
                    value=f"```{current_status}```",
                    inline=True
                )
                
                if current_end and now < current_end:
                    remaining = current_end - now
                    hours = remaining.seconds // 3600
                    minutes = (remaining.seconds % 3600) // 60
                    embed.add_field(
                        name="⏳ 마감까지",
                        value=f"```{hours}시간 {minutes}분```",
                        inline=True
                    )
                elif next_start:
                    remaining = next_start - now
                    if remaining.days > 0:
                        hours = remaining.seconds // 3600
                        embed.add_field(
                            name="⏳ 다음 시작까지",
                            value=f"```{remaining.days}일 {hours}시간```",
                            inline=True
                        )
                    else:
                        hours = remaining.seconds // 3600
                        minutes = (remaining.seconds % 3600) // 60
                        embed.add_field(
                            name="⏳ 다음 시작까지",
                            value=f"```{hours}시간 {minutes}분```",
                            inline=True
                        )
                
                embed.add_field(
                    name="💡 팁",
                    value="```• 마감 30분 전에 자동 알림\n• 5분마다 상인 상태 체크\n• !새로고침으로 수동 업데이트```",
                    inline=False
                )
                
                embed.set_footer(text="Selenium 기반 | 한국 시간 기준")
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 시간표 조회 중 오류: {e}")
        
        @self.bot.command(name='상인목록', aliases=['merchants', 'list'])
        async def list_merchants(ctx):
            """현재 활성 상인들의 간단한 목록"""
            try:
                await self.refresh_data_if_needed()
                
                if not self.merchant_data:
                    await ctx.send("❌ 상인 데이터를 가져올 수 없습니다.")
                    return
                
                if not self.merchant_data:
                    embed = discord.Embed(
                        title="🏪 활성 상인 목록",
                        description="현재 활성화된 상인이 없습니다.",
                        color=0x808080,
                        timestamp=datetime.now()
                    )
                else:
                    embed = discord.Embed(
                        title="🏪 활성 상인 목록",
                        description=f"현재 **{len(self.merchant_data)}명**의 상인이 활성화되어 있습니다.",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    merchant_list = []
                    for i, merchant in enumerate(self.merchant_data, 1):
                        region = merchant['region_name']
                        npc = merchant['npc_name']
                        item_count = len(merchant['items'])
                        
                        # 최고 등급 아이템 찾기
                        grade_priority = {'전설': 4, '영웅': 3, '희귀': 2, '고급': 1, '일반': 0}
                        best_grade = '일반'
                        for item in merchant['items']:
                            if grade_priority.get(item['grade'], 0) > grade_priority.get(best_grade, 0):
                                best_grade = item['grade']
                        
                        merchant_list.append(f"{i}. **{region}** - {npc} ({item_count}개, 최고: {best_grade})")
                    
                    # 10개씩 나누어서 표시
                    for i in range(0, len(merchant_list), 10):
                        chunk = merchant_list[i:i+10]
                        embed.add_field(
                            name=f"📋 상인 목록 ({i+1}-{min(i+10, len(merchant_list))})",
                            value='\n'.join(chunk),
                            inline=False
                        )
                
                embed.add_field(
                    name="💡 상세 정보",
                    value="`!떠상` - 모든 아이템 보기\n`!떠상검색 아이템명` - 특정 아이템 검색",
                    inline=False
                )
                
                embed.set_footer(text="Selenium 기반 | 간단한 상인 목록")
                await ctx.send(embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ 상인 목록 조회 중 오류: {e}")
    
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
                    
                    # 색상이 적용된 아이템 목록 생성
                    colored_items = self.format_items_for_discord(merchant['items'])
                    
                    # 아이템을 2개씩 나누어 표시
                    item_chunks = [colored_items[i:i+2] for i in range(0, len(colored_items), 2)]
                    item_text = '\n'.join([' • '.join(chunk) for chunk in item_chunks])
                    
                    embed.add_field(
                        name=f"📍 {region} - {npc}",
                        value=f"```\n{item_text}```",
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

# ============================================================================
# 로스트아크 캐릭터 정보 조회 기능 (떠돌이상인 봇과 구분)
# ============================================================================

import requests
import urllib.parse

class LostArkCharacterAPI:
    """로스트아크 캐릭터 정보 조회 API 클래스"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://developer-lostark.game.onstove.com"
        self.headers = {
            'accept': 'application/json',
            'authorization': f'bearer {api_key}'
        }
    
    async def get_character_info(self, character_name: str) -> Optional[Dict]:
        """캐릭터 기본 정보 조회"""
        try:
            encoded_name = urllib.parse.quote(character_name)
            url = f"{self.base_url}/characters/{encoded_name}"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"API 오류: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"캐릭터 정보 조회 오류: {e}")
            return None
    
    async def get_character_siblings(self, character_name: str) -> Optional[List[Dict]]:
        """캐릭터 원정대 정보 조회"""
        try:
            encoded_name = urllib.parse.quote(character_name)
            url = f"{self.base_url}/characters/{encoded_name}/siblings"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"API 오류: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"원정대 정보 조회 오류: {e}")
            return None

class CharacterInfoBot:
    """캐릭터 정보 조회 디스코드 봇 (떠돌이상인 봇과 별도)"""
    
    def __init__(self, discord_token: str, lostark_api_key: str):
        self.discord_token = discord_token
        self.lostark_api = LostArkCharacterAPI(lostark_api_key)
        
        # Discord 봇 설정
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='/', intents=intents)
        
        self.setup_commands()
    
    def setup_commands(self):
        """디스코드 명령어 설정"""
        
        @self.bot.event
        async def on_ready():
            print(f'✅ 캐릭터 정보 봇 로그인: {self.bot.user}')
        
        @self.bot.command(name='캐릭터정보')
        async def character_info(ctx, *, character_name: str = None):
            """캐릭터 정보 조회 명령어"""
            if not character_name:
                await ctx.send("❌ 캐릭터명을 입력해주세요!\n사용법: `/캐릭터정보 캐릭터명`")
                return
            
            # 로딩 메시지
            loading_msg = await ctx.send(f"🔍 `{character_name}` 캐릭터 정보를 조회중...")
            
            try:
                # 캐릭터 기본 정보 조회
                char_info = await self.lostark_api.get_character_info(character_name)
                
                if not char_info:
                    await loading_msg.edit(content=f"❌ `{character_name}` 캐릭터를 찾을 수 없습니다.")
                    return
                
                # 원정대 정보 조회
                siblings_info = await self.lostark_api.get_character_siblings(character_name)
                
                # Discord Embed 생성
                embed = await self.create_character_embed(char_info, siblings_info)
                
                await loading_msg.edit(content="", embed=embed)
                
            except Exception as e:
                await loading_msg.edit(content=f"❌ 오류가 발생했습니다: {str(e)}")
                print(f"캐릭터 정보 조회 오류: {e}")
    
    async def create_character_embed(self, char_info: Dict, siblings_info: Optional[List[Dict]]) -> discord.Embed:
        """캐릭터 정보 Discord Embed 생성"""
        
        # 기본 정보
        char_name = char_info.get('CharacterName', 'Unknown')
        server_name = char_info.get('ServerName', 'Unknown')
        char_class = char_info.get('CharacterClassName', 'Unknown')
        char_level = char_info.get('CharacterLevel', 0)
        item_level = char_info.get('ItemAvgLevel', 'Unknown')
        item_max_level = char_info.get('ItemMaxLevel', 'Unknown')
        
        # Embed 생성
        embed = discord.Embed(
            title=f"⚔️ {char_name}",
            description=f"**{server_name}** 서버의 **{char_class}**",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        # 기본 정보 필드
        embed.add_field(
            name="📊 기본 정보",
            value=f"```\n레벨: {char_level}\n평균 아이템레벨: {item_level}\n최고 아이템레벨: {item_max_level}```",
            inline=False
        )
        
        # 원정대 정보 (있는 경우)
        if siblings_info and len(siblings_info) > 0:
            expedition_text = ""
            for sibling in siblings_info[:10]:  # 최대 10개만 표시
                sib_name = sibling.get('CharacterName', 'Unknown')
                sib_class = sibling.get('CharacterClassName', 'Unknown')
                sib_level = sibling.get('ItemAvgLevel', 'Unknown')
                expedition_text += f"{sib_name} ({sib_class}) - {sib_level}\n"
            
            if expedition_text:
                embed.add_field(
                    name="👥 원정대 캐릭터",
                    value=f"```\n{expedition_text}```",
                    inline=False
                )
        
        embed.set_footer(text="로스트아크 공식 API | 캐릭터 정보 조회")
        
        return embed
    
    def run(self):
        """봇 실행"""
        try:
            self.bot.run(self.discord_token)
        except Exception as e:
            print(f"❌ 캐릭터 정보 봇 실행 오류: {e}")

# ============================================================================
# 통합 봇 실행 함수 (떠돌이상인 + 캐릭터정보)
# ============================================================================

def main_character_bot():
    """캐릭터 정보 봇만 실행"""
    print("🚀 로스트아크 캐릭터 정보 봇 시작")
    print("=" * 60)
    print("기능: 캐릭터 정보 조회 (/캐릭터정보 명령어)")
    print("=" * 60)
    
    # Discord 봇 토큰 입력
    discord_token = input("Discord 봇 토큰을 입력하세요: ").strip()
    if not discord_token:
        print("❌ Discord 봇 토큰이 필요합니다!")
        return
    
    # 로스트아크 API 키 입력
    lostark_api_key = input("로스트아크 API 키를 입력하세요: ").strip()
    if not lostark_api_key:
        print("❌ 로스트아크 API 키가 필요합니다!")
        return
    
    print(f"✅ 설정 완료:")
    print(f"   - 캐릭터 정보 조회: /캐릭터정보 명령어")
    print(f"   - 데이터 소스: 로스트아크 공식 API")
    
    # 캐릭터정보 봇 실행
    character_bot = CharacterInfoBot(discord_token, lostark_api_key)
    character_bot.run()

def main_integrated():
    """통합 봇 선택 메뉴"""
    print("🚀 로스트아크 봇 선택")
    print("=" * 60)
    print("사용 가능한 봇:")
    print("1. 떠돌이상인 봇 (Selenium 기반)")
    print("2. 캐릭터 정보 조회 봇 (API 기반)")
    print("=" * 60)
    
    choice = input("실행할 봇을 선택하세요 (1-2): ").strip()
    
    if choice == "1":
        # 기존 떠돌이상인 봇 실행
        main()
    elif choice == "2":
        # 캐릭터정보 봇 실행
        main_character_bot()
    else:
        print("❌ 잘못된 선택입니다.")
        return

# 기존 main 함수는 그대로 유지 (떠돌이상인 봇)
