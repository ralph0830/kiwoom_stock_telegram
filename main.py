"""
텔레그램 채널 매수 신호 자동 매매 시스템

텔레그램 채널에서 매수 신호를 받아 키움증권 API로 자동 매수합니다.
"""

import os
import re
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
from kiwoom_order import KiwoomOrderAPI

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_auto_trading.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Telegram API 설정
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "session")
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")  # 매수 신호를 받을 채널
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")  # 로그를 보낼 채널 (선택)

# 키움증권 설정
ACCOUNT_NO = os.getenv("ACCOUNT_NO")
MAX_INVESTMENT = int(os.getenv("MAX_INVESTMENT", "2000000"))  # 최대 투자금액 (기본: 200만원)

# 일일 매매 제한 파일
DAILY_LOCK_FILE = "daily_trading_lock.json"

# Telethon 클라이언트
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# 키움증권 API
kiwoom = KiwoomOrderAPI()


def parse_stock_signal(message_text: str) -> dict:
    """
    텔레그램 메시지에서 종목 정보 파싱

    예시 메시지:
    ⭐️ Ai 종목포착 시그널
    ￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
    포착 종목명 : 유일에너테크 (340930)
    적정 매수가 : 2,870원 👉 6.49%
    포착 현재가 : 2,860원 👉 6.12%

    Returns:
        {
            "stock_name": "유일에너테크",
            "stock_code": "340930",
            "target_price": 2870,
            "current_price": 2860
        }
    """
    try:
        # 매수 신호인지 확인
        if "Ai 종목포착 시그널" not in message_text and "종목포착" not in message_text:
            return None

        # 종목명과 종목코드 추출
        # 패턴: "포착 종목명 : 유일에너테크 (340930)" 또는 "종목명 : 유일에너테크 (340930)"
        stock_pattern = r'종목명\s*[:：]\s*([가-힣a-zA-Z0-9]+)\s*\((\d{6})\)'
        stock_match = re.search(stock_pattern, message_text)

        if not stock_match:
            logger.warning("⚠️ 종목명/종목코드를 찾을 수 없습니다")
            return None

        stock_name = stock_match.group(1).strip()
        stock_code = stock_match.group(2).strip()

        # 적정 매수가 추출 (선택)
        target_price = None
        target_pattern = r'적정\s*매수가?\s*[:：]\s*([\d,]+)원?'
        target_match = re.search(target_pattern, message_text)
        if target_match:
            target_price = int(target_match.group(1).replace(',', ''))

        # 현재가 추출 (선택)
        current_price = None
        current_pattern = r'(?:포착\s*)?현재가\s*[:：]\s*([\d,]+)원?'
        current_match = re.search(current_pattern, message_text)
        if current_match:
            current_price = int(current_match.group(1).replace(',', ''))

        result = {
            "stock_name": stock_name,
            "stock_code": stock_code,
            "target_price": target_price,
            "current_price": current_price
        }

        logger.info(f"✅ 신호 파싱 완료: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ 신호 파싱 실패: {e}")
        return None


