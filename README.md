# 🤖 니나브 서버 떠돌이 상인 디스코드 봇

로스트아크 니나브 서버 전용 떠돌이 상인 알림 디스코드 봇입니다.

## 🌟 주요 기능

### 🔥 **실시간 떠상 알림**
- 5분마다 자동으로 떠상 상태 체크
- 새로운 상인 등장시 즉시 디스코드 알림
- 30분마다 정기 알림 (상인이 활성화되어 있을 때)

### 🎯 **정확한 데이터**
- kloa.gg에서 실시간 데이터 수집
- 니나브 서버 전용 필터링
- 아이템 등급, 타입 정보 포함

### 💬 **디스코드 명령어**
- `!떠상` - 현재 활성 떠돌이 상인 조회
- `!새로고침` - 데이터 수동 새로고침
- `!떠상검색 아이템명` - 특정 아이템 검색
- `!도움말` - 명령어 도움말

## 🚀 설치 및 실행

### 1. 필수 요구사항
```bash
pip install -r requirements.txt
```

### 2. Chrome Driver 설치
- [ChromeDriver 다운로드](https://chromedriver.chromium.org/)
- PATH에 추가하거나 프로젝트 폴더에 배치

### 3. 봇 실행
```bash
python selenium_merchant_fetcher.py
```

## 📁 주요 파일 설명

### 🤖 **메인 봇 파일들**
- `selenium_merchant_fetcher.py` - **Selenium 기반 떠상봇** (최신)
- `ninav_dynamic_bot.py` - 니나브 서버 전용 동적 데이터 봇
- `real_time_merchant_fetcher.py` - 실시간 데이터 가져오기 클래스

### 📊 **분석 및 테스트**
- `analyze_merchant_data.py` - 상인 데이터 분석
- `test_default_items.py` - 기본 아이템 테스트
- `verify_current_data.py` - 현재 데이터 검증

### 📚 **문서**
- `README_상인봇_사용법.md` - 상인봇 사용법
- `README_실시간_떠상봇.md` - 실시간 떠상봇 가이드
- `README_완전체_사용법.md` - 완전체 사용법
- `INSTALL.md` - 설치 가이드

## ⏰ 떠상 시간표

| 시간대 | 상태 |
|--------|------|
| 04:00 ~ 09:30 | 🟢 활성 |
| 10:00 ~ 15:30 | 🟢 활성 |
| 16:00 ~ 21:30 | 🟢 활성 |
| 22:00 ~ 03:30 | 🟢 활성 |
| 기타 시간 | 🔴 비활성 |

## 🛠️ 기술 스택

- **Python 3.8+**
- **Discord.py** - 디스코드 봇 API
- **Selenium** - 웹 자동화 및 데이터 수집
- **BeautifulSoup4** - HTML 파싱
- **Requests** - HTTP 요청

## 🔧 설정

### 디스코드 봇 토큰
봇 실행시 채널 ID만 입력하면 됩니다. (토큰은 코드에 하드코딩됨)

### Chrome 옵션
```python
chrome_options.add_argument('--headless')  # 브라우저 창 숨기기
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
```

## 📈 데이터 수집 방식

### Selenium 기반 (권장)
- `div.bg-elevated` 클래스의 두 번째 요소에서 데이터 추출
- 구조화된 HTML 파싱으로 정확한 데이터 수집
- 니나브 서버 자동 필터링

### 데이터 구조
```python
{
    'region_name': '유디아',
    'npc_name': '루카스',
    'group': 1,
    'items': [
        {
            'name': '모리나',
            'type': 1,  # 1=카드, 2=호감도, 3=특수
            'grade': 1,  # 1~5 등급
            'hidden': False
        }
    ]
}
```

## 🚨 알림 예시

```
🚨 떠돌이 상인 알림 (Selenium)
현재 3명의 상인이 활성화되어 있습니다!

📍 유디아 - 루카스
```
모리나 • 천둥 • 유디아 주술서
유디아 천연소금
```

📍 루테란 서부 - 말론
```
베르하트 • 카도건 • 레이크바 토마토 주스
사슬전쟁 실록 • 머리초
```

⏰ 마감까지 남은 시간: 2시간 23분 남음
🕐 마감 시간: 21:30
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트 관련 문의사항이 있으시면 GitHub Issues를 이용해주세요.

---

**⚠️ 주의사항**
- 이 봇은 니나브 서버 전용입니다
- kloa.gg 사이트 정책을 준수하여 사용해주세요
- 과도한 요청으로 인한 차단에 주의하세요
