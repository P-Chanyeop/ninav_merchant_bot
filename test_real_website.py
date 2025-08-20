# -*- coding: utf-8 -*-
"""
실제 KLOA 웹사이트에서 HTML 긁어와서 파싱 테스트
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def fetch_kloa_merchant_page():
    """KLOA 상인 페이지 HTML 가져오기"""
    url = "https://kloa.gg/merchant"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print("🌐 KLOA 상인 페이지에 접속 중...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"✅ 응답 코드: {response.status_code}")
        print(f"📄 HTML 크기: {len(response.text):,} 바이트")
        
        return response.text
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 웹사이트 접속 실패: {e}")
        return None

def analyze_html_structure(html_content):
    """HTML 구조 분석"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("\n🔍 HTML 구조 분석:")
    print("=" * 50)
    
    # 페이지 제목
    title = soup.find('title')
    if title:
        print(f"📋 페이지 제목: {title.get_text()}")
    
    # 상인 관련 요소들 찾기
    print("\n🏪 상인 관련 요소 검색:")
    
    # 다양한 선택자로 상인 정보 찾기
    selectors_to_try = [
        'div[class*="merchant"]',
        'div[class*="trader"]',
        'div[class*="npc"]',
        'div[class*="px-8"]',
        'div[class*="border-b"]',
        '[data-merchant]',
        '[data-npc]',
        'div:contains("아르테미스")',
        'div:contains("유디아")',
        'div:contains("루테란")',
    ]
    
    for selector in selectors_to_try:
        try:
            elements = soup.select(selector)
            if elements:
                print(f"  ✅ '{selector}': {len(elements)}개 요소 발견")
            else:
                print(f"  ❌ '{selector}': 요소 없음")
        except Exception as e:
            print(f"  ⚠️ '{selector}': 오류 - {e}")
    
    # 텍스트에서 지역명 검색
    print("\n📍 지역명 검색:")
    regions = ['아르테미스', '유디아', '루테란', '토토이크', '애니츠', '페이튼', '푸른바다']
    
    for region in regions:
        if region in html_content:
            print(f"  ✅ '{region}' 발견")
        else:
            print(f"  ❌ '{region}' 없음")

def find_merchant_containers(html_content):
    """상인 컨테이너 요소들 찾기"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("\n🎯 상인 컨테이너 찾기:")
    print("=" * 50)
    
    # 가능한 상인 컨테이너 패턴들
    patterns = [
        # 클래스 기반
        {'class': lambda x: x and 'px-8' in ' '.join(x)},
        {'class': lambda x: x and 'py-3' in ' '.join(x)},
        {'class': lambda x: x and 'border-b' in ' '.join(x)},
        {'class': lambda x: x and 'flex' in ' '.join(x) and 'items-center' in ' '.join(x)},
        
        # 복합 조건
        {'class': lambda x: x and any(cls in ' '.join(x) for cls in ['merchant', 'trader', 'npc'])},
    ]
    
    for i, pattern in enumerate(patterns, 1):
        try:
            containers = soup.find_all('div', pattern)
            print(f"패턴 {i}: {len(containers)}개 컨테이너 발견")
            
            if containers:
                # 첫 번째 컨테이너 분석
                first_container = containers[0]
                print(f"  📦 첫 번째 컨테이너 클래스: {first_container.get('class', [])}")
                print(f"  📝 텍스트 미리보기: {first_container.get_text()[:100]}...")
                
                # 하위 요소들 확인
                child_divs = first_container.find_all('div')
                print(f"  🔗 하위 div 개수: {len(child_divs)}")
                
                # 이미지 요소 확인
                images = first_container.find_all('img')
                print(f"  🖼️ 이미지 개수: {len(images)}")
                
                if images:
                    for img in images[:3]:  # 처음 3개만
                        alt_text = img.get('alt', '')
                        src = img.get('src', '')
                        print(f"    - 이미지: alt='{alt_text}', src='{src[:50]}...'")
                
                print()
                
        except Exception as e:
            print(f"패턴 {i} 오류: {e}")

def extract_merchant_info_attempt(html_content):
    """상인 정보 추출 시도"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("\n🎣 상인 정보 추출 시도:")
    print("=" * 50)
    
    # 모든 텍스트에서 지역명이 포함된 요소 찾기
    regions = ['아르테미스', '유디아', '루테란', '토토이크', '애니츠', '페이튼', '푸른바다']
    
    merchants_found = []
    
    for region in regions:
        # 해당 지역명을 포함한 요소들 찾기
        elements = soup.find_all(text=lambda text: text and region in text)
        
        if elements:
            print(f"\n📍 {region} 관련 요소 {len(elements)}개 발견:")
            
            for element in elements[:3]:  # 처음 3개만 확인
                parent = element.parent
                if parent:
                    print(f"  - 부모 태그: {parent.name}")
                    print(f"  - 부모 클래스: {parent.get('class', [])}")
                    print(f"  - 텍스트: {str(element).strip()[:100]}...")
                    
                    # 상위 컨테이너 찾기
                    container = parent
                    for _ in range(5):  # 최대 5단계 상위까지
                        if container.parent and container.parent.name == 'div':
                            container = container.parent
                            classes = container.get('class', [])
                            if any(cls in ' '.join(classes) for cls in ['px-', 'py-', 'border-', 'flex']):
                                print(f"    → 상위 컨테이너: {classes}")
                                break
                    
                    print()

def save_html_for_analysis(html_content):
    """분석용 HTML 파일 저장"""
    filename = f"kloa_merchant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = f"/mnt/c/Users/user/Documents/카카오톡 받은 파일/디스코드봇/{filename}"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"💾 HTML 파일 저장됨: {filename}")
        return filepath
    except Exception as e:
        print(f"❌ HTML 파일 저장 실패: {e}")
        return None

def main():
    """메인 테스트 함수"""
    print("🚀 KLOA 웹사이트 HTML 파싱 테스트 시작")
    print("=" * 60)
    
    # 1. HTML 가져오기
    html_content = fetch_kloa_merchant_page()
    
    if not html_content:
        print("❌ HTML을 가져올 수 없어서 테스트를 중단합니다.")
        return
    
    # 2. HTML 파일 저장
    saved_file = save_html_for_analysis(html_content)
    
    # 3. HTML 구조 분석
    analyze_html_structure(html_content)
    
    # 4. 상인 컨테이너 찾기
    find_merchant_containers(html_content)
    
    # 5. 상인 정보 추출 시도
    extract_merchant_info_attempt(html_content)
    
    print("\n" + "=" * 60)
    print("🎉 테스트 완료!")
    
    if saved_file:
        print(f"📁 저장된 HTML 파일을 직접 확인해보세요: {saved_file}")

if __name__ == "__main__":
    main()
