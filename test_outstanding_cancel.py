"""
미체결 매수 주문 취소 기능 테스트
"""
import asyncio
import sys
import logging
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, '/home/ralph/work/python/stock_tel')

from trading_system_base import TradingSystemBase

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
        self.outstanding_orders = []
        self.cancelled_orders = []

    def get_outstanding_orders(self, query_date=None):
        """미체결 주문 조회 (Mock)"""
        logger.info(f"   🔹 API 호출: get_outstanding_orders")
        logger.info(f"      outstanding_orders count: {len(self.outstanding_orders)}")

        return {
            "success": True,
            "outstanding_orders": self.outstanding_orders
        }

    def cancel_order(self, order_no, stock_code, quantity):
        """주문 취소 (Mock)"""
        logger.info(f"   🔹 API 호출: cancel_order")
        logger.info(f"      order_no={order_no}")
        logger.info(f"      stock_code={stock_code}")
        logger.info(f"      quantity={quantity}")

        self.cancelled_orders.append({
            "order_no": order_no,
            "stock_code": stock_code,
            "quantity": quantity
        })

        # 미체결 주문에서 제거
        self.outstanding_orders = [
            order for order in self.outstanding_orders
            if order.get("ord_no") != order_no
        ]

        return {
            "success": True,
            "cancel_order_no": f"CANCEL-{datetime.now().strftime('%H%M%S')}",
            "original_order_no": order_no,
            "stock_code": stock_code,
            "quantity": quantity,
            "message": "주문 취소가 완료되었습니다"
        }

    def get_access_token(self):
        """Access Token 발급 (Mock)"""
        return "mock_token"


async def test_cancel_outstanding_buy_orders_with_partial():
    """테스트 1: 부분 체결 후 미체결 주문 취소"""
    print("\n" + "=" * 80)
    print("📊 테스트 1: 부분 체결 후 미체결 매수 주문 취소")
    print("=" * 80)

    # Mock API 초기화
    mock_api = MockKiwoomAPI()

    # TradingSystemBase의 간단한 서브클래스 생성
    class TestTradingSystem(TradingSystemBase):
        def __init__(self):
            self.kiwoom_api = mock_api
            self.buy_info = {
                "stock_code": "051980",
                "stock_name": "중앙첨단소재",
                "buy_price": 10000,
                "quantity": 60,  # 부분 체결 (원주문 100주, 체결 60주)
                "buy_order_no": "BUY-123456",  # 미체결 주문번호
                "target_profit_rate": 0.01
            }
            self.sell_executed = False
            self.websocket = None

        async def start_monitoring(self):
            """추상 메서드 구현 (테스트용)"""
            pass

    trading_system = TestTradingSystem()

    # 미체결 주문 설정 (40주 미체결)
    mock_api.outstanding_orders = [
        {
            "ord_no": "BUY-123456",
            "stk_cd": "051980",
            "stk_nm": "중앙첨단소재",
            "ord_qty": "100",
            "rmndr_qty": "40"  # 미체결 수량
        }
    ]

    logger.info(f"\n💰 초기 상태:")
    logger.info(f"   체결 수량: 60주")
    logger.info(f"   미체결 수량: 40주")
    logger.info(f"   주문번호: BUY-123456")

    # 미체결 매수 주문 취소 실행
    logger.info(f"\n🎯 미체결 매수 주문 취소 실행:")
    result = await trading_system.cancel_outstanding_buy_orders()

    # 결과 검증
    print("\n" + "=" * 80)
    print("✅ 검증 결과:")
    print("=" * 80)

    success = True

    if result:
        print("✅ 미체결 주문 취소 성공")
    else:
        print("❌ 미체결 주문 취소 실패")
        success = False

    if len(mock_api.cancelled_orders) == 1:
        cancel = mock_api.cancelled_orders[0]
        print(f"✅ 취소 주문 기록 확인")
        print(f"   주문번호: {cancel['order_no']}")
        print(f"   취소 수량: {cancel['quantity']}주")

        if cancel['quantity'] == 40:
            print("✅ 취소 수량 정확 (40주)")
        else:
            print(f"❌ 취소 수량 불일치: {cancel['quantity']}주 (예상: 40주)")
            success = False
    else:
        print("❌ 취소 주문 기록 없음")
        success = False

    if trading_system.buy_info.get("buy_order_no") is None:
        print("✅ buy_order_no 제거됨")
    else:
        print("❌ buy_order_no가 여전히 존재")
        success = False

    return success


