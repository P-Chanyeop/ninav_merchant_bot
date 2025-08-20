# -*- coding: utf-8 -*-
"""
현재 실제 데이터와 봇 파싱 결과 비교 검증
"""

from final_live_merchant_bot import FinalLiveMerchantBot
from datetime import datetime

def verify_current_data():
    """현재 실제 데이터와 봇 결과 비교"""
    
    print("🔍 실제 사이트 데이터와 봇 파싱 결과 비교")
    print("=" * 60)
    
    # 실제 사이트에서 확인된 정보
    expected_merchants = [
        "아르테미스 - 벤",
        "베른 북부 - 피터", 
        "욘 - 라이티르",
        "베른 남부 - 에반",
        "로웬 - 세라한",
        "엘가시아 - 플라노스",
        "쿠르잔 북부 - 콜빈",
        "림레이크 남섬 - 재마"
    ]
    
    print(f"📋 실제 사이트 활성 상인 ({len(expected_merchants)}명):")
    for i, merchant in enumerate(expected_merchants, 1):
        print(f"  {i}. {merchant}")
    
    print(f"\n⏰ 실제 사이트 정보:")
    print(f"  시간: 오전 10:00 ~ 오후 3:30")
    print(f"  남은 시간: 약 3시간 58분")
    
    print(f"\n" + "="*60)
    
    # 봇으로 파싱한 결과
    print(f"🤖 봇 파싱 결과:")
    
    bot = FinalLiveMerchantBot()
    active_merchants = bot.get_current_active_merchants()
    
    print(f"📊 봇이 감지한 활성 상인 ({len(active_merchants)}명):")
    
    bot_merchants = []
    for i, merchant in enumerate(active_merchants, 1):
        merchant_name = f"{merchant['region_name']} - {merchant['npc_name']}"
        bot_merchants.append(merchant_name)
        
        # 남은 시간 계산
        now = datetime.now()
        time_left = merchant['end_time'] - now
        hours_left = int(time_left.total_seconds() / 3600)
        minutes_left = int((time_left.total_seconds() % 3600) / 60)
        
        print(f"  {i}. {merchant_name}")
        print(f"     마감시간: {merchant['end_time'].strftime('%H:%M:%S')}")
        print(f"     남은시간: {hours_left}시간 {minutes_left}분")
        
        # 주요 아이템 표시
        high_grade_items = [item for item in merchant['items'] if item['grade'] >= 3]
        if high_grade_items:
            print(f"     주요아이템: {', '.join([item['name'] for item in high_grade_items[:3]])}")
        print()
    
    print(f"" + "="*60)
    
    # 비교 결과
    print(f"📈 비교 결과:")
    
    # 상인 수 비교
    print(f"상인 수 - 실제: {len(expected_merchants)}명, 봇: {len(active_merchants)}명")
    
    if len(expected_merchants) == len(active_merchants):
        print("✅ 상인 수 일치!")
    else:
        print("❌ 상인 수 불일치!")
    
    # 상인 목록 비교
    print(f"\n상인 목록 비교:")
    
    found_merchants = []
    missing_merchants = []
    
    for expected in expected_merchants:
        found = False
        for bot_merchant in bot_merchants:
            if expected in bot_merchant or bot_merchant in expected:
                found = True
                found_merchants.append(expected)
                break
        
        if not found:
            missing_merchants.append(expected)
    
    print(f"✅ 일치하는 상인 ({len(found_merchants)}명):")
    for merchant in found_merchants:
        print(f"  - {merchant}")
    
    if missing_merchants:
        print(f"\n❌ 누락된 상인 ({len(missing_merchants)}명):")
        for merchant in missing_merchants:
            print(f"  - {merchant}")
    
    # 추가로 감지된 상인
    extra_merchants = []
    for bot_merchant in bot_merchants:
        found = False
        for expected in expected_merchants:
            if expected in bot_merchant or bot_merchant in expected:
                found = True
                break
        if not found:
            extra_merchants.append(bot_merchant)
    
    if extra_merchants:
        print(f"\n⚠️ 추가로 감지된 상인 ({len(extra_merchants)}명):")
        for merchant in extra_merchants:
            print(f"  - {merchant}")
    
    # 정확도 계산
    accuracy = len(found_merchants) / len(expected_merchants) * 100 if expected_merchants else 0
    print(f"\n📊 정확도: {accuracy:.1f}%")
    
    if accuracy >= 90:
        print("🎉 매우 정확한 파싱!")
    elif accuracy >= 70:
        print("👍 양호한 파싱")
    else:
        print("⚠️ 파싱 개선 필요")
    
    # Discord 메시지 형식으로 출력
    print(f"\n" + "="*60)
    print(f"💬 Discord 메시지 형식:")
    print(f"" + "="*60)
    
    discord_message = bot.format_current_merchants()
    print(discord_message)

if __name__ == "__main__":
    verify_current_data()
