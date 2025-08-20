"""
설정 파일 - 환경 변수 또는 직접 입력으로 봇 설정
"""
import os
from dotenv import load_dotenv

# .env 파일 로드 (있는 경우)
load_dotenv()

def get_bot_config():
    """봇 설정 가져오기"""
    
    # 환경 변수에서 먼저 확인
    token = os.getenv('DISCORD_TOKEN')
    channel_id = os.getenv('CHANNEL_ID')
    
    # 환경 변수가 없으면 사용자 입력
    if not token:
        token = input("Discord 봇 토큰을 입력하세요: ").strip()
        if not token:
            raise ValueError("봇 토큰이 필요합니다!")
    
    if not channel_id:
        channel_id = input("알림을 보낼 채널 ID를 입력하세요: ").strip()
        if not channel_id or not channel_id.isdigit():
            raise ValueError("올바른 채널 ID가 필요합니다!")
    
    return token, int(channel_id)

# 사용 예시:
# from config import get_bot_config
# TOKEN, CHANNEL_ID = get_bot_config()
