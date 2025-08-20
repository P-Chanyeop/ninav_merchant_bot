# -*- coding: utf-8 -*-
"""
실시간 KLOA 사이트 크롤링 모듈
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class RealTimeCrawler:
    """실시간 KLOA 사이트 크롤링 클래스"""
    
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
        
        # 실제 아이템 등급 매핑
        self.item_grades = {
            # 카드
            '바루투': 2, '페일린': 2, '위대한 성 네리아': 2, '케이사르': 3,
            '킬리언': 1, '베른 젠로드': 2, '레퓌스': 1, '사일러스': 2,
            '앙케': 2, '피엘라': 2, '하눈': 2, '다르시': 3,
            '코니': 1, '티엔': 2, '프리우나': 2, '디오게네스': 2,
            '벨루마테': 2, '아그리스': 1, '린': 2, '타라코룸': 2, '유즈': 3,
            
            # 호감도 아이템
            '더욱 화려한 꽃다발': 3, '아르테미스 성수': 3, '기사단 가입 신청서': 3,
            '마법 옷감': 3, '피에르의 비법서': 3, '모형 반딧불이': 3,
            '페브리 포션': 3, '늑대 이빨 목걸이': 3, '최상급 육포': 3,
            '빛을 머금은 과실주': 3, '크레도프 유리경': 3, '둥근 뿌리 차': 3,
            '전투 식량': 3, '기묘한 주전자': 3, '날씨 상자': 3,
            
            # 특수 아이템
            '뒷골목 럼주': 1, '보석 장식 주머니': 3, '신기한 마법 주머니': 3,
            '집중 룬': 5, '반짝이는 주머니': 3, '향기 나는 주머니': 3,
            '비법의 주머니': 3,
        }
    
    def setup_selenium_driver(self):
        """Selenium 드라이버 설정"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 브라우저 창 숨김
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"❌ Selenium 드라이버 설정 실패: {e}")
            return None
    
    def crawl_with_selenium(self) -> List[Dict]:
        """Selenium을 사용한 동적 크롤링"""
        driver = self.setup_selenium_driver()
        if not driver:
            return []
        
        try:
            print("🌐 Selenium으로 KLOA 사이트 접속 중...")
            driver.get(self.base_url)
            
            # 페이지 로딩 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 니나브 서버 탭 클릭 (있다면)
            try:
                ninav_tab = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '니나브')]"))
                )
                ninav_tab.click()
                time.sleep(2)  # 탭 전환 대기
                print("✅ 니나브 서버 탭 선택됨")
            except:
                print("⚠️ 니나브 서버 탭을 찾을 수 없음, 기본 서버 사용")
            
            # 상인 정보 요소들 찾기
            merchants = []
            
            # 다양한 선택자로 상인 컨테이너 찾기
            selectors = [
                "div[class*='px-8'][class*='py-3']",
                "div[class*='border-b']",
                "div[class*='merchant']",
                "div[class*='flex'][class*='items-center']"
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"✅ '{selector}'로 {len(elements)}개 요소 발견")
                        
                        for element in elements:
                            merchant_info = self.parse_merchant_element_selenium(element)
                            if merchant_info and merchant_info.get('region_name'):
                                merchants.append(merchant_info)
                        
                        if merchants:
                            break
                except Exception as e:
                    print(f"⚠️ 선택자 '{selector}' 오류: {e}")
            
            print(f"🎯 총 {len(merchants)}명의 상인 발견")
            return merchants
            
        except Exception as e:
            print(f"❌ Selenium 크롤링 오류: {e}")
            return []
        finally:
            driver.quit()
    
    def parse_merchant_element_selenium(self, element) -> Optional[Dict]:
        """Selenium 요소에서 상인 정보 파싱"""
        try:
            text_content = element.text
            
            # 지역명 찾기
            regions = ['아르테미스', '유디아', '루테란 서부', '루테란 동부', '토토이크', 
                      '애니츠', '페이튼', '베른 북부', '베른 남부', '슈샤이어', 
                      '로헨델', '욘', '파푸니카', '아르데타인', '로웬', '엘가시아', 
                      '플레체', '볼다이크', '쿠르잔 남부', '쿠르잔 북부', '림레이크']
            
            found_region = None
            for region in regions:
                if region in text_content:
                    found_region = region
                    break
            
            if not found_region:
                return None
            
            # NPC명 찾기
            npc_names = ['벤', '루카스', '말론', '모리스', '버트', '올리버', '맥', 
                        '녹스', '피터', '제프리', '아리세르', '라이티르', '도렐라', 
                        '레이니', '에반', '세라한', '플라노스', '페드로', '구디스', 
                        '도니아', '콜빈', '재마']
            
            found_npc = None
            for npc in npc_names:
                if npc in text_content:
                    found_npc = npc
                    break
            
            # 아이템 정보 추출
            items = self.extract_items_from_text(text_content)
            
            # 시간 정보 (현재는 고정값, 실제로는 파싱 필요)
            end_time = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
            
            return {
                'region_name': found_region,
                'npc_name': found_npc or '알 수 없음',
                'start_time': '10:00:00',
                'end_time': end_time,
                'items': items
            }
            
        except Exception as e:
            print(f"⚠️ 상인 요소 파싱 오류: {e}")
            return None
    
    def extract_items_from_text(self, text_content: str) -> List[Dict]:
        """텍스트에서 아이템 정보 추출"""
        items = []
        
        # 알려진 아이템들 검색
        for item_name, grade in self.item_grades.items():
            if item_name in text_content:
                # 아이템 타입 결정
                item_type = '아이템'
                if any(card in item_name for card in ['바루투', '페일린', '케이사르', '킬리언', '베른', '레퓌스', '사일러스', '앙케', '피엘라', '하눈', '다르시', '코니', '티엔', '프리우나', '디오게네스', '벨루마테', '아그리스', '린', '타라코룸', '유즈']):
                    item_type = '카드'
                elif any(favor in item_name for favor in ['꽃다발', '성수', '신청서', '옷감', '비법서', '반딧불이', '포션', '목걸이', '육포', '과실주', '유리경', '차', '식량', '주전자', '상자']):
                    item_type = '호감도 아이템'
                elif any(special in item_name for special in ['럼주', '주머니', '룬']):
                    item_type = '특수 아이템'
                
                item_info = {
                    'name': item_name,
                    'grade': grade,
                    'grade_text': self.get_grade_text(grade),
                    'grade_emoji': self.get_grade_emoji(grade),
                    'type_text': item_type
                }
                items.append(item_info)
        
        return items
    
    def get_grade_text(self, grade: int) -> str:
        """등급 텍스트 반환"""
        grade_map = {1: '일반', 2: '고급', 3: '희귀', 4: '영웅', 5: '전설'}
        return grade_map.get(grade, '알 수 없음')
    
    def get_grade_emoji(self, grade: int) -> str:
        """등급 이모지 반환"""
        grade_emoji = {1: '⚪', 2: '🟢', 3: '🔵', 4: '🟣', 5: '🟠'}
        return grade_emoji.get(grade, '⚪')
    
    def crawl_with_requests(self) -> List[Dict]:
        """requests를 사용한 기본 크롤링 (백업용)"""
        try:
            print("🌐 requests로 KLOA 사이트 접속 중...")
            response = requests.get(self.base_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # JSON 데이터 추출 시도
            script_tags = soup.find_all('script', {'id': '__NEXT_DATA__'})
            if script_tags:
                json_data = json.loads(script_tags[0].string)
                return self.parse_json_data(json_data)
            
            return []
            
        except Exception as e:
            print(f"❌ requests 크롤링 오류: {e}")
            return []
    
    def parse_json_data(self, json_data: Dict) -> List[Dict]:
        """JSON 데이터에서 상인 정보 파싱"""
        try:
            regions = json_data['props']['pageProps']['initialData']['scheme']['regions']
            schedules = json_data['props']['pageProps']['initialData']['scheme']['schedules']
            
            # 현재 시간 기준 활성 상인 찾기
            now = datetime.now()
            current_day = (now.weekday() + 1) % 7  # KLOA 요일 형식
            
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
                            merchant_info = self.create_merchant_from_region(region, start_time, duration, now)
                            active_merchants.append(merchant_info)
            
            return active_merchants
            
        except Exception as e:
            print(f"❌ JSON 데이터 파싱 오류: {e}")
            return []
    
    def is_time_active(self, start_time: str, duration: str, current_time: datetime) -> bool:
        """시간이 활성 범위인지 확인"""
        try:
            start_hour, start_min, start_sec = map(int, start_time.split(':'))
            duration_hour, duration_min, duration_sec = map(int, duration.split(':'))
            
            start_datetime = current_time.replace(hour=start_hour, minute=start_min, second=start_sec, microsecond=0)
            end_datetime = start_datetime + timedelta(hours=duration_hour, minutes=duration_min, seconds=duration_sec)
            
            return start_datetime <= current_time <= end_datetime
        except:
            return False
    
    def create_merchant_from_region(self, region: Dict, start_time: str, duration: str, current_time: datetime) -> Dict:
        """지역 데이터에서 상인 정보 생성"""
        # 마감 시간 계산
        start_hour, start_min, start_sec = map(int, start_time.split(':'))
        duration_hour, duration_min, duration_sec = map(int, duration.split(':'))
        
        start_datetime = current_time.replace(hour=start_hour, minute=start_min, second=start_sec, microsecond=0)
        end_datetime = start_datetime + timedelta(hours=duration_hour, minutes=duration_min, seconds=duration_sec)
        
        # 아이템 정보 처리
        items = []
        for item in region.get('items', []):
            if item.get('hidden', False):
                continue
            
            item_name = item.get('name', '')
            
            # 실제 등급 정보 사용
            actual_grade = self.item_grades.get(item_name, item.get('grade', 1))
            
            item_info = {
                'name': item_name,
                'grade': actual_grade,
                'grade_text': self.get_grade_text(actual_grade),
                'grade_emoji': self.get_grade_emoji(actual_grade),
                'type_text': self.get_item_type_text(item.get('type', 1))
            }
            items.append(item_info)
        
        return {
            'region_name': region.get('name', '알 수 없음'),
            'npc_name': region.get('npcName', '알 수 없음'),
            'start_time': start_time,
            'end_time': end_datetime,
            'items': items
        }
    
    def get_item_type_text(self, item_type: int) -> str:
        """아이템 타입 텍스트 반환"""
        type_map = {1: '카드', 2: '아이템', 3: '재료'}
        return type_map.get(item_type, '알 수 없음')
    
    def get_current_active_merchants(self) -> List[Dict]:
        """현재 활성 상인 정보 가져오기 (메인 메서드)"""
        print("🚀 실시간 상인 정보 크롤링 시작")
        
        # 1. Selenium 시도 (더 정확함)
        merchants = self.crawl_with_selenium()
        
        # 2. Selenium 실패시 requests 시도
        if not merchants:
            print("🔄 Selenium 실패, requests로 재시도...")
            merchants = self.crawl_with_requests()
        
        # 3. 둘 다 실패시 빈 리스트 반환
        if not merchants:
            print("❌ 모든 크롤링 방법 실패")
            return []
        
        print(f"✅ {len(merchants)}명의 활성 상인 크롤링 완료")
        return merchants

def test_real_time_crawler():
    """실시간 크롤러 테스트"""
    print("🧪 실시간 크롤러 테스트")
    print("=" * 50)
    
    crawler = RealTimeCrawler()
    merchants = crawler.get_current_active_merchants()
    
    if merchants:
        print(f"✅ {len(merchants)}명의 상인 발견:")
        for merchant in merchants:
            print(f"- {merchant['region_name']} {merchant['npc_name']}: {len(merchant['items'])}개 아이템")
    else:
        print("❌ 상인을 찾을 수 없습니다.")

if __name__ == "__main__":
    test_real_time_crawler()
