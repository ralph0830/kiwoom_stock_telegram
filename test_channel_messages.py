"""
텔레그램 채널 최근 메시지 분석 스크립트

기존 로직 vs 새로운 로직(괄호 안 6자리 숫자) 비교 테스트
"""
import asyncio
import re
import os
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient

# 환경변수 로드
load_dotenv()

# Telegram 설정
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "channel_copier")
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")


def parse_stock_signal_old(message_text: str) -> dict:
    """
    기존 로직: 키워드 기반 파싱
    """
    try:
        # 매수 신호인지 확인 (두 가지 형식 지원)
        is_ai_signal = "Ai 종목포착 시그널" in message_text or "종목포착" in message_text
        is_buy_signal = "#매수신호" in message_text or "매수신호" in message_text

        if not is_ai_signal and not is_buy_signal:
            return None

        # 형식 1: Ai 종목포착 시그널
        if is_ai_signal:
            stock_pattern = r'(?:포착\s*)?종목명\s*[:：]\s*([가-힣a-zA-Z0-9＆&\s]*?)\s*\((\d{6})\)'
            stock_match = re.search(stock_pattern, message_text)

            if not stock_match:
                return None

            stock_name = stock_match.group(1).strip()
            stock_code = stock_match.group(2).strip()

            if not stock_name:
                stock_name = stock_code

            # 적정 매수가 추출
            target_price = None
            target_pattern = r'적정\s*매수가?\s*[:：]\s*([\d,]+)원?'
            target_match = re.search(target_pattern, message_text)
            if target_match:
                target_price = int(target_match.group(1).replace(',', ''))

            # 현재가 추출
            current_price = None
            current_pattern = r'(?:포착\s*)?현재가\s*[:：]\s*([\d,]+)원?'
            current_match = re.search(current_pattern, message_text)
            if current_match:
                current_price = int(current_match.group(1).replace(',', ''))

        # 형식 2: #매수신호
        elif is_buy_signal:
            stock_pattern = r'종목명\s*👉\s*([가-힣a-zA-Z0-9＆&\s]+?)\s*\((\d{6})\)'
            stock_match = re.search(stock_pattern, message_text)

            if not stock_match:
                return None

            stock_name = stock_match.group(1).strip()
            stock_code = stock_match.group(2).strip()

            # 매수가 추출
            current_price = None
            buy_price_pattern = r'매수가\s*👉\s*([\d,]+)원?'
            buy_price_match = re.search(buy_price_pattern, message_text)
            if buy_price_match:
                current_price = int(buy_price_match.group(1).replace(',', ''))

            # 매도가 추출
            target_price = None
            sell_price_pattern = r'매도가\s*👉\s*([\d,]+)원?'
            sell_price_match = re.search(sell_price_pattern, message_text)
            if sell_price_match:
                target_price = int(sell_price_match.group(1).replace(',', ''))

        return {
            "stock_name": stock_name,
            "stock_code": stock_code,
            "target_price": target_price,
            "current_price": current_price
        }

    except Exception as e:
        return None


def parse_stock_signal_new(message_text: str) -> dict:
    """
    새로운 로직: 괄호 안 6자리 숫자 기반 파싱
    """
    try:
        # 괄호 안의 6자리 숫자 추출
        stock_code_pattern = r'\((\d{6})\)'
        match = re.search(stock_code_pattern, message_text)

        if not match:
            return None

        stock_code = match.group(1)

        # 종목명 추출 (괄호 앞의 텍스트)
        stock_name = extract_stock_name(message_text, stock_code)

        if not stock_name:
            stock_name = stock_code

        # 가격 정보 추출
        prices = extract_prices(message_text)

        return {
            "stock_name": stock_name,
            "stock_code": stock_code,
            "target_price": prices.get("target"),
            "current_price": prices.get("current")
        }

    except Exception as e:
        return None


def extract_stock_name(message_text: str, stock_code: str) -> str:
    """
    괄호 앞에서 종목명 추출
    """
    # 괄호 앞의 텍스트 패턴
    pattern = r'([가-힣a-zA-Z0-9＆&]+)\s*\(' + re.escape(stock_code) + r'\)'
    match = re.search(pattern, message_text)

    if not match:
        return ""

    stock_name = match.group(1).strip()

    # 불필요한 접두사 제거
    stock_name = re.sub(r'.*[:：]\s*', '', stock_name).strip()
    stock_name = re.sub(r'.*👉\s*', '', stock_name).strip()

    return stock_name


def extract_prices(message_text: str) -> dict:
    """
    메시지에서 가격 정보 추출
    """
    prices = {"target": None, "current": None}

    # 적정 매수가, 매도가 → target_price
    target_patterns = [
        r'적정\s*매수가?\s*[:：]\s*([\d,]+)원?',
        r'매도가\s*[:：👉]\s*([\d,]+)원?',
        r'목표가\s*[:：👉]\s*([\d,]+)원?'
    ]

    for pattern in target_patterns:
        match = re.search(pattern, message_text)
        if match:
            try:
                prices["target"] = int(match.group(1).replace(',', ''))
                break
            except:
                pass

    # 현재가, 매수가 → current_price
    current_patterns = [
        r'(?:포착\s*)?현재가\s*[:：]\s*([\d,]+)원?',
        r'매수가\s*[:：👉]\s*([\d,]+)원?'
    ]

    for pattern in current_patterns:
        match = re.search(pattern, message_text)
        if match:
            try:
                prices["current"] = int(match.group(1).replace(',', ''))
                break
            except:
                pass

    return prices


