# -*- coding: utf-8 -*-
"""
새로운 상인 파싱 기능 테스트
"""

import json
from merchant_parser import MerchantParser

# 테스트용 샘플 데이터 (실제 API 응답 구조)
sample_data = {
    "pageProps": {
        "initialData": {
            "scheme": {
                "schedules": [
                    {
                        "dayOfWeek": 0,
                        "startTime": "10:00:00",
                        "duration": "05:30:00",
                        "groups": [2]
                    },
                    {
                        "dayOfWeek": 0,
                        "startTime": "22:00:00",
                        "duration": "05:30:00",
                        "groups": [2]
                    },
                    {
                        "dayOfWeek": 1,
                        "startTime": "04:00:00",
                        "duration": "05:30:00",
                        "groups": [1, 2]
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
                                "id": "1",
                                "type": 1,
                                "name": "시이라",
                                "grade": 1,
                                "icon": "efui_iconatlas/use/use_2_13.png",
                                "default": False,
                                "hidden": False
                            },
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

def test_merchant_parser():
    """상인 파서 테스트"""
    print("=== 상인 파서 테스트 시작 ===\n")
    
    try:
        parser = MerchantParser(sample_data)
        
        print("1. 상인 목록 테스트:")
        print(parser.format_merchant_list())
        print("\n" + "="*50 + "\n")
        
        print("2. 스케줄 테스트:")
        print(parser.format_schedule())
        print("\n" + "="*50 + "\n")
        
        print("3. 특정 상인 정보 테스트 (벤):")
        print(parser.format_merchant_detail("벤"))
        print("\n" + "="*50 + "\n")
        
        print("4. 아이템 검색 테스트 (카마인):")
        print(parser.format_item_search("카마인"))
        print("\n" + "="*50 + "\n")
        
        print("5. 현재 활성 상인 테스트:")
        print(parser.format_active_merchants())
        print("\n" + "="*50 + "\n")
        
        print("✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_merchant_parser()
