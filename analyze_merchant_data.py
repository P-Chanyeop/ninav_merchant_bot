#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kloa.gg 떠상 데이터 분석 스크립트
"""

import json
import requests
from datetime import datetime, timedelta
import pytz

def fetch_merchant_data():
    """kloa.gg에서 떠상 데이터 가져오기"""
    url = "https://kloa.gg/_next/data/zg-3f6yHQunqL3skcaU9x/merchant.json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"데이터 가져오기 실패: {e}")
        return None

def analyze_schedule_data(data):
    """스케줄 데이터 분석"""
    if not data or 'pageProps' not in data:
        print("데이터 구조가 올바르지 않습니다.")
        return
    
    scheme = data['pageProps']['initialData']['scheme']
    schedules = scheme['schedules']
    regions = scheme['regions']
    
    print("=== 떠상 스케줄 분석 ===")
    print(f"총 스케줄 수: {len(schedules)}")
    print(f"총 지역 수: {len(regions)}")
    
    # 요일별 스케줄 정리
    days = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일']
    
    for day_num in range(7):
        day_schedules = [s for s in schedules if s['dayOfWeek'] == day_num]
        print(f"\n{days[day_num]} ({day_num}):")
        
        for schedule in sorted(day_schedules, key=lambda x: x['startTime']):
            start_time = schedule['startTime']
            duration = schedule['duration']
            groups = schedule['groups']
            
            # 종료 시간 계산
            start_hour, start_min = map(int, start_time.split(':')[:2])
            duration_hour, duration_min = map(int, duration.split(':')[:2])
            
            end_hour = start_hour + duration_hour
            end_min = start_min + duration_min
            if end_min >= 60:
                end_hour += 1
                end_min -= 60
            if end_hour >= 24:
                end_hour -= 24
            
            print(f"  {start_time[:5]} - {end_hour:02d}:{end_min:02d} | 그룹: {groups}")

def analyze_region_data(data):
    """지역별 아이템 데이터 분석"""
    if not data or 'pageProps' not in data:
        return
    
    regions = data['pageProps']['initialData']['scheme']['regions']
    
    print("\n=== 지역별 아이템 분석 ===")
    
    total_items = 0
    default_true_items = 0
    default_false_items = 0
    hidden_items = 0
    
    for region in regions:
        region_name = region['name']
        npc_name = region['npcName']
        group = region['group']
        items = region['items']
        
        region_default_true = len([item for item in items if item.get('default', False)])
        region_default_false = len([item for item in items if not item.get('default', False)])
        region_hidden = len([item for item in items if item.get('hidden', False)])
        
        total_items += len(items)
        default_true_items += region_default_true
        default_false_items += region_default_false
        hidden_items += region_hidden
        
        print(f"\n{region_name} (NPC: {npc_name}, 그룹: {group})")
        print(f"  총 아이템: {len(items)}개")
        print(f"  default: true: {region_default_true}개")
        print(f"  default: false: {region_default_false}개")
        print(f"  hidden: true: {region_hidden}개")
        
        # default: true 아이템들 출력
        default_items = [item for item in items if item.get('default', False)]
        if default_items:
            print("  기본 아이템:")
            for item in default_items:
                item_type = "카드" if item['type'] == 1 else "호감도" if item['type'] == 2 else "기타"
                print(f"    - {item['name']} ({item_type}, 등급: {item['grade']})")
    
    print(f"\n=== 전체 통계 ===")
    print(f"총 아이템 수: {total_items}개")
    print(f"default: true 아이템: {default_true_items}개 ({default_true_items/total_items*100:.1f}%)")
    print(f"default: false 아이템: {default_false_items}개 ({default_false_items/total_items*100:.1f}%)")
    print(f"hidden: true 아이템: {hidden_items}개 ({hidden_items/total_items*100:.1f}%)")

def find_default_items_by_region(data):
    """지역별 default: true 아이템 찾기"""
    if not data or 'pageProps' not in data:
        return
    
    regions = data['pageProps']['initialData']['scheme']['regions']
    
    print("\n=== 지역별 기본 아이템 (default: true) ===")
    
    for region in regions:
        default_items = [item for item in region['items'] if item.get('default', False)]
        if default_items:
            print(f"\n{region['name']} (그룹 {region['group']}):")
            for item in default_items:
                item_type_map = {1: "카드", 2: "호감도", 3: "기타"}
                item_type = item_type_map.get(item['type'], "알 수 없음")
                print(f"  - {item['name']} ({item_type}, 등급: {item['grade']})")

def analyze_groups(data):
    """그룹별 분석"""
    if not data or 'pageProps' not in data:
        return
    
    regions = data['pageProps']['initialData']['scheme']['regions']
    
    print("\n=== 그룹별 지역 분석 ===")
    
    groups = {}
    for region in regions:
        group = region['group']
        if group not in groups:
            groups[group] = []
        groups[group].append(region['name'])
    
    for group_num in sorted(groups.keys()):
        print(f"\n그룹 {group_num}: {', '.join(groups[group_num])}")

if __name__ == "__main__":
    print("kloa.gg 떠상 데이터 분석 시작...")
    
    data = fetch_merchant_data()
    if data:
        analyze_schedule_data(data)
        analyze_region_data(data)
        find_default_items_by_region(data)
        analyze_groups(data)
    else:
        print("데이터를 가져올 수 없습니다.")
