import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import discord
from discord.ext import commands, tasks
import asyncio
import threading
import json
from datetime import datetime
import logging
from typing import Optional, Dict, Any
from merchant_parser import MerchantParser
from wandering_merchant_tracker import WanderingMerchantTracker

class Main:
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
        self.root.title("니나브 떠상봇 - Premium Discord Bot")
        self.root.geometry("800x700")
        self.root.configure(bg='#2C2F33')
        self.root.resizable(True, True)
        
        # 스타일 설정
        style = ttk.Style()
        style.theme_use('clam')
        
        # 커스텀 스타일 정의
        style.configure('Title.TLabel', 
                       background='#2C2F33', 
                       foreground='#7289DA', 
                       font=('Arial', 16, 'bold'))
        
        style.configure('Subtitle.TLabel', 
                       background='#2C2F33', 
                       foreground='#99AAB5', 
                       font=('Arial', 10))
        
        style.configure('Custom.TButton', 
                       background='#7289DA', 
                       foreground='white', 
                       font=('Arial', 10, 'bold'),
                       borderwidth=0)
        
        style.map('Custom.TButton',
                 background=[('active', '#5B6EAE')])
        
        style.configure('Stop.TButton', 
                       background='#E74C3C', 
                       foreground='white', 
                       font=('Arial', 10, 'bold'),
                       borderwidth=0)
        
        style.map('Stop.TButton',
                 background=[('active', '#C0392B')])
        
        # 메인 프레임
        main_frame = tk.Frame(self.root, bg='#2C2F33', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # 타이틀
        title_label = ttk.Label(main_frame, text="🤖 니나브 떠상봇", style='Title.TLabel')
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="KLOA 상인 정보 모니터링 봇", style='Subtitle.TLabel')
        subtitle_label.pack(pady=(0, 20))
        
        # 설정 프레임
        config_frame = tk.LabelFrame(main_frame, text="봇 설정", bg='#36393F', fg='#FFFFFF', 
                                   font=('Arial', 12, 'bold'), padx=15, pady=15)
        config_frame.pack(fill='x', pady=(0, 15))
        
        # 디스코드 토큰 입력
        tk.Label(config_frame, text="디스코드 봇 토큰:", bg='#36393F', fg='#FFFFFF', 
                font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        
        self.token_entry = tk.Entry(config_frame, width=50, show='*', bg='#40444B', fg='#FFFFFF',
                                   insertbackground='#FFFFFF', font=('Arial', 10))
        self.token_entry.grid(row=0, column=1, padx=(10, 0), pady=5, sticky='ew')
        
        # 채널 ID 입력
        tk.Label(config_frame, text="채널 ID:", bg='#36393F', fg='#FFFFFF', 
                font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
        
        self.channel_entry = tk.Entry(config_frame, width=50, bg='#40444B', fg='#FFFFFF',
                                     insertbackground='#FFFFFF', font=('Arial', 10))
        self.channel_entry.grid(row=1, column=1, padx=(10, 0), pady=5, sticky='ew')
        
        # 모니터링 간격 설정
        tk.Label(config_frame, text="모니터링 간격 (초):", bg='#36393F', fg='#FFFFFF', 
                font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
        
        self.interval_var = tk.StringVar(value="30")
        interval_spinbox = tk.Spinbox(config_frame, from_=10, to=300, textvariable=self.interval_var,
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
        
        self.test_button = ttk.Button(control_frame, text="🔍 API 테스트", 
                                     command=self.test_api, style='Custom.TButton')
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
        
        footer_label = ttk.Label(footer_frame, text="© 2024 니나브 떠상봇 - Premium Edition", 
                                style='Subtitle.TLabel')
        footer_label.pack()
        
    def setup_variables(self):
        """변수 초기화"""
        self.last_data = None
        self.api_url = "https://kloa.gg/_next/data/zg-3f6yHQunqL3skcaU9x/statistics/merchant.json"
        self.merchant_tracker = WanderingMerchantTracker()  # 떠돌이 상인 추적기 추가
        
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
        
    def fetch_merchant_data(self) -> Optional[Dict[Any, Any]]:
        """KLOA API에서 상인 데이터 가져오기"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(self.api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.log_message("API 데이터 가져오기 성공", "SUCCESS")
            return data
            
        except requests.exceptions.RequestException as e:
            self.log_message(f"API 요청 실패: {str(e)}", "ERROR")
            return None
        except json.JSONDecodeError as e:
            self.log_message(f"JSON 파싱 실패: {str(e)}", "ERROR")
            return None
        except Exception as e:
            self.log_message(f"예상치 못한 오류: {str(e)}", "ERROR")
            return None
            
    def format_merchant_data(self, data: Dict[Any, Any]) -> str:
        """상인 데이터를 디스코드 메시지 형식으로 포맷팅"""
        try:
            if not data or 'pageProps' not in data:
                return "❌ 데이터 형식이 올바르지 않습니다."
            
            # 새로운 파서 사용
            parser = MerchantParser(data)
            
            # 현재 활성 상인 정보 가져오기
            active_merchants_msg = parser.format_active_merchants()
            
            # 전체 상인 목록도 포함
            all_merchants_msg = parser.format_merchant_list()
            
            # 메시지 조합
            message = active_merchants_msg + "\n\n" + all_merchants_msg
            message += f"\n🕐 업데이트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return message
            
        except Exception as e:
            self.log_message(f"데이터 포맷팅 오류: {str(e)}", "ERROR")
            return f"❌ 데이터 처리 중 오류가 발생했습니다: {str(e)}"
    
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
            
        @bot.command(name='상인')
        async def merchant_command(ctx):
            """수동으로 상인 정보 요청"""
            self.log_message(f"{ctx.author}가 상인 정보를 요청했습니다.", "INFO")
            
            data = self.fetch_merchant_data()
            if data:
                message = self.format_merchant_data(data)
                
                # 메시지가 너무 길면 분할해서 전송
                if len(message) > 2000:
                    chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
                    for chunk in chunks:
                        await ctx.send(chunk)
                else:
                    await ctx.send(message)
            else:
                await ctx.send("❌ 상인 정보를 가져올 수 없습니다.")
        
        @bot.command(name='상인목록')
        async def merchant_list_command(ctx):
            """전체 상인 목록 조회"""
            self.log_message(f"{ctx.author}가 상인 목록을 요청했습니다.", "INFO")
            
            data = self.fetch_merchant_data()
            if data:
                try:
                    parser = MerchantParser(data)
                    message = parser.format_merchant_list()
                    
                    if len(message) > 2000:
                        chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
                        for chunk in chunks:
                            await ctx.send(chunk)
                    else:
                        await ctx.send(message)
                except Exception as e:
                    await ctx.send(f"❌ 상인 목록 처리 중 오류: {str(e)}")
            else:
                await ctx.send("❌ 상인 정보를 가져올 수 없습니다.")
        
        @bot.command(name='스케줄')
        async def schedule_command(ctx, day: str = None):
            """상인 스케줄 조회 (예: !스케줄 또는 !스케줄 월요일)"""
            self.log_message(f"{ctx.author}가 스케줄을 요청했습니다.", "INFO")
            
            data = self.fetch_merchant_data()
            if data:
                try:
                    parser = MerchantParser(data)
                    
                    # 요일 변환
                    target_day = None
                    if day:
                        day_map = {
                            '일요일': 0, '월요일': 1, '화요일': 2, '수요일': 3,
                            '목요일': 4, '금요일': 5, '토요일': 6,
                            '일': 0, '월': 1, '화': 2, '수': 3, '목': 4, '금': 5, '토': 6
                        }
                        target_day = day_map.get(day)
                    
                    message = parser.format_schedule(target_day)
                    
                    if len(message) > 2000:
                        chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
                        for chunk in chunks:
                            await ctx.send(chunk)
                    else:
                        await ctx.send(message)
                except Exception as e:
                    await ctx.send(f"❌ 스케줄 처리 중 오류: {str(e)}")
            else:
                await ctx.send("❌ 상인 정보를 가져올 수 없습니다.")
        
        @bot.command(name='상인정보')
        async def merchant_info_command(ctx, *, merchant_name: str):
            """특정 상인 상세 정보 조회 (예: !상인정보 벤)"""
            self.log_message(f"{ctx.author}가 {merchant_name} 상인 정보를 요청했습니다.", "INFO")
            
            data = self.fetch_merchant_data()
            if data:
                try:
                    parser = MerchantParser(data)
                    message = parser.format_merchant_detail(merchant_name)
                    
                    if len(message) > 2000:
                        chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
                        for chunk in chunks:
                            await ctx.send(chunk)
                    else:
                        await ctx.send(message)
                except Exception as e:
                    await ctx.send(f"❌ 상인 정보 처리 중 오류: {str(e)}")
            else:
                await ctx.send("❌ 상인 정보를 가져올 수 없습니다.")
        
        @bot.command(name='아이템검색')
        async def item_search_command(ctx, *, item_name: str):
            """아이템을 판매하는 상인 검색 (예: !아이템검색 카마인)"""
            self.log_message(f"{ctx.author}가 {item_name} 아이템을 검색했습니다.", "INFO")
            
            data = self.fetch_merchant_data()
            if data:
                try:
                    parser = MerchantParser(data)
                    message = parser.format_item_search(item_name)
                    
                    if len(message) > 2000:
                        chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
                        for chunk in chunks:
                            await ctx.send(chunk)
                    else:
                        await ctx.send(message)
                except Exception as e:
                    await ctx.send(f"❌ 아이템 검색 중 오류: {str(e)}")
            else:
                await ctx.send("❌ 상인 정보를 가져올 수 없습니다.")
        
        @bot.command(name='현재떠상')
        async def current_wandering_merchants(ctx):
            """현재 활성화된 떠돌이 상인 조회"""
            self.log_message(f"{ctx.author}가 현재 떠돌이 상인을 요청했습니다.", "INFO")
            
            data = self.fetch_merchant_data()
            if data:
                try:
                    active_merchants = self.merchant_tracker.get_active_merchants_now(data)
                    message = self.merchant_tracker.format_current_active_summary(active_merchants)
                    
                    if len(message) > 2000:
                        chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
                        for chunk in chunks:
                            await ctx.send(chunk)
                    else:
                        await ctx.send(message)
                except Exception as e:
                    await ctx.send(f"❌ 떠돌이 상인 정보 처리 중 오류: {str(e)}")
            else:
                await ctx.send("❌ 상인 정보를 가져올 수 없습니다.")
        
        @bot.command(name='떠상알림')
        async def force_merchant_check(ctx):
            """수동으로 떠돌이 상인 변경사항 확인"""
            self.log_message(f"{ctx.author}가 수동 떠상 확인을 요청했습니다.", "INFO")
            
            data = self.fetch_merchant_data()
            if data:
                try:
                    changes = self.merchant_tracker.check_merchant_changes(data)
                    
                    if changes['new_merchants']:
                        alert_message = self.merchant_tracker.format_new_merchant_alert(changes['new_merchants'])
                        await ctx.send(alert_message)
                    elif changes['ending_merchants']:
                        ending_message = self.merchant_tracker.format_ending_merchant_alert(changes['ending_merchants'])
                        await ctx.send(ending_message)
                    else:
                        active_merchants = self.merchant_tracker.get_active_merchants_now(data)
                        summary_message = self.merchant_tracker.format_current_active_summary(active_merchants)
                        await ctx.send(summary_message)
                        
                except Exception as e:
                    await ctx.send(f"❌ 떠상 확인 중 오류: {str(e)}")
            else:
                await ctx.send("❌ 상인 정보를 가져올 수 없습니다.")
                
        @bot.command(name='도움말')
        async def help_command(ctx):
            """도움말 명령어"""
            help_text = """
🤖 **니나브 떠상봇 명령어**

**🚨 실시간 떠돌이 상인 알림:**
• 새로운 떠돌이 상인 등장시 자동 알림
• 마감 30분 전 알림
• 판매 아이템 및 마감시간 표시

**📋 수동 명령어:**
`!현재떠상` - 현재 활성화된 떠돌이 상인 조회
`!떠상알림` - 수동으로 떠상 변경사항 확인
`!상인목록` - 전체 상인 목록 조회
`!스케줄` - 오늘의 상인 스케줄 조회
`!상인정보 벤` - 특정 상인의 상세 정보 조회
`!아이템검색 카마인` - 특정 아이템을 파는 상인 찾기
`!도움말` - 이 도움말 표시

**⚡ 자동 기능:**
봇이 자동으로 떠돌이 상인 등장/마감을 실시간 모니터링합니다.
            """
            await ctx.send(help_text)
        
        @tasks.loop(seconds=30)
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
                
                data = self.fetch_merchant_data()
                if not data:
                    return
                
                # 떠돌이 상인 변경사항 확인
                changes = self.merchant_tracker.check_merchant_changes(data)
                
                # 새로운 상인 등장 알림
                if changes['new_merchants']:
                    self.log_message(f"새로운 상인 {len(changes['new_merchants'])}명 등장!", "SUCCESS")
                    alert_message = self.merchant_tracker.format_new_merchant_alert(changes['new_merchants'])
                    
                    if len(alert_message) > 2000:
                        chunks = [alert_message[i:i+2000] for i in range(0, len(alert_message), 2000)]
                        for chunk in chunks:
                            await channel.send(chunk)
                    else:
                        await channel.send(alert_message)
                
                # 마감 임박 상인 알림 (30분 전)
                if changes['ending_merchants']:
                    self.log_message(f"마감 임박 상인 {len(changes['ending_merchants'])}명", "WARNING")
                    ending_message = self.merchant_tracker.format_ending_merchant_alert(changes['ending_merchants'])
                    await channel.send(ending_message)
                
                # 사라진 상인 로그 (Discord에는 보내지 않음)
                if changes['disappeared_merchants']:
                    self.log_message(f"상인 {len(changes['disappeared_merchants'])}명 마감됨", "INFO")
                
                # 변경사항이 없을 때는 로그만
                if not any(changes.values()):
                    self.log_message("떠돌이 상인 변경사항 없음", "INFO")
                    
            except ValueError:
                self.log_message("올바른 채널 ID를 입력해주세요.", "ERROR")
            except Exception as e:
                self.log_message(f"모니터링 오류: {str(e)}", "ERROR")
        
        # 모니터링 간격 업데이트
        @tasks.loop(seconds=1)
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
        
        self.log_message("봇을 시작하는 중...", "INFO")
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
        
    def test_api(self):
        """API 테스트"""
        self.log_message("API 연결을 테스트하는 중...", "INFO")
        
        data = self.fetch_merchant_data()
        if data:
            formatted_data = self.format_merchant_data(data)
            self.log_message("API 테스트 성공!", "SUCCESS")
            self.log_message("받은 데이터 미리보기:", "INFO")
            
            # 데이터 미리보기 (처음 500자만)
            preview = formatted_data[:500] + "..." if len(formatted_data) > 500 else formatted_data
            self.log_message(preview, "INFO")
        else:
            self.log_message("API 테스트 실패!", "ERROR")
    
    def update_status(self, status: str, color: str):
        """상태 업데이트"""
        self.status_label.config(text=status, fg=color)
        
    def run(self):
        """GUI 실행"""
        self.log_message("니나브 떠상봇이 시작되었습니다!", "SUCCESS")
        self.log_message("봇 토큰과 채널 ID를 입력한 후 '봇 시작' 버튼을 클릭하세요.", "INFO")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log_message("프로그램이 종료되었습니다.", "INFO")
        finally:
            if self.bot:
                self.stop_bot()

if __name__ == "__main__":
    app = Main()
    app.run()
