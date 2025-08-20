# -*- coding: utf-8 -*-
"""
떠돌이 상인 실시간 추적 및 알림 시스템
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import json
from merchant_parser import MerchantParser

class WanderingMerchantTracker:
    """떠돌이 상인 실시간 추적 클래스"""
    
    def __init__(self):
        self.current_active_merchants: Set[str] = set()
        self.last_check_time = None
        self.merchant_end_times: Dict[str, datetime] = {}
        
    def get_current_time_info(self) -> Dict[str, Any]:
        """현재 시간 정보 반환"""
        now = datetime.now()
        return {
            'datetime': now,
            'day_of_week': now.weekday(),  # 0=월요일, 6=일요일
            'kloa_day': (now.weekday() + 1) % 7,  # 0=일요일, 6=토요일 (KLOA 형식)
            'time_str': now.strftime('%H:%M:%S'),
            'formatted_time': now.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def calculate_end_time(self, start_time: str, duration: str, current_date: datetime) -> datetime:
        """상인 마감 시간 계산"""
        try:
            # 시작 시간 파싱
            start_hour, start_min, start_sec = map(int, start_time.split(':'))
            
            # 지속 시간 파싱
            duration_hour, duration_min, duration_sec = map(int, duration.split(':'))
            
            # 시작 시간 생성
            start_datetime = current_date.replace(
                hour=start_hour, 
                minute=start_min, 
                second=start_sec, 
                microsecond=0
            )
            
            # 마감 시간 계산
            end_datetime = start_datetime + timedelta(
                hours=duration_hour,
                minutes=duration_min,
                seconds=duration_sec
            )
            
            return end_datetime
            
        except Exception as e:
            print(f"시간 계산 오류: {e}")
            return current_date + timedelta(hours=5, minutes=30)  # 기본값
    
    def get_active_merchants_now(self, api_data: Dict[Any, Any]) -> List[Dict[str, Any]]:
        """현재 시간에 활성화된 떠돌이 상인들 반환"""
        try:
            parser = MerchantParser(api_data)
            time_info = self.get_current_time_info()
            
            active_merchants = []
            
            for schedule in parser.schedules:
                # 오늘 스케줄인지 확인
                if schedule.get('dayOfWeek') != time_info['kloa_day']:
                    continue
                
                start_time = schedule.get('startTime', '00:00:00')
                duration = schedule.get('duration', '05:30:00')
                
                # 마감 시간 계산
                end_time = self.calculate_end_time(start_time, duration, time_info['datetime'])
                
                # 현재 시간이 활성 시간 범위 내인지 확인
                if self.is_merchant_active_now(start_time, duration, time_info):
                    # 해당 그룹의 상인들 찾기
                    for group_id in schedule.get('groups', []):
                        region = next((r for r in parser.regions if r.get('group') == group_id), None)
                        if region:
                            merchant_info = {
                                'region_name': region.get('name', '알 수 없음'),
                                'npc_name': region.get('npcName', '알 수 없음'),
                                'group_id': group_id,
                                'start_time': start_time,
                                'duration': duration,
                                'end_time': end_time,
                                'items': self.get_merchant_items(region.get('items', [])),
                                'schedule_key': f"{region.get('name')}_{start_time}"
                            }
                            active_merchants.append(merchant_info)
            
            return active_merchants
            
        except Exception as e:
            print(f"활성 상인 조회 오류: {e}")
            return []
    
    def is_merchant_active_now(self, start_time: str, duration: str, time_info: Dict) -> bool:
        """상인이 현재 활성 상태인지 확인"""
        try:
            current_time = time_info['datetime']
            
            # 시작 시간 생성
            start_hour, start_min, start_sec = map(int, start_time.split(':'))
            start_datetime = current_time.replace(
                hour=start_hour, 
                minute=start_min, 
                second=start_sec, 
                microsecond=0
            )
            
            # 마감 시간 계산
            end_datetime = self.calculate_end_time(start_time, duration, current_time)
            
            # 자정을 넘어가는 경우 처리
            if end_datetime.day > start_datetime.day:
                # 자정을 넘어가는 경우: 시작시간 이후이거나 마감시간 이전
                return current_time >= start_datetime or current_time <= end_datetime.replace(day=start_datetime.day)
            else:
                # 같은 날인 경우: 시작시간과 마감시간 사이
                return start_datetime <= current_time <= end_datetime
                
        except Exception as e:
            print(f"활성 상태 확인 오류: {e}")
            return False
    
    def get_merchant_items(self, items: List[Dict]) -> List[Dict[str, Any]]:
        """상인 아이템 정보 정리"""
        processed_items = []
        
        for item in items:
            if item.get('hidden', False):
                continue  # 숨김 아이템 제외
                
            item_info = {
                'name': item.get('name', '알 수 없음'),
                'grade': item.get('grade', 1),
                'grade_text': self.get_grade_text(item.get('grade', 1)),
                'grade_emoji': self.get_grade_emoji(item.get('grade', 1)),
                'type': item.get('type', 1),
                'type_text': self.get_item_type_text(item.get('type', 1))
            }
            processed_items.append(item_info)
        
        # 등급순으로 정렬 (높은 등급부터)
        processed_items.sort(key=lambda x: x['grade'], reverse=True)
        return processed_items
    
    def get_grade_text(self, grade: int) -> str:
        """등급 텍스트 반환"""
        grade_map = {1: '일반', 2: '고급', 3: '희귀', 4: '영웅', 5: '전설'}
        return grade_map.get(grade, '알 수 없음')
    
    def get_grade_emoji(self, grade: int) -> str:
        """등급 이모지 반환"""
        grade_emoji = {1: '⚪', 2: '🟢', 3: '🔵', 4: '🟣', 5: '🟠'}
        return grade_emoji.get(grade, '⚪')
    
    def get_item_type_text(self, item_type: int) -> str:
        """아이템 타입 텍스트 반환"""
        type_map = {1: '카드', 2: '아이템', 3: '재료'}
        return type_map.get(item_type, '알 수 없음')
    
    def check_merchant_changes(self, api_data: Dict[Any, Any]) -> Dict[str, List[Dict]]:
        """상인 변경사항 확인 (새로 등장/사라진 상인)"""
        current_merchants = self.get_active_merchants_now(api_data)
        current_keys = {m['schedule_key'] for m in current_merchants}
        
        changes = {
            'new_merchants': [],      # 새로 등장한 상인
            'ending_merchants': [],   # 곧 마감되는 상인
            'disappeared_merchants': [] # 사라진 상인
        }
        
        # 새로 등장한 상인 찾기
        if self.current_active_merchants:
            new_merchant_keys = current_keys - self.current_active_merchants
            changes['new_merchants'] = [m for m in current_merchants if m['schedule_key'] in new_merchant_keys]
        else:
            # 첫 실행시에는 모든 활성 상인을 새로운 상인으로 처리
            changes['new_merchants'] = current_merchants
        
        # 사라진 상인 찾기
        disappeared_keys = self.current_active_merchants - current_keys
        changes['disappeared_merchants'] = list(disappeared_keys)
        
        # 곧 마감되는 상인 찾기 (30분 이내)
        now = datetime.now()
        for merchant in current_merchants:
            time_until_end = merchant['end_time'] - now
            if timedelta(0) < time_until_end <= timedelta(minutes=30):
                changes['ending_merchants'].append(merchant)
        
        # 현재 활성 상인 목록 업데이트
        self.current_active_merchants = current_keys
        
        return changes
    
    def format_new_merchant_alert(self, merchants: List[Dict]) -> str:
        """새로운 상인 등장 알림 메시지 포맷팅"""
        if not merchants:
            return ""
        
        message = "🚨 **새로운 떠돌이 상인 등장!** 🚨\n"
        message += "=" * 35 + "\n\n"
        
        for merchant in merchants:
            message += f"📍 **{merchant['region_name']} - {merchant['npc_name']}**\n"
            message += f"⏰ 마감시간: {merchant['end_time'].strftime('%H:%M:%S')}\n"
            
            # 주요 아이템 (등급 3 이상)
            high_grade_items = [item for item in merchant['items'] if item['grade'] >= 3]
            if high_grade_items:
                message += "🛍️ **주요 아이템:**\n"
                for item in high_grade_items[:5]:  # 최대 5개
                    message += f"  • {item['grade_emoji']} **{item['name']}** ({item['grade_text']} {item['type_text']})\n"
            
            # 전체 아이템 수
            total_items = len(merchant['items'])
            if total_items > 5:
                message += f"  📦 총 {total_items}개 아이템\n"
            
            message += "\n"
        
        return message
    
    def format_ending_merchant_alert(self, merchants: List[Dict]) -> str:
        """마감 임박 상인 알림 메시지 포맷팅"""
        if not merchants:
            return ""
        
        message = "⚠️ **마감 임박 상인 알림** ⚠️\n"
        message += "=" * 30 + "\n\n"
        
        for merchant in merchants:
            now = datetime.now()
            time_left = merchant['end_time'] - now
            minutes_left = int(time_left.total_seconds() / 60)
            
            message += f"📍 **{merchant['region_name']} - {merchant['npc_name']}**\n"
            message += f"⏰ 남은 시간: **{minutes_left}분**\n"
            message += f"🔚 마감시간: {merchant['end_time'].strftime('%H:%M:%S')}\n\n"
        
        return message
    
    def format_current_active_summary(self, merchants: List[Dict]) -> str:
        """현재 활성 상인 요약 메시지 포맷팅"""
        if not merchants:
            return "📭 현재 활성화된 떠돌이 상인이 없습니다."
        
        message = f"🏪 **현재 활성 상인 ({len(merchants)}명)** 🏪\n"
        message += "=" * 30 + "\n\n"
        
        for merchant in merchants:
            now = datetime.now()
            time_left = merchant['end_time'] - now
            hours_left = int(time_left.total_seconds() / 3600)
            minutes_left = int((time_left.total_seconds() % 3600) / 60)
            
            message += f"📍 **{merchant['region_name']} - {merchant['npc_name']}**\n"
            
            if hours_left > 0:
                message += f"⏰ 남은 시간: {hours_left}시간 {minutes_left}분\n"
            else:
                message += f"⏰ 남은 시간: {minutes_left}분\n"
            
            # 최고 등급 아이템 1개만 표시
            if merchant['items']:
                best_item = merchant['items'][0]  # 이미 등급순 정렬됨
                message += f"🛍️ {best_item['grade_emoji']} {best_item['name']}\n"
            
            message += "\n"
        
        return message
