#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 로스트아크 디스코드 봇 (슬래시 명령어 버전)
- 떠돌이상인 실시간 알림 (Selenium 기반)
- 캐릭터 정보 조회 (로스트아크 API 기반)
"""

import json
import time
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Optional
import pytz
import requests
import urllib.parse

# Selenium 관련
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Discord 봇 관련 (슬래시 명령어용)
import discord
from discord.ext import commands, tasks
from discord import app_commands

# ============================================================================
# Selenium 떠돌이상인 데이터 수집 클래스
# ============================================================================

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
        """Selenium으로 떠상 데이터 가져오기"""
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
                    # 서버명 확인
                    server_element = merchant_div.find_element(By.CSS_SELECTOR, "p.text-sm.font-medium.text-bola")
                    server_name = server_element.text.strip()
                    
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
                            
                            if grade_attr is not None and grade_attr.strip() != "":
                                try:
                                    grade_num = int(grade_attr)
                                except ValueError:
                                    grade_num = 3
                            else:
                                grade_num = 3
                            
                            # 등급 숫자를 텍스트로 변환
                            grade_map = {
                                4: "전설",
                                3: "영웅", 
                                2: "희귀",
                                1: "고급",
                                0: "일반"
                            }
                            grade = grade_map.get(grade_num, "영웅")
                            
                            # 아이템명 추출
                            item_name = item_element.text.strip()
                            
                            # 아이템 타입 추출
                            img_element = item_element.find_element(By.TAG_NAME, "img")
                            item_type_title = img_element.get_attribute("title")
                            
                            # 타입 매핑
                            if "카드" in item_type_title:
                                item_type = 1
                            elif "호감도" in item_type_title:
                                item_type = 2
                            else:
                                item_type = 3  # 특수 아이템
                            
                            if item_name:
                                items.append({
                                    'name': item_name,
                                    'type': item_type,
                                    'grade': grade,
                                    'hidden': False
                                })
                        
                        except Exception as e:
                            print(f"아이템 파싱 오류: {e}")
                            continue
                    
                    if items:
                        merchant_info = {
                            'region_name': region_name,
                            'npc_name': npc_name,
                            'group': 1,
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
        """현재 활성화된 상인들 가져오기"""
        try:
            print("🔄 Selenium으로 실시간 데이터 가져오는 중...")
            
            merchants_data = self.fetch_merchant_data_selenium()
            if not merchants_data:
                return []
            
            print(f"✅ 니나브 서버 상인 {len(merchants_data)}명 발견")
            return merchants_data
            
        except Exception as e:
            print(f"❌ 실시간 데이터 가져오기 실패: {e}")
            return []

# ============================================================================
# 로스트아크 캐릭터 정보 조회 API 클래스
# ============================================================================

class LostArkCharacterAPI:
    """로스트아크 캐릭터 정보 조회 API 클래스"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://developer-lostark.game.onstove.com"
        self.headers = {
            'accept': 'application/json',
            'authorization': f'Bearer {api_key}'  # Bearer의 B를 대문자로!
        }
    
    async def get_character_info(self, character_name: str) -> Optional[Dict]:
        """캐릭터 기본 정보 조회"""
        try:
            encoded_name = urllib.parse.quote(character_name)
            url = f"{self.base_url}/characters/{encoded_name}/siblings"
            
            print(f"🔍 API 요청: {url}")
            print(f"🔑 API 키: {self.api_key[:10]}...")
            
            response = requests.get(url, headers=self.headers)
            
            print(f"📡 응답 상태: {response.status_code}")
            print(f"📄 응답 헤더: {dict(response.headers)}")
            print(f"📝 응답 내용 (처음 200자): {response.text[:200]}")
            
            if response.status_code == 200:
                # 응답이 비어있는지 확인
                if not response.text or response.text.strip() == "":
                    print("❌ 빈 응답 받음")
                    return None
                
                try:
                    data = response.json()
                    print(f"✅ 캐릭터 정보 조회 성공: {data.get('CharacterName', 'Unknown')}")
                    return data
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 오류: {e}")
                    print(f"전체 응답 내용: {response.text}")
                    return None
                    
            elif response.status_code == 404:
                print(f"❌ 캐릭터 '{character_name}'를 찾을 수 없음")
                return None
            elif response.status_code == 401:
                print(f"❌ API 키 인증 실패")
                return None
            elif response.status_code == 429:
                print(f"❌ API 요청 한도 초과")
                return None
            else:
                print(f"❌ API 오류: {response.status_code}")
                print(f"응답 내용: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 캐릭터 정보 조회 오류: {e}")
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

# ============================================================================
# 통합 로스트아크 디스코드 봇 (떠돌이상인 + 캐릭터정보)
# ============================================================================

