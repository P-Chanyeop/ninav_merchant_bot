# -*- coding: utf-8 -*-
"""
시간 계산 로직 디버깅
"""

from final_live_merchant_bot import FinalLiveMerchantBot
from wandering_merchant_tracker import WanderingMerchantTracker
from datetime import datetime, timedelta

def debug_time_calculation():
    """시간 계산 로직 디버깅"""
    
    print("🔍 시간 계산 로직 디버깅")
    print("=" * 50)
    
    bot = FinalLiveMerchantBot()
    data = bot.fetch_live_merchant_data()
    
    if not data:
        print("❌ 데이터를 가져올 수 없습니다.")
        return
    
    # 현재 시간 정보
    now = datetime.now()
    current_day = now.weekday()
    kloa_day = (current_day + 1) % 7  # KLOA 요일 형식 (0=일요일)
    current_time_str = now.strftime('%H:%M:%S')
    
    print(f"📅 현재 시간 정보:")
    print(f"  현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Python 요일: {current_day} (0=월요일)")
    print(f"  KLOA 요일: {kloa_day} (0=일요일)")
    print(f"  현재 시각: {current_time_str}")
    
    print(f"\n📋 오늘의 모든 스케줄:")
    
    schedules = data['pageProps']['initialData']['scheme']['schedules']
    regions = data['pageProps']['initialData']['scheme']['regions']
    
    today_schedules = [s for s in schedules if s['dayOfWeek'] == kloa_day]
    
    print(f"오늘({kloa_day}) 스케줄 수: {len(today_schedules)}")
    
    for i, schedule in enumerate(today_schedules, 1):
        start_time = schedule['startTime']
        duration = schedule['duration']
        groups = schedule['groups']
        
        print(f"\n스케줄 {i}:")
        print(f"  시작시간: {start_time}")
        print(f"  지속시간: {duration}")
        print(f"  그룹: {groups}")
        
        # 마감시간 계산
        try:
            start_hour, start_min, start_sec = map(int, start_time.split(':'))
            duration_hour, duration_min, duration_sec = map(int, duration.split(':'))
            
            start_datetime = now.replace(hour=start_hour, minute=start_min, second=start_sec, microsecond=0)
            end_datetime = start_datetime + timedelta(hours=duration_hour, minutes=duration_min, seconds=duration_sec)
            
            print(f"  계산된 시작: {start_datetime.strftime('%H:%M:%S')}")
            print(f"  계산된 마감: {end_datetime.strftime('%H:%M:%S')}")
            
            # 현재 시간이 범위 내인지 확인
            is_active = start_datetime <= now <= end_datetime
            print(f"  현재 활성: {is_active}")
            
            if is_active:
                time_left = end_datetime - now
                hours_left = int(time_left.total_seconds() / 3600)
                minutes_left = int((time_left.total_seconds() % 3600) / 60)
                print(f"  남은 시간: {hours_left}시간 {minutes_left}분")
            
            # 해당 그룹의 상인들
            group_merchants = []
            for group_id in groups:
                region = next((r for r in regions if r.get('group') == group_id), None)
                if region:
                    group_merchants.append(f"{region.get('name')} - {region.get('npcName')}")
            
            print(f"  상인들: {', '.join(group_merchants)}")
            
        except Exception as e:
            print(f"  ❌ 시간 계산 오류: {e}")
    
    print(f"\n" + "="*50)
    
    # WanderingMerchantTracker의 로직 확인
    print(f"🔍 WanderingMerchantTracker 로직 확인:")
    
    tracker = WanderingMerchantTracker()
    
    # 시간 정보 확인
    time_info = tracker.get_current_time_info()
    print(f"Tracker 시간 정보:")
    print(f"  datetime: {time_info['datetime']}")
    print(f"  day_of_week: {time_info['day_of_week']} (Python 형식)")
    print(f"  kloa_day: {time_info['kloa_day']} (KLOA 형식)")
    print(f"  time_str: {time_info['time_str']}")
    
    # 활성 상인 직접 확인
    print(f"\n🎯 활성 상인 직접 확인:")
    
    api_format_data = {'pageProps': {'initialData': data['pageProps']['initialData']}}
    active_merchants = tracker.get_active_merchants_now(api_format_data)
    
    print(f"감지된 활성 상인 수: {len(active_merchants)}")
    
    for merchant in active_merchants:
        print(f"- {merchant['region_name']} - {merchant['npc_name']}")
        print(f"  시작: {merchant['start_time']}")
        print(f"  마감: {merchant['end_time'].strftime('%H:%M:%S')}")
    
    # 수동으로 10:00 스케줄 확인
    print(f"\n🕙 10:00 스케줄 수동 확인:")
    
    target_schedules = [s for s in today_schedules if s['startTime'] == '10:00:00']
    print(f"10:00 시작 스케줄 수: {len(target_schedules)}")
    
    all_10am_merchants = []
    for schedule in target_schedules:
        for group_id in schedule['groups']:
            region = next((r for r in regions if r.get('group') == group_id), None)
            if region:
                merchant_name = f"{region.get('name')} - {region.get('npcName')}"
                if merchant_name not in all_10am_merchants:
                    all_10am_merchants.append(merchant_name)
    
    print(f"10:00 시작 상인들 ({len(all_10am_merchants)}명):")
    for merchant in all_10am_merchants:
        print(f"  - {merchant}")

if __name__ == "__main__":
    debug_time_calculation()
