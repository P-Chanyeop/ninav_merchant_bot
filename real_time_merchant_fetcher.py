# -*- coding: utf-8 -*-
"""
실시간 떠돌이 상인 데이터 가져오기
kloa.gg에서 실시간 데이터를 가져와서 현재 활성 상인들을 계산
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class RealTimeMerchantFetcher:
    """실시간 떠돌이 상인 데이터 가져오기"""
    
    def __init__(self):
        self.base_url = "https://kloa.gg"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://kloa.gg/merchant',
        }
    
    def get_current_active_merchants(self) -> List[Dict]:
        """현재 활성화된 니나브 서버 상인들 가져오기"""
        try:
            print("🔄 kloa.gg에서 실시간 데이터 가져오는 중...")
            
            # HTML 페이지 가져오기
            url = f"{self.base_url}/merchant"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # __NEXT_DATA__ 스크립트에서 JSON 데이터 추출
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            if not next_data_script:
                print("❌ __NEXT_DATA__ 스크립트를 찾을 수 없습니다.")
                return []
            
            # JSON 파싱
            json_data = json.loads(next_data_script.string)
            
            # 스케줄과 지역 데이터 추출
            initial_data = json_data['props']['pageProps']['initialData']
            scheme = initial_data['scheme']
            schedules = scheme['schedules']
            regions = scheme['regions']
            
            print(f"✅ 데이터 로드 성공: {len(schedules)}개 스케줄, {len(regions)}개 지역")
            
            # 현재 활성 그룹 계산
            active_groups = self.get_current_active_groups(schedules)
            print(f"🎯 현재 활성 그룹: {active_groups}")
            
            if not active_groups:
                print("⚠️ 현재 활성화된 그룹이 없습니다.")
                return []
            
            # 활성 그룹에 해당하는 지역들 필터링
            active_merchants = []
            for region in regions:
                if region['group'] in active_groups:
                    merchant_info = {
                        'region_name': region['name'],
                        'npc_name': region['npcName'],
                        'group': region['group'],
                        'items': [
                            {
                                'name': item['name'],
                                'type': item['type'],
                                'grade': item['grade'],
                                'hidden': item.get('hidden', False)
                            }
                            for item in region['items']
                            if not item.get('hidden', False)  # hidden이 true인 아이템 제외
                        ]
                    }
                    active_merchants.append(merchant_info)
            
            print(f"✅ 활성 상인 {len(active_merchants)}명 발견:")
            for merchant in active_merchants:
                visible_items = [item for item in merchant['items'] if not item['hidden']]
                print(f"  - {merchant['region_name']} {merchant['npc_name']}: {len(visible_items)}개 아이템")
            
            return active_merchants
            
        except Exception as e:
            print(f"❌ 실시간 데이터 가져오기 실패: {e}")
            return []
    
    def get_current_active_groups(self, schedules: List[Dict]) -> List[int]:
        """현재 시간 기준으로 활성화된 그룹들 계산"""
        try:
            now = datetime.now()
            current_day = now.weekday()  # 0=월요일, 6=일요일
            
            # kloa.gg는 일요일을 0으로 사용하므로 변환
            kloa_day = (current_day + 1) % 7
            
            active_groups = set()
            
            for schedule in schedules:
                if schedule['dayOfWeek'] != kloa_day:
                    continue
                
                # 시작 시간과 지속 시간 파싱
                start_time_str = schedule['startTime']  # "16:00:00"
                duration_str = schedule['duration']     # "05:30:00"
                
                start_hour, start_min, start_sec = map(int, start_time_str.split(':'))
                duration_hour, duration_min, duration_sec = map(int, duration_str.split(':'))
                
                # 시작 시간과 종료 시간 계산
                start_datetime = now.replace(hour=start_hour, minute=start_min, second=start_sec, microsecond=0)
                end_datetime = start_datetime + timedelta(
                    hours=duration_hour, 
                    minutes=duration_min, 
                    seconds=duration_sec
                )
                
                # 다음날로 넘어가는 경우 처리
                if end_datetime.day != start_datetime.day:
                    # 22:00 ~ 03:30 같은 경우
                    if now.hour >= start_hour or now.hour <= end_datetime.hour:
                        if now >= start_datetime or now <= end_datetime:
                            active_groups.update(schedule['groups'])
                            print(f"  ✅ 활성 스케줄: {start_time_str} ~ {end_datetime.strftime('%H:%M:%S')} (다음날), 그룹: {schedule['groups']}")
                else:
                    # 일반적인 경우
                    if start_datetime <= now <= end_datetime:
                        active_groups.update(schedule['groups'])
                        print(f"  ✅ 활성 스케줄: {start_time_str} ~ {end_datetime.strftime('%H:%M:%S')}, 그룹: {schedule['groups']}")
            
            return list(active_groups)
            
        except Exception as e:
            print(f"❌ 활성 그룹 계산 오류: {e}")
            return []

def main():
    """테스트 함수"""
    print("🚀 실시간 떠돌이 상인 데이터 테스트")
    print("=" * 50)
    
    fetcher = RealTimeMerchantFetcher()
    merchants = fetcher.get_current_active_merchants()
    
    if merchants:
        print(f"\n🎉 성공! {len(merchants)}명의 활성 상인 발견:")
        for merchant in merchants:
            print(f"\n📍 {merchant['region_name']} - {merchant['npc_name']} (그룹 {merchant['group']})")
            for item in merchant['items']:
                item_type = "카드" if item['type'] == 1 else "호감도 아이템" if item['type'] == 2 else "특수 아이템"
                print(f"  - [{item_type}] {item['name']} (등급 {item['grade']})")
    else:
        print("\n❌ 활성 상인을 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
