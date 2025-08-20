# -*- coding: utf-8 -*-
"""
HTML 구조 디버깅 및 분석
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_html_structure():
    """HTML 구조 상세 분석"""
    
    url = "https://kloa.gg/merchant"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("🔍 HTML 구조 디버깅 시작")
    print("=" * 50)
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. headlessui 탭 패널 찾기
        print("1. 📋 Headless UI 탭 패널 분석:")
        tab_panels = soup.find_all('div', {'role': 'tabpanel'})
        
        for i, panel in enumerate(tab_panels):
            panel_id = panel.get('id', 'no-id')
            is_hidden = 'position:fixed' in panel.get('style', '')
            state = panel.get('data-headlessui-state', 'no-state')
            
            print(f"  패널 {i+1}: ID={panel_id}")
            print(f"    숨김여부: {is_hidden}")
            print(f"    상태: {state}")
            print(f"    텍스트 길이: {len(panel.get_text())}")
            
            if not is_hidden and len(panel.get_text()) > 100:
                print(f"    📝 내용 미리보기: {panel.get_text()[:200]}...")
                
                # 하위 div들 분석
                child_divs = panel.find_all('div', recursive=False)
                print(f"    🔗 직계 자식 div 수: {len(child_divs)}")
                
                for j, child_div in enumerate(child_divs[:3]):
                    print(f"      자식 {j+1}: 클래스={child_div.get('class', [])}")
                    print(f"        텍스트: {child_div.get_text()[:100]}...")
            
            print()
        
        # 2. 활성 탭 패널에서 상인 정보 찾기
        print("2. 🏪 활성 탭 패널에서 상인 정보 검색:")
        active_panel = None
        
        for panel in tab_panels:
            if ('position:fixed' not in panel.get('style', '') and 
                panel.get('data-headlessui-state') == 'selected'):
                active_panel = panel
                break
        
        if not active_panel:
            # 첫 번째 보이는 패널 사용
            for panel in tab_panels:
                if 'position:fixed' not in panel.get('style', ''):
                    active_panel = panel
                    break
        
        if active_panel:
            print(f"✅ 활성 패널 발견: {active_panel.get('id', 'no-id')}")
            
            # 지역명 검색
            regions = ['아르테미스', '유디아', '루테란', '토토이크', '애니츠', '페이튼']
            found_regions = []
            
            panel_text = active_panel.get_text()
            for region in regions:
                if region in panel_text:
                    found_regions.append(region)
            
            print(f"🗺️ 발견된 지역: {found_regions}")
            
            # 상인 컨테이너 패턴 찾기
            print("\n3. 🎯 상인 컨테이너 패턴 분석:")
            
            # 다양한 패턴으로 검색
            patterns = [
                ('px-8 py-3', 'div[class*="px-8"][class*="py-3"]'),
                ('border-b', 'div[class*="border-b"]'),
                ('flex items-center', 'div[class*="flex"][class*="items-center"]'),
                ('relative overflow-hidden', 'div[class*="relative"][class*="overflow-hidden"]'),
            ]
            
            for pattern_name, selector in patterns:
                try:
                    elements = active_panel.select(selector)
                    print(f"  {pattern_name}: {len(elements)}개 요소")
                    
                    if elements:
                        for k, elem in enumerate(elements[:2]):
                            elem_text = elem.get_text()[:150]
                            print(f"    요소 {k+1}: {elem_text}...")
                            
                            # 지역명이 포함되어 있는지 확인
                            has_region = any(region in elem_text for region in regions)
                            print(f"      지역명 포함: {has_region}")
                            
                except Exception as e:
                    print(f"    오류: {e}")
            
            # 4. 모든 하위 div에서 지역명 포함 요소 찾기
            print("\n4. 🔍 지역명 포함 요소 직접 검색:")
            all_divs = active_panel.find_all('div')
            
            region_divs = []
            for div in all_divs:
                div_text = div.get_text()
                for region in regions:
                    if region in div_text and len(div_text) < 500:  # 너무 긴 텍스트 제외
                        region_divs.append((region, div, div_text))
                        break
            
            print(f"지역명 포함 div 수: {len(region_divs)}")
            
            for region, div, text in region_divs[:5]:
                print(f"\n📍 {region} 발견:")
                print(f"  클래스: {div.get('class', [])}")
                print(f"  텍스트: {text[:200]}...")
                
                # 이미지 태그 확인
                images = div.find_all('img')
                print(f"  이미지 수: {len(images)}")
                
                for img in images[:3]:
                    alt_text = img.get('alt', '')
                    title_text = img.get('title', '')
                    print(f"    이미지: alt='{alt_text}', title='{title_text}'")
        
        else:
            print("❌ 활성 패널을 찾을 수 없습니다.")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_html_structure()
