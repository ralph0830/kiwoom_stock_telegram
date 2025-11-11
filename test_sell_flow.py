"""
익절/손절 플로우 통합 테스트
"""
import asyncio
import sys
import logging
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, '/home/ralph/work/python/stock_tel')

from order_executor import OrderExecutor
from kiwoom_order import get_tick_size

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class MockKiwoomAPI:
    """Mock Kiwoom API"""

    def __init__(self):
        self.orders = []

    def place_limit_sell_order(self, stock_code, quantity, price, account_no):
        """지정가 매도 주문 (익절)"""
        logger.info(f"   🔹 API 호출: place_limit_sell_order")
        logger.info(f"      stock_code={stock_code}")
        logger.info(f"      quantity={quantity}")
        logger.info(f"      price={price:,}원")
        logger.info(f"      account_no={account_no}")

        self.orders.append({
            "type": "limit_sell",
            "stock_code": stock_code,
            "quantity": quantity,
            "price": price,
            "account_no": account_no
        })

        return {
            "success": True,
            "order_no": f"SELL-{datetime.now().strftime('%H%M%S')}",
            "message": "지정가 매도 주문 성공"
        }

    def place_market_sell_order(self, stock_code, quantity, account_no):
        """시장가 매도 주문 (손절)"""
        logger.info(f"   🔹 API 호출: place_market_sell_order")
        logger.info(f"      stock_code={stock_code}")
        logger.info(f"      quantity={quantity}")
        logger.info(f"      account_no={account_no}")

        self.orders.append({
            "type": "market_sell",
            "stock_code": stock_code,
            "quantity": quantity,
            "account_no": account_no
        })

        return {
            "success": True,
            "order_no": f"SELL-{datetime.now().strftime('%H%M%S')}",
            "message": "시장가 매도 주문 성공"
        }


async def test_profit_sell():
    """익절 플로우 테스트"""
    print("\n" + "=" * 80)
    print("📊 테스트 1: 익절 플로우")
    print("=" * 80)

    # Mock API 초기화
    mock_api = MockKiwoomAPI()
    executor = OrderExecutor(mock_api, "12345678-01")

    # 테스트 데이터
    stock_code = "051980"
    stock_name = "중앙첨단소재"
    buy_price = 10000
    quantity = 100
    current_price = 10100  # +1% 수익
    profit_rate = 0.01

    logger.info(f"\n💰 매수 정보:")
    logger.info(f"   종목: {stock_name} ({stock_code})")
    logger.info(f"   매수가: {buy_price:,}원")
    logger.info(f"   수량: {quantity}주")
    logger.info(f"   현재가: {current_price:,}원")
    logger.info(f"   수익률: {profit_rate*100:.2f}%")

    # 매도가 계산
    sell_price = executor.calculate_sell_price(buy_price, profit_rate)
    logger.info(f"\n📈 매도가 계산:")
    logger.info(f"   목표가: {current_price:,}원")
    logger.info(f"   틱 크기: {get_tick_size(current_price)}원")
    logger.info(f"   매도가: {sell_price:,}원 (목표가 - 1틱)")

    # 익절 매도 실행
    logger.info(f"\n🎯 익절 매도 실행:")
    result = await executor.execute_limit_sell(
        stock_code=stock_code,
        stock_name=stock_name,
        quantity=quantity,
        sell_price=sell_price,
        reason="익절"
    )

    # 결과 검증
    print("\n" + "=" * 80)
    print("✅ 검증 결과:")
    print("=" * 80)

    success = True

    if result.get("success"):
        print("✅ 익절 주문 성공")
    else:
        print("❌ 익절 주문 실패")
        success = False

    if mock_api.orders:
        order = mock_api.orders[0]
        print(f"✅ 주문 타입: {order['type']}")
        print(f"✅ 주문가: {order['price']:,}원")
        print(f"✅ 수량: {order['quantity']}주")
        print(f"✅ 계좌번호: {order['account_no']}")

        if order['account_no'] != "12345678-01":
            print(f"❌ 계좌번호 불일치: {order['account_no']}")
            success = False
    else:
        print("❌ 주문 기록 없음")
        success = False

    return success


async def test_stop_loss():
    """손절 플로우 테스트"""
    print("\n" + "=" * 80)
    print("📊 테스트 2: 손절 플로우")
    print("=" * 80)

    # Mock API 초기화
    mock_api = MockKiwoomAPI()
    executor = OrderExecutor(mock_api, "12345678-01")

    # 테스트 데이터
    stock_code = "051980"
    stock_name = "중앙첨단소재"
    buy_price = 10000
    quantity = 100
    current_price = 9750  # -2.5% 손실

    logger.info(f"\n💰 매수 정보:")
    logger.info(f"   종목: {stock_name} ({stock_code})")
    logger.info(f"   매수가: {buy_price:,}원")
    logger.info(f"   수량: {quantity}주")
    logger.info(f"   현재가: {current_price:,}원")
    logger.info(f"   손실률: {((current_price - buy_price) / buy_price)*100:.2f}%")

    # 손절 매도 실행
    logger.info(f"\n🚨 손절 매도 실행:")
    result = await executor.execute_market_sell(
        stock_code=stock_code,
        stock_name=stock_name,
        quantity=quantity,
        current_price=current_price,
        reason="손절"
    )

    # 결과 검증
    print("\n" + "=" * 80)
    print("✅ 검증 결과:")
    print("=" * 80)

    success = True

    if result.get("success"):
        print("✅ 손절 주문 성공")
    else:
        print("❌ 손절 주문 실패")
        success = False

    if mock_api.orders:
        order = mock_api.orders[0]
        print(f"✅ 주문 타입: {order['type']}")
        print(f"✅ 수량: {order['quantity']}주")
        print(f"✅ 계좌번호: {order['account_no']}")

        if order['account_no'] != "12345678-01":
            print(f"❌ 계좌번호 불일치: {order['account_no']}")
            success = False
    else:
        print("❌ 주문 기록 없음")
        success = False

    return success


async def main():
    """메인 테스트"""
    print("\n" + "🔬" * 40)
    print("익절/손절 플로우 통합 테스트")
    print("🔬" * 40)

    results = []

    # 테스트 1: 익절
    result1 = await test_profit_sell()
    results.append(("익절 플로우", result1))

    # 테스트 2: 손절
    result2 = await test_stop_loss()
    results.append(("손절 플로우", result2))

    # 최종 결과
    print("\n" + "=" * 80)
    print("📊 최종 테스트 결과")
    print("=" * 80)

    all_passed = True
    for name, passed in results:
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 모든 테스트 통과! 익절/손절 로직 정상 작동!")
    else:
        print("⚠️ 일부 테스트 실패. 로직 점검 필요.")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
