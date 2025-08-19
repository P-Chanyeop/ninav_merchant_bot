# -*- coding: utf-8 -*-
"""
HTML에서 상인 정보 파싱하는 모듈
"""

from bs4 import BeautifulSoup
import requests
import re
from typing import List, Dict, Optional
from datetime import datetime

class HTMLMerchantParser:
    """HTML에서 상인 정보를 파싱하는 클래스"""
    
    def __init__(self):
        self.base_url = "https://kloa.gg/statistics/merchant"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch_merchant_html(self) -> Optional[str]:
        """상인 페이지 HTML 가져오기"""
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"HTML 가져오기 실패: {e}")
            return None
    
    def parse_merchant_from_html_element(self, html_element: str) -> Dict:
        """단일 상인 HTML 요소에서 정보 추출"""
        soup = BeautifulSoup(html_element, 'html.parser')
        
        merchant_info = {
            'region': '',
            'npc_name': '',
            'player_name': '',
            'time': '',
            'items': []
        }
        
        try:
            # 지역명과 NPC명 추출
            location_section = soup.find('div', class_='flex items-center')
            if location_section:
                region_npc = location_section.find('p')
                if region_npc:
                    spans = region_npc.find_all('span')
                    if len(spans) >= 2:
                        merchant_info['region'] = spans[0].get_text(strip=True)
                        merchant_info['npc_name'] = spans[1].get_text(strip=True)
            
            # 플레이어명 추출
            player_link = soup.find('a', href=lambda x: x and '/characters/' in x)
            if player_link:
                merchant_info['player_name'] = player_link.get_text(strip=True)
            
            # 시간 추출
            time_element = soup.find('p', class_='tabular-nums text-secondary')
            if time_element:
                merchant_info['time'] = time_element.get_text(strip=True)
            
            # 아이템 정보 추출
            items_section = soup.find('div', class_='text-base font-medium space-y-1.5')
            if items_section:
                item_elements = items_section.find_all('p', class_='px-1 rounded text-lostark-grade bg-current/20')
                
                for item_element in item_elements:
                    item_info = self.parse_item_element(item_element)
                    if item_info:
                        merchant_info['items'].append(item_info)
        
        except Exception as e:
            print(f"상인 정보 파싱 오류: {e}")
        
        return merchant_info
    
    def parse_item_element(self, item_element) -> Optional[Dict]:
        """아이템 요소에서 정보 추출"""
        try:
            # 등급 정보 (data-grade 속성에서)
            grade = int(item_element.get('data-grade', 1))
            
            # 아이템 이름 (텍스트에서 추출)
            item_text = item_element.get_text(strip=True)
            
            # 아이템 타입 (img의 alt 속성에서)
            img_element = item_element.find('img')
            item_type = ''
            if img_element:
                alt_text = img_element.get('alt', '')
                if '[카드]' in alt_text:
                    item_type = '카드'
                elif '[호감도 아이템]' in alt_text:
                    item_type = '호감도 아이템'
                else:
                    item_type = '아이템'
            
            return {
                'name': item_text,
                'grade': grade,
                'type': item_type,
                'grade_text': self.get_grade_text(grade),
                'grade_emoji': self.get_grade_emoji(grade)
            }
            
        except Exception as e:
            print(f"아이템 파싱 오류: {e}")
            return None
    
    def get_grade_text(self, grade: int) -> str:
        """등급 번호를 텍스트로 변환"""
        grade_map = {1: '일반', 2: '고급', 3: '희귀', 4: '영웅', 5: '전설'}
        return grade_map.get(grade, '알 수 없음')
    
    def get_grade_emoji(self, grade: int) -> str:
        """등급별 이모지 반환"""
        grade_emoji = {1: '⚪', 2: '🟢', 3: '🔵', 4: '🟣', 5: '🟠'}
        return grade_emoji.get(grade, '⚪')
    
    def parse_all_merchants_from_page(self) -> List[Dict]:
        """전체 페이지에서 모든 상인 정보 추출"""
        html_content = self.fetch_merchant_html()
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        merchants = []
        
        try:
            # 상인 정보가 들어있는 div 요소들 찾기
            merchant_divs = soup.find_all('div', class_='px-8 py-3 flex items-center border-b')
            
            for merchant_div in merchant_divs:
                merchant_info = self.parse_merchant_from_div(merchant_div)
                if merchant_info and merchant_info['region']:  # 유효한 정보만 추가
                    merchants.append(merchant_info)
        
        except Exception as e:
            print(f"전체 상인 파싱 오류: {e}")
        
        return merchants
    
    def parse_merchant_from_div(self, merchant_div) -> Dict:
        """div 요소에서 상인 정보 추출"""
        merchant_info = {
            'region': '',
            'npc_name': '',
            'player_name': '',
            'time': '',
            'items': []
        }
        
        try:
            # 지역명과 NPC명 추출
            location_p = merchant_div.find('p')
            if location_p:
                spans = location_p.find_all('span')
                if len(spans) >= 2:
                    merchant_info['region'] = spans[0].get_text(strip=True)
                    merchant_info['npc_name'] = spans[1].get_text(strip=True)
            
            # 플레이어명과 시간 추출
            right_section = merchant_div.find('div', class_='flex gap-x-5')
            if right_section:
                # 플레이어명
                player_link = right_section.find('a')
                if player_link:
                    merchant_info['player_name'] = player_link.get_text(strip=True)
                
                # 시간
                time_p = right_section.find('p', class_='tabular-nums text-secondary')
                if time_p:
                    merchant_info['time'] = time_p.get_text(strip=True)
            
            # 아이템 정보 추출
            items_section = merchant_div.find('div', class_='text-base font-medium space-y-1.5')
            if items_section:
                item_elements = items_section.find_all('p', class_='px-1 rounded text-lostark-grade bg-current/20')
                
                for item_element in item_elements:
                    item_info = self.parse_item_element(item_element)
                    if item_info:
                        merchant_info['items'].append(item_info)
        
        except Exception as e:
            print(f"div 상인 파싱 오류: {e}")
        
        return merchant_info
    
    def format_merchants_for_discord(self, merchants: List[Dict]) -> str:
        """Discord 메시지 형식으로 포맷팅"""
        if not merchants:
            return "📭 현재 활성화된 상인이 없습니다."
        
        message = "🏪 **현재 떠돌이 상인 정보** 🏪\n"
        message += "=" * 35 + "\n\n"
        
        for i, merchant in enumerate(merchants, 1):
            message += f"**{i}. 📍 {merchant['region']} - {merchant['npc_name']}**\n"
            
            if merchant['player_name']:
                message += f"👤 발견자: {merchant['player_name']}\n"
            
            if merchant['time']:
                message += f"⏰ 시간: {merchant['time']}\n"
            
            if merchant['items']:
                message += "🛍️ **판매 아이템:**\n"
                for item in merchant['items']:
                    message += f"  • {item['grade_emoji']} **{item['name']}** ({item['grade_text']} {item['type']})\n"
            else:
                message += "🛍️ 판매 아이템: 정보 없음\n"
            
            message += "\n"
        
        message += f"🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return message
    
    def search_merchant_by_region(self, merchants: List[Dict], region_name: str) -> List[Dict]:
        """지역명으로 상인 검색"""
        return [m for m in merchants if region_name.lower() in m['region'].lower()]
    
    def search_merchant_by_item(self, merchants: List[Dict], item_name: str) -> List[Dict]:
        """아이템명으로 상인 검색"""
        result = []
        for merchant in merchants:
            for item in merchant['items']:
                if item_name.lower() in item['name'].lower():
                    result.append(merchant)
                    break
        return result
    
    def get_high_grade_merchants(self, merchants: List[Dict], min_grade: int = 3) -> List[Dict]:
        """고등급 아이템을 파는 상인만 필터링"""
        result = []
        for merchant in merchants:
            has_high_grade = any(item['grade'] >= min_grade for item in merchant['items'])
            if has_high_grade:
                result.append(merchant)
        return result

