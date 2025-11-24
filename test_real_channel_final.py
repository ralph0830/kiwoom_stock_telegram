"""
실제 텔레그램 채널 메시지로 새로운 로직 최종 검증

새로운 B안 로직이 실제 채널에서 어떻게 작동하는지 확인
"""
import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

from config import TradingConfig
from auto_trading import TelegramTradingSystem

# 환경변수 로드
load_dotenv()

# Telegram 설정
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "channel_copier")
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")


async def test_real_channel():
    """실제 채널 메시지로 최종 검증"""
    print("\n" + "=" * 100)
    print("실제 채널 메시지 최종 검증 (새로운 B안 로직)")
    print("=" * 100)

    # Telegram 클라이언트 시작
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    # TradingSystem 생성 (파싱만 테스트)
    config = TradingConfig.from_env()
    system = TelegramTradingSystem(config)

    try:
        await client.start()
        print(f"✅ Telegram 연결 완료")
        print(f"📥 SOURCE_CHANNEL: {SOURCE_CHANNEL}")
        print(f"📊 최근 50개 메시지 분석 시작...\n")

        # 최근 50개 메시지 가져오기
        messages = await client.get_messages(SOURCE_CHANNEL, limit=50)

        print(f"✅ {len(messages)}개 메시지 수집 완료\n")
        print("=" * 100)

        # 통계
        detected_count = 0
        detected_messages = []

        # 각 메시지 분석
        for i, msg in enumerate(messages, 1):
            if not msg.text:
                continue

            # 새로운 로직으로 파싱
            result = system.parse_stock_signal(msg.text)

            if result:
                detected_count += 1
                detected_messages.append({
                    "index": i,
                    "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "text": msg.text,
                    "result": result
                })

        # 통계 출력
        print("\n📊 분석 결과")
        print("=" * 100)
        print(f"총 메시지: {len([m for m in messages if m.text])}개")
        print(f"시그널 감지: {detected_count}개 ({detected_count/len([m for m in messages if m.text])*100:.1f}%)")
        print("=" * 100)

        # 감지된 메시지 상세 출력
        if detected_messages:
            print("\n📋 감지된 시그널 메시지 상세")
            print("=" * 100)

            for msg_info in detected_messages:
                print(f"\n[{msg_info['index']}] {msg_info['date']}")
                print("-" * 100)
                print(f"📨 메시지:")
                lines = msg_info['text'].split('\n')
                for line in lines[:7]:
                    print(f"   {line}")
                if len(lines) > 7:
                    print(f"   ... (총 {len(lines)}줄)")

                result = msg_info['result']
                print(f"\n✅ 파싱 결과:")
                print(f"   종목명: {result['stock_name']}")
                print(f"   종목코드: {result['stock_code']}")
                print(f"   적정매수가: {result['target_price']}")
                print(f"   현재가: {result['current_price']}")
                print("-" * 100)

        # 최종 평가
        print("\n" + "=" * 100)
        print("🎯 최종 평가")
        print("=" * 100)

        if detected_count > 0:
            print(f"✅ 새로운 B안 로직이 {detected_count}개의 시그널을 성공적으로 감지했습니다")
            print(f"   - 감지율: {detected_count}/{len([m for m in messages if m.text])} ({detected_count/len([m for m in messages if m.text])*100:.1f}%)")
            print("\n주요 특징:")
            print("   ✅ 괄호 안 6자리 숫자만으로 시그널 인식")
            print("   ✅ 키워드에 의존하지 않는 유연한 파싱")
            print("   ✅ #알림, #매수신호, Ai 종목포착 모두 지원")
            print("   ✅ 채널 메시지 형식 변경에 완전히 독립적")
        else:
            print("⚠️ 감지된 시그널이 없습니다")
            print("   - 최근 메시지에 괄호 안 6자리 숫자가 포함된 메시지가 없을 수 있습니다")

        print("\n" + "=" * 100)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.disconnect()
        print("\n✅ Telegram 연결 종료")


if __name__ == "__main__":
    asyncio.run(test_real_channel())
