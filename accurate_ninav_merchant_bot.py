# -*- coding: utf-8 -*-
"""
정확한 니나브 서버 떠돌이 상인 봇 (실제 데이터 기반)
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class AccurateNinavMerchantBot:
    """정확한 니나브 서버 떠돌이 상인 봇"""
    
    def __init__(self):
        self.server_name = "니나브"
        self.last_merchants = []
        
    def get_current_active_merchants(self) -> List[Dict]:
        """현재 활성화된 상인들 반환 (실시간 API 호출)"""
        
        # API 엔드포인트에서 실시간 데이터 가져오기
        api_url = "https://kloa.gg/_next/data/zg-3f6yHQunqL3skcaU9x/merchant.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://kloa.gg/merchant',
        }
        
        try:
            print("🌐 실시간 API 데이터 요청 중...")
            response = requests.get(api_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            print("✅ API 데이터 가져오기 성공!")
            
            # 현재 시간 기준 활성 상인 찾기
            now = datetime.now()
            current_day = (now.weekday() + 1) % 7  # KLOA 요일 형식 (0=일요일)
            
            schedules = data['pageProps']['initialData']['scheme']['schedules']
            regions = data['pageProps']['initialData']['scheme']['regions']
            
            active_merchants = []
            
            for schedule in schedules:
                if schedule['dayOfWeek'] != current_day:
                    continue
                
                start_time = schedule['startTime']
                duration = schedule['duration']
                
                # 시간 범위 확인
                if self.is_time_active(start_time, duration, now):
                    for group_id in schedule['groups']:
                        region = next((r for r in regions if r.get('group') == group_id), None)
                        if region:
                            merchant_info = self.create_merchant_from_api_data(region, start_time, duration, now)
                            active_merchants.append(merchant_info)
            
            print(f"✅ {len(active_merchants)}명의 활성 상인 발견")
            return active_merchants
            
        except Exception as e:
            print(f"❌ API 호출 실패: {e}")
            return []
    
    def is_time_active(self, start_time: str, duration: str, current_time: datetime) -> bool:
        """시간이 활성 범위인지 확인"""
        try:
            start_hour, start_min, start_sec = map(int, start_time.split(':'))
            duration_hour, duration_min, duration_sec = map(int, duration.split(':'))
            
            start_datetime = current_time.replace(hour=start_hour, minute=start_min, second=start_sec, microsecond=0)
            end_datetime = start_datetime + timedelta(hours=duration_hour, minutes=duration_min, seconds=duration_sec)
            
            # 자정을 넘어가는 경우 처리
            if end_datetime.day > start_datetime.day:
                return current_time >= start_datetime or current_time <= end_datetime.replace(day=start_datetime.day)
            else:
                return start_datetime <= current_time <= end_datetime
        except:
            return False
    
    def create_merchant_from_api_data(self, region: Dict, start_time: str, duration: str, current_time: datetime) -> Dict:
        """API 데이터에서 상인 정보 생성"""
        # 마감 시간 계산
        start_hour, start_min, start_sec = map(int, start_time.split(':'))
        duration_hour, duration_min, duration_sec = map(int, duration.split(':'))
        
        start_datetime = current_time.replace(hour=start_hour, minute=start_min, second=start_sec, microsecond=0)
        end_datetime = start_datetime + timedelta(hours=duration_hour, minutes=duration_min, seconds=duration_sec)
        
        # 아이템 정보 처리 (등급 정보 제거)
        items = []
        for item in region.get('items', []):
            if item.get('hidden', False):
                continue
            
            item_info = {
                'name': item.get('name', '알 수 없음')
            }
            items.append(item_info)
        
        return {
            'region_name': region.get('name', '알 수 없음'),
            'npc_name': region.get('npcName', '알 수 없음'),
            'start_time': start_time,
            'end_time': end_datetime,
            'items': items
        }
    
    def check_merchant_changes(self) -> Dict[str, List]:
        """상인 변경사항 확인"""
        current_merchants = self.get_current_active_merchants()
        current_keys = {f"{m['region_name']}_{m['npc_name']}" for m in current_merchants}
        last_keys = {f"{m['region_name']}_{m['npc_name']}" for m in self.last_merchants}
        
        changes = {
            'new_merchants': [],
            'ending_merchants': [],
            'disappeared_merchants': []
        }
        
        # 새로운 상인
        new_keys = current_keys - last_keys
        changes['new_merchants'] = [m for m in current_merchants 
                                  if f"{m['region_name']}_{m['npc_name']}" in new_keys]
        
        # 사라진 상인
        disappeared_keys = last_keys - current_keys
        changes['disappeared_merchants'] = list(disappeared_keys)
        
        # 마감 임박 상인 (30분 이내)
        now = datetime.now()
        for merchant in current_merchants:
            time_left = merchant['end_time'] - now
            if timedelta(0) < time_left <= timedelta(minutes=30):
                changes['ending_merchants'].append(merchant)
        
        # 현재 상인 목록 업데이트
        self.last_merchants = current_merchants.copy()
        
        return changes
    
    def format_current_merchants(self) -> str:
        """현재 상인들을 Discord 메시지로 포맷팅"""
        active_merchants = self.get_current_active_merchants()
        
        if not active_merchants:
            return f"📭 현재 {self.server_name} 서버에 활성화된 떠돌이 상인이 없습니다."
        
        now = datetime.now()
        
        # 시간 정보 계산
        if active_merchants:
            time_left = active_merchants[0]['end_time'] - now
            hours_left = int(time_left.total_seconds() / 3600)
            minutes_left = int((time_left.total_seconds() % 3600) / 60)
            
            if hours_left > 0:
                remaining_time = f"{hours_left}시간 {minutes_left}분"
            else:
                remaining_time = f"{minutes_left}분"
        
        message = f"🚨 **{self.server_name} 서버 떠돌이 상인 등장!** 🚨\n"
        message += f"⏰ **오전 10:00 ~ 오후 3:30** (판매 종료까지 {remaining_time})\n"
        message += "=" * 40 + "\n\n"
        
        for i, merchant in enumerate(active_merchants, 1):
            message += f"**{i}. 📍 {merchant['region_name']} - {merchant['npc_name']}**\n"
            
            # 아이템 이름만 표시
            if merchant['items']:
                for item in merchant['items'][:6]:  # 최대 6개
                    message += f"  {item['name']}\n"
            
            message += "\n"
        
        message += f"🕐 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return message
    
    def format_new_merchant_alert(self, new_merchants: List[Dict]) -> str:
        """새로운 상인 등장 알림"""
        if not new_merchants:
            return ""
        
        now = datetime.now()
        time_left = new_merchants[0]['end_time'] - now
        hours_left = int(time_left.total_seconds() / 3600)
        minutes_left = int((time_left.total_seconds() % 3600) / 60)
        
        if hours_left > 0:
            remaining_time = f"{hours_left}시간 {minutes_left}분"
        else:
            remaining_time = f"{minutes_left}분"
        
        message = f"🚨 **{self.server_name} 서버 떠돌이 상인 등장!** 🚨\n"
        message += f"⏰ **오전 10:00 ~ 오후 3:30** (판매 종료까지 {remaining_time})\n\n"
        
        # 전체 구매 정보
        message += "💰 **전체 구매 시 실링 394,000 소모**\n"
        message += "📈 **최대 카드 경험치 6,800 호감도 3,000 획득 가능**\n"
        message += "=" * 40 + "\n\n"
        
        for i, merchant in enumerate(new_merchants, 1):
            message += f"**📍 {merchant['region_name']} - {merchant['npc_name']}**\n"
            
            # 아이템 이름만 표시
            for item in merchant['items']:
                message += f"  {item['name']}\n"
            
            message += "\n"
        
        return message
    
    def format_ending_alert(self, ending_merchants: List[Dict]) -> str:
        """마감 임박 알림"""
        if not ending_merchants:
            return ""
        
        now = datetime.now()
        time_left = ending_merchants[0]['end_time'] - now
        minutes_left = int(time_left.total_seconds() / 60)
        
        message = f"⚠️ **{self.server_name} 서버 떠돌이 상인 마감 임박!** ⚠️\n"
        message += f"🔚 **{minutes_left}분 후 마감** (오후 3:30)\n"
        message += "=" * 30 + "\n\n"
        
        message += "마지막 기회! 놓치지 마세요! 🏃‍♂️💨"
        
        return message
    
    def search_item(self, item_name: str) -> str:
        """아이템 검색"""
        merchants = self.get_current_active_merchants()
        
        found_merchants = []
        for merchant in merchants:
            for item in merchant['items']:
                if item_name.lower() in item['name'].lower():
                    found_merchants.append((merchant, item))
                    break
        
        if not found_merchants:
            return f"❌ '{item_name}' 아이템을 판매하는 상인을 찾을 수 없습니다."
        
        message = f"🔍 **'{item_name}' 검색 결과** 🔍\n"
        message += "=" * 25 + "\n\n"
        
        for merchant, item in found_merchants:
            message += f"📍 **{merchant['region_name']} - {merchant['npc_name']}**\n"
            message += f"🛍️ **{item['name']}**\n\n"
        
        return message

def test_accurate_bot():
    """정확한 봇 테스트"""
    print("🚀 정확한 니나브 서버 떠돌이 상인 봇 테스트")
    print("=" * 50)
    
    bot = AccurateNinavMerchantBot()
    
    # 1. 현재 활성 상인 조회
    print("1. 📍 현재 활성 상인:")
    current_message = bot.format_current_merchants()
    print(current_message)
    print("\n" + "="*50 + "\n")
    
    # 2. 변경사항 확인 (첫 실행)
    print("2. 🔄 변경사항 확인:")
    changes = bot.check_merchant_changes()
    
    if changes['new_merchants']:
        new_alert = bot.format_new_merchant_alert(changes['new_merchants'])
        print("새로운 상인 알림:")
        print(new_alert)
    
    print("\n" + "="*50 + "\n")
    
    # 3. 아이템 검색
    print("3. 🔍 아이템 검색 (집중 룬):")
    search_result = bot.search_item("집중 룬")
    print(search_result)
    
    print("\n🎉 테스트 완료!")

if __name__ == "__main__":
    test_accurate_bot()
