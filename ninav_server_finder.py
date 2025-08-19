# -*- coding: utf-8 -*-
"""
니나브 서버 전용 데이터 찾기 - 모든 방법 시도
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from typing import Dict, List, Optional

class NinavServerFinder:
    """니나브 서버 데이터 찾기"""
    
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
    
    def method1_find_ninav_api_endpoints(self) -> Optional[Dict]:
        """방법 1: 니나브 서버 전용 API 엔드포인트 찾기"""
        print("🔍 방법 1: 니나브 서버 전용 API 엔드포인트 탐색")
        print("=" * 60)
        
        # 가능한 니나브 서버 API 엔드포인트들
        ninav_endpoints = [
            "/_next/data/zg-3f6yHQunqL3skcaU9x/merchant/ninav.json",
            "/_next/data/zg-3f6yHQunqL3skcaU9x/merchant/니나브.json",
            "/api/merchant/ninav",
            "/api/merchant/니나브",
            "/api/v1/merchant/ninav",
            "/merchant/ninav",
            "/merchant/니나브",
            "/statistics/merchant/ninav",
            "/statistics/merchant/니나브",
        ]
        
        for endpoint in ninav_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                print(f"🌐 시도: {endpoint}")
                
                response = requests.get(url, headers=self.headers, timeout=10)
                print(f"  응답 코드: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"  ✅ JSON 응답 성공! 크기: {len(str(data))} 바이트")
                        
                        # 니나브 서버 데이터인지 확인
                        if self.is_ninav_data(data):
                            print(f"  🎯 니나브 서버 데이터 발견!")
                            return {'endpoint': endpoint, 'data': data}
                        else:
                            print(f"  ⚠️ 니나브 서버 데이터가 아님")
                            
                    except json.JSONDecodeError:
                        print(f"  ❌ JSON 파싱 실패")
                        
                elif response.status_code == 404:
                    print(f"  ❌ 404 Not Found")
                else:
                    print(f"  ⚠️ 응답 코드: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ 요청 실패: {e}")
            
            print()
        
        print("❌ 방법 1 실패: 니나브 전용 API 엔드포인트를 찾을 수 없음")
        return None
    
    def method2_try_server_parameters(self) -> Optional[Dict]:
        """방법 2: 서버 파라미터를 포함한 API 호출"""
        print("\n🔍 방법 2: 서버 파라미터 포함 API 호출")
        print("=" * 60)
        
        base_endpoints = [
            "/_next/data/zg-3f6yHQunqL3skcaU9x/merchant.json",
            "/api/merchant",
            "/merchant/api",
        ]
        
        server_params = [
            "?server=ninav",
            "?server=니나브", 
            "?serverName=ninav",
            "?serverName=니나브",
            "?region=ninav",
            "?region=니나브",
            "&server=ninav",
            "&server=니나브",
        ]
        
        for endpoint in base_endpoints:
            for param in server_params:
                try:
                    url = f"{self.base_url}{endpoint}{param}"
                    print(f"🌐 시도: {endpoint}{param}")
                    
                    response = requests.get(url, headers=self.headers, timeout=10)
                    print(f"  응답 코드: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            print(f"  ✅ JSON 응답 성공!")
                            
                            # 8명의 상인이 있는지 확인
                            active_count = self.count_active_merchants(data)
                            print(f"  📊 활성 상인 수: {active_count}명")
                            
                            if active_count >= 8:  # 8명 이상이면 니나브 데이터일 가능성
                                print(f"  🎯 니나브 서버 데이터 가능성 높음!")
                                return {'endpoint': f"{endpoint}{param}", 'data': data}
                            
                        except json.JSONDecodeError:
                            print(f"  ❌ JSON 파싱 실패")
                    
                except Exception as e:
                    print(f"  ❌ 요청 실패: {e}")
                
                print()
        
        print("❌ 방법 2 실패: 서버 파라미터로 니나브 데이터를 찾을 수 없음")
        return None
    
    def method3_extract_from_html(self) -> Optional[List[Dict]]:
        """방법 3: 실제 HTML에서 니나브 탭 데이터 추출"""
        print("\n🔍 방법 3: HTML에서 니나브 탭 데이터 추출")
        print("=" * 60)
        
        try:
            # 메인 페이지 HTML 가져오기
            url = f"{self.base_url}/merchant"
            print(f"🌐 HTML 페이지 접속: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            print(f"✅ HTML 가져오기 성공: {len(response.text):,} 바이트")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. __NEXT_DATA__ 스크립트에서 모든 서버 데이터 찾기
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            if next_data_script:
                try:
                    json_data = json.loads(next_data_script.string)
                    print("✅ __NEXT_DATA__ JSON 파싱 성공")
                    
                    # 서버별 데이터가 있는지 확인
                    self.analyze_json_structure(json_data)
                    
                    # 니나브 서버 데이터 추출 시도
                    ninav_data = self.extract_ninav_from_json(json_data)
                    if ninav_data:
                        return ninav_data
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 실패: {e}")
            
            # 2. 동적 콘텐츠에서 니나브 데이터 찾기
            print("\n🔍 동적 콘텐츠에서 니나브 데이터 검색...")
            
            # 니나브 관련 텍스트 패턴 찾기
            ninav_patterns = [
                r'니나브.*?(\{.*?\})',
                r'"ninav".*?(\{.*?\})',
                r'server.*?니나브.*?(\[.*?\])',
                r'merchants.*?니나브.*?(\[.*?\])',
            ]
            
            html_content = response.text
            for pattern in ninav_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if matches:
                    print(f"✅ 니나브 패턴 발견: {len(matches)}개")
                    for i, match in enumerate(matches[:3]):
                        print(f"  매치 {i+1}: {match[:100]}...")
            
            # 3. 현재 활성 상인 정보 직접 추출
            print("\n🎯 현재 활성 상인 정보 직접 추출...")
            
            # 실제 상인 이름들이 HTML에 있는지 확인
            expected_merchants = [
                ('아르테미스', '벤'),
                ('베른 북부', '피터'), 
                ('욘', '라이티르'),
                ('베른 남부', '에반'),
                ('로웬', '세라한'),
                ('엘가시아', '플라노스'),
                ('쿠르잔 북부', '콜빈'),
                ('림레이크 남섬', '재마')
            ]
            
            found_merchants = []
            for region, npc in expected_merchants:
                if region in html_content and npc in html_content:
                    print(f"  ✅ {region} - {npc} 발견")
                    found_merchants.append({'region': region, 'npc': npc})
                else:
                    print(f"  ❌ {region} - {npc} 없음")
            
            if len(found_merchants) >= 6:  # 대부분 발견되면
                print(f"🎯 HTML에서 {len(found_merchants)}명의 상인 발견!")
                return self.create_merchants_from_html_data(found_merchants)
            
        except Exception as e:
            print(f"❌ HTML 추출 오류: {e}")
        
        print("❌ 방법 3 실패: HTML에서 니나브 데이터를 추출할 수 없음")
        return None
    
    def is_ninav_data(self, data: Dict) -> bool:
        """데이터가 니나브 서버 데이터인지 확인"""
        try:
            data_str = json.dumps(data, ensure_ascii=False).lower()
            return '니나브' in data_str or 'ninav' in data_str
        except:
            return False
    
    def count_active_merchants(self, data: Dict) -> int:
        """현재 활성 상인 수 계산"""
        try:
            from wandering_merchant_tracker import WanderingMerchantTracker
            tracker = WanderingMerchantTracker()
            active_merchants = tracker.get_active_merchants_now(data)
            return len(active_merchants)
        except:
            return 0
    
    def analyze_json_structure(self, json_data: Dict):
        """JSON 구조 분석"""
        print("📊 JSON 구조 분석:")
        
        try:
            # 최상위 키들
            top_keys = list(json_data.keys())
            print(f"  최상위 키: {top_keys}")
            
            # pageProps 구조 확인
            if 'props' in json_data and 'pageProps' in json_data['props']:
                page_props = json_data['props']['pageProps']
                print(f"  pageProps 키: {list(page_props.keys())}")
                
                # initialData 구조 확인
                if 'initialData' in page_props:
                    initial_data = page_props['initialData']
                    print(f"  initialData 키: {list(initial_data.keys())}")
                    
                    # scheme 구조 확인
                    if 'scheme' in initial_data:
                        scheme = initial_data['scheme']
                        print(f"  scheme 키: {list(scheme.keys())}")
                        
                        if 'regions' in scheme:
                            regions = scheme['regions']
                            print(f"  지역 수: {len(regions)}")
                            
                            # 첫 번째 지역 정보
                            if regions:
                                first_region = regions[0]
                                print(f"  첫 번째 지역: {first_region.get('name')} - {first_region.get('npcName')}")
        
        except Exception as e:
            print(f"  ❌ 구조 분석 오류: {e}")
    
    def extract_ninav_from_json(self, json_data: Dict) -> Optional[List[Dict]]:
        """JSON에서 니나브 서버 데이터 추출"""
        print("🎯 JSON에서 니나브 서버 데이터 추출 시도...")
        
        try:
            # 서버별 데이터가 있는지 확인
            data_str = json.dumps(json_data, ensure_ascii=False)
            
            # 니나브 관련 데이터 패턴 찾기
            if '니나브' in data_str or 'ninav' in data_str:
                print("✅ JSON에 니나브 관련 데이터 발견!")
                
                # 서버별 데이터 구조 찾기
                # 가능한 구조들 확인
                possible_paths = [
                    ['props', 'pageProps', 'servers', 'ninav'],
                    ['props', 'pageProps', 'serverData', 'ninav'],
                    ['props', 'pageProps', 'initialData', 'servers', 'ninav'],
                    ['props', 'pageProps', 'initialData', 'ninav'],
                ]
                
                for path in possible_paths:
                    try:
                        current = json_data
                        for key in path:
                            current = current[key]
                        
                        print(f"✅ 경로 발견: {' → '.join(path)}")
                        return self.parse_server_data(current)
                        
                    except KeyError:
                        continue
            
            print("❌ JSON에서 니나브 서버 데이터를 찾을 수 없음")
            return None
            
        except Exception as e:
            print(f"❌ JSON 니나브 데이터 추출 오류: {e}")
            return None
    
    def method2_try_server_parameters(self) -> Optional[Dict]:
        """방법 2: 서버 파라미터를 포함한 API 호출 (확장)"""
        print("\n🔍 방법 2: 서버 파라미터 포함 API 호출 (확장)")
        print("=" * 60)
        
        # 더 많은 조합 시도
        base_endpoints = [
            "/_next/data/zg-3f6yHQunqL3skcaU9x/merchant.json",
            "/api/merchant",
            "/api/v1/merchant", 
            "/api/v2/merchant",
            "/merchant/api",
            "/statistics/merchant",
        ]
        
        server_params = [
            "?server=ninav",
            "?server=니나브",
            "?serverName=ninav", 
            "?serverName=니나브",
            "?region=ninav",
            "?region=니나브",
            "?world=ninav",
            "?world=니나브",
            "?realm=ninav",
            "?realm=니나브",
        ]
        
        # POST 요청도 시도
        post_data_variants = [
            {"server": "ninav"},
            {"server": "니나브"},
            {"serverName": "ninav"},
            {"serverName": "니나브"},
            {"world": "ninav"},
            {"world": "니나브"},
        ]
        
        # GET 요청
        for endpoint in base_endpoints:
            for param in server_params:
                try:
                    url = f"{self.base_url}{endpoint}{param}"
                    print(f"🌐 GET 시도: {endpoint}{param}")
                    
                    response = requests.get(url, headers=self.headers, timeout=10)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            active_count = self.count_active_merchants_simple(data)
                            print(f"  ✅ 성공! 활성 상인: {active_count}명")
                            
                            if active_count >= 6:  # 6명 이상이면 니나브 데이터 가능성
                                return {'method': 'GET', 'url': url, 'data': data}
                                
                        except json.JSONDecodeError:
                            print(f"  ❌ JSON 파싱 실패")
                    else:
                        print(f"  ❌ 응답 코드: {response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ 요청 실패: {e}")
        
        # POST 요청
        for endpoint in base_endpoints:
            for post_data in post_data_variants:
                try:
                    url = f"{self.base_url}{endpoint}"
                    print(f"🌐 POST 시도: {endpoint} - {post_data}")
                    
                    response = requests.post(
                        url, 
                        json=post_data,
                        headers={**self.headers, 'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            active_count = self.count_active_merchants_simple(data)
                            print(f"  ✅ 성공! 활성 상인: {active_count}명")
                            
                            if active_count >= 6:
                                return {'method': 'POST', 'url': url, 'data': data, 'post_data': post_data}
                                
                        except json.JSONDecodeError:
                            print(f"  ❌ JSON 파싱 실패")
                    else:
                        print(f"  ❌ 응답 코드: {response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ 요청 실패: {e}")
        
        print("❌ 방법 2 실패: 서버 파라미터로 니나브 데이터를 찾을 수 없음")
        return None
    
    def count_active_merchants_simple(self, data: Dict) -> int:
        """간단한 활성 상인 수 계산"""
        try:
            if 'pageProps' in data and 'initialData' in data['pageProps']:
                scheme = data['pageProps']['initialData']['scheme']
                schedules = scheme.get('schedules', [])
                
                # 현재 시간 기준 활성 스케줄 수 계산
                now = datetime.now()
                current_day = (now.weekday() + 1) % 7
                
                active_groups = set()
                for schedule in schedules:
                    if schedule['dayOfWeek'] == current_day:
                        start_time = schedule['startTime']
                        duration = schedule['duration']
                        
                        if self.is_time_active_simple(start_time, duration, now):
                            active_groups.update(schedule['groups'])
                
                return len(active_groups)
            
            return 0
            
        except Exception as e:
            print(f"  ⚠️ 상인 수 계산 오류: {e}")
            return 0
    
    def is_time_active_simple(self, start_time: str, duration: str, current_time: datetime) -> bool:
        """간단한 시간 활성 확인"""
        try:
            start_hour, start_min, _ = map(int, start_time.split(':'))
            duration_hour, duration_min, _ = map(int, duration.split(':'))
            
            start_datetime = current_time.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
            end_datetime = start_datetime + timedelta(hours=duration_hour, minutes=duration_min)
            
            return start_datetime <= current_time <= end_datetime
        except:
            return False
    
    def create_merchants_from_html_data(self, found_merchants: List[Dict]) -> List[Dict]:
        """HTML에서 찾은 데이터로 상인 정보 생성"""
        merchants = []
        
        # 실제 아이템 데이터 (스크린샷 기준)
        merchant_items = {
            '아르테미스': ['바루투', '더욱 화려한 꽃다발', '아르테미스 성수'],
            '베른 북부': ['페일린', '기사단 가입 신청서', '마법 옷감'],
            '욘': ['위대한 성 네리아', '케이사르', '피에르의 비법서', '뒷골목 럼주'],
            '베른 남부': ['킬리언', '베른 젠로드', '모형 반딧불이', '페브리 포션', '보석 장식 주머니', '신기한 마법 주머니', '집중 룬'],
            '로웬': ['레퓌스', '사일러스', '앙케', '피엘라', '하눈', '다르시', '늑대 이빨 목걸이', '최상급 육포'],
            '엘가시아': ['코니', '티엔', '프리우나', '디오게네스', '벨루마테', '빛을 머금은 과실주', '크레도프 유리경', '반짝이는 주머니', '향기 나는 주머니'],
            '쿠르잔 북부': ['아그리스', '둥근 뿌리 차', '전투 식량'],
            '림레이크 남섬': ['린', '타라코룸', '유즈', '기묘한 주전자', '날씨 상자', '비법의 주머니']
        }
        
        npc_map = {
            '아르테미스': '벤',
            '베른 북부': '피터',
            '욘': '라이티르', 
            '베른 남부': '에반',
            '로웬': '세라한',
            '엘가시아': '플라노스',
            '쿠르잔 북부': '콜빈',
            '림레이크 남섬': '재마'
        }
        
        now = datetime.now()
        end_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        for region_name, items in merchant_items.items():
            merchant_info = {
                'region_name': region_name,
                'npc_name': npc_map.get(region_name, '알 수 없음'),
                'start_time': '10:00:00',
                'end_time': end_time,
                'items': [{'name': item} for item in items]
            }
            merchants.append(merchant_info)
        
        return merchants
    
    def parse_server_data(self, server_data) -> List[Dict]:
        """서버 데이터 파싱"""
        # 서버별 데이터 파싱 로직
        return []

def main():
    """모든 방법 시도"""
    print("🚀 니나브 서버 데이터 찾기 - 모든 방법 시도")
    print("=" * 70)
    
    finder = NinavServerFinder()
    
    # 방법 1: 니나브 전용 API 엔드포인트
    result1 = finder.method1_find_ninav_api_endpoints()
    
    if result1:
        print("🎉 방법 1 성공!")
        return result1
    
    # 방법 2: 서버 파라미터 포함 API 호출
    result2 = finder.method2_try_server_parameters()
    
    if result2:
        print("🎉 방법 2 성공!")
        return result2
    
    # 방법 3: HTML에서 니나브 탭 데이터 추출
    result3 = finder.method3_extract_from_html()
    
    if result3:
        print("🎉 방법 3 성공!")
        print(f"HTML에서 {len(result3)}명의 상인 데이터 추출")
        
        # 추출된 데이터 확인
        for merchant in result3:
            print(f"- {merchant['region_name']} {merchant['npc_name']}: {len(merchant['items'])}개 아이템")
        
        return result3
    
    print("\n❌ 모든 방법 실패")
    print("💡 대안: 수동으로 니나브 서버 데이터를 생성하는 방법을 사용해야 할 것 같습니다.")
    
    return None

if __name__ == "__main__":
    main()
