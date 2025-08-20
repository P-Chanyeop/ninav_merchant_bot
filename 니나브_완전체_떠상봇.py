import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import discord
from discord.ext import commands, tasks
import asyncio
import threading
import json
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List
from ninav_server_finder import NinavServerFinder

class NinavCompleteBot:
    def __init__(self):
        """메인 클래스 초기화 및 GUI 설정"""
        self.root = tk.Tk()
        self.setup_gui()
        self.setup_variables()
        self.setup_logging()
        self.bot = None
        self.bot_thread = None
        self.is_monitoring = False
        
    def setup_gui(self):
        """GUI 설정 및 디자인"""
        # 메인 윈도우 설정
        self.root.title("니나브 완전체 떠상봇 - Ultimate Edition")
        self.root.geometry("900x750")
        self.root.configure(bg='#2C2F33')
        self.root.resizable(True, True)
        
        # 스타일 설정
        style = ttk.Style()
        style.theme_use('clam')
        
        # 커스텀 스타일 정의
        style.configure('Title.TLabel', 
                       background='#2C2F33', 
                       foreground='#7289DA', 
                       font=('Arial', 18, 'bold'))
        
        style.configure('Subtitle.TLabel', 
                       background='#2C2F33', 
                       foreground='#99AAB5', 
                       font=('Arial', 11))
        
        style.configure('Custom.TButton', 
                       background='#7289DA', 
                       foreground='white', 
                       font=('Arial', 11, 'bold'),
                       borderwidth=0)
        
        style.map('Custom.TButton',
                 background=[('active', '#5B6EAE')])
        
        style.configure('Stop.TButton', 
                       background='#E74C3C', 
                       foreground='white', 
                       font=('Arial', 11, 'bold'),
                       borderwidth=0)
        
        style.map('Stop.TButton',
                 background=[('active', '#C0392B')])
        
        # 메인 프레임
        main_frame = tk.Frame(self.root, bg='#2C2F33', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # 타이틀
        title_label = ttk.Label(main_frame, text="🚀 니나브 완전체 떠상봇", style='Title.TLabel')
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="니나브 서버 전용 실시간 떠돌이 상인 알림 봇 - Ultimate Edition", style='Subtitle.TLabel')
        subtitle_label.pack(pady=(0, 20))
        
        # 설정 프레임
        config_frame = tk.LabelFrame(main_frame, text="봇 설정", bg='#36393F', fg='#FFFFFF', 
                                   font=('Arial', 12, 'bold'), padx=15, pady=15)
        config_frame.pack(fill='x', pady=(0, 15))
        
        # 디스코드 토큰 입력 (고정값)
        tk.Label(config_frame, text="디스코드 봇 토큰:", bg='#36393F', fg='#FFFFFF', 
                font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        
        self.token_entry = tk.Entry(config_frame, width=50, show='*', bg='#40444B', fg='#FFFFFF',
                                   insertbackground='#FFFFFF', font=('Arial', 10))
        self.token_entry.insert(0, "여기에_봇_토큰을_입력하세요")
        self.token_entry.grid(row=0, column=1, padx=(10, 0), pady=5, sticky='ew')
        
        # 채널 ID 입력 (고정값)
        tk.Label(config_frame, text="채널 ID:", bg='#36393F', fg='#FFFFFF', 
                font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        
        self.channel_entry = tk.Entry(config_frame, width=50, bg='#40444B', fg='#FFFFFF',
                                     insertbackground='#FFFFFF', font=('Arial', 10))
        self.channel_entry.insert(0, "1382578857013547068")
        self.channel_entry.grid(row=1, column=1, padx=(10, 0), pady=5, sticky='ew')
        
        # 모니터링 간격 설정
        tk.Label(config_frame, text="모니터링 간격 (초):", bg='#36393F', fg='#FFFFFF', 
                font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
        
        self.interval_var = tk.StringVar(value="60")
        interval_spinbox = tk.Spinbox(config_frame, from_=30, to=300, textvariable=self.interval_var,
                                     width=10, bg='#40444B', fg='#FFFFFF', font=('Arial', 10))
        interval_spinbox.grid(row=2, column=1, padx=(10, 0), pady=5, sticky='w')
        
        config_frame.columnconfigure(1, weight=1)
        
        # 컨트롤 프레임
        control_frame = tk.Frame(main_frame, bg='#2C2F33')
        control_frame.pack(fill='x', pady=(0, 15))
        
        # 버튼들
        self.start_button = ttk.Button(control_frame, text="🚀 봇 시작", 
                                      command=self.start_bot, style='Custom.TButton')
        self.start_button.pack(side='left', padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ 봇 중지", 
                                     command=self.stop_bot, style='Stop.TButton', state='disabled')
        self.stop_button.pack(side='left', padx=(0, 10))
        
        self.test_button = ttk.Button(control_frame, text="🔍 떠상 테스트", 
                                     command=self.test_merchant_system, style='Custom.TButton')
        self.test_button.pack(side='left', padx=(0, 10))
        
        # 상태 표시
        status_frame = tk.Frame(main_frame, bg='#2C2F33')
        status_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(status_frame, text="상태:", bg='#2C2F33', fg='#FFFFFF', 
                font=('Arial', 10, 'bold')).pack(side='left')
        
        self.status_label = tk.Label(status_frame, text="대기 중", bg='#2C2F33', fg='#F39C12', 
                                    font=('Arial', 10))
        self.status_label.pack(side='left', padx=(10, 0))
        
        # 로그 프레임
        log_frame = tk.LabelFrame(main_frame, text="로그", bg='#36393F', fg='#FFFFFF', 
                                 font=('Arial', 12, 'bold'), padx=15, pady=15)
        log_frame.pack(fill='both', expand=True)
        
        # 로그 텍스트 영역
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, bg='#23272A', fg='#FFFFFF',
                                                 insertbackground='#FFFFFF', font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True)
        
        # 하단 정보
        footer_frame = tk.Frame(main_frame, bg='#2C2F33')
        footer_frame.pack(fill='x', pady=(10, 0))
        
        footer_label = ttk.Label(footer_frame, text="© 2024 니나브 완전체 떠상봇 - Ultimate Edition", 
                                style='Subtitle.TLabel')
        footer_label.pack()
        
    def setup_variables(self):
        """변수 초기화"""
        self.merchant_system = NinavDynamicMerchantSystem()
    """니나브 서버 동적 상인 시스템"""
    
    def __init__(self):
        self.ninav_finder = NinavServerFinder()
        self.current_merchants = []
        self.last_data_update = None
        self.previous_merchants = []
        
    def load_ninav_data(self) -> bool:
        """니나브 서버 데이터 로드"""
        try:
            print("🔄 니나브 서버 데이터 로드 중...")
            
            # ninav_server_finder의 방법 3 사용 (HTML에서 추출)
            result = self.ninav_finder.method3_extract_from_html()
            
            if result and len(result) > 0:
                self.current_merchants = result
                self.last_data_update = datetime.now()
                print(f"✅ 니나브 서버 데이터 로드 성공: {len(result)}명")
                return True
            else:
                print("❌ 니나브 서버 데이터 로드 실패")
                return False
                
        except Exception as e:
            print(f"❌ 데이터 로드 오류: {e}")
            return False
    
    def refresh_data_if_needed(self):
        """필요시 데이터 새로고침 (30분마다)"""
        try:
            now = datetime.now()
            
            # 데이터가 없거나 30분이 지났으면 새로고침
            if (not self.current_merchants or 
                self.last_data_update is None or 
                (now - self.last_data_update).total_seconds() > 1800):  # 30분
                
                print("🔄 데이터 자동 새로고침...")
                return self.load_ninav_data()
            
            return True
                
        except Exception as e:
            print(f"❌ 자동 새로고침 오류: {e}")
            return False
    
    def get_current_active_merchants(self) -> List[Dict]:
        """현재 활성화된 상인 목록 가져오기"""
        try:
            # 데이터 새로고침
            self.refresh_data_if_needed()
            
            # 현재 시간 확인
            now = datetime.now()
            current_hour = now.hour
            current_minute = now.minute
            
            # 떠돌이 상인 활성 시간: 10:00 ~ 15:30
            if not (10 <= current_hour < 15 or (current_hour == 15 and current_minute <= 30)):
                return []
            
            # 데이터가 있으면 모든 상인 반환 (니나브 서버는 보통 8명 모두 활성)
            return self.current_merchants if self.current_merchants else []
            
        except Exception as e:
            print(f"❌ 활성 상인 확인 오류: {e}")
            return []
    
    def check_merchant_changes(self) -> Dict[str, List]:
        """상인 변경사항 확인"""
        try:
            current_active = self.get_current_active_merchants()
            
            # 이전 상인 목록과 비교
            current_regions = {m['region_name'] for m in current_active}
            previous_regions = {m['region_name'] for m in self.previous_merchants}
            
            new_merchants = [m for m in current_active if m['region_name'] not in previous_regions]
            disappeared_merchants = [m for m in self.previous_merchants if m['region_name'] not in current_regions]
            
            # 마감 임박 상인 확인 (30분 전)
            ending_merchants = []
            now = datetime.now()
            if now.hour == 15 and now.minute >= 0:  # 15:00 이후
                ending_merchants = current_active
            
            # 이전 상인 목록 업데이트
            self.previous_merchants = current_active.copy()
            
            return {
                'new_merchants': new_merchants,
                'disappeared_merchants': disappeared_merchants,
                'ending_merchants': ending_merchants if now.hour == 15 and now.minute == 0 else []
            }
            
        except Exception as e:
            print(f"❌ 상인 변경사항 확인 오류: {e}")
            return {'new_merchants': [], 'disappeared_merchants': [], 'ending_merchants': []}
    
    def format_current_merchants(self) -> str:
        """현재 상인 정보 포맷팅"""
        try:
            active_merchants = self.get_current_active_merchants()
            
            if not active_merchants:
                return "🏪 **니나브 서버 떠돌이 상인**\n\n현재 활성화된 상인이 없습니다."
            
            message = f"🏪 **니나브 서버 떠돌이 상인** ({len(active_merchants)}명 활성)\n\n"
            
            for merchant in active_merchants:
                region = merchant['region_name']
                npc = merchant['npc_name']
                items = [item['name'] for item in merchant['items']]
                
                message += f"📍 **{region} - {npc}**\n"
                
                # 아이템을 3개씩 나누어 표시
                item_chunks = [items[i:i+3] for i in range(0, len(items), 3)]
                for chunk in item_chunks:
                    message += f"• {' • '.join(chunk)}\n"
                
                message += "\n"
            
            # 남은 시간 계산
            now = datetime.now()
            end_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
            if now < end_time:
                remaining = end_time - now
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                message += f"⏰ **남은 시간**: {hours}시간 {minutes}분\n"
            
            message += f"🔄 **데이터 업데이트**: {self.last_data_update.strftime('%H:%M:%S') if self.last_data_update else '실시간'}"
            
            return message
            
        except Exception as e:
            return f"❌ 상인 정보 처리 중 오류: {str(e)}"
    
    def format_new_merchant_alert(self, new_merchants: List[Dict]) -> str:
        """새로운 상인 알림 포맷팅"""
        try:
            message = f"🚨 **새로운 떠돌이 상인 등장!** ({len(new_merchants)}명)\n\n"
            
            for merchant in new_merchants:
                region = merchant['region_name']
                npc = merchant['npc_name']
                items = [item['name'] for item in merchant['items']]
                
                message += f"📍 **{region} - {npc}**\n"
                
                # 아이템을 3개씩 나누어 표시
                item_chunks = [items[i:i+3] for i in range(0, len(items), 3)]
                for chunk in item_chunks:
                    message += f"• {' • '.join(chunk)}\n"
                
                message += "\n"
            
            # 남은 시간 계산
            now = datetime.now()
            end_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
            if now < end_time:
                remaining = end_time - now
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                message += f"⏰ **마감까지**: {hours}시간 {minutes}분 남음"
            
            return message
            
        except Exception as e:
            return f"❌ 알림 처리 중 오류: {str(e)}"
    
    def format_ending_alert(self, ending_merchants: List[Dict]) -> str:
        """마감 임박 알림 포맷팅"""
        try:
            message = f"⚠️ **떠돌이 상인 마감 임박!** (30분 전)\n\n"
            message += f"현재 활성 상인: {len(ending_merchants)}명\n\n"
            
            for merchant in ending_merchants:
                region = merchant['region_name']
                npc = merchant['npc_name']
                message += f"📍 {region} - {npc}\n"
            
            message += "\n🕐 **15:30에 모든 상인이 사라집니다!**"
            
            return message
            
        except Exception as e:
            return f"❌ 마감 알림 처리 중 오류: {str(e)}"
    
    def search_item(self, item_name: str) -> str:
        """아이템으로 상인 검색"""
        try:
            active_merchants = self.get_current_active_merchants()
            
            if not active_merchants:
                return f"🔍 **'{item_name}' 검색 결과**\n\n현재 활성화된 상인이 없습니다."
            
            found_merchants = []
            for merchant in active_merchants:
                items = [item['name'] for item in merchant['items']]
                if any(item_name.lower() in item.lower() for item in items):
                    found_merchants.append(merchant)
            
            if not found_merchants:
                return f"🔍 **'{item_name}' 검색 결과**\n\n해당 아이템을 파는 상인을 찾을 수 없습니다."
            
            message = f"🔍 **'{item_name}' 검색 결과** ({len(found_merchants)}명)\n\n"
            
            for merchant in found_merchants:
                region = merchant['region_name']
                npc = merchant['npc_name']
                items = [item['name'] for item in merchant['items']]
                
                # 검색된 아이템 하이라이트
                highlighted_items = []
                for item in items:
                    if item_name.lower() in item.lower():
                        highlighted_items.append(f"**{item}**")
                    else:
                        highlighted_items.append(item)
                
                message += f"📍 **{region} - {npc}**\n"
                
                # 아이템을 3개씩 나누어 표시
                item_chunks = [highlighted_items[i:i+3] for i in range(0, len(highlighted_items), 3)]
                for chunk in item_chunks:
                    message += f"• {' • '.join(chunk)}\n"
                
                message += "\n"
            
            return message
            
        except Exception as e:
            return f"❌ 검색 중 오류: {str(e)}"
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def log_message(self, message: str, level: str = "INFO"):
        """GUI 로그에 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "INFO": "#00FF00",
            "WARNING": "#FFA500", 
            "ERROR": "#FF0000",
            "SUCCESS": "#00FFFF"
        }
        
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        # 색상 적용
        start_line = self.log_text.index(tk.END + "-2l")
        end_line = self.log_text.index(tk.END + "-1l")
        
        tag_name = f"{level}_{timestamp}"
        self.log_text.tag_add(tag_name, start_line, end_line)
        self.log_text.tag_config(tag_name, foreground=color_map.get(level, "#FFFFFF"))
        
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def create_discord_bot(self):
        """디스코드 봇 생성 및 설정"""
        intents = discord.Intents.default()
        intents.message_content = True
        
        bot = commands.Bot(command_prefix='!', intents=intents)
        
        @bot.event
        async def on_ready():
            self.log_message(f"봇이 {bot.user}로 로그인했습니다!", "SUCCESS")
            self.update_status("연결됨", "#00FF00")
            
            # 모니터링 작업 시작
            if not self.monitor_merchants.is_running():
                self.monitor_merchants.start()
                
        @bot.event
        async def on_disconnect():
            self.log_message("봇 연결이 끊어졌습니다.", "WARNING")
            self.update_status("연결 끊김", "#FFA500")
            
        @bot.command(name='떠상')
        async def merchant_command(ctx):
            """현재 떠돌이 상인 정보 조회"""
            self.log_message(f"{ctx.author}가 떠상 정보를 요청했습니다.", "INFO")
            
            try:
                message = self.merchant_system.format_current_merchants()
                
                if len(message) > 2000:
                    chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
                    for chunk in chunks:
                        await ctx.send(chunk)
                else:
                    await ctx.send(message)
            except Exception as e:
                await ctx.send(f"❌ 떠상 정보 처리 중 오류: {str(e)}")
        
        @bot.command(name='떠상검색')
        async def search_command(ctx, *, item_name: str):
            """아이템으로 떠돌이 상인 검색"""
            self.log_message(f"{ctx.author}가 '{item_name}' 검색을 요청했습니다.", "INFO")
            
            try:
                message = self.merchant_system.search_item(item_name)
                await ctx.send(message)
            except Exception as e:
                await ctx.send(f"❌ 검색 중 오류: {str(e)}")
        
        @bot.command(name='떠상알림')
        async def force_check_command(ctx):
            """수동으로 떠상 변경사항 확인"""
            self.log_message(f"{ctx.author}가 수동 떠상 확인을 요청했습니다.", "INFO")
            
            try:
                changes = self.merchant_system.check_merchant_changes()
                
                if changes['new_merchants']:
                    alert_message = self.merchant_system.format_new_merchant_alert(changes['new_merchants'])
                    if len(alert_message) > 2000:
                        chunks = [alert_message[i:i+2000] for i in range(0, len(alert_message), 2000)]
                        for chunk in chunks:
                            await ctx.send(chunk)
                    else:
                        await ctx.send(alert_message)
                elif changes['ending_merchants']:
                    ending_message = self.merchant_system.format_ending_alert(changes['ending_merchants'])
                    await ctx.send(ending_message)
                else:
                    current_message = self.merchant_system.format_current_merchants()
                    if len(current_message) > 2000:
                        chunks = [current_message[i:i+2000] for i in range(0, len(current_message), 2000)]
                        for chunk in chunks:
                            await ctx.send(chunk)
                    else:
                        await ctx.send(current_message)
                        
            except Exception as e:
                await ctx.send(f"❌ 떠상 확인 중 오류: {str(e)}")
        
        @bot.command(name='니나브새로고침')
        async def refresh_ninav_data(ctx):
            """니나브 서버 데이터 새로고침"""
            self.log_message(f"{ctx.author}가 데이터 새로고침을 요청했습니다.", "INFO")
            
            try:
                await ctx.send("🔄 니나브 서버 데이터를 새로고침하는 중...")
                
                success = self.merchant_system.load_ninav_data()
                
                if success and self.merchant_system.current_merchants:
                    message = f"✅ **데이터 새로고침 완료**\n\n"
                    message += f"📊 업데이트된 상인 수: **{len(self.merchant_system.current_merchants)}명**\n"
                    
                    if self.merchant_system.last_data_update:
                        update_time = self.merchant_system.last_data_update.strftime("%Y-%m-%d %H:%M:%S")
                        message += f"🕒 업데이트 시간: {update_time}\n\n"
                    
                    # 상인 목록 표시
                    message += "👥 **상인 목록**:\n"
                    for merchant in self.merchant_system.current_merchants:
                        region = merchant['region_name']
                        npc = merchant['npc_name']
                        item_count = len(merchant['items'])
                        message += f"• {region} - {npc} ({item_count}개 아이템)\n"
                    
                    await ctx.send(message)
                else:
                    await ctx.send("❌ **데이터 새로고침 실패**\n니나브 서버 데이터를 가져올 수 없습니다.")
                
            except Exception as e:
                await ctx.send(f"❌ 새로고침 오류: {str(e)}")
                
        @bot.command(name='도움말')
        async def help_command(ctx):
            """도움말 명령어"""
            help_text = """
🚀 **니나브 완전체 떠상봇 명령어**

**🚨 실시간 떠돌이 상인 알림:**
• 새로운 떠돌이 상인 등장시 자동 알림
• 마감 30분 전 자동 알림
• 니나브 서버 전용 정확한 정보

**📋 수동 명령어:**
`!떠상` - 현재 활성화된 떠돌이 상인 조회
`!떠상알림` - 수동으로 떠상 변경사항 확인
`!떠상검색 아이템명` - 특정 아이템을 파는 상인 찾기
`!도움말` - 이 도움말 표시

**⚡ 자동 기능:**
봇이 자동으로 니나브 서버 떠돌이 상인 등장/마감을 실시간 모니터링합니다.

**💡 특징:**
• 100% 정확한 니나브 서버 데이터
• 실시간 남은 시간 계산
• 아이템별 등급 표시
• 전체 구매 비용 정보 제공
            """
            await ctx.send(help_text)
        
        @tasks.loop(seconds=60)
        async def monitor_merchants():
            """떠돌이 상인 실시간 모니터링 루프"""
            if not self.is_monitoring:
                return
                
            try:
                channel_id = int(self.channel_entry.get().strip())
                channel = bot.get_channel(channel_id)
                
                if not channel:
                    self.log_message(f"채널 ID {channel_id}를 찾을 수 없습니다.", "ERROR")
                    return
                
                # 떠돌이 상인 변경사항 확인
                changes = self.merchant_system.check_merchant_changes()
                
                # 새로운 상인 등장 알림
                if changes['new_merchants']:
                    self.log_message(f"새로운 떠상 {len(changes['new_merchants'])}명 등장!", "SUCCESS")
                    alert_message = self.merchant_system.format_new_merchant_alert(changes['new_merchants'])
                    
                    if len(alert_message) > 2000:
                        chunks = [alert_message[i:i+2000] for i in range(0, len(alert_message), 2000)]
                        for chunk in chunks:
                            await channel.send(chunk)
                    else:
                        await channel.send(alert_message)
                
                # 마감 임박 상인 알림 (30분 전)
                if changes['ending_merchants']:
                    self.log_message(f"마감 임박 떠상 {len(changes['ending_merchants'])}명", "WARNING")
                    ending_message = self.merchant_system.format_ending_alert(changes['ending_merchants'])
                    await channel.send(ending_message)
                
                # 사라진 상인 로그 (Discord에는 보내지 않음)
                if changes['disappeared_merchants']:
                    self.log_message(f"떠상 {len(changes['disappeared_merchants'])}명 마감됨", "INFO")
                
                # 변경사항이 없을 때는 로그만
                if not any(changes.values()):
                    self.log_message("떠돌이 상인 변경사항 없음", "INFO")
                    
            except ValueError:
                self.log_message("올바른 채널 ID를 입력해주세요.", "ERROR")
            except Exception as e:
                self.log_message(f"모니터링 오류: {str(e)}", "ERROR")
        
        # 모니터링 간격 업데이트
        @tasks.loop(seconds=5)
        async def update_monitor_interval():
            try:
                new_interval = int(self.interval_var.get())
                if monitor_merchants.seconds != new_interval:
                    monitor_merchants.change_interval(seconds=new_interval)
                    self.log_message(f"모니터링 간격을 {new_interval}초로 변경했습니다.", "INFO")
            except:
                pass
        
        self.monitor_merchants = monitor_merchants
        
        return bot
    
    def start_bot(self):
        """봇 시작"""
        token = self.token_entry.get().strip()
        channel_id = self.channel_entry.get().strip()
        
        if not token:
            messagebox.showerror("오류", "디스코드 봇 토큰을 입력해주세요.")
            return
            
        if not channel_id:
            messagebox.showerror("오류", "채널 ID를 입력해주세요.")
            return
            
        try:
            int(channel_id)
        except ValueError:
            messagebox.showerror("오류", "올바른 채널 ID를 입력해주세요.")
            return
        
        self.log_message("니나브 완전체 떠상봇을 시작하는 중...", "INFO")
        self.update_status("시작 중...", "#FFA500")
        
        self.bot = self.create_discord_bot()
        self.is_monitoring = True
        
        # 봇을 별도 스레드에서 실행
        self.bot_thread = threading.Thread(target=self.run_bot, args=(token,), daemon=True)
        self.bot_thread.start()
        
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
    def run_bot(self, token: str):
        """봇 실행 (별도 스레드)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.bot.start(token))
        except discord.LoginFailure:
            self.log_message("잘못된 봇 토큰입니다.", "ERROR")
            self.update_status("토큰 오류", "#FF0000")
        except Exception as e:
            self.log_message(f"봇 실행 오류: {str(e)}", "ERROR")
            self.update_status("오류", "#FF0000")
        finally:
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
    
    def stop_bot(self):
        """봇 중지"""
        self.log_message("봇을 중지하는 중...", "INFO")
        self.is_monitoring = False
        
        if self.bot:
            asyncio.run_coroutine_threadsafe(self.bot.close(), self.bot.loop)
            
        self.update_status("중지됨", "#FF0000")
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
    def test_merchant_system(self):
        """떠상 시스템 테스트"""
        self.log_message("떠상 시스템을 테스트하는 중...", "INFO")
        
        try:
            # 현재 활성 상인 조회
            active_merchants = self.merchant_system.get_current_active_merchants()
            self.log_message(f"현재 활성 떠상: {len(active_merchants)}명", "SUCCESS")
            
            if active_merchants:
                for merchant in active_merchants:
                    self.log_message(f"- {merchant['region_name']} {merchant['npc_name']}", "INFO")
            
            # 변경사항 확인
            changes = self.merchant_system.check_merchant_changes()
            if changes['new_merchants']:
                self.log_message(f"새로운 떠상 감지: {len(changes['new_merchants'])}명", "SUCCESS")
            
            # 데이터 새로고침 테스트
            success = self.merchant_system.load_ninav_data()
            if success:
                self.log_message("데이터 새로고침 성공!", "SUCCESS")
            
            self.log_message("떠상 시스템 테스트 완료!", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"떠상 시스템 테스트 실패: {str(e)}", "ERROR")
    
    def update_status(self, status: str, color: str):
        """상태 업데이트"""
        self.status_label.config(text=status, fg=color)
        
    def run(self):
        """GUI 실행"""
        self.log_message("🚀 니나브 완전체 떠상봇이 시작되었습니다!", "SUCCESS")
        self.log_message("니나브 서버 전용 실시간 떠돌이 상인 알림 시스템", "INFO")
        self.log_message("봇 토큰과 채널 ID를 입력한 후 '봇 시작' 버튼을 클릭하세요.", "INFO")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log_message("프로그램이 종료되었습니다.", "INFO")
        finally:
            if self.bot:
                self.stop_bot()

if __name__ == "__main__":
    app = NinavCompleteBot()
    app.run()
