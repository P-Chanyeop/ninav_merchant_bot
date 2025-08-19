# -*- coding: utf-8 -*-
"""
실시간 떠돌이 상인 API 엔드포인트 찾기
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

class LiveAPIFinder:
    """실시간 떠돌이 상인 API 찾기"""
    
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
    
    def try_api_endpoints(self) -> Optional[Dict]:
        """다양한 API 엔드포인트 시도"""
        
        # 가능한 API 엔드포인트들
        endpoints = [
            "/api/merchant",
            "/api/merchant/live",
            "/api/merchant/current",
            "/api/merchant/active",
            "/api/wandering-merchant",
            "/api/wandering-merchant/live",
            "/api/wandering-merchant/current",
            "/api/v1/merchant",
            "/api/v1/merchant/live",
            "/api/v2/merchant",
            "/merchant/api",
            "/merchant/api/live",
            "/merchant/api/current",
            "/_next/data/zg-3f6yHQunqL3skcaU9x/merchant.json",
            "/statistics/merchant/api",
            "/statistics/merchant/live",
        ]
        
        print("🔍 API 엔드포인트 탐색 중...")
        print("=" * 50)
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                print(f"🌐 시도: {endpoint}")
                
                response = requests.get(url, headers=self.headers, timeout=10)
                
                print(f"  응답 코드: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"  ✅ JSON 응답 성공!")
                        print(f"  📊 데이터 크기: {len(str(data))} 바이트")
                        
                        # 상인 관련 데이터인지 확인
                        if self.is_merchant_data(data):
                            print(f"  🎯 상인 데이터 발견!")
                            return {'endpoint': endpoint, 'data': data}
                        else:
                            print(f"  ⚠️ 상인 데이터가 아님")
                            
                    except json.JSONDecodeError:
                        print(f"  ❌ JSON 파싱 실패")
                        # HTML 응답인 경우 일부만 출력
                        content_preview = response.text[:200]
                        print(f"  📄 응답 미리보기: {content_preview}...")
                        
                elif response.status_code == 404:
                    print(f"  ❌ 404 Not Found")
                else:
                    print(f"  ⚠️ 응답 코드: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ❌ 요청 실패: {e}")
            
            print()
        
        return None
    
    def is_merchant_data(self, data: Dict) -> bool:
        """데이터가 상인 정보인지 확인"""
        try:
            # JSON을 문자열로 변환해서 키워드 검색
            data_str = json.dumps(data, ensure_ascii=False).lower()
            
            # 상인 관련 키워드들
            merchant_keywords = [
                '아르테미스', '유디아', '루테란', '벤', '루카스', '말론',
                'merchant', 'npc', 'wandering', '떠돌이', '상인',
                'schedule', 'region', 'item', 'grade'
            ]
            
            found_keywords = []
            for keyword in merchant_keywords:
                if keyword in data_str:
                    found_keywords.append(keyword)
            
            print(f"    발견된 키워드: {found_keywords}")
            
            # 3개 이상의 키워드가 발견되면 상인 데이터로 판단
            return len(found_keywords) >= 3
            
        except Exception as e:
            print(f"    키워드 검색 오류: {e}")
            return False
    
    def try_graphql_endpoints(self) -> Optional[Dict]:
        """GraphQL 엔드포인트 시도"""
        
        graphql_endpoints = [
            "/graphql",
            "/api/graphql",
            "/query",
            "/api/query"
        ]
        
        # 상인 정보를 요청하는 GraphQL 쿼리들
        queries = [
            {
                "query": "{ merchants { id name region items } }"
            },
            {
                "query": "{ wanderingMerchants { region npc items } }"
            },
            {
                "query": "{ liveMerchants { region npcName items schedule } }"
            }
        ]
        
        print("🔍 GraphQL 엔드포인트 탐색 중...")
        print("=" * 50)
        
        for endpoint in graphql_endpoints:
            for query in queries:
                try:
                    url = f"{self.base_url}{endpoint}"
                    print(f"🌐 시도: {endpoint} - {query['query'][:50]}...")
                    
                    response = requests.post(
                        url, 
                        json=query,
                        headers={**self.headers, 'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    print(f"  응답 코드: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            print(f"  ✅ GraphQL 응답 성공!")
                            
                            if self.is_merchant_data(data):
                                print(f"  🎯 상인 데이터 발견!")
                                return {'endpoint': endpoint, 'query': query, 'data': data}
                                
                        except json.JSONDecodeError:
                            print(f"  ❌ JSON 파싱 실패")
                    
                except requests.exceptions.RequestException as e:
                    print(f"  ❌ 요청 실패: {e}")
                
                print()
        
        return None
    
    def check_websocket_info(self) -> None:
        """WebSocket 연결 정보 확인"""
        print("🔍 WebSocket 연결 정보 확인...")
        print("=" * 50)
        
        try:
            # 메인 페이지에서 WebSocket 관련 정보 찾기
            response = requests.get(f"{self.base_url}/merchant", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # WebSocket 관련 패턴 찾기
                ws_patterns = [
                    r'ws://[^\s"\']+',
                    r'wss://[^\s"\']+',
                    r'socket\.io[^\s"\']*',
                    r'websocket[^\s"\']*'
                ]
                
                import re
                for pattern in ws_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        print(f"WebSocket 패턴 발견: {matches}")
                
                # 실시간 업데이트 관련 키워드 찾기
                realtime_keywords = ['realtime', 'live', 'socket', 'push', 'update']
                for keyword in realtime_keywords:
                    if keyword in content.lower():
                        print(f"실시간 키워드 '{keyword}' 발견")
        
        except Exception as e:
            print(f"WebSocket 정보 확인 실패: {e}")

def main():
    """메인 함수"""
    print("🚀 실시간 떠돌이 상인 API 탐색 시작")
    print("=" * 60)
    
    finder = LiveAPIFinder()
    
    # 1. REST API 엔드포인트 시도
    api_result = finder.try_api_endpoints()
    
    if api_result:
        print("🎉 API 엔드포인트 발견!")
        print(f"엔드포인트: {api_result['endpoint']}")
        
        # 데이터 구조 분석
        data = api_result['data']
        print(f"데이터 구조 분석:")
        print(f"  타입: {type(data)}")
        
        if isinstance(data, dict):
            print(f"  키들: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"  리스트 길이: {len(data)}")
            if data:
                print(f"  첫 번째 요소 타입: {type(data[0])}")
        
        return api_result
    
    # 2. GraphQL 엔드포인트 시도
    print("\n" + "=" * 60)
    graphql_result = finder.try_graphql_endpoints()
    
    if graphql_result:
        print("🎉 GraphQL 엔드포인트 발견!")
        return graphql_result
    
    # 3. WebSocket 정보 확인
    print("\n" + "=" * 60)
    finder.check_websocket_info()
    
    print("\n❌ 실시간 API를 찾을 수 없습니다.")
    print("💡 대안: 기존 JSON 데이터를 사용하여 실시간 계산하는 방법을 권장합니다.")
    
    return None

if __name__ == "__main__":
    main()
