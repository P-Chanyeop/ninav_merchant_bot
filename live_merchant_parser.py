# -*- coding: utf-8 -*-
"""
실시간 활성 떠돌이 상인만 파싱하는 모듈
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict, Optional

class LiveMerchantParser:
    """실시간 활성 떠돌이 상인만 파싱하는 클래스"""
    
    def __init__(self):
        self.base_url = "https://kloa.gg/merchant"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def fetch_page_html(self) -> Optional[str]:
        """KLOA 상인 페이지 HTML 가져오기"""
        try:
            print("🌐 KLOA 상인 페이지 접속 중...")
            response = requests.get(self.base_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            print(f"✅ 응답 성공: {response.status_code}")
            return response.text
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 페이지 접속 실패: {e}")
            return None
    
    def find_active_merchant_container(self, html_content: str) -> Optional[BeautifulSoup]:
        """현재 활성화된 상인 컨테이너 찾기"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 여러 가능한 패턴으로 활성 상인 컨테이너 찾기
            possible_selectors = [
                # headlessui 탭 패널들
                'div[id*="headlessui-tabs-panel"]:not([style*="position:fixed"])',
                'div[role="tabpanel"]:not([style*="position:fixed"])',
                'div[data-headlessui-state="selected"]',
                
                # 일반적인 패턴들
                'div[class*="px-8"][class*="py-3"]',
                'div[class*="border-b"]',
            ]
            
            for selector in possible_selectors:
                try:
                    containers = soup.select(selector)
                    print(f"🔍 '{selector}': {len(containers)}개 요소 발견")
                    
                    if containers:
                        # 첫 번째 유효한 컨테이너 반환
                        for container in containers:
                            # 상인 정보가 있는지 확인
                            if self.has_merchant_info(container):
                                print(f"✅ 활성 상인 컨테이너 발견!")
                                return container
                                
                except Exception as e:
                    print(f"⚠️ 선택자 '{selector}' 오류: {e}")
                    continue
            
            print("❌ 활성 상인 컨테이너를 찾을 수 없습니다.")
            return None
            
        except Exception as e:
            print(f"❌ 컨테이너 검색 오류: {e}")
            return None
    
    def has_merchant_info(self, container) -> bool:
        """컨테이너에 상인 정보가 있는지 확인"""
        try:
            # 지역명이 포함되어 있는지 확인
            text_content = container.get_text()
            regions = ['아르테미스', '유디아', '루테란', '토토이크', '애니츠', '페이튼', '베른', '슈샤이어', 
                      '로헨델', '욘', '파푸니카', '아르데타인', '로웬', '엘가시아', '플레체', '볼다이크', 
                      '쿠르잔', '림레이크']
            
            for region in regions:
                if region in text_content:
                    return True
            
            return False
            
        except:
            return False
    
    def parse_active_merchants(self, html_content: str) -> List[Dict]:
        """현재 활성화된 상인들 파싱"""
        try:
            # 활성 상인 컨테이너 찾기
            container = self.find_active_merchant_container(html_content)
            if not container:
                return []
            
            merchants = []
            
            # 상인 정보가 들어있는 div들 찾기
            merchant_divs = container.find_all('div', recursive=True)
            
            for div in merchant_divs:
                merchant_info = self.extract_merchant_from_div(div)
                if merchant_info and merchant_info['region']:
                    # 중복 제거
                    if not any(m['region'] == merchant_info['region'] and 
                             m['npc_name'] == merchant_info['npc_name'] 
                             for m in merchants):
                        merchants.append(merchant_info)
            
            print(f"✅ {len(merchants)}명의 활성 상인 파싱 완료")
            return merchants
            
        except Exception as e:
            print(f"❌ 상인 파싱 오류: {e}")
            return []
    
    def extract_merchant_from_div(self, div) -> Optional[Dict]:
        """div에서 상인 정보 추출"""
        try:
            text_content = div.get_text()
            
            # 지역명 찾기
            regions = ['아르테미스', '유디아', '루테란 서부', '루테란 동부', '토토이크', '애니츠', '페이튼', 
                      '베른 북부', '베른 남부', '슈샤이어', '로헨델', '욘', '파푸니카', '아르데타인', 
                      '로웬', '엘가시아', '플레체', '볼다이크', '쿠르잔 남부', '쿠르잔 북부', '림레이크']
            
            found_region = None
            for region in regions:
                if region in text_content:
                    found_region = region
                    break
            
            if not found_region:
                return None
            
            # NPC명 찾기 (지역명 다음에 오는 텍스트)
            npc_names = ['벤', '루카스', '말론', '모리스', '버트', '올리버', '맥', '녹스', '피터', '제프리', 
                        '아리세르', '라이티르', '도렐라', '레이니', '에반', '세라한', '플라노스', '페드로', 
                        '구디스', '도니아', '콜빈', '재마']
            
            found_npc = None
            for npc in npc_names:
                if npc in text_content:
                    found_npc = npc
                    break
            
            # 시간 정보 찾기 (HH:MM 형식)
            time_pattern = r'\b(\d{1,2}):(\d{2})\b'
            time_matches = re.findall(time_pattern, text_content)
            found_time = None
            if time_matches:
                hour, minute = time_matches[0]
                found_time = f"{hour.zfill(2)}:{minute}"
            
            # 플레이어명 찾기 (영문/숫자 조합)
            player_pattern = r'\b[A-Za-z][A-Za-z0-9]{2,11}\b'
            player_matches = re.findall(player_pattern, text_content)
            found_player = None
            if player_matches:
                # NPC명이 아닌 것 중 첫 번째
                for match in player_matches:
                    if match not in npc_names:
                        found_player = match
                        break
            
            # 아이템 정보 추출
            items = self.extract_items_from_div(div)
            
            merchant_info = {
                'region': found_region or '',
                'npc_name': found_npc or '',
                'player_name': found_player or '',
                'time': found_time or '',
                'items': items,
                'raw_text': text_content[:200]  # 디버깅용
            }
            
            return merchant_info
            
        except Exception as e:
            print(f"⚠️ 상인 정보 추출 오류: {e}")
            return None
    
    def extract_items_from_div(self, div) -> List[Dict]:
        """div에서 아이템 정보 추출"""
        items = []
        
        try:
            # 이미지 태그에서 아이템 정보 추출
            img_tags = div.find_all('img')
            
            for img in img_tags:
                alt_text = img.get('alt', '')
                title_text = img.get('title', '')
                
                # 아이템 관련 이미지인지 확인
                if any(keyword in alt_text.lower() for keyword in ['카드', '아이템', '호감도']):
                    # 부모 요소에서 아이템명 찾기
                    parent = img.parent
                    if parent:
                        item_text = parent.get_text(strip=True)
                        
                        # 등급 정보 (data-grade 속성)
                        grade_element = parent
                        grade = 1
                        
                        # 상위 요소들에서 data-grade 찾기
                        for _ in range(3):
                            if grade_element and grade_element.get('data-grade'):
                                try:
                                    grade = int(grade_element.get('data-grade'))
                                    break
                                except:
                                    pass
                            if grade_element.parent:
                                grade_element = grade_element.parent
                        
                        # 아이템 타입 결정
                        item_type = '아이템'
                        if '[카드]' in alt_text:
                            item_type = '카드'
                        elif '[호감도 아이템]' in alt_text:
                            item_type = '호감도 아이템'
                        
                        if item_text and len(item_text) > 1:
                            item_info = {
                                'name': item_text,
                                'grade': grade,
                                'type': item_type,
                                'grade_text': self.get_grade_text(grade),
                                'grade_emoji': self.get_grade_emoji(grade)
                            }
                            items.append(item_info)
            
        except Exception as e:
            print(f"⚠️ 아이템 추출 오류: {e}")
        
        return items
    
    def get_grade_text(self, grade: int) -> str:
        """등급 텍스트 반환"""
        grade_map = {1: '일반', 2: '고급', 3: '희귀', 4: '영웅', 5: '전설'}
        return grade_map.get(grade, '알 수 없음')
    
    def get_grade_emoji(self, grade: int) -> str:
        """등급 이모지 반환"""
        grade_emoji = {1: '⚪', 2: '🟢', 3: '🔵', 4: '🟣', 5: '🟠'}
        return grade_emoji.get(grade, '⚪')
    
    def format_merchants_for_discord(self, merchants: List[Dict]) -> str:
        """Discord 메시지 형식으로 포맷팅"""
        if not merchants:
            return "📭 현재 활성화된 떠돌이 상인이 없습니다."
        
        message = "🚨 **현재 활성 떠돌이 상인** 🚨\n"
        message += "=" * 30 + "\n\n"
        
        for i, merchant in enumerate(merchants, 1):
            message += f"**{i}. 📍 {merchant['region']}**\n"
            
            if merchant['npc_name']:
                message += f"👤 상인: {merchant['npc_name']}\n"
            
            if merchant['player_name']:
                message += f"🔍 발견자: {merchant['player_name']}\n"
            
            if merchant['time']:
                message += f"⏰ 시간: {merchant['time']}\n"
            
            if merchant['items']:
                message += "🛍️ **판매 아이템:**\n"
                # 등급순으로 정렬
                sorted_items = sorted(merchant['items'], key=lambda x: x['grade'], reverse=True)
                for item in sorted_items[:5]:  # 최대 5개
                    message += f"  • {item['grade_emoji']} **{item['name']}** ({item['grade_text']} {item['type']})\n"
            else:
                message += "🛍️ 판매 아이템: 정보 없음\n"
            
            message += "\n"
        
        message += f"🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return message
    
    def get_live_merchants(self) -> List[Dict]:
        """현재 활성 상인 정보 가져오기 (전체 프로세스)"""
        # HTML 가져오기
        html_content = self.fetch_page_html()
        if not html_content:
            return []
        
        # 활성 상인 파싱
        merchants = self.parse_active_merchants(html_content)
        return merchants

def test_live_merchant_parser():
    """실시간 상인 파서 테스트"""
    print("🚀 실시간 떠돌이 상인 파서 테스트")
    print("=" * 50)
    
    parser = LiveMerchantParser()
    
    # 현재 활성 상인 가져오기
    merchants = parser.get_live_merchants()
    
    print(f"\n📊 결과:")
    print(f"활성 상인 수: {len(merchants)}")
    
    if merchants:
        print(f"\n📋 상인 목록:")
        for i, merchant in enumerate(merchants, 1):
            print(f"{i}. {merchant['region']} - {merchant['npc_name']}")
            print(f"   발견자: {merchant['player_name']}")
            print(f"   시간: {merchant['time']}")
            print(f"   아이템 수: {len(merchant['items'])}")
            if merchant['items']:
                for item in merchant['items'][:3]:
                    print(f"     - {item['grade_emoji']} {item['name']} ({item['grade_text']})")
            print()
        
        print(f"\n💬 Discord 메시지:")
        discord_message = parser.format_merchants_for_discord(merchants)
        print(discord_message)
    else:
        print("❌ 활성 상인을 찾을 수 없습니다.")
    
    print(f"\n🎉 테스트 완료!")

if __name__ == "__main__":
    test_live_merchant_parser()