async def test_cancel_outstanding_buy_orders_without_partial():
    """테스트 2: 100% 체결 시 미체결 주문 없음"""
    print("\n" + "=" * 80)
    print("📊 테스트 2: 100% 체결 시 미체결 주문 취소 건너뛰기")
    print("=" * 80)

    # Mock API 초기화
    mock_api = MockKiwoomAPI()

    # TradingSystemBase의 간단한 서브클래스 생성
    class TestTradingSystem(TradingSystemBase):
        def __init__(self):
            self.kiwoom_api = mock_api
            self.buy_info = {
                "stock_code": "051980",
                "stock_name": "중앙첨단소재",
                "buy_price": 10000,
                "quantity": 100,  # 100% 체결
                # buy_order_no 없음 (100% 체결이므로)
                "target_profit_rate": 0.01
            }
            self.sell_executed = False
            self.websocket = None

        async def start_monitoring(self):
            """추상 메서드 구현 (테스트용)"""
            pass

    trading_system = TestTradingSystem()

    logger.info(f"\n💰 초기 상태:")
    logger.info(f"   체결 수량: 100주 (100% 체결)")
    logger.info(f"   미체결 수량: 0주")
    logger.info(f"   주문번호: 없음")

    # 미체결 매수 주문 취소 실행
    logger.info(f"\n🎯 미체결 매수 주문 취소 실행:")
    result = await trading_system.cancel_outstanding_buy_orders()

    # 결과 검증
    print("\n" + "=" * 80)
    print("✅ 검증 결과:")
    print("=" * 80)

    success = True

    if result:
        print("✅ 미체결 주문 취소 건너뛰기 성공 (buy_order_no 없음)")
    else:
        print("❌ 미체결 주문 취소 실패")
        success = False

    if len(mock_api.cancelled_orders) == 0:
        print("✅ 취소 주문 없음 (예상대로)")
    else:
        print("❌ 취소 주문이 발생했습니다 (예상 밖)")
        success = False

    return success


async def test_cancel_outstanding_buy_orders_already_cancelled():
    """테스트 3: 이미 취소된 미체결 주문"""
    print("\n" + "=" * 80)
    print("📊 테스트 3: 이미 취소된 미체결 주문 처리")
    print("=" * 80)

    # Mock API 초기화
    mock_api = MockKiwoomAPI()

    # TradingSystemBase의 간단한 서브클래스 생성
    class TestTradingSystem(TradingSystemBase):
        def __init__(self):
            self.kiwoom_api = mock_api
            self.buy_info = {
                "stock_code": "051980",
                "stock_name": "중앙첨단소재",
                "buy_price": 10000,
                "quantity": 60,
                "buy_order_no": "BUY-999999",  # 존재하지 않는 주문번호
                "target_profit_rate": 0.01
            }
            self.sell_executed = False
            self.websocket = None

        async def start_monitoring(self):
            """추상 메서드 구현 (테스트용)"""
            pass

    trading_system = TestTradingSystem()

    # 미체결 주문 없음 (이미 취소됨)
    mock_api.outstanding_orders = []

    logger.info(f"\n💰 초기 상태:")
    logger.info(f"   주문번호: BUY-999999 (이미 취소됨)")
    logger.info(f"   미체결 주문 목록: 비어있음")

    # 미체결 매수 주문 취소 실행
    logger.info(f"\n🎯 미체결 매수 주문 취소 실행:")
    result = await trading_system.cancel_outstanding_buy_orders()

    # 결과 검증
    print("\n" + "=" * 80)
    print("✅ 검증 결과:")
    print("=" * 80)

    success = True

    if result:
        print("✅ 미체결 주문 없음 확인 (이미 취소됨)")
    else:
        print("❌ 미체결 주문 확인 실패")
        success = False

    if trading_system.buy_info.get("buy_order_no") is None:
        print("✅ buy_order_no 제거됨")
    else:
        print("❌ buy_order_no가 여전히 존재")
        success = False

    return success


async def main():
    """메인 테스트"""
    print("\n" + "🔬" * 40)
    print("미체결 매수 주문 취소 기능 테스트")
    print("🔬" * 40)

    results = []

    # 테스트 1: 부분 체결 후 미체결 주문 취소
    result1 = await test_cancel_outstanding_buy_orders_with_partial()
    results.append(("부분 체결 후 미체결 주문 취소", result1))

    # 테스트 2: 100% 체결 시 미체결 주문 없음
    result2 = await test_cancel_outstanding_buy_orders_without_partial()
    results.append(("100% 체결 시 취소 건너뛰기", result2))

    # 테스트 3: 이미 취소된 미체결 주문
    result3 = await test_cancel_outstanding_buy_orders_already_cancelled()
    results.append(("이미 취소된 주문 처리", result3))

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
        print("🎉 모든 테스트 통과! 미체결 매수 주문 취소 기능 정상 작동!")
    else:
        print("⚠️ 일부 테스트 실패. 기능 점검 필요.")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
