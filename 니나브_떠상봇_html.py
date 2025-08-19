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
from typing import Optional, Dict, Any, List
from html_merchant_parser import HTMLMerchantParser

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
        self.root.title("니나브 떠상봇 HTML - Premium Discord Bot")
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
        title_label = ttk.Label(main_frame, text="🤖 니나브 떠상봇 HTML", style='Title.TLabel')
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="HTML 스크래핑 기반 상인 정보 모니터링 봇", style='Subtitle.TLabel')
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
        
        self.test_button = ttk.Button(control_frame, text="🔍 HTML 테스트", 
                                     command=self.test_html_parsing, style='Custom.TButton')
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
        
        footer_label = ttk.Label(footer_frame, text="© 2024 니나브 떠상봇 HTML - Premium Edition", 
                                style='Subtitle.TLabel')
        footer_label.pack()
        
    def setup_variables(self):
        """변수 초기화"""
        self.last_merchants = []
        self.html_parser = HTMLMerchantParser()
        
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
        
    def fetch_merchant_data(self) -> List[Dict]:
        """HTML에서 상인 데이터 가져오기"""
        try:
            merchants = self.html_parser.parse_all_merchants_from_page()
            if merchants:
                self.log_message(f"HTML에서 {len(merchants)}명의 상인 정보 가져오기 성공", "SUCCESS")
            else:
                self.log_message("HTML에서 상인 정보를 찾을 수 없음", "WARNING")
            return merchants
            
        except Exception as e:
            self.log_message(f"HTML 파싱 실패: {str(e)}", "ERROR")
            return []
            
    def format_merchant_data(self, merchants: List[Dict]) -> str:
        """상인 데이터를 디스코드 메시지 형식으로 포맷팅"""
        try:
            if not merchants:
                return "📭 현재 활성화된 떠돌이 상인이 없습니다."
            
            return self.html_parser.format_merchants_for_discord(merchants)
            
        except Exception as e:
            self.log_message(f"데이터 포맷팅 오류: {str(e)}", "ERROR")
            return f"❌ 데이터 처리 중 오류가 발생했습니다: {str(e)}"
    
    def merchants_changed(self, new_merchants: List[Dict]) -> bool:
        """상인 정보 변경 여부 확인"""
        if len(new_merchants) != len(self.last_merchants):
            return True
        
        # 간단한 비교 (지역, NPC명, 아이템 수로)
        for new_merchant in new_merchants:
            found = False
            for old_merchant in self.last_merchants:
                if (new_merchant['region'] == old_merchant['region'] and 
                    new_merchant['npc_name'] == old_merchant['npc_name'] and
                    len(new_merchant['items']) == len(old_merchant['items'])):
                    found = True
                    break
            if not found:
                return True
        
        return False
    
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
            
            merchants = self.fetch_merchant_data()
            if merchants:
                message = self.format_merchant_data(merchants)
                
                if len(message) > 2000:
                    chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
                    for chunk in chunks:
                        await ctx.send(chunk)
                else:
                    await ctx.send(message)
            else:
                await ctx.send("❌ 떠돌이 상인 정보를 가져올 수 없습니다.")
        
        @bot.command(name='떠상검색')
        async def search_merchant_command(ctx, *, search_term: str):
            """지역명 또는 아이템명으로 상인 검색"""
            self.log_message(f"{ctx.author}가 '{search_term}' 검색을 요청했습니다.", "INFO")
            
            merchants = self.fetch_merchant_data()
            if not merchants:
                await ctx.send("❌ 떠돌이 상인 정보를 가져올 수 없습니다.")
                return
            
            # 지역명으로 검색
            region_results = self.html_parser.search_merchant_by_region(merchants, search_term)
            
            # 아이템명으로 검색
            item_results = self.html_parser.search_merchant_by_item(merchants, search_term)
            
            # 결과 합치기 (중복 제거)
            all_results = region_results + [m for m in item_results if m not in region_results]
            
            if all_results:
                message = f"🔍 **'{search_term}' 검색 결과** 🔍\n"
                message += "=" * 30 + "\n\n"
                message += self.html_parser.format_merchants_for_discord(all_results)
                
                if len(message) > 2000:
                    chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
                    for chunk in chunks:
                        await ctx.send(chunk)
                else:
                    await ctx.send(message)
            else:
                await ctx.send(f"❌ '{search_term}'에 대한 검색 결과가 없습니다.")
        
        @bot.command(name='고급떠상')
        async def high_grade_merchants_command(ctx):
            """고등급 아이템을 파는 상인만 조회"""
            self.log_message(f"{ctx.author}가 고급 떠상을 요청했습니다.", "INFO")
            
            merchants = self.fetch_merchant_data()
            if not merchants:
                await ctx.send("❌ 떠돌이 상인 정보를 가져올 수 없습니다.")
                return
            
            high_grade_merchants = self.html_parser.get_high_grade_merchants(merchants, min_grade=3)
            
            if high_grade_merchants:
                message = "💎 **고등급 아이템 판매 상인** 💎\n"
                message += "=" * 30 + "\n\n"
                message += self.html_parser.format_merchants_for_discord(high_grade_merchants)
                
                if len(message) > 2000:
                    chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
                    for chunk in chunks:
                        await ctx.send(chunk)
                else:
                    await ctx.send(message)
            else:
                await ctx.send("📭 현재 고등급 아이템을 파는 상인이 없습니다.")
                
        @bot.command(name='도움말')
        async def help_command(ctx):
            """도움말 명령어"""
            help_text = """
🤖 **니나브 떠상봇 HTML 명령어**

**🏪 떠돌이 상인 관련:**
`!떠상` - 현재 떠돌이 상인 정보 조회
`!떠상검색 아르테미스` - 지역명으로 상인 검색
`!떠상검색 카마인` - 아이템명으로 상인 검색
`!고급떠상` - 고등급 아이템 판매 상인만 조회

**ℹ️ 기타:**
`!도움말` - 이 도움말 표시

**⚡ 자동 기능:**
봇이 자동으로 HTML을 파싱하여 떠돌이 상인 변경사항을 모니터링합니다.
            """
            await ctx.send(help_text)
        
        @tasks.loop(seconds=60)
        async def monitor_merchants():
            """떠돌이 상인 HTML 모니터링 루프"""
            if not self.is_monitoring:
                return
                
            try:
                channel_id = int(self.channel_entry.get().strip())
                channel = bot.get_channel(channel_id)
                
                if not channel:
                    self.log_message(f"채널 ID {channel_id}를 찾을 수 없습니다.", "ERROR")
                    return
                
                merchants = self.fetch_merchant_data()
                if not merchants:
                    return
                
                # 상인 정보 변경 확인
                if self.merchants_changed(merchants):
                    self.log_message(f"떠돌이 상인 정보 변경 감지! ({len(merchants)}명)", "SUCCESS")
                    message = self.format_merchant_data(merchants)
                    
                    if len(message) > 2000:
                        chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
                        for chunk in chunks:
                            await channel.send(chunk)
                    else:
                        await channel.send(message)
                    
                    self.last_merchants = merchants
                else:
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
        
    def test_html_parsing(self):
        """HTML 파싱 테스트"""
        self.log_message("HTML 파싱을 테스트하는 중...", "INFO")
        
        merchants = self.fetch_merchant_data()
        if merchants:
            formatted_data = self.format_merchant_data(merchants)
            self.log_message("HTML 파싱 테스트 성공!", "SUCCESS")
            self.log_message(f"발견된 상인 수: {len(merchants)}", "INFO")
            
            # 데이터 미리보기 (처음 500자만)
            preview = formatted_data[:500] + "..." if len(formatted_data) > 500 else formatted_data
            self.log_message("받은 데이터 미리보기:", "INFO")
            self.log_message(preview, "INFO")
        else:
            self.log_message("HTML 파싱 테스트 실패!", "ERROR")
    
    def update_status(self, status: str, color: str):
        """상태 업데이트"""
        self.status_label.config(text=status, fg=color)
        
    def run(self):
        """GUI 실행"""
        self.log_message("니나브 떠상봇 HTML이 시작되었습니다!", "SUCCESS")
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