async def analyze_channel_messages():
    """
    텔레그램 채널 메시지 분석
    """
    print("\n" + "=" * 100)
    print("텔레그램 채널 메시지 분석 시작")
    print("=" * 100)

    # Telegram 클라이언트 시작
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    try:
        await client.start()
        print(f"✅ Telegram 연결 완료")
        print(f"📥 SOURCE_CHANNEL: {SOURCE_CHANNEL}")
        print(f"📊 최근 50개 메시지 수집 중...\n")

        # 최근 50개 메시지 가져오기
        messages = await client.get_messages(SOURCE_CHANNEL, limit=50)

        print(f"✅ {len(messages)}개 메시지 수집 완료\n")
        print("=" * 100)

        # 통계 변수
        old_detected = 0
        new_detected = 0
        both_detected = 0
        only_old = 0
        only_new = 0
        none_detected = 0

        detailed_results = []

        # 각 메시지 분석
        for i, msg in enumerate(messages, 1):
            if not msg.text:
                continue

            # 기존 로직 테스트
            result_old = parse_stock_signal_old(msg.text)

            # 새로운 로직 테스트
            result_new = parse_stock_signal_new(msg.text)

            # 통계 업데이트
            has_old = result_old is not None
            has_new = result_new is not None

            if has_old and has_new:
                both_detected += 1
                old_detected += 1
                new_detected += 1
            elif has_old and not has_new:
                only_old += 1
                old_detected += 1
            elif not has_old and has_new:
                only_new += 1
                new_detected += 1
            else:
                none_detected += 1

            # 상세 결과 저장 (시그널 감지된 것만)
            if has_old or has_new:
                detailed_results.append({
                    "index": i,
                    "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "text": msg.text,
                    "old": result_old,
                    "new": result_new,
                    "match": has_old and has_new
                })

        # 통계 출력
        print("\n📊 분석 결과 통계")
        print("=" * 100)
        print(f"총 메시지 수: {len([m for m in messages if m.text])}개")
        print(f"\n🔵 기존 로직 감지: {old_detected}개")
        print(f"🟢 새 로직 감지: {new_detected}개")
        print(f"🟣 둘 다 감지: {both_detected}개")
        print(f"🔴 기존만 감지: {only_old}개")
        print(f"🟡 새것만 감지: {only_new}개")
        print(f"⚪ 둘 다 미감지: {none_detected}개")

        # 상세 결과 출력
        if detailed_results:
            print("\n" + "=" * 100)
            print("📋 시그널 감지된 메시지 상세 분석")
            print("=" * 100)

            for result in detailed_results:
                print(f"\n[{result['index']}] {result['date']}")
                print("-" * 100)
                print(f"📨 메시지:")
                lines = result['text'].split('\n')
                for line in lines[:5]:  # 처음 5줄만 출력
                    print(f"   {line}")
                if len(lines) > 5:
                    print(f"   ... (총 {len(lines)}줄)")

                print(f"\n🔵 기존 로직: ", end="")
                if result['old']:
                    print(f"✅ 감지")
                    print(f"   종목명: {result['old']['stock_name']}")
                    print(f"   종목코드: {result['old']['stock_code']}")
                    print(f"   적정매수가: {result['old']['target_price']}")
                    print(f"   현재가: {result['old']['current_price']}")
                else:
                    print("❌ 미감지")

                print(f"\n🟢 새 로직: ", end="")
                if result['new']:
                    print(f"✅ 감지")
                    print(f"   종목명: {result['new']['stock_name']}")
                    print(f"   종목코드: {result['new']['stock_code']}")
                    print(f"   적정매수가: {result['new']['target_price']}")
                    print(f"   현재가: {result['new']['current_price']}")
                else:
                    print("❌ 미감지")

                # 결과 비교
                if result['match']:
                    if result['old'] == result['new']:
                        print(f"\n✅ 완전 일치")
                    else:
                        print(f"\n⚠️ 부분 일치 (값이 다름)")
                        if result['old']['stock_code'] != result['new']['stock_code']:
                            print(f"   종목코드 차이: {result['old']['stock_code']} vs {result['new']['stock_code']}")
                        if result['old']['stock_name'] != result['new']['stock_name']:
                            print(f"   종목명 차이: {result['old']['stock_name']} vs {result['new']['stock_name']}")
                else:
                    if result['old'] and not result['new']:
                        print(f"\n🔴 기존 로직만 감지 (새 로직 놓침)")
                    else:
                        print(f"\n🟡 새 로직만 감지 (오탐 가능성)")

                print("-" * 100)

        # 최종 평가
        print("\n" + "=" * 100)
        print("🎯 최종 평가")
        print("=" * 100)

        if new_detected >= old_detected and only_new == 0:
            print("✅ 새 로직이 기존 로직과 동등하거나 더 우수합니다")
            print(f"   - 기존 로직 감지율: {old_detected}/{len([m for m in messages if m.text])} ({old_detected/len([m for m in messages if m.text])*100:.1f}%)")
            print(f"   - 새 로직 감지율: {new_detected}/{len([m for m in messages if m.text])} ({new_detected/len([m for m in messages if m.text])*100:.1f}%)")
            print(f"   - 오탐(새것만 감지): {only_new}개")
        elif only_new > 0:
            print("⚠️ 새 로직에서 오탐이 발견되었습니다")
            print(f"   - 오탐 수: {only_new}개")
            print(f"   - 검토 필요: 위의 '새것만 감지' 메시지를 확인하세요")
        elif only_old > 0:
            print("⚠️ 새 로직이 일부 시그널을 놓쳤습니다")
            print(f"   - 놓친 시그널: {only_old}개")
            print(f"   - 개선 필요: 위의 '기존만 감지' 메시지를 확인하세요")

        print("\n" + "=" * 100)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.disconnect()
        print("\n✅ Telegram 연결 종료")


if __name__ == "__main__":
    asyncio.run(analyze_channel_messages())
