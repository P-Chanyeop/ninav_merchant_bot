# -*- coding: utf-8 -*-
"""
상인 정보 파싱 및 처리 모듈
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

class MerchantParser:
    """상인 정보 파싱 클래스"""
    
    def __init__(self, api_data: Dict[Any, Any]):
        """
        초기화
        Args:
            api_data: KLOA API에서 받은 데이터
        """
        self.data = api_data
        self.schedules = self._get_schedules()
        self.regions = self._get_regions()
        
    def _get_schedules(self) -> List[Dict]:
        """스케줄 데이터 추출"""
        try:
            return self.data.get('pageProps', {}).get('initialData', {}).get('scheme', {}).get('schedules', [])
        except:
            return []
    
    def _get_regions(self) -> List[Dict]:
        """지역 데이터 추출"""
        try:
            return self.data.get('pageProps', {}).get('initialData', {}).get('scheme', {}).get('regions', [])
        except:
            return []
    
    def get_day_name(self, day_num: int) -> str:
        """요일 번호를 한글 요일명으로 변환"""
        day_names = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일']
        return day_names[day_num] if 0 <= day_num < 7 else '알 수 없음'
    
    def get_grade_text(self, grade: int) -> str:
        """등급 번호를 텍스트로 변환"""
        grade_map = {
            1: '일반',
            2: '고급', 
            3: '희귀',
            4: '영웅',
            5: '전설'
        }
        return grade_map.get(grade, '알 수 없음')
    
    def get_grade_emoji(self, grade: int) -> str:
        """등급별 이모지 반환"""
        grade_emoji = {
            1: '⚪',  # 일반
            2: '🟢',  # 고급
            3: '🔵',  # 희귀
            4: '🟣',  # 영웅
            5: '🟠'   # 전설
        }
        return grade_emoji.get(grade, '⚪')
    
    def get_item_type_text(self, item_type: int) -> str:
        """아이템 타입을 텍스트로 변환"""
        type_map = {
            1: '카드',
            2: '아이템',
            3: '재료'
        }
        return type_map.get(item_type, '알 수 없음')
    
    def get_merchants_by_region(self) -> List[Dict]:
        """지역별 상인 정보 반환"""
        merchants = []
        
        for region in self.regions:
            merchant_info = {
                '지역명': region.get('name', '알 수 없음'),
                '상인명': region.get('npcName', '알 수 없음'),
                '그룹': region.get('group', 0),
                '아이템수': len(region.get('items', [])),
                '주요아이템': self._get_main_items(region.get('items', []))
            }
            merchants.append(merchant_info)
            
        return merchants
    
    def _get_main_items(self, items: List[Dict]) -> List[str]:
        """주요 아이템 추출 (등급 3 이상, 숨김 아님)"""
        main_items = []
        
        for item in items:
            if item.get('grade', 0) >= 3 and not item.get('hidden', True):
                grade_emoji = self.get_grade_emoji(item.get('grade', 1))
                item_name = item.get('name', '알 수 없음')
                main_items.append(f"{grade_emoji} {item_name}")
        
        return main_items[:5]  # 최대 5개만
    
    def get_schedule_by_day(self, target_day: Optional[int] = None) -> Dict[str, List[Dict]]:
        """요일별 스케줄 반환"""
        if target_day is None:
            target_day = datetime.now().weekday()
            target_day = (target_day + 1) % 7  # Python의 월요일=0을 일요일=0으로 변환
        
        schedule_by_day = {}
        
        for schedule in self.schedules:
            day_num = schedule.get('dayOfWeek', 0)
            day_name = self.get_day_name(day_num)
            
            if target_day is not None and day_num != target_day:
                continue
                
            if day_name not in schedule_by_day:
                schedule_by_day[day_name] = []
            
            merchant_names = []
            for group_id in schedule.get('groups', []):
                region = next((r for r in self.regions if r.get('group') == group_id), None)
                if region:
                    merchant_names.append(f"{region.get('name', '알 수 없음')} ({region.get('npcName', '알 수 없음')})")
            
            schedule_info = {
                '시작시간': schedule.get('startTime', '00:00:00'),
                '지속시간': schedule.get('duration', '00:00:00'),
                '상인들': merchant_names
            }
            
            schedule_by_day[day_name].append(schedule_info)
        
        return schedule_by_day
    
    def get_merchant_info(self, merchant_name: str) -> Optional[Dict]:
        """특정 상인 정보 조회"""
        target_region = None
        
        for region in self.regions:
            if (merchant_name.lower() in region.get('name', '').lower() or 
                merchant_name.lower() in region.get('npcName', '').lower()):
                target_region = region
                break
        
        if not target_region:
            return None
        
        # 해당 상인의 스케줄 찾기
        merchant_schedules = []
        group_id = target_region.get('group', 0)
        
        for schedule in self.schedules:
            if group_id in schedule.get('groups', []):
                day_name = self.get_day_name(schedule.get('dayOfWeek', 0))
                schedule_info = {
                    '요일': day_name,
                    '시작시간': schedule.get('startTime', '00:00:00'),
                    '지속시간': schedule.get('duration', '00:00:00')
                }
                merchant_schedules.append(schedule_info)
        
        return {
            '지역명': target_region.get('name', '알 수 없음'),
            '상인명': target_region.get('npcName', '알 수 없음'),
            '그룹': target_region.get('group', 0),
            '스케줄': merchant_schedules,
            '아이템목록': target_region.get('items', [])
        }
    
    def search_item(self, item_name: str) -> List[Dict]:
        """아이템을 판매하는 상인 검색"""
        sellers = []
        
        for region in self.regions:
            for item in region.get('items', []):
                if item_name.lower() in item.get('name', '').lower():
                    seller_info = {
                        '지역명': region.get('name', '알 수 없음'),
                        '상인명': region.get('npcName', '알 수 없음'),
                        '아이템명': item.get('name', '알 수 없음'),
                        '등급': self.get_grade_text(item.get('grade', 1)),
                        '등급이모지': self.get_grade_emoji(item.get('grade', 1)),
                        '타입': self.get_item_type_text(item.get('type', 1)),
                        '숨김여부': item.get('hidden', False)
                    }
                    sellers.append(seller_info)
        
        return sellers
    
    def get_current_active_merchants(self) -> List[Dict]:
        """현재 시간 기준 활성 상인 조회"""
        now = datetime.now()
        current_day = now.weekday()
        current_day = (current_day + 1) % 7  # Python의 월요일=0을 일요일=0으로 변환
        current_time = now.strftime('%H:%M:%S')
        
        active_merchants = []
        
        for schedule in self.schedules:
            if schedule.get('dayOfWeek') != current_day:
                continue
            
            start_time = schedule.get('startTime', '00:00:00')
            duration = schedule.get('duration', '00:00:00')
            
            if self._is_time_in_range(current_time, start_time, duration):
                merchant_names = []
                for group_id in schedule.get('groups', []):
                    region = next((r for r in self.regions if r.get('group') == group_id), None)
                    if region:
                        merchant_names.append(f"{region.get('name', '알 수 없음')} ({region.get('npcName', '알 수 없음')})")
                
                active_info = {
                    '시작시간': start_time,
                    '지속시간': duration,
                    '활성상인들': merchant_names
                }
                active_merchants.append(active_info)
        
        return active_merchants
    
    def _is_time_in_range(self, current_time: str, start_time: str, duration: str) -> bool:
        """시간이 범위 내에 있는지 확인"""
        try:
            # 시간 문자열을 datetime 객체로 변환
            current = datetime.strptime(current_time, '%H:%M:%S')
            start = datetime.strptime(start_time, '%H:%M:%S')
            
            # 지속시간을 timedelta로 변환
            duration_parts = duration.split(':')
            duration_delta = timedelta(
                hours=int(duration_parts[0]),
                minutes=int(duration_parts[1]),
                seconds=int(duration_parts[2])
            )
            
            end = start + duration_delta
            
            # 자정을 넘어가는 경우 처리
            if end.day > start.day:
                return current >= start or current <= end.replace(day=start.day)
            else:
                return start <= current <= end
                
        except:
            return False
    
    def format_merchant_list(self) -> str:
        """상인 목록을 디스코드 메시지 형식으로 포맷팅"""
        merchants = self.get_merchants_by_region()
        
        if not merchants:
            return "📭 상인 정보를 찾을 수 없습니다."
        
        message = "🏪 **떠돌이 상인 목록** 🏪\n"
        message += "=" * 35 + "\n\n"
        
        for i, merchant in enumerate(merchants, 1):
            message += f"**{i}. 📍 {merchant['지역명']}**\n"
            message += f"👤 상인: {merchant['상인명']}\n"
            
            if merchant['주요아이템']:
                message += f"🛍️ 주요 아이템:\n"
                for item in merchant['주요아이템']:
                    message += f"  • {item}\n"
            else:
                message += "🛍️ 주요 아이템: 없음\n"
            
            message += "\n"
        
        return message
    
    def format_schedule(self, target_day: Optional[int] = None) -> str:
        """스케줄을 디스코드 메시지 형식으로 포맷팅"""
        schedule_data = self.get_schedule_by_day(target_day)
        
        if not schedule_data:
            return "📅 스케줄 정보를 찾을 수 없습니다."
        
        message = ""
        for day_name, schedules in schedule_data.items():
            message += f"📅 **{day_name} 스케줄**\n"
            message += "=" * 25 + "\n\n"
            
            if schedules:
                for schedule in schedules:
                    message += f"⏰ **{schedule['시작시간']}** ({schedule['지속시간']})\n"
                    for merchant in schedule['상인들']:
                        message += f"  • {merchant}\n"
                    message += "\n"
            else:
                message += "해당 요일에는 상인이 없습니다.\n\n"
        
        return message
    
    def format_merchant_detail(self, merchant_name: str) -> str:
        """특정 상인 상세 정보를 디스코드 메시지 형식으로 포맷팅"""
        merchant_info = self.get_merchant_info(merchant_name)
        
        if not merchant_info:
            return f"❌ '{merchant_name}' 상인을 찾을 수 없습니다."
        
        message = f"🏪 **{merchant_info['상인명']} ({merchant_info['지역명']})** 🏪\n"
        message += "=" * 35 + "\n\n"
        
        # 스케줄 정보
        message += "📅 **출현 스케줄**\n"
        for schedule in merchant_info['스케줄']:
            message += f"• {schedule['요일']}: {schedule['시작시간']} ({schedule['지속시간']})\n"
        message += "\n"
        
        # 아이템 정보
        items = merchant_info['아이템목록']
        if items:
            # 등급별로 정렬 (높은 등급부터)
            visible_items = [item for item in items if not item.get('hidden', False)]
            visible_items.sort(key=lambda x: x.get('grade', 0), reverse=True)
            
            message += "🛍️ **판매 아이템**\n"
            for item in visible_items[:15]:  # 최대 15개만 표시
                grade_emoji = self.get_grade_emoji(item.get('grade', 1))
                grade_text = self.get_grade_text(item.get('grade', 1))
                item_name = item.get('name', '알 수 없음')
                item_type = self.get_item_type_text(item.get('type', 1))
                
                message += f"• {grade_emoji} **{item_name}** ({grade_text} {item_type})\n"
        else:
            message += "🛍️ **판매 아이템**: 없음\n"
        
        return message
    
    def format_item_search(self, item_name: str) -> str:
        """아이템 검색 결과를 디스코드 메시지 형식으로 포맷팅"""
        sellers = self.search_item(item_name)
        
        if not sellers:
            return f"❌ '{item_name}' 아이템을 판매하는 상인을 찾을 수 없습니다."
        
        message = f"🔍 **'{item_name}' 검색 결과** 🔍\n"
        message += "=" * 30 + "\n\n"
        
        for seller in sellers:
            if seller['숨김여부']:
                continue  # 숨김 아이템은 제외
                
            message += f"📍 **{seller['지역명']} - {seller['상인명']}**\n"
            message += f"🛍️ {seller['등급이모지']} **{seller['아이템명']}** ({seller['등급']} {seller['타입']})\n\n"
        
        return message
    
    def format_active_merchants(self) -> str:
        """현재 활성 상인을 디스코드 메시지 형식으로 포맷팅"""
        active_merchants = self.get_current_active_merchants()
        
        if not active_merchants:
            return "🔴 현재 활성화된 상인이 없습니다."
        
        message = "🟢 **현재 활성 상인** 🟢\n"
        message += "=" * 25 + "\n\n"
        
        for merchant in active_merchants:
            message += f"⏰ **{merchant['시작시간']}** ({merchant['지속시간']})\n"
            for active_merchant in merchant['활성상인들']:
                message += f"  • {active_merchant}\n"
            message += "\n"
        
        return message