# 테스트용 함수
def test_html_parsing():
    """HTML 파싱 테스트"""
    sample_html = '''
    <div class="px-8 py-3 flex items-center border-b last:border-b-0 relative overflow-hidden first:rounded-t-lg last:rounded-b-lg">
        <div class="shrink-0 w-20 py-px bg-[#DECFF6] rounded text-center mr-5">
            <p class="text-sm font-medium text-bola">니나브</p>
        </div>
        <div class="grow">
            <div class="flex justify-between">
                <div class="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" data-slot="icon" class="mr-1.5 size-5 text-disabled">
                        <path fill-rule="evenodd" d="m11.54 22.351.07.04.028.016a.76.76 0 0 0 .723 0l.028-.015.071-.041a16.975 16.975 0 0 0 1.144-.742 19.58 19.58 0 0 0 2.683-2.282c1.944-1.99 3.963-4.98 3.963-8.827a8.25 8.25 0 0 0-16.5 0c0 3.846 2.02 6.837 3.963 8.827a19.58 19.58 0 0 0 2.682 2.282 16.975 16.975 0 0 0 1.145.742ZM12 13.5a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" clip-rule="evenodd"></path>
                    </svg>
                    <p><span class="text-base font-medium">아르테미스</span>&nbsp;<span class="text-sm font-medium text-secondary">벤</span></p>
                </div>
                <div class="flex gap-x-5">
                    <div class="w-48">
                        <a class="hover:text-abola hover:font-medium" href="/characters/NavyTopaz">
                            <img alt="플래티넘" title="플래티넘" loading="lazy" width="18" height="18" decoding="async" data-nimg="1" class="inline-block -mt-0.5 mr-1" src="https://pica.korlark.com/EFUI_IconAtlas/PVP/PVP_4.png" style="color: transparent;">NavyTopaz
                        </a>
                    </div>
                    <p class="tabular-nums text-secondary">10:00</p>
                </div>
            </div>
            <div class="flex justify-between items-end mt-1">
                <div class="text-base font-medium space-y-1.5">
                    <div class="flex items-center">
                        <p class="px-1 rounded text-lostark-grade bg-current/20" data-grade="2">
                            <img alt="[카드]" title="카드" loading="lazy" width="18" height="18" decoding="async" data-nimg="1" class="inline-block -mt-0.5 mr-1" src="https://pica.korlark.com/efui_iconatlas/use/use_2_13.png" style="color: transparent;">바루투
                        </p>
                        <p class="px-1 rounded text-lostark-grade bg-current/20" data-grade="3">
                            <img alt="[호감도 아이템]" title="호감도 아이템" loading="lazy" width="18" height="18" decoding="async" data-nimg="1" class="inline-block -mt-0.5 mr-1" src="https://pica.korlark.com/efui_iconatlas/all_quest/all_quest_03_133.png" style="color: transparent;">더욱 화려한 꽃다발
                        </p>
                        <p class="px-1 rounded text-lostark-grade bg-current/20" data-grade="3">
                            <img alt="[호감도 아이템]" title="호감도 아이템" loading="lazy" width="18" height="18" decoding="async" data-nimg="1" class="inline-block -mt-0.5 mr-1" src="https://pica.korlark.com/efui_iconatlas/all_quest/all_quest_01_23.png" style="color: transparent;">아르테미스 성수
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    parser = HTMLMerchantParser()
    merchant_info = parser.parse_merchant_from_html_element(sample_html)
    
    print("=== HTML 파싱 테스트 결과 ===")
    print(f"지역: {merchant_info['region']}")
    print(f"NPC: {merchant_info['npc_name']}")
    print(f"발견자: {merchant_info['player_name']}")
    print(f"시간: {merchant_info['time']}")
    print("아이템:")
    for item in merchant_info['items']:
        print(f"  - {item['grade_emoji']} {item['name']} ({item['grade_text']} {item['type']})")

if __name__ == "__main__":
    test_html_parsing()
