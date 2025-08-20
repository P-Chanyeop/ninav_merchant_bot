# 니나브 떠상봇 설치 가이드

## 🚀 빠른 설치

### 1. Python 확인
Python 3.8 이상이 설치되어 있는지 확인하세요:
```bash
python --version
```

### 2. 라이브러리 설치

#### 최소 설치 (권장)
```bash
pip install -r requirements-minimal.txt
```

#### 전체 설치 (모든 기능)
```bash
pip install -r requirements.txt
```

#### 개별 설치
```bash
pip install discord.py>=2.3.2
pip install requests>=2.31.0
```

### 3. 선택적 라이브러리 설치

더 나은 성능과 기능을 위해 추가 라이브러리를 설치할 수 있습니다:

```bash
# 환경 변수 관리 (토큰 보안)
pip install python-dotenv

# 더 나은 로깅 (색상 로그)
pip install colorlog

# 더 빠른 JSON 처리
pip install orjson
```

## 🔧 환경 설정

### 1. 디스코드 봇 생성
1. [Discord Developer Portal](https://discord.com/developers/applications) 접속
2. "New Application" 클릭
3. 봇 이름 입력 후 생성
4. "Bot" 탭으로 이동
5. "Add Bot" 클릭
6. 토큰 복사 (Reset Token으로 새 토큰 생성 가능)

### 2. 봇 권한 설정
봇에게 다음 권한을 부여하세요:
- Send Messages
- Read Message History
- Use Slash Commands (선택사항)

### 3. 봇 초대
1. "OAuth2" > "URL Generator" 탭
2. Scopes: "bot" 선택
3. Bot Permissions: 필요한 권한 선택
4. 생성된 URL로 봇을 서버에 초대

### 4. 채널 ID 확인
1. 디스코드에서 개발자 모드 활성화 (설정 > 고급 > 개발자 모드)
2. 알림받을 채널 우클릭 > "ID 복사"

## 🏃‍♂️ 실행

```bash
python 니나브_떠상봇.py
```

## 📋 시스템 요구사항

- **Python**: 3.8 이상
- **운영체제**: Windows, macOS, Linux
- **메모리**: 최소 512MB RAM
- **네트워크**: 인터넷 연결 필수

## 🐛 문제 해결

### 일반적인 오류

1. **ModuleNotFoundError**: 라이브러리가 설치되지 않음
   ```bash
   pip install discord.py requests
   ```

2. **discord.LoginFailure**: 잘못된 봇 토큰
   - 토큰을 다시 확인하거나 재생성하세요

3. **채널을 찾을 수 없음**: 잘못된 채널 ID
   - 채널 ID를 다시 확인하세요
   - 봇이 해당 채널에 접근 권한이 있는지 확인하세요

4. **tkinter 오류** (Linux):
   ```bash
   sudo apt-get install python3-tk
   ```

### 성능 최적화

- 모니터링 간격을 너무 짧게 설정하지 마세요 (최소 10초 권장)
- 안정적인 인터넷 연결을 유지하세요
- 봇 토큰을 안전하게 보관하세요

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. Python 버전 (3.8+)
2. 라이브러리 설치 상태
3. 봇 토큰 유효성
4. 네트워크 연결 상태
5. 디스코드 봇 권한
