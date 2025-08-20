# -*- coding: utf-8 -*-
"""
떠돌이 상인 추적 시스템 테스트
"""

import json
from datetime import datetime, timedelta
from wandering_merchant_tracker import WanderingMerchantTracker

# 테스트용 샘플 데이터
sample_data = {
    "pageProps": {
        "initialData": {
            "scheme": {
                "schedules": [
                    {
                        "dayOfWeek": datetime.now().weekday() if datetime.now().weekday() != 6 else 0,  # 오늘 요일
                        "startTime": (datetime.now() - timedelta(minutes=30)).strftime("%H:%M:%S"),  # 30분 전 시작
                        "duration": "02:00:00",  # 2시간 지속
                        "groups": [1]
                    },
                    {
                        "dayOfWeek": datetime.now().weekday() if datetime.now().weekday() != 6 else 0,  # 오늘 요일
                        "startTime": (datetime.now() + timedelta(minutes=10)).strftime("%H:%M:%S"),  # 10분 후 시작
                        "duration": "01:30:00",  # 1시간 30분 지속
                        "groups": [2]
                    }
                ],
                "regions": [
                    {
                        "id": "1",
                        "name": "아르테미스",
                        "npcName": "벤",
                        "group": 1,
                        "items": [
                            {
                                "id": "4",
                                "type": 1,
                                "name": "카마인",
                                "grade": 4,
                                "icon": "efui_iconatlas/use/use_2_13.png",
                                "default": False,
                                "hidden": False
                            },
                            {
                                "id": "8",
                                "type": 2,
                                "name": "두근두근 상자",
                                "grade": 4,
                                "icon": "efui_iconatlas/all_quest/all_quest_02_230.png",
                                "default": False,
                                "hidden": False
                            },
                            {
                                "id": "1",
                                "type": 1,
                                "name": "시이라",
                                "grade": 1,
                                "icon": "efui_iconatlas/use/use_2_13.png",
                                "default": False,
                                "hidden": False
                            }
                        ]
                    },
                    {
                        "id": "2",
                        "name": "유디아",
                        "npcName": "루카스",
                        "group": 2,
                        "items": [
                            {
                                "id": "14",
                                "type": 2,
                                "name": "하늘을 비추는 기름",
                                "grade": 4,
                                "icon": "efui_iconatlas/all_quest/all_quest_01_117.png",
                                "default": False,
                                "hidden": False
                            },
                            {
                                "id": "13",
                                "type": 2,
                                "name": "유디아 주술서",
                                "grade": 3,
                                "icon": "efui_iconatlas/use/use_8_39.png",
                                "default": False,
                                "hidden": False
                            }
                        ]
                    }
                ]
            }
        }
    }
}

def test_wandering_merchant_tracker():
    """떠돌이 상인 추적기 테스트"""
    print("=== 떠돌이 상인 추적 시스템 테스트 ===\n")
    
    try:
        tracker = WanderingMerchantTracker()
        
        print("1. 현재 시간 정보:")
        time_info = tracker.get_current_time_info()
        print(f"현재 시간: {time_info['formatted_time']}")
        print(f"요일: {time_info['kloa_day']} (KLOA 형식)")
        print("\n" + "="*50 + "\n")
        
        print("2. 현재 활성 떠돌이 상인 조회:")
        active_merchants = tracker.get_active_merchants_now(sample_data)
        print(f"활성 상인 수: {len(active_merchants)}")
        
        for merchant in active_merchants:
            print(f"- {merchant['region_name']} ({merchant['npc_name']})")
            print(f"  시작: {merchant['start_time']}, 마감: {merchant['end_time'].strftime('%H:%M:%S')}")
            print(f"  아이템 수: {len(merchant['items'])}")
        print("\n" + "="*50 + "\n")
        
        print("3. 현재 활성 상인 요약 메시지:")
        summary_message = tracker.format_current_active_summary(active_merchants)
        print(summary_message)
        print("\n" + "="*50 + "\n")
        
        print("4. 변경사항 확인 (첫 실행):")
        changes = tracker.check_merchant_changes(sample_data)
        print(f"새로운 상인: {len(changes['new_merchants'])}명")
        print(f"마감 임박: {len(changes['ending_merchants'])}명")
        print(f"사라진 상인: {len(changes['disappeared_merchants'])}명")
        print("\n" + "="*50 + "\n")
        
        print("5. 새로운 상인 알림 메시지:")
        if changes['new_merchants']:
            alert_message = tracker.format_new_merchant_alert(changes['new_merchants'])
            print(alert_message)
        else:
            print("새로운 상인이 없습니다.")
        print("\n" + "="*50 + "\n")
        
        print("6. 두 번째 확인 (변경사항 없음):")
        changes2 = tracker.check_merchant_changes(sample_data)
        print(f"새로운 상인: {len(changes2['new_merchants'])}명")
        print(f"마감 임박: {len(changes2['ending_merchants'])}명")
        print(f"사라진 상인: {len(changes2['disappeared_merchants'])}명")
        print("\n" + "="*50 + "\n")
        
        print("✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_wandering_merchant_tracker()
