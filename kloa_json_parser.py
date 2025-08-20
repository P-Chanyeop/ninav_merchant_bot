# -*- coding: utf-8 -*-
"""
KLOA 웹사이트에서 JSON 데이터 추출 및 파싱
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional, Any

class KLOAJSONParser:
    """KLOA 웹사이트에서 JSON 데이터를 추출하고 파싱하는 클래스"""
    
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
    
    def extract_next_data_json(self, html_content: str) -> Optional[Dict]:
        """HTML에서 __NEXT_DATA__ JSON 추출"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # __NEXT_DATA__ 스크립트 태그 찾기
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            
            if not next_data_script:
                print("❌ __NEXT_DATA__ 스크립트를 찾을 수 없습니다.")
                return None
            
            # JSON 텍스트 추출
            json_text = next_data_script.string
            if not json_text:
                print("❌ 스크립트 내용이 비어있습니다.")
                return None
            
            # JSON 파싱
            json_data = json.loads(json_text)
            print("✅ JSON 데이터 추출 성공!")
            
            return json_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            return None
        except Exception as e:
            print(f"❌ JSON 추출 중 오류: {e}")
            return None
    
    def get_merchant_data(self) -> Optional[Dict]:
        """상인 데이터 가져오기 (전체 프로세스)"""
        # 1. HTML 가져오기
        html_content = self.fetch_page_html()
        if not html_content:
            return None
        
        # 2. JSON 추출
        json_data = self.extract_next_data_json(html_content)
        if not json_data:
            return None
        
        # 3. 상인 데이터 추출
        try:
            merchant_data = json_data['props']['pageProps']['initialData']
            print(f"✅ 상인 데이터 추출 성공!")
            return merchant_data
            
        except KeyError as e:
            print(f"❌ 상인 데이터 구조 오류: {e}")
            return None
    
    def get_current_active_merchants(self, merchant_data: Dict) -> List[Dict]:
        """현재 활성화된 상인들 반환"""
        if not merchant_data:
            return []
        
        try:
            from wandering_merchant_tracker import WanderingMerchantTracker
            
            # API 데이터 형식으로 변환
            api_format_data = {
                'pageProps': {
                    'initialData': merchant_data
                }
            }
            
            tracker = WanderingMerchantTracker()
            active_merchants = tracker.get_active_merchants_now(api_format_data)
            
            return active_merchants
            
        except Exception as e:
            print(f"❌ 활성 상인 조회 오류: {e}")
            return []
    
    def format_merchants_for_discord(self, merchants: List[Dict]) -> str:
        """Discord 메시지 형식으로 포맷팅"""
        if not merchants:
            return "📭 현재 활성화된 떠돌이 상인이 없습니다."
        
        message = "🏪 **현재 떠돌이 상인 정보** 🏪\n"
        message += "=" * 35 + "\n\n"
        
        for i, merchant in enumerate(merchants, 1):
            message += f"**{i}. 📍 {merchant['region_name']} - {merchant['npc_name']}**\n"
            
            # 남은 시간 계산
            now = datetime.now()
            time_left = merchant['end_time'] - now
            hours_left = int(time_left.total_seconds() / 3600)
            minutes_left = int((time_left.total_seconds() % 3600) / 60)
            
            if hours_left > 0:
                message += f"⏰ 남은 시간: {hours_left}시간 {minutes_left}분\n"
            else:
                message += f"⏰ 남은 시간: {minutes_left}분\n"
            
            # 주요 아이템 (등급 3 이상)
            high_grade_items = [item for item in merchant['items'] if item['grade'] >= 3]
            if high_grade_items:
                message += "🛍️ **주요 아이템:**\n"
                for item in high_grade_items[:5]:  # 최대 5개
                    message += f"  • {item['grade_emoji']} **{item['name']}** ({item['grade_text']} {item['type_text']})\n"
            else:
                message += "🛍️ 주요 아이템: 없음\n"
            
            message += "\n"
        
        message += f"🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return message
    
    def get_all_regions_info(self, merchant_data: Dict) -> List[Dict]:
        """모든 지역 정보 반환"""
        try:
            regions = merchant_data['scheme']['regions']
            
            region_info = []
            for region in regions:
                info = {
                    'id': region.get('id'),
                    'name': region.get('name'),
                    'npc_name': region.get('npcName'),
                    'group': region.get('group'),
                    'items': []
                }
                
                # 아이템 정보 처리
                for item in region.get('items', []):
                    if not item.get('hidden', False):  # 숨김 아이템 제외
                        item_info = {
                            'name': item.get('name'),
                            'grade': item.get('grade', 1),
                            'type': item.get('type', 1),
                            'grade_text': self.get_grade_text(item.get('grade', 1)),
                            'grade_emoji': self.get_grade_emoji(item.get('grade', 1)),
                            'type_text': self.get_item_type_text(item.get('type', 1))
                        }
                        info['items'].append(item_info)
                
                # 등급순으로 정렬
                info['items'].sort(key=lambda x: x['grade'], reverse=True)
                region_info.append(info)
            
            return region_info
            
        except Exception as e:
            print(f"❌ 지역 정보 처리 오류: {e}")
            return []
    
    def get_grade_text(self, grade: int) -> str:
        """등급 텍스트 반환"""
        grade_map = {1: '일반', 2: '고급', 3: '희귀', 4: '영웅', 5: '전설'}
        return grade_map.get(grade, '알 수 없음')
    
    def get_grade_emoji(self, grade: int) -> str:
        """등급 이모지 반환"""
        grade_emoji = {1: '⚪', 2: '🟢', 3: '🔵', 4: '🟣', 5: '🟠'}
        return grade_emoji.get(grade, '⚪')
    
    def get_item_type_text(self, item_type: int) -> str:
        """아이템 타입 텍스트 반환"""
        type_map = {1: '카드', 2: '아이템', 3: '재료'}
        return type_map.get(item_type, '알 수 없음')
    
    def search_by_region(self, regions: List[Dict], region_name: str) -> List[Dict]:
        """지역명으로 검색"""
        return [r for r in regions if region_name.lower() in r['name'].lower()]
    
    def search_by_item(self, regions: List[Dict], item_name: str) -> List[Dict]:
        """아이템명으로 검색"""
        result = []
        for region in regions:
            for item in region['items']:
                if item_name.lower() in item['name'].lower():
                    result.append(region)
                    break
        return result
    
    def get_high_grade_regions(self, regions: List[Dict], min_grade: int = 3) -> List[Dict]:
        """고등급 아이템을 파는 지역만 필터링"""
        result = []
        for region in regions:
            has_high_grade = any(item['grade'] >= min_grade for item in region['items'])
            if has_high_grade:
                result.append(region)
        return result