class IntegratedLostArkBot:
    """통합 로스트아크 디스코드 봇 (슬래시 명령어 버전)"""
    
    def __init__(self, discord_token: str, lostark_api_key: str = None):
        self.discord_token = discord_token
        self.lostark_api_key = lostark_api_key
        
        # Discord 봇 설정 (슬래시 명령어용)
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)  # prefix는 슬래시 명령어에서 사용안함
        
        # 서버별 알림 채널 설정 (여러 서버 지원)
        self.merchant_channels = {}  # {guild_id: channel_id}
        
        # 로스트아크 API 초기화 (API 키가 있는 경우)
        if self.lostark_api_key:
            self.lostark_api = LostArkCharacterAPI(self.lostark_api_key)
        else:
            self.lostark_api = None
        
        # Selenium 떠돌이상인 데이터 가져오기 초기화
        self.merchant_fetcher = SeleniumMerchantFetcher()
        
        # 떠돌이상인 관련 변수들
        self.merchant_data = None
        self.last_data_update = None
        self.last_notification = None
        
        self.setup_commands()
    
    def format_item_with_color(self, item):
        """아이템을 등급별 색깔로 포맷팅"""
        grade = item['grade']
        name = item['name']
        
        # 등급별 이모지 추가
        grade_emoji = {
            "전설": "🟠",
            "영웅": "🟣", 
            "희귀": "🔵",
            "고급": "🟢",
            "일반": "⚪"
        }
        
        emoji = grade_emoji.get(grade, "⚪")
        return f"{emoji} {name}"
    
    def format_items_for_discord(self, items):
        """Discord용 아이템 목록 포맷팅"""
        formatted_items = []
        for item in items:
            formatted_items.append(self.format_item_with_color(item))
        return formatted_items
    
    async def load_merchant_data(self) -> bool:
        """Selenium으로 상인 데이터 로드"""
        try:
            print("🔄 Selenium으로 상인 데이터 가져오는 중...")
            
            merchant_data = self.merchant_fetcher.get_current_active_merchants()
            
            if merchant_data:
                self.merchant_data = merchant_data
                self.last_data_update = datetime.now()
                print(f"✅ Selenium 데이터 로드 성공: {len(merchant_data)}명의 상인")
                return True
            else:
                print("❌ Selenium 데이터 로드 실패")
                return False
                
        except Exception as e:
            print(f"❌ Selenium 데이터 로드 오류: {e}")
            return False
    
    async def refresh_data_if_needed(self):
        """필요시 데이터 자동 새로고침 (30분마다)"""
        try:
            now = datetime.now()
            
            if (self.merchant_data is None or 
                self.last_data_update is None or 
                (now - self.last_data_update).total_seconds() > 1800):  # 30분
                
                print("🔄 데이터 자동 새로고침...")
                await self.load_merchant_data()
                
        except Exception as e:
            print(f"❌ 자동 새로고침 오류: {e}")
    
    @tasks.loop(minutes=5)
    async def check_merchants(self):
        """5분마다 상인 상태 확인 및 데이터 변경시에만 알림"""
        try:
            # 알림 채널이 설정된 서버가 없으면 체크만 하고 알림은 보내지 않음
            if not self.merchant_channels:
                # 데이터만 새로고침
                await self.refresh_data_if_needed()
                return
            
            # 이전 데이터 백업
            previous_data = self.merchant_data.copy() if self.merchant_data else None
            
            # 데이터 새로고침
            await self.refresh_data_if_needed()
            
            # 데이터 변경 감지
            data_changed = self.has_merchant_data_changed(previous_data, self.merchant_data)
            
            if data_changed:
                now = datetime.now()
                
                # 상인이 새로 등장하거나 변경된 경우
                if self.merchant_data and len(self.merchant_data) > 0:
                    # 처음 등장인지 변경인지 구분
                    if not previous_data or len(previous_data) == 0:
                        title = "🚨 떠돌이 상인 등장 알림"
                        description = f"떠돌이 상인이 등장했습니다! 현재 **{len(self.merchant_data)}명**의 상인이 활성화되어 있습니다."
                    else:
                        title = "🔄 떠돌이 상인 변경 알림"
                        description = f"상인 정보가 업데이트되었습니다! 현재 **{len(self.merchant_data)}명**의 상인이 활성화되어 있습니다."
                    
                    embed = discord.Embed(
                        title=title,
                        description=description,
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
                    
                    embed.set_footer(text="통합 봇 | 상인 정보 알림")
                    
                    # 모든 등록된 서버에 알림 전송
                    await self.send_notification_to_all_servers(embed)
                    self.last_notification = now
                    print(f"✅ 상인 알림 전송: {len(self.merchant_data)}명 → {len(self.merchant_channels)}개 서버")
                
                # 상인이 모두 사라진 경우
                elif previous_data and len(previous_data) > 0:
                    embed = discord.Embed(
                        title="📴 떠돌이 상인 종료 알림",
                        description="모든 떠돌이 상인이 비활성화되었습니다.",
                        color=0x808080,
                        timestamp=now
                    )
                    embed.set_footer(text="통합 봇 | 상인 종료 알림")
                    
                    # 모든 등록된 서버에 알림 전송
                    await self.send_notification_to_all_servers(embed)
                    print(f"✅ 상인 종료 알림 전송 → {len(self.merchant_channels)}개 서버")
            
        except Exception as e:
            print(f"❌ 상인 체크 오류: {e}")
    
    async def send_notification_to_all_servers(self, embed):
        """모든 등록된 서버에 알림 전송"""
        failed_channels = []
        
        for guild_id, channel_id in self.merchant_channels.items():
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)
                else:
                    failed_channels.append(guild_id)
                    print(f"⚠️ 채널을 찾을 수 없음: {channel_id} (서버: {guild_id})")
            except Exception as e:
                failed_channels.append(guild_id)
                print(f"❌ 알림 전송 실패: {channel_id} (서버: {guild_id}) - {e}")
        
        # 실패한 채널들 제거
        for guild_id in failed_channels:
            del self.merchant_channels[guild_id]
    
    def has_merchant_data_changed(self, previous_data, current_data):
        """상인 데이터 변경 여부 확인"""
        try:
            # 이전 데이터가 없고 현재 데이터가 있으면 = 처음 상인 등장
            if not previous_data and current_data and len(current_data) > 0:
                return True
            
            # 둘 다 None이거나 빈 리스트인 경우 = 변경 없음
            if not previous_data and not current_data:
                return False
            
            # 이전에 데이터가 있었는데 현재 없으면 = 상인 모두 사라짐
            if previous_data and len(previous_data) > 0 and (not current_data or len(current_data) == 0):
                return True
            
            # 현재 데이터가 없으면 변경 없음
            if not current_data:
                return False
            
            # 상인 수가 다른 경우
            if len(previous_data) != len(current_data):
                return True
            
            # 각 상인의 정보를 비교
            for prev_merchant in previous_data:
                # 현재 데이터에서 같은 상인 찾기
                current_merchant = None
                for curr_merchant in current_data:
                    if (curr_merchant.get('region_name') == prev_merchant.get('region_name') and 
                        curr_merchant.get('npc_name') == prev_merchant.get('npc_name')):
                        current_merchant = curr_merchant
                        break
                
                # 상인이 사라진 경우
                if not current_merchant:
                    return True
                
                # 아이템 목록 비교
                prev_items = set(item['name'] for item in prev_merchant.get('items', []))
                curr_items = set(item['name'] for item in current_merchant.get('items', []))
                
                if prev_items != curr_items:
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ 데이터 변경 감지 오류: {e}")
            return True  # 오류 발생시 변경된 것으로 간주
    
    def setup_commands(self):
        """슬래시 명령어 설정"""
        
        @self.bot.event
        async def on_ready():
            print(f'✅ 통합 로스트아크 봇 로그인: {self.bot.user}')
            print('=' * 60)
            print('기능:')
            print('📍 떠돌이상인 실시간 알림 (Selenium 기반)')
            if self.lostark_api:
                print('⚔️  캐릭터 정보 조회 (로스트아크 API)')
            print('=' * 60)
            
            # 슬래시 명령어 강제 동기화
            try:
                print("🔄 슬래시 명령어 동기화 중...")
                
                # 글로벌 동기화 (모든 서버에 적용, 최대 1시간 소요)
                synced = await self.bot.tree.sync()
                print(f"✅ {len(synced)}개의 글로벌 슬래시 명령어가 동기화되었습니다.")
                
                # 동기화된 명령어 목록 출력
                for cmd in synced:
                    print(f"   - /{cmd.name}: {cmd.description}")
                
            except Exception as e:
                print(f"❌ 슬래시 명령어 동기화 실패: {e}")
            
            print('=' * 60)
            print('사용 가능한 슬래시 명령어:')
            print('📍 떠돌이상인: /떠상, /새로고침, /떠상검색')
            if self.lostark_api:
                print('⚔️  캐릭터정보: /캐릭터정보')
            print('❓ 도움말: /도움말')
            print('=' * 60)
            print('⚠️  슬래시 명령어가 나타나지 않으면 최대 1시간 기다려주세요.')
            print('⚠️  또는 Discord 앱을 재시작해보세요.')
            print('=' * 60)
            
            # 초기 데이터 로드
            await self.load_merchant_data()
            
            # 주기적 체크 시작
            self.check_merchants.start()
        
        # ============================================================================
        # 떠돌이상인 슬래시 명령어들
        # ============================================================================
        
        @self.bot.tree.command(name="떠상", description="현재 활성화된 떠돌이상인을 확인합니다")
        async def merchant_info(interaction: discord.Interaction):
            """현재 활성 떠돌이상인 확인"""
            try:
                await interaction.response.defer()  # 응답 지연 (처리 시간이 길 수 있음)
                
                # 최신 데이터 확인
                await self.refresh_data_if_needed()
                
                if not self.merchant_data:
                    embed = discord.Embed(
                        title="🏪 떠돌이 상인",
                        description="상인 데이터를 가져올 수 없습니다.",
                        color=0xff0000,
                        timestamp=datetime.now()
                    )
                    await interaction.followup.send(embed=embed)
                    return
                
                if len(self.merchant_data) == 0:
                    embed = discord.Embed(
                        title="🏪 떠돌이 상인",
                        description="현재 활성화된 상인이 없습니다.",
                        color=0x808080,
                        timestamp=datetime.now()
                    )
                else:
                    embed = discord.Embed(
                        title="🏪 떠돌이 상인",
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
                            value=f"{item_text}",
                            inline=False
                        )
                
                # 데이터 업데이트 시간 표시
                if self.last_data_update:
                    update_time = self.last_data_update.strftime("%H:%M:%S")
                    embed.set_footer(text=f"통합 봇 | 데이터 업데이트: {update_time}")
                else:
                    embed.set_footer(text="통합 봇 | 실시간 데이터")
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                await interaction.followup.send(f"❌ 오류가 발생했습니다: {e}")
        
        @self.bot.tree.command(name="새로고침", description="떠돌이상인 데이터를 새로고침합니다")
        async def refresh_data(interaction: discord.Interaction):
            """데이터 새로고침"""
            try:
                await interaction.response.defer()
                
                success = await self.load_merchant_data()
                
                if success and self.merchant_data:
                    embed = discord.Embed(
                        title="✅ 데이터 새로고침 완료",
                        description=f"상인 데이터를 성공적으로 업데이트했습니다.",
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
                        description="데이터를 가져올 수 없습니다.",
                        color=0xff0000,
                        timestamp=datetime.now()
                    )
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                await interaction.followup.send(f"❌ 새로고침 오류: {e}")
        
        @self.bot.tree.command(name="떠상검색", description="특정 아이템을 판매하는 떠돌이상인을 검색합니다")
        @app_commands.describe(아이템명="검색할 아이템 이름")
        async def search_item(interaction: discord.Interaction, 아이템명: str):
            """아이템으로 상인 검색"""
            try:
                await interaction.response.defer()
                
                await self.refresh_data_if_needed()
                
                if not self.merchant_data:
                    await interaction.followup.send("❌ 상인 데이터를 가져올 수 없습니다.")
                    return
                
                # 아이템 검색
                found_merchants = []
                for merchant in self.merchant_data:
                    for item in merchant['items']:
                        if 아이템명.lower() in item['name'].lower():
                            found_merchants.append({
                                'merchant': merchant,
                                'item': item
                            })
                            break
                
                if not found_merchants:
                    embed = discord.Embed(
                        title="🔍 아이템 검색 결과",
                        description=f"`{아이템명}` 아이템을 판매하는 상인을 찾을 수 없습니다.",
                        color=0x808080,
                        timestamp=datetime.now()
                    )
                else:
                    embed = discord.Embed(
                        title="🔍 아이템 검색 결과",
                        description=f"`{아이템명}` 검색 결과: **{len(found_merchants)}명**의 상인이 발견되었습니다.",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    for result in found_merchants:
                        merchant = result['merchant']
                        region = merchant['region_name']
                        npc = merchant['npc_name']
                        
                        # 해당 상인의 모든 아이템 표시
                        colored_items = self.format_items_for_discord(merchant['items'])
                        item_text = ' • '.join(colored_items)
                        
                        embed.add_field(
                            name=f"📍 {region} - {npc}",
                            value=item_text,
                            inline=False
                        )
                
                embed.set_footer(text="통합 봇 | 아이템 검색")
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                await interaction.followup.send(f"❌ 검색 오류: {e}")
        
        # ============================================================================
        # 캐릭터 정보 조회 슬래시 명령어
        # ============================================================================
        
        @self.bot.tree.command(name="캐릭터정보", description="로스트아크 캐릭터 정보를 조회합니다")
        @app_commands.describe(캐릭터명="조회할 캐릭터 이름")
        async def character_info(interaction: discord.Interaction, 캐릭터명: str):
            """캐릭터 정보 조회 명령어 (siblings에서 해당 캐릭터 찾기)"""
            if not self.lostark_api:
                await interaction.response.send_message("❌ 로스트아크 API 키가 설정되지 않았습니다!", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            try:
                # 디버깅 정보 출력
                print(f"🔍 캐릭터 조회 요청: '{캐릭터명}'")
                
                # siblings 정보 조회 (기본 정보)
                siblings_info = await self.lostark_api.get_character_siblings(캐릭터명)
                
                if not siblings_info:
                    await interaction.followup.send(
                        f"❌ `{캐릭터명}` 캐릭터를 찾을 수 없습니다.\n\n"
                        f"**확인사항:**\n"
                        f"• 캐릭터명이 정확한지 확인해주세요\n"
                        f"• 대소문자를 정확히 입력했는지 확인해주세요\n"
                        f"• 해당 캐릭터가 실제로 존재하는지 확인해주세요"
                    )
                    return
                
                # siblings 리스트에서 입력한 캐릭터명과 일치하는 캐릭터 찾기
                target_character = None
                for sibling in siblings_info:
                    if sibling.get('CharacterName') == 캐릭터명:
                        target_character = sibling
                        break
                
                if not target_character:
                    await interaction.followup.send(f"❌ 원정대에서 `{캐릭터명}` 캐릭터를 찾을 수 없습니다.")
                    return
                
                # Discord Embed 생성 (해당 캐릭터 정보만)
                embed = await self.create_character_embed_from_sibling(target_character, siblings_info)
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                await interaction.followup.send(f"❌ 오류가 발생했습니다: {str(e)}")
                print(f"캐릭터 정보 조회 오류: {e}")
        
        @self.bot.tree.command(name="원정대정보", description="로스트아크 원정대의 모든 캐릭터 정보를 조회합니다")
        @app_commands.describe(캐릭터명="원정대를 조회할 캐릭터 이름")
        async def expedition_info(interaction: discord.Interaction, 캐릭터명: str):
            """원정대 정보 조회 명령어 (siblings 전체 데이터)"""
            if not self.lostark_api:
                await interaction.response.send_message("❌ 로스트아크 API 키가 설정되지 않았습니다!", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            try:
                print(f"🔍 원정대 조회 요청: '{캐릭터명}'")
                
                # siblings 정보 조회
                siblings_info = await self.lostark_api.get_character_siblings(캐릭터명)
                
                if not siblings_info:
                    await interaction.followup.send(f"❌ `{캐릭터명}` 캐릭터의 원정대 정보를 찾을 수 없습니다.")
                    return
                
                # 원정대 전체 정보 Embed 생성
                embed = await self.create_expedition_embed(siblings_info, 캐릭터명)
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                await interaction.followup.send(f"❌ 오류가 발생했습니다: {str(e)}")
                print(f"원정대 정보 조회 오류: {e}")
        
        @self.bot.tree.command(name="동기화", description="[개발자용] 슬래시 명령어를 강제 동기화합니다")
        async def sync_commands(interaction: discord.Interaction):
            """개발자용 동기화 명령어"""
            # 봇 소유자만 사용 가능하도록 제한
            if interaction.user.id != interaction.guild.owner_id:
                await interaction.response.send_message("❌ 이 명령어는 서버 관리자만 사용할 수 있습니다.", ephemeral=True)
                return
            
            await interaction.response.defer(ephemeral=True)
            
            try:
                synced = await self.bot.tree.sync()
                await interaction.followup.send(f"✅ {len(synced)}개의 슬래시 명령어가 동기화되었습니다!\n명령어 목록: {', '.join([cmd.name for cmd in synced])}", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ 동기화 실패: {e}", ephemeral=True)
        
        @self.bot.tree.command(name="알림설정", description="현재 채널을 떠돌이상인 자동 알림 채널로 설정합니다")
        async def set_notification_channel(interaction: discord.Interaction):
            """알림 채널 설정 명령어 (관리자만 사용 가능)"""
            # 관리자 권한 확인
            if not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("❌ 이 명령어는 채널 관리 권한이 있는 사용자만 사용할 수 있습니다.", ephemeral=True)
                return
            
            guild_id = interaction.guild_id
            channel_id = interaction.channel_id
            channel_name = interaction.channel.name
            
            # 알림 채널 설정
            self.merchant_channels[guild_id] = channel_id
            
            embed = discord.Embed(
                title="✅ 알림 채널 설정 완료",
                description=f"**#{channel_name}** 채널이 떠돌이상인 자동 알림 채널로 설정되었습니다.",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 설정 정보",
                value=f"```\n서버: {interaction.guild.name}\n채널: #{channel_name}\n설정자: {interaction.user.display_name}```",
                inline=False
            )
            
            embed.add_field(
                name="🔔 알림 안내",
                value="이제 떠돌이상인 정보가 변경될 때마다 이 채널로 자동 알림이 전송됩니다.",
                inline=False
            )
            
            embed.set_footer(text="통합 봇 | 알림 채널 설정")
            await interaction.response.send_message(embed=embed)
            
            print(f"✅ 알림 채널 설정: {interaction.guild.name} - #{channel_name} ({channel_id})")
        
        @self.bot.tree.command(name="알림해제", description="떠돌이상인 자동 알림을 해제합니다")
        async def remove_notification_channel(interaction: discord.Interaction):
            """알림 해제 명령어 (관리자만 사용 가능)"""
            # 관리자 권한 확인
            if not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("❌ 이 명령어는 채널 관리 권한이 있는 사용자만 사용할 수 있습니다.", ephemeral=True)
                return
            
            guild_id = interaction.guild_id
            
            if guild_id in self.merchant_channels:
                del self.merchant_channels[guild_id]
                
                embed = discord.Embed(
                    title="✅ 알림 해제 완료",
                    description="떠돌이상인 자동 알림이 해제되었습니다.",
                    color=0xff9900,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📋 안내",
                    value="더 이상 자동 알림을 받지 않습니다.\n`/알림설정` 명령어로 언제든 다시 설정할 수 있습니다.",
                    inline=False
                )
                
                embed.set_footer(text="통합 봇 | 알림 해제")
                await interaction.response.send_message(embed=embed)
                
                print(f"✅ 알림 해제: {interaction.guild.name}")
            else:
                await interaction.response.send_message("❌ 현재 설정된 알림 채널이 없습니다.", ephemeral=True)
        
        @self.bot.tree.command(name="알림상태", description="현재 설정된 알림 채널 정보를 확인합니다")
        async def check_notification_status(interaction: discord.Interaction):
            """알림 상태 확인 명령어"""
            guild_id = interaction.guild_id
            
            if guild_id in self.merchant_channels:
                channel_id = self.merchant_channels[guild_id]
                channel = self.bot.get_channel(channel_id)
                
                if channel:
                    embed = discord.Embed(
                        title="🔔 알림 상태",
                        description="떠돌이상인 자동 알림이 **활성화**되어 있습니다.",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="📍 알림 채널",
                        value=f"<#{channel_id}> (#{channel.name})",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="📊 등록된 서버 수",
                        value=f"현재 **{len(self.merchant_channels)}개** 서버에서 알림을 사용 중입니다.",
                        inline=False
                    )
                else:
                    # 채널이 삭제된 경우
                    del self.merchant_channels[guild_id]
                    embed = discord.Embed(
                        title="⚠️ 알림 채널 오류",
                        description="설정된 알림 채널이 삭제되었습니다.\n`/알림설정` 명령어로 다시 설정해주세요.",
                        color=0xff9900,
                        timestamp=datetime.now()
                    )
            else:
                embed = discord.Embed(
                    title="📴 알림 비활성화",
                    description="떠돌이상인 자동 알림이 설정되지 않았습니다.",
                    color=0x808080,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="💡 알림 설정 방법",
                    value="`/알림설정` 명령어를 사용하여 현재 채널을 알림 채널로 설정할 수 있습니다.",
                    inline=False
                )
            
            embed.set_footer(text="통합 봇 | 알림 상태 확인")
            await interaction.response.send_message(embed=embed)
        
        @self.bot.tree.command(name="도움말", description="봇의 모든 명령어를 확인합니다")
        async def help_command(interaction: discord.Interaction):
            """도움말 명령어"""
            embed = discord.Embed(
                title="🎮 통합 로스트아크 봇",
                description="떠돌이상인 알림과 캐릭터 정보 조회를 제공하는 봇입니다.",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📍 떠돌이상인 명령어",
                value="`/떠상` - 현재 활성 상인 확인\n`/새로고침` - 데이터 새로고침\n`/떠상검색` - 아이템으로 상인 검색",
                inline=False
            )
            
            embed.add_field(
                name="🔔 알림 설정 명령어",
                value="`/알림설정` - 현재 채널을 알림 채널로 설정 (관리자)\n`/알림해제` - 자동 알림 해제 (관리자)\n`/알림상태` - 알림 설정 상태 확인",
                inline=False
            )
            
            if self.lostark_api:
                embed.add_field(
                    name="⚔️ 캐릭터 정보 명령어",
                    value="`/캐릭터정보` - 특정 캐릭터 정보 조회\n`/원정대정보` - 원정대 전체 캐릭터 조회",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚔️ 캐릭터 정보 명령어",
                    value="❌ API 키가 설정되지 않음",
                    inline=False
                )
            
            embed.add_field(
                name="💡 사용 예시",
                value="`/알림설정` - 자동 알림 설정\n`/떠상` - 상인 정보 확인\n`/떠상검색 아이템명:실링`\n`/캐릭터정보 캐릭터명:유우니유니`",
                inline=False
            )
            
            # 현재 서버의 알림 상태 표시
            guild_id = interaction.guild_id
            if guild_id in self.merchant_channels:
                channel_id = self.merchant_channels[guild_id]
                embed.add_field(
                    name="🔔 현재 서버 알림 상태",
                    value=f"✅ 활성화됨 - <#{channel_id}>",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🔔 현재 서버 알림 상태",
                    value="❌ 비활성화됨\n`/알림설정` 명령어로 알림을 활성화하세요.",
                    inline=False
                )
            
            embed.add_field(
                name="📋 알림 설정 방법",
                value="1️⃣ 알림을 받고 싶은 채널에서 `/알림설정` 명령어 사용\n2️⃣ 관리자 권한 필요 (채널 관리 권한)\n3️⃣ 설정 완료 후 자동 알림 시작",
                inline=False
            )
            
            embed.set_footer(text="통합 로스트아크 봇 | Selenium + 로스트아크 API")
            await interaction.response.send_message(embed=embed)
    
    async def create_character_embed_from_sibling(self, character_data: Dict, siblings_info: List[Dict]) -> discord.Embed:
        """siblings 데이터에서 특정 캐릭터 정보 Discord Embed 생성"""
        
        # siblings API 응답 모델에 맞는 필드들
        # CharacterInfo: ServerName, CharacterName, CharacterLevel, CharacterClassName, ItemAvgLevel
        char_name = character_data.get('CharacterName', 'Unknown')
        server_name = character_data.get('ServerName', 'Unknown')
        char_class = character_data.get('CharacterClassName', 'Unknown')
        char_level = character_data.get('CharacterLevel', 0)
        item_avg_level = character_data.get('ItemAvgLevel', 'Unknown')
        
        # Embed 생성
        embed = discord.Embed(
            title=f"⚔️ {char_name}",
            description=f"**{server_name}** 서버의 **{char_class}**",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        # 모든 기본 정보 필드를 개별적으로 표시
        embed.add_field(
            name="🏠 서버",
            value=f"```{server_name}```",
            inline=True
        )
        
        embed.add_field(
            name="👤 캐릭터명",
            value=f"```{char_name}```",
            inline=True
        )
        
        embed.add_field(
            name="🎯 캐릭터 레벨",
            value=f"```Lv. {char_level}```",
            inline=True
        )
        
        embed.add_field(
            name="⚔️ 직업 (클래스)",
            value=f"```{char_class}```",
            inline=True
        )
        
        embed.add_field(
            name="💎 평균 아이템레벨",
            value=f"```{item_avg_level}```",
            inline=True
        )
        
        # 빈 필드로 정렬 맞추기
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        
        # 원정대 정보 (간략하게)
        if siblings_info and len(siblings_info) > 1:
            other_chars = [s for s in siblings_info if s.get('CharacterName') != char_name]
            if other_chars:
                expedition_text = ""
                for sibling in other_chars[:8]:  # 최대 8개만 표시
                    sib_name = sibling.get('CharacterName', 'Unknown')
                    sib_server = sibling.get('ServerName', 'Unknown')
                    sib_class = sibling.get('CharacterClassName', 'Unknown')
                    sib_level = sibling.get('CharacterLevel', 0)
                    sib_item_level = sibling.get('ItemAvgLevel', 'Unknown')
                    expedition_text += f"• {sib_name}\n"
                    expedition_text += f"  🏠 {sib_server} | 📋 {sib_class} | 🎯 Lv.{sib_level} | ⚔️ {sib_item_level}\n\n"
                
                if len(other_chars) > 8:
                    expedition_text += f"... 외 {len(other_chars) - 8}명"
                
                embed.add_field(
                    name=f"👥 원정대 캐릭터 ({len(siblings_info)}명)",
                    value=f"```\n{expedition_text}```",
                    inline=False
                )
        
        embed.set_footer(text="로스트아크 공식 | 캐릭터 정보 조회")
        
        return embed
    
    async def create_expedition_embed(self, siblings_info: List[Dict], search_name: str) -> discord.Embed:
        """원정대 전체 정보 Discord Embed 생성"""
        
        if not siblings_info:
            return discord.Embed(title="❌ 원정대 정보 없음", color=0xff0000)
        
        # 첫 번째 캐릭터의 서버명 사용
        server_name = siblings_info[0].get('ServerName', 'Unknown')
        
        embed = discord.Embed(
            title=f"👥 {search_name}의 원정대",
            description=f"**{server_name}** 서버 | 총 **{len(siblings_info)}명**의 캐릭터",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        # 캐릭터들을 아이템레벨 순으로 정렬
        sorted_chars = sorted(siblings_info, key=lambda x: float(x.get('ItemAvgLevel', '0').replace(',', '')), reverse=True)
        
        # 서버별로 캐릭터 그룹핑
        servers = {}
        for character in sorted_chars:
            server_name = character.get('ServerName', 'Unknown')
            if server_name not in servers:
                servers[server_name] = []
            servers[server_name].append(character)
        
        # 서버별로 표시
        for server_name, server_chars in servers.items():
            field_text = ""
            
            for i, character in enumerate(server_chars):
                char_name = character.get('CharacterName', 'Unknown')
                char_class = character.get('CharacterClassName', 'Unknown')
                char_level = character.get('CharacterLevel', 0)
                item_level = character.get('ItemAvgLevel', 'Unknown')
                
                # 검색한 캐릭터는 강조 표시
                if char_name == search_name:
                    name_display = f"⭐ {char_name}"
                else:
                    name_display = char_name
                
                # 전체 순위 계산 (아이템레벨 기준)
                rank = sorted_chars.index(character) + 1
                field_text += f"{rank}. {name_display}\n"
                field_text += f"   📋 {char_class} | 🎯 Lv.{char_level} | ⚔️ {item_level}\n\n"
            
            # 서버별 필드 추가
            embed.add_field(
                name=f"🏠 {server_name} 서버 ({len(server_chars)}명)",
                value=f"```\n{field_text.strip()}```",
                inline=False
            )
        
        # 통계 정보 추가
        if len(sorted_chars) > 0:
            # 최고 아이템레벨과 평균 계산
            item_levels = []
            for char in sorted_chars:
                try:
                    level = float(char.get('ItemAvgLevel', '0').replace(',', ''))
                    item_levels.append(level)
                except:
                    pass
            
            if item_levels:
                max_level = max(item_levels)
                avg_level = sum(item_levels) / len(item_levels)
                
                embed.add_field(
                    name="📊 원정대 통계",
                    value=f"```\n최고 아이템레벨: {max_level:,.1f}\n평균 아이템레벨: {avg_level:,.1f}\n총 캐릭터 수: {len(sorted_chars)}명```",
                    inline=False
                )
        
        embed.set_footer(text="로스트아크 공식 API | 원정대 정보 조회")
        
        return embed
    
    def run(self):
        """봇 실행"""
        try:
            self.bot.run(self.discord_token)
        except Exception as e:
            print(f"❌ 통합 봇 실행 오류: {e}")

def main():
    """메인 함수"""
    print("🚀 통합 로스트아크 봇 시작")
    print("=" * 60)
    print("기능:")
    print("1. 떠돌이상인 변경 감지 알림 (Selenium 기반)")
    print("2. 캐릭터 정보 조회 (/캐릭터정보 명령어)")
    print("3. 원정대 정보 조회 (/원정대정보 명령어)")
    print("4. 서버별 알림 채널 설정 (/알림설정 명령어)")
    print("5. 자동 데이터 변경 감지 (5분마다)")
    print("6. 실시간 데이터 새로고침")
    print("=" * 60)
    
    # Discord 봇 토큰 입력
    discord_token = input("Discord 봇 토큰을 입력하세요: ").strip()
    if not discord_token:
        print("❌ Discord 봇 토큰이 필요합니다!")
        return
    
    # 로스트아크 API 키 입력 (선택사항)
    print("\n로스트아크 API 키를 입력하면 캐릭터 정보 조회 기능을 사용할 수 있습니다.")
    lostark_api_key = input("로스트아크 API 키 (선택사항, 엔터로 건너뛰기): ").strip()
    
    if not lostark_api_key:
        print("⚠️  로스트아크 API 키가 없으면 캐릭터 정보 조회 기능을 사용할 수 없습니다.")
        lostark_api_key = None
    
    print(f"\n✅ 설정 완료:")
    print(f"   - 캐릭터 정보 조회: {'활성화' if lostark_api_key else '비활성화'}")
    print(f"   - 데이터 소스: Selenium + 로스트아크 API")
    print(f"   - 자동 체크: 5분마다")
    print(f"   - 자동 알림: 데이터 변경시에만")
    print(f"   - 데이터 새로고침: 30분마다")
    print(f"   - 다중 서버 지원: 활성화")
    print(f"\n사용 가능한 명령어:")
    print(f"   - /알림설정 : 현재 채널을 알림 채널로 설정 (관리자)")
    print(f"   - /떠상 : 현재 활성 상인 확인")
    print(f"   - /새로고침 : 데이터 새로고침")
    print(f"   - /떠상검색 아이템명 : 아이템으로 상인 검색")
    if lostark_api_key:
        print(f"   - /캐릭터정보 캐릭터명 : 캐릭터 정보 조회")
        print(f"   - /원정대정보 캐릭터명 : 원정대 정보 조회")
    print(f"   - /도움말 : 전체 명령어 보기")
    print(f"\n📋 알림 설정 방법:")
    print(f"   1. 봇을 서버에 초대")
    print(f"   2. 알림을 받고 싶은 채널에서 '/알림설정' 명령어 사용")
    print(f"   3. 관리자 권한 필요 (채널 관리 권한)")
    print(f"   4. 설정 완료 후 자동 알림 시작")
    print(f"\n🚀 봇을 시작합니다...")
    
    # 통합 봇 실행
    bot = IntegratedLostArkBot(discord_token, lostark_api_key)
    bot.run()

if __name__ == "__main__":
    main()
