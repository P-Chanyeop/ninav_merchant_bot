# -*- coding: utf-8 -*-
"""
default: true 아이템만 필터링해서 실제 게임 데이터와 비교
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

def get_default_true_items():
    """default: true인 아이템들만 가져오기"""
    try:
        print("🔄 kloa.gg에서 default: true 아이템만 가져오는 중...")
        
        # HTML 페이지 가져오기
        url = "https://kloa.gg/merchant"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
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
        
        # 현재 활성 그룹 계산 (16:00~21:30 시간대)
        now = datetime.now()
        current_day = now.weekday()  # 0=월요일, 6=일요일
        kloa_day = (current_day + 1) % 7  # kloa.gg는 일요일을 0으로 사용
        
        active_groups = set()
        for schedule in schedules:
            if schedule['dayOfWeek'] != kloa_day:
                continue
            
            start_time_str = schedule['startTime']
            duration_str = schedule['duration']
            
            start_hour, start_min, start_sec = map(int, start_time_str.split(':'))
            duration_hour, duration_min, duration_sec = map(int, duration_str.split(':'))
            
            start_datetime = now.replace(hour=start_hour, minute=start_min, second=start_sec, microsecond=0)
            end_datetime = start_datetime + timedelta(hours=duration_hour, minutes=duration_min, seconds=duration_sec)
            
            if start_datetime <= now <= end_datetime:
                active_groups.update(schedule['groups'])
                print(f"  ✅ 활성 스케줄: {start_time_str} ~ {end_datetime.strftime('%H:%M:%S')}, 그룹: {schedule['groups']}")
        
        print(f"🎯 현재 활성 그룹: {list(active_groups)}")
        
        # 활성 그룹의 지역들에서 default: true 아이템만 추출
        active_merchants = []
        for region in regions:
            if region['group'] in active_groups:
                # default: true인 아이템들만 필터링
                default_items = []
                for item in region['items']:
                    if item.get('default', False) and not item.get('hidden', False):
                        default_items.append({
                            'name': item['name'],
                            'type': item['type'],
                            'grade': item['grade']
                        })
                
                if default_items:  # default: true 아이템이 있는 경우만
                    merchant_info = {
                        'region_name': region['name'],
                        'npc_name': region['npcName'],
                        'group': region['group'],
                        'default_items': default_items
                    }
                    active_merchants.append(merchant_info)
        
        print(f"\n📊 default: true 아이템을 가진 상인들:")
        for merchant in active_merchants:
            print(f"  - {merchant['region_name']} {merchant['npc_name']}: {len(merchant['default_items'])}개 default 아이템")
            for item in merchant['default_items']:
                item_type = "카드" if item['type'] == 1 else "호감도 아이템" if item['type'] == 2 else "특수 아이템"
                print(f"    • [{item_type}] {item['name']}")
        
        return active_merchants
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        return []

def compare_with_actual_data():
    """실제 게임 데이터와 비교"""
    print("\n" + "="*60)
    print("🎮 실제 게임 데이터와 비교")
    print("="*60)
    
    # 실제 게임 데이터 (사용자가 제공한 데이터)
    actual_data = {
        "유디아": ["모리나", "천둥", "유디아 주술서", "유디아 천연소금"],
        "루테란 서부": ["베르하트", "카도건", "레이크바 토마토 주스", "사슬전쟁 실록", "머리초"],
        "루테란 동부": {
            "모리스": ["모르페오", "미한", "진저웨일", "디오리카 밀짚모자", "아제나포리움 브로치", "드라이에이징 된 고기"],
            "버트": ["집행관 솔라스", "녹스", "디오리카 밀짚모자", "루테란의 검 모형", "뜨거운 초코 커피"]
        },
        "토토이크": ["수호자 에오로", "모코코 당근", "특대 무당벌레 인형"],
        "애니츠": ["월향도사", "가디언 루", "비무제 참가 인장"],
        "아르데타인": ["슈테른 네리아", "에너지 X7 캡슐", "아드레날린 강화 수액"],
        "슈샤이어": ["시안", "빛나는 정수", "사파이어 정어리"],
        "로헨델": ["알리페르", "그노시스", "새벽의 마력석", "정령의 깃털", "두근두근 마카롱"],
        "페이튼": ["비올레", "칼도르", "부러진 단검", "붉은 달의 눈물", "선지 덩어리"],
        "파푸니카": ["세토", "키케라", "광기를 잃은 쿠크세이튼", "피냐타 제작 세트", "오레하의 수석", "멧돼지 생고기", "부드러운 주머니", "신비한 녹색 주머니"],
        "플레체": ["안토니오 주교", "알폰스 베디체", "자크라", "교육용 해도", "불과 얼음의 축제", "미술품 캐리어"],
        "볼다이크": ["닐라이", "마레가", "마리우", "베히모스", "세헤라데", "칼테이야", "속삭이는 휘스피", "쿠리구리 물약"],
        "쿠르잔 남부": ["까미", "프타", "투케투스 고래 기름", "흑요석 거울", "간이 정화제"]
    }
    
    # kloa.gg에서 default: true 아이템 가져오기
    kloa_merchants = get_default_true_items()
    
    print(f"\n🔍 비교 결과:")
    
    for merchant in kloa_merchants:
        region = merchant['region_name']
        npc = merchant['npc_name']
        default_items = [item['name'] for item in merchant['default_items']]
        
        print(f"\n📍 {region} - {npc}")
        print(f"  kloa.gg default: true 아이템: {default_items}")
        
        # 실제 데이터와 비교
        if region in actual_data:
            if isinstance(actual_data[region], dict):
                # 루테란 동부처럼 NPC별로 나뉜 경우
                if npc == "모리스" and "모리스" in actual_data[region]:
                    actual_items = actual_data[region]["모리스"]
                elif npc == "버트" and "버트" in actual_data[region]:
                    actual_items = actual_data[region]["버트"]
                else:
                    actual_items = []
            else:
                actual_items = actual_data[region]
            
            print(f"  실제 게임 아이템: {actual_items}")
            
            # 일치하는 아이템 확인
            matching_items = set(default_items) & set(actual_items)
            missing_in_kloa = set(actual_items) - set(default_items)
            extra_in_kloa = set(default_items) - set(actual_items)
            
            if matching_items:
                print(f"  ✅ 일치하는 아이템: {list(matching_items)}")
            if missing_in_kloa:
                print(f"  ❌ kloa.gg에 없는 아이템: {list(missing_in_kloa)}")
            if extra_in_kloa:
                print(f"  ⚠️ kloa.gg에만 있는 아이템: {list(extra_in_kloa)}")
            
            # 일치율 계산
            if actual_items:
                match_rate = len(matching_items) / len(actual_items) * 100
                print(f"  📊 일치율: {match_rate:.1f}%")

if __name__ == "__main__":
    compare_with_actual_data()