def test_kloa_json_parser():
    """KLOA JSON 파서 테스트"""
    print("🚀 KLOA JSON 파서 테스트 시작")
    print("=" * 50)
    
    parser = KLOAJSONParser()
    
    # 1. 상인 데이터 가져오기
    merchant_data = parser.get_merchant_data()
    
    if not merchant_data:
        print("❌ 상인 데이터를 가져올 수 없습니다.")
        return
    
    print(f"✅ 상인 데이터 가져오기 성공!")
    
    # 2. 현재 활성 상인 조회
    print("\n📍 현재 활성 상인 조회:")
    active_merchants = parser.get_current_active_merchants(merchant_data)
    print(f"활성 상인 수: {len(active_merchants)}")
    
    if active_merchants:
        discord_message = parser.format_merchants_for_discord(active_merchants)
        print("\n💬 Discord 메시지 형식:")
        print(discord_message)
    
    # 3. 전체 지역 정보
    print("\n🗺️ 전체 지역 정보:")
    all_regions = parser.get_all_regions_info(merchant_data)
    print(f"총 지역 수: {len(all_regions)}")
    
    for region in all_regions[:5]:  # 처음 5개만 표시
        print(f"- {region['name']} ({region['npc_name']}): {len(region['items'])}개 아이템")
    
    # 4. 검색 테스트
    print("\n🔍 검색 테스트:")
    
    # 지역 검색
    artemis_regions = parser.search_by_region(all_regions, "아르테미스")
    print(f"'아르테미스' 검색 결과: {len(artemis_regions)}개")
    
    # 아이템 검색
    kamine_regions = parser.search_by_item(all_regions, "카마인")
    print(f"'카마인' 검색 결과: {len(kamine_regions)}개")
    
    # 고등급 아이템 지역
    high_grade_regions = parser.get_high_grade_regions(all_regions, min_grade=4)
    print(f"영웅 등급 이상 아이템 지역: {len(high_grade_regions)}개")
    
    print("\n🎉 테스트 완료!")

if __name__ == "__main__":
    test_kloa_json_parser()
