// 테스트용 파일
const { MerchantParser, displayMerchantInfo } = require('./merchant_parser');

// 제공해주신 API 데이터 (일부)
const testApiData = {
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
                                "default": false,
                                "hidden": false
                            },
                            {
                                "id": "8",
                                "type": 2,
                                "name": "두근두근 상자",
                                "grade": 4,
                                "icon": "efui_iconatlas/all_quest/all_quest_02_230.png",
                                "default": false,
                                "hidden": false
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
                                "default": false,
                                "hidden": false
                            }
                        ]
                    }
                ]
            }
        }
    }
};

// 테스트 실행
console.log('=== 상인 파서 테스트 ===\n');

const parser = new MerchantParser(testApiData);

// 1. 지역별 상인 정보
console.log('1. 지역별 상인 정보:');
const merchants = parser.getMerchantsByRegion();
console.table(merchants);

// 2. 특정 상인 스케줄 조회
console.log('\n2. 벤 상인 스케줄:');
const benSchedule = parser.getMerchantSchedule('벤');
console.log(benSchedule);

// 3. 아이템 검색
console.log('\n3. "상자" 아이템 검색:');
const boxSellers = parser.getItemSellers('상자');
console.table(boxSellers);

// 4. 요일별 스케줄
console.log('\n4. 요일별 스케줄:');
const schedule = parser.getScheduleByDay();
console.log(schedule);

// 5. 전체 요약 정보 표시
console.log('\n5. 전체 요약:');
displayMerchantInfo(testApiData);