def check_today_trading_done() -> bool:
    """오늘 이미 매수했는지 확인"""
    if not os.path.exists(DAILY_LOCK_FILE):
        return False

    try:
        with open(DAILY_LOCK_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        last_date = data.get("last_trading_date", "")
        today = datetime.now().strftime("%Y%m%d")

        if last_date == today:
            logger.info(f"⚠️ 오늘 이미 매수했습니다 ({data.get('stock_name')})")
            return True

        return False

    except Exception as e:
        logger.error(f"❌ 매수 이력 확인 실패: {e}")
        return False


def record_today_trading(stock_code: str, stock_name: str, buy_price: int, quantity: int):
    """오늘 매수 기록 저장"""
    data = {
        "last_trading_date": datetime.now().strftime("%Y%m%d"),
        "trading_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stock_code": stock_code,
        "stock_name": stock_name,
        "buy_price": buy_price,
        "quantity": quantity
    }

    try:
        with open(DAILY_LOCK_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 매수 기록 저장 완료")
    except Exception as e:
        logger.error(f"❌ 매수 기록 저장 실패: {e}")


async def execute_auto_buy(signal: dict) -> bool:
    """
    자동 매수 실행

    Args:
        signal: 파싱된 종목 신호 정보

    Returns:
        성공 여부
    """
    stock_code = signal["stock_code"]
    stock_name = signal["stock_name"]

    try:
        logger.info("=" * 80)
        logger.info(f"🎯 자동 매수 시작: {stock_name} ({stock_code})")
        logger.info("=" * 80)

        # 1. 현재가 조회
        logger.info("📊 현재가 조회 중...")
        price_result = kiwoom.get_current_price(stock_code)

        if not price_result.get("success"):
            logger.error(f"❌ 현재가 조회 실패: {price_result.get('message')}")
            return False

        current_price = price_result["current_price"]
        logger.info(f"💰 현재가: {current_price:,}원")

        # 2. 매수 수량 계산
        logger.info(f"💵 최대 투자금액: {MAX_INVESTMENT:,}원")
        quantity_result = kiwoom.calculate_order_quantity(current_price, MAX_INVESTMENT)
        quantity = quantity_result["quantity"]
        estimated_cost = quantity_result["estimated_cost"]

        logger.info(f"📦 매수 수량: {quantity}주")
        logger.info(f"💸 예상 매수금액: {estimated_cost:,}원")

        if quantity == 0:
            logger.error("❌ 매수 수량이 0입니다. 투자금액을 확인하세요.")
            return False

        # 3. 시장가 매수 주문
        logger.info("📝 시장가 매수 주문 실행 중...")
        order_result = kiwoom.place_market_buy_order(
            stock_code=stock_code,
            quantity=quantity,
            account_no=ACCOUNT_NO
        )

        if not order_result.get("success"):
            logger.error(f"❌ 매수 주문 실패: {order_result.get('message')}")
            return False

        # 4. 매수 완료
        logger.info("=" * 80)
        logger.info("✅ 시장가 매수 주문 성공!")
        logger.info(f"📌 종목명: {stock_name}")
        logger.info(f"📌 종목코드: {stock_code}")
        logger.info(f"📌 주문번호: {order_result.get('order_no', 'N/A')}")
        logger.info(f"📌 매수 수량: {quantity}주")
        logger.info(f"📌 예상 매수가: {current_price:,}원")
        logger.info(f"📌 예상 금액: {estimated_cost:,}원")
        logger.info("=" * 80)

        # 5. 오늘 매수 기록
        record_today_trading(stock_code, stock_name, current_price, quantity)

        # 6. 타겟 채널로 알림 전송 (선택)
        if TARGET_CHANNEL:
            await send_notification(
                f"✅ 자동 매수 완료\n\n"
                f"종목: {stock_name} ({stock_code})\n"
                f"수량: {quantity}주\n"
                f"매수가: {current_price:,}원\n"
                f"금액: {estimated_cost:,}원"
            )

        return True

    except Exception as e:
        logger.error(f"❌ 자동 매수 실행 중 오류: {e}")
        return False


async def send_notification(message: str):
    """타겟 채널로 알림 전송"""
    try:
        if TARGET_CHANNEL:
            await client.send_message(TARGET_CHANNEL, message)
            logger.info("📤 알림 전송 완료")
    except Exception as e:
        logger.error(f"❌ 알림 전송 실패: {e}")


# 새 메시지 이벤트 핸들러
@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handle_new_message(event):
    """텔레그램 새 메시지 수신 이벤트"""
    msg = event.message

    try:
        if not msg.text:
            return

        logger.info("=" * 80)
        logger.info("📨 새 메시지 수신")
        logger.info(f"💬 내용: {msg.text[:100]}...")
        logger.info("=" * 80)

        # 1. 메시지 파싱
        signal = parse_stock_signal(msg.text)

        if not signal:
            logger.info("ℹ️ 매수 신호가 아니거나 파싱 실패")
            return

        # 2. 일일 매수 제한 확인
        if check_today_trading_done():
            logger.warning("⚠️ 오늘은 이미 매수했습니다. 내일 다시 시도해주세요.")
            return

        # 3. 자동 매수 실행
        success = await execute_auto_buy(signal)

        if success:
            logger.info("🎉 자동 매수가 완료되었습니다!")
        else:
            logger.error("❌ 자동 매수에 실패했습니다.")

    except Exception as e:
        logger.error(f"⚠️ 메시지 처리 중 오류: {e}")


# 메인 함수
async def main():
    """메인 실행 함수"""
    logger.info("=" * 80)
    logger.info("🚀 텔레그램 자동매매 시스템 시작")
    logger.info("=" * 80)

    # Telegram 로그인
    await client.start()
    me = await client.get_me()

    logger.info(f"✅ Telegram 로그인: {me.first_name} (@{me.username})")
    logger.info(f"📥 모니터링 채널: {SOURCE_CHANNEL}")
    logger.info(f"📤 알림 채널: {TARGET_CHANNEL or '없음'}")
    logger.info(f"💰 최대 투자금액: {MAX_INVESTMENT:,}원")
    logger.info("=" * 80)

    # 키움증권 토큰 발급
    try:
        kiwoom.get_access_token()
        logger.info("✅ 키움증권 API 인증 완료")
    except Exception as e:
        logger.error(f"❌ 키움증권 API 인증 실패: {e}")
        logger.error("프로그램을 종료합니다.")
        return

    logger.info("=" * 80)
    logger.info("👀 매수 신호 모니터링 시작... (Ctrl+C로 종료)")
    logger.info("=" * 80)

    # 무한 실행 (메시지 대기)
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        with client:
            client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("\n프로그램을 종료합니다.")
    except Exception as e:
        logger.error(f"❌ 프로그램 실행 중 오류: {e}")
