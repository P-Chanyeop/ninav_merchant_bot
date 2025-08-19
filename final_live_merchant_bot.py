# -*- coding: utf-8 -*-
"""
최종 실시간 떠돌이 상인 봇
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from wandering_merchant_tracker import WanderingMerchantTracker

class FinalLiveMerchantBot:
    """최종 실시간 떠돌이 상인 봇"""
    
    def __init__(self):
        self.api_url = "https://kloa.gg/_next/data/zg-3f6yHQunqL3skcaU9x/merchant.json"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://kloa.gg/merchant',
        }
        self.tracker = WanderingMerchantTracker()
        self.last_merchants = []
    
    def fetch_live_merchant_data(self) -> Optional[Dict]:
        """실시간 상인 데이터 가져오기"""
        try:
            print("🌐 실시간 상인 데이터 요청 중...")
            response = requests.get(self.api_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            print("✅ 실시간 데이터 가져오기 성공!")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 실패: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            return None
    
    def get_current_active_merchants(self) -> List[Dict]:
        """현재 활성화된 떠돌이 상인들 반환"""
        data = self.fetch_live_merchant_data()
        if not data:
            return []
        
        try:
            # WanderingMerchantTracker 사용
            active_merchants = self.tracker.get_active_merchants_now(data)
            print(f"✅ 현재 활성 상인 {len(active_merchants)}명 발견")
            return active_merchants
            
        except Exception as e:
            print(f"❌ 활성 상인 조회 오류: {e}")
            return []
    
    def check_merchant_changes(self) -> Dict[str, List]:
        """상인 변경사항 확인"""
        data = self.fetch_live_merchant_data()
        if not data:
            return {'new_merchants': [], 'ending_merchants': [], 'disappeared_merchants': []}
        
        try:
            changes = self.tracker.check_merchant_changes(data)
            return changes
            
        except Exception as e:
            print(f"❌ 변경사항 확인 오류: {e}")
            return {'new_merchants': [], 'ending_merchants': [], 'disappeared_merchants': []}
    
    def format_current_merchants(self) -> str:
        """현재 상인들을 Discord 메시지로 포맷팅"""
        active_merchants = self.get_current_active_merchants()
        
        if not active_merchants:
            return "📭 현재 활성화된 떠돌이 상인이 없습니다."
        
        message = "🚨 **현재 활성 떠돌이 상인** 🚨\n"
        message += "=" * 30 + "\n\n"
        
        for i, merchant in enumerate(active_merchants, 1):
            message += f"**{i}. 📍 {merchant['region_name']} - {merchant['npc_name']}**\n"
            
            # 남은 시간 계산
            now = datetime.now()
            time_left = merchant['end_time'] - now
            
            if time_left.total_seconds() > 0:
                hours_left = int(time_left.total_seconds() / 3600)
                minutes_left = int((time_left.total_seconds() % 3600) / 60)
                
                if hours_left > 0:
                    message += f"⏰ 남은 시간: **{hours_left}시간 {minutes_left}분**\n"
                else:
                    message += f"⏰ 남은 시간: **{minutes_left}분**\n"
                
                message += f"🔚 마감시간: {merchant['end_time'].strftime('%H:%M:%S')}\n"
            else:
                message += "⏰ **마감됨**\n"
            
            # 주요 아이템 (등급 3 이상)
            high_grade_items = [item for item in merchant['items'] if item['grade'] >= 3]
            if high_grade_items:
                message += "🛍️ **주요 아이템:**\n"
                for item in high_grade_items[:5]:  # 최대 5개
                    message += f"  • {item['grade_emoji']} **{item['name']}** ({item['grade_text']} {item['type_text']})\n"
            
            # 전체 아이템 수 표시
            total_items = len(merchant['items'])
            if total_items > 5:
                message += f"  📦 총 {total_items}개 아이템\n"
            
            message += "\n"
        
        message += f"🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return message
    
    def format_new_merchant_alert(self, new_merchants: List[Dict]) -> str:
        """새로운 상인 등장 알림"""
        if not new_merchants:
            return ""
        
        message = "🚨 **새로운 떠돌이 상인 등장!** 🚨\n"
        message += "=" * 35 + "\n\n"
        
        for merchant in new_merchants:
            message += f"📍 **{merchant['region_name']} - {merchant['npc_name']}**\n"
            
            # 마감시간
            message += f"🔚 마감시간: **{merchant['end_time'].strftime('%H:%M:%S')}**\n"
            
            # 남은 시간
            now = datetime.now()
            time_left = merchant['end_time'] - now
            hours_left = int(time_left.total_seconds() / 3600)
            minutes_left = int((time_left.total_seconds() % 3600) / 60)
            
            if hours_left > 0:
                message += f"⏰ 지속시간: **{hours_left}시간 {minutes_left}분**\n"
            else:
                message += f"⏰ 지속시간: **{minutes_left}분**\n"
            
            # 주요 아이템
            high_grade_items = [item for item in merchant['items'] if item['grade'] >= 3]
            if high_grade_items:
                message += "🛍️ **주요 아이템:**\n"
                for item in high_grade_items[:5]:
                    message += f"  • {item['grade_emoji']} **{item['name']}** ({item['grade_text']} {item['type_text']})\n"
            
            message += "\n"
        
        return message
    
    def format_ending_merchant_alert(self, ending_merchants: List[Dict]) -> str:
        """마감 임박 상인 알림"""
        if not ending_merchants:
            return ""
        
        message = "⚠️ **마감 임박 상인 알림** ⚠️\n"
        message += "=" * 25 + "\n\n"
        
        for merchant in ending_merchants:
            now = datetime.now()
            time_left = merchant['end_time'] - now
            minutes_left = int(time_left.total_seconds() / 60)
            
            message += f"📍 **{merchant['region_name']} - {merchant['npc_name']}**\n"
            message += f"⏰ 남은 시간: **{minutes_left}분**\n"
            message += f"🔚 마감시간: {merchant['end_time'].strftime('%H:%M:%S')}\n\n"
        
        return message
    
    def get_all_regions_info(self) -> List[Dict]:
        """모든 지역 정보 반환"""
        data = self.fetch_live_merchant_data()
        if not data:
            return []
        
        try:
            regions = data['pageProps']['initialData']['scheme']['regions']
            
            region_info = []
            for region in regions:
                info = {
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
    
    def search_by_item(self, item_name: str) -> str:
        """아이템으로 상인 검색"""
        regions = self.get_all_regions_info()
        
        found_regions = []
        for region in regions:
            for item in region['items']:
                if item_name.lower() in item['name'].lower():
                    found_regions.append(region)
                    break
        
        if not found_regions:
            return f"❌ '{item_name}' 아이템을 판매하는 상인을 찾을 수 없습니다."
        
        message = f"🔍 **'{item_name}' 검색 결과** 🔍\n"
        message += "=" * 25 + "\n\n"
        
        for region in found_regions:
            message += f"📍 **{region['name']} - {region['npc_name']}**\n"
            
            # 해당 아이템들만 표시
            matching_items = [item for item in region['items'] 
                            if item_name.lower() in item['name'].lower()]
            
            for item in matching_items:
                message += f"🛍️ {item['grade_emoji']} **{item['name']}** ({item['grade_text']} {item['type_text']})\n"
            
            message += "\n"
        
        return message

def test_final_bot():
    """최종 봇 테스트"""
    print("🚀 최종 실시간 떠돌이 상인 봇 테스트")
    print("=" * 50)
    
    bot = FinalLiveMerchantBot()
    
    # 1. 현재 활성 상인 조회
    print("1. 📍 현재 활성 상인 조회:")
    current_message = bot.format_current_merchants()
    print(current_message)
    print("\n" + "="*50 + "\n")
    
    # 2. 변경사항 확인
    print("2. 🔄 변경사항 확인:")
    changes = bot.check_merchant_changes()
    
    if changes['new_merchants']:
        new_alert = bot.format_new_merchant_alert(changes['new_merchants'])
        print("새로운 상인 알림:")
        print(new_alert)
    
    if changes['ending_merchants']:
        ending_alert = bot.format_ending_merchant_alert(changes['ending_merchants'])
        print("마감 임박 알림:")
        print(ending_alert)
    
    if not changes['new_merchants'] and not changes['ending_merchants']:
        print("변경사항 없음")
    
    print("\n" + "="*50 + "\n")
    
    # 3. 아이템 검색 테스트
    print("3. 🔍 아이템 검색 테스트:")
    search_result = bot.search_by_item("카마인")
    print(search_result)
    
    print("\n🎉 테스트 완료!")

if __name__ == "__main__":
    test_final_bot()
