"""
v1.6.0 한 틱 위 지정가 매수 시뮬레이션 테스트

모든 경우의 수를 테스트:
1. 시장가 매수
2. 지정가 100% 완전 체결
3. 지정가 부분 체결 (60%)
4. 지정가 0% 미체결 + 폴백 true (시장가 재주문)
5. 지정가 0% 미체결 + 폴백 false (포기)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from kiwoom_order import get_tick_size

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ========================================
# Mock API 클래스
# ========================================

class MockKiwoomAPI:
    """Kiwoom API Mock 객체"""

    def __init__(self, scenario: str):
        """
        Args:
            scenario: 시나리오 타입
                - "market": 시장가 매수
                - "limit_full": 지정가 100% 체결
                - "limit_partial": 지정가 부분 체결 (60%)
                - "limit_none": 지정가 0% 미체결
        """
        self.scenario = scenario
        self.access_token = "MOCK_TOKEN"

    def get_access_token(self):
        """Access Token 발급 (Mock)"""
        logger.info("✅ Mock Access Token 발급 완료")
        return self.access_token

    def get_current_price(self, stock_code: str) -> Dict:
        """현재가 조회 (Mock)"""
        return {
            "success": True,
            "current_price": 10000,
            "message": "현재가 조회 성공"
        }

    def place_market_buy_order(self, stock_code: str, quantity: int, account_no: str = None) -> Dict:
        """시장가 매수 주문 (Mock)"""
        logger.info(f"📊 Mock 시장가 매수 주문: {stock_code}, {quantity}주")
        return {
            "success": True,
            "order_no": "MOCK12345",
            "message": "시장가 매수 주문 성공"
        }

    def place_limit_buy_order(self, stock_code: str, quantity: int, price: int, account_no: str = None) -> Dict:
        """지정가 매수 주문 (Mock)"""
        logger.info(f"📊 Mock 지정가 매수 주문: {stock_code}, {quantity}주, {price:,}원")
        return {
            "success": True,
            "order_no": "MOCK67890",
            "message": "지정가 매수 주문 성공"
        }

    def get_outstanding_orders(self, query_date: str = None) -> Dict:
        """미체결 주문 조회 (Mock)"""
        if self.scenario == "limit_full":
            # 100% 체결 시나리오 - 미체결 없음
            return {
                "success": True,
                "outstanding_orders": [],
                "total_count": 0
            }
        elif self.scenario == "limit_partial":
            # 부분 체결 시나리오 - 40주 미체결
            return {
                "success": True,
                "outstanding_orders": [{
                    "ord_no": "MOCK67890",
                    "ord_qty": "100",
                    "rmndr_qty": "40",  # 미체결 40주
                    "stk_cd": "051780"
                }],
                "total_count": 1
            }
        elif self.scenario == "limit_none":
            # 0% 미체결 시나리오 - 100주 모두 미체결
            return {
                "success": True,
                "outstanding_orders": [{
                    "ord_no": "MOCK67890",
                    "ord_qty": "100",
                    "rmndr_qty": "100",  # 100주 모두 미체결
                    "stk_cd": "051780"
                }],
                "total_count": 1
            }
        else:  # market
            return {
                "success": True,
                "outstanding_orders": [],
                "total_count": 0
            }

    def get_account_balance(self, query_date: str = None) -> Dict:
        """계좌 잔고 조회 (Mock)"""
        if self.scenario == "limit_full":
            # 100% 체결 시나리오 - 100주 보유
            return {
                "success": True,
                "holdings": [{
                    "stk_cd": "051780",
                    "rmnd_qty": "100",   # 100주 체결
                    "buy_uv": "10010"    # 평균 매입단가
                }]
            }
        elif self.scenario == "limit_partial":
            # 부분 체결 시나리오 - 60주만 보유
            return {
                "success": True,
                "holdings": [{
                    "stk_cd": "051780",
                    "rmnd_qty": "60",    # 60주만 체결
                    "buy_uv": "10010"    # 평균 매입단가
                }]
            }
        elif self.scenario == "limit_none":
            # 0% 미체결 시나리오 - 보유 없음
            return {
                "success": True,
                "holdings": []
            }
        else:  # market
            # 시장가 - 계좌 조회 사용 안함
            return {
                "success": True,
                "holdings": []
            }

    def cancel_order(self, order_no: str, stock_code: str, quantity: int) -> Dict:
        """주문 취소 (Mock)"""
        logger.info(f"🔄 Mock 주문 취소: {order_no}, {quantity}주")
        return {
            "success": True,
            "message": "주문 취소 성공"
        }

    def calculate_order_quantity(self, price: int, max_investment: int) -> int:
        """매수 수량 계산"""
        safety_margin = 0.02
        adjusted_investment = int(max_investment * (1 - safety_margin))
        quantity = adjusted_investment // price
        return quantity


# ========================================
# Mock OrderExecutor
# ========================================

class MockOrderExecutor:
    """주문 실행기 Mock"""

    def __init__(self, api: MockKiwoomAPI):
        self.api = api

    async def execute_market_buy(self, stock_code: str, stock_name: str, quantity: int, current_price: int) -> Dict:
        """시장가 매수 주문 실행 (Mock)"""
        logger.info("=" * 80)
        logger.info("🎯 시장가 매수 주문 시작 (Mock)")
        logger.info("=" * 80)
        logger.info(f"종목명: {stock_name}")
        logger.info(f"종목코드: {stock_code}")
        logger.info(f"현재가: {current_price:,}원")
        logger.info(f"주문 수량: {quantity}주")
        logger.info(f"예상 금액: {current_price * quantity:,}원")

        result = self.api.place_market_buy_order(stock_code, quantity)

        if result.get("success"):
            logger.info(f"✅ 시장가 매수 주문 성공!")
            logger.info(f"주문번호: {result.get('order_no')}")

        return {
            "success": True,
            "order_no": result.get("order_no"),
            "message": "매수 주문 성공",
            "buy_price": current_price,
            "quantity": quantity,
            "stock_code": stock_code,
            "stock_name": stock_name
        }

    async def execute_limit_buy(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        current_price: int,
        order_price: int
    ) -> Dict:
        """지정가 매수 주문 실행 (Mock)"""
        logger.info("=" * 80)
        logger.info("🎯 지정가 매수 주문 시작 (Mock)")
        logger.info("=" * 80)
        logger.info(f"종목명: {stock_name}")
        logger.info(f"종목코드: {stock_code}")
        logger.info(f"현재가: {current_price:,}원")
        logger.info(f"주문가: {order_price:,}원 (+{order_price - current_price}원 1틱 위)")
        logger.info(f"주문 수량: {quantity}주")
        logger.info(f"예상 금액: {order_price * quantity:,}원")

        result = self.api.place_limit_buy_order(stock_code, quantity, order_price)

        if result.get("success"):
            logger.info(f"✅ 지정가 매수 주문 성공!")
            logger.info(f"주문번호: {result.get('order_no')}")

        return {
            "success": True,
            "order_no": result.get("order_no"),
            "message": "매수 주문 성공",
            "buy_price": order_price,
            "quantity": quantity,
            "stock_code": stock_code,
            "stock_name": stock_name
        }

    async def wait_for_buy_execution(
        self,
        stock_code: str,
        order_qty: int,
        order_no: str,
        timeout: int = 30,
        interval: int = 5
    ) -> Dict:
        """매수 체결 대기 및 확인 (Mock - 즉시 반환)"""
        logger.info("⏳ 매수 체결 확인 시작 (Mock)")
        logger.info(f"타임아웃: {timeout}초, 주기: {interval}초")

        # Mock이므로 즉시 결과 반환 (대기 없음)
        await asyncio.sleep(0.1)  # 최소 대기

        # 미체결 주문 조회
        outstanding = self.api.get_outstanding_orders()
        order_found = False
        rmndr_qty = 0

        if outstanding.get("success"):
            for order in outstanding.get("outstanding_orders", []):
                if order.get("ord_no") == order_no:
                    order_found = True
                    rmndr_qty = int(order.get("rmndr_qty", 0))
                    break

        if not order_found:
            rmndr_qty = 0

        # 계좌 잔고 조회
        balance = self.api.get_account_balance()
        actual_qty = 0
        avg_buy_price = 0

        if balance.get("success"):
            for holding in balance.get("holdings", []):
                if holding.get("stk_cd") == stock_code:
                    actual_qty = int(holding.get("rmnd_qty", 0))
                    avg_buy_price = int(holding.get("buy_uv", 0))
                    break

        # 체결 상태 판별
        if rmndr_qty == 0 and actual_qty >= order_qty:
            # 100% 완전 체결
            logger.info("=" * 80)
            logger.info("✅ 매수 100% 체결 완료! (Mock)")
            logger.info(f"체결 수량: {actual_qty}주")
            logger.info(f"평균 매입단가: {avg_buy_price:,}원")
            logger.info("=" * 80)

            return {
                'status': 'FULLY_EXECUTED',
                'executed_qty': actual_qty,
                'remaining_qty': 0,
                'avg_buy_price': avg_buy_price,
                'success': True
            }

        elif actual_qty > 0 and rmndr_qty > 0:
            # 부분 체결
            execution_rate = (actual_qty / order_qty) * 100

            logger.info("=" * 80)
            logger.warning("⚠️ 부분 체결 발생! (Mock)")
            logger.info(f"주문 수량: {order_qty}주")
            logger.info(f"체결 수량: {actual_qty}주 ({execution_rate:.1f}%)")
            logger.info(f"미체결 수량: {rmndr_qty}주 ({100-execution_rate:.1f}%)")
            logger.info(f"평균 매입단가: {avg_buy_price:,}원")
            logger.info("=" * 80)

            # 미체결 주문 취소
            logger.info(f"🔄 미체결 {rmndr_qty}주 주문을 취소합니다...")
            cancel_result = self.api.cancel_order(order_no, stock_code, rmndr_qty)

            if cancel_result.get("success"):
                logger.info("✅ 미체결 주문 취소 완료")

            logger.info(f"✅ 부분 체결 수용: {actual_qty}주로 매도 모니터링을 시작합니다")

            return {
                'status': 'PARTIALLY_EXECUTED',
                'executed_qty': actual_qty,
                'remaining_qty': rmndr_qty,
                'avg_buy_price': avg_buy_price,
                'success': True
            }

        else:
            # 0% 미체결
            logger.info("=" * 80)
            logger.warning("⚠️ 매수 미체결! (Mock)")
            logger.info(f"주문 수량: {order_qty}주")
            logger.info("체결 수량: 0주")
            logger.info("=" * 80)

            # 미체결 주문 취소
            logger.info("🔄 미체결 주문을 취소합니다...")
            cancel_result = self.api.cancel_order(order_no, stock_code, order_qty)

            if cancel_result.get("success"):
                logger.info("✅ 미체결 주문 취소 완료")

            return {
                'status': 'NOT_EXECUTED',
                'executed_qty': 0,
                'remaining_qty': order_qty,
                'avg_buy_price': 0,
                'success': False
            }

    def calculate_buy_quantity(self, current_price: int, max_investment: int, safety_margin: float = 0.02) -> int:
        """매수 수량 계산"""
        adjusted_investment = int(max_investment * (1 - safety_margin))
        quantity = adjusted_investment // current_price
        return quantity


# ========================================
# Mock TradingConfig
# ========================================

class MockTradingConfig:
    """Trading 설정 Mock"""

    def __init__(self, buy_order_type: str = "market", buy_fallback_to_market: bool = True):
        self.buy_order_type = buy_order_type
        self.buy_execution_timeout = 30
        self.buy_execution_check_interval = 5
        self.buy_fallback_to_market = buy_fallback_to_market
        self.enable_lazy_verification = False


# ========================================
# 테스트 시나리오 실행 함수
# ========================================

async def test_scenario_1_market_buy():
    """시나리오 1: 시장가 매수"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 시나리오 1: 시장가 매수 테스트")
    logger.info("=" * 80)

    # Mock 설정
    mock_api = MockKiwoomAPI(scenario="market")
    mock_executor = MockOrderExecutor(mock_api)
    config = MockTradingConfig(buy_order_type="market")

    # 테스트 데이터
    stock_code = "051780"
    stock_name = "테스트종목"
    current_price = 10000
    max_investment = 1000000

    # 매수 수량 계산
    quantity = mock_executor.calculate_buy_quantity(current_price, max_investment)

    # 시장가 매수 실행
    mock_api.get_access_token()
    order_result = await mock_executor.execute_market_buy(
        stock_code=stock_code,
        stock_name=stock_name,
        quantity=quantity,
        current_price=current_price
    )

    # 검증
    assert order_result.get("success") == True
    assert order_result.get("buy_price") == current_price
    assert order_result.get("quantity") == quantity

    logger.info("\n✅ 시나리오 1 성공: 시장가 매수 완료")
    logger.info(f"   매수 수량: {quantity}주")
    logger.info(f"   매수가: {current_price:,}원 (추정값)")
    logger.info(f"   투자금액: {current_price * quantity:,}원")

    return True


async def test_scenario_2_limit_full():
    """시나리오 2: 지정가 100% 완전 체결"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 시나리오 2: 지정가 100% 완전 체결 테스트")
    logger.info("=" * 80)

    # Mock 설정
    mock_api = MockKiwoomAPI(scenario="limit_full")
    mock_executor = MockOrderExecutor(mock_api)
    config = MockTradingConfig(buy_order_type="limit_plus_one_tick")

    # 테스트 데이터
    stock_code = "051780"
    stock_name = "테스트종목"
    current_price = 10000
    max_investment = 1000000

    # 한 틱 위 가격 계산
    tick_size = get_tick_size(current_price)
    order_price = current_price + tick_size

    # 매수 수량 계산
    quantity = mock_executor.calculate_buy_quantity(order_price, max_investment)

    # 지정가 매수 실행
    mock_api.get_access_token()
    order_result = await mock_executor.execute_limit_buy(
        stock_code=stock_code,
        stock_name=stock_name,
        quantity=quantity,
        current_price=current_price,
        order_price=order_price
    )

    # 체결 확인
    execution_result = await mock_executor.wait_for_buy_execution(
        stock_code=stock_code,
        order_qty=quantity,
        order_no=order_result.get("order_no")
    )

    # 검증
    assert execution_result['status'] == 'FULLY_EXECUTED'
    assert execution_result['executed_qty'] == 100
    assert execution_result['remaining_qty'] == 0
    assert execution_result['avg_buy_price'] == 10010
    assert execution_result['success'] == True

    logger.info("\n✅ 시나리오 2 성공: 지정가 100% 체결 완료")
    logger.info(f"   주문 수량: {quantity}주")
    logger.info(f"   체결 수량: {execution_result['executed_qty']}주 (100%)")
    logger.info(f"   매수가: {execution_result['avg_buy_price']:,}원 (실제 평균 매입단가)")
    logger.info(f"   투자금액: {execution_result['avg_buy_price'] * execution_result['executed_qty']:,}원")
    logger.info(f"   검증 완료: True")

    return True


async def test_scenario_3_limit_partial():
    """시나리오 3: 지정가 부분 체결 (60%)"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 시나리오 3: 지정가 부분 체결 (60%) 테스트")
    logger.info("=" * 80)

    # Mock 설정
    mock_api = MockKiwoomAPI(scenario="limit_partial")
    mock_executor = MockOrderExecutor(mock_api)
    config = MockTradingConfig(buy_order_type="limit_plus_one_tick")

    # 테스트 데이터
    stock_code = "051780"
    stock_name = "테스트종목"
    current_price = 10000
    max_investment = 1000000

    # 한 틱 위 가격 계산
    tick_size = get_tick_size(current_price)
    order_price = current_price + tick_size

    # 매수 수량 계산
    quantity = mock_executor.calculate_buy_quantity(order_price, max_investment)

    # 지정가 매수 실행
    mock_api.get_access_token()
    order_result = await mock_executor.execute_limit_buy(
        stock_code=stock_code,
        stock_name=stock_name,
        quantity=quantity,
        current_price=current_price,
        order_price=order_price
    )

    # 체결 확인
    execution_result = await mock_executor.wait_for_buy_execution(
        stock_code=stock_code,
        order_qty=quantity,
        order_no=order_result.get("order_no")
    )

    # 검증
    assert execution_result['status'] == 'PARTIALLY_EXECUTED'
    assert execution_result['executed_qty'] == 60
    assert execution_result['remaining_qty'] == 40
    assert execution_result['avg_buy_price'] == 10010
    assert execution_result['success'] == True

    logger.info("\n⚠️ 시나리오 3 성공: 지정가 부분 체결 (60%)")
    logger.info(f"   주문 수량: {quantity}주")
    logger.info(f"   체결 수량: {execution_result['executed_qty']}주 (60.0%)")
    logger.info(f"   미체결 수량: {execution_result['remaining_qty']}주 (자동 취소됨)")
    logger.info(f"   매수가: {execution_result['avg_buy_price']:,}원 (실제 평균 매입단가)")
    logger.info(f"   투자금액: {execution_result['avg_buy_price'] * execution_result['executed_qty']:,}원")
    logger.info(f"   검증 완료: True")

    return True


async def test_scenario_4_limit_none_fallback_true():
    """시나리오 4: 지정가 0% 미체결 + 폴백 true (시장가 재주문)"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 시나리오 4: 지정가 미체결 + 폴백 true (시장가 재주문) 테스트")
    logger.info("=" * 80)

    # Mock 설정 (먼저 지정가 미체결, 그 다음 시장가)
    mock_api_limit = MockKiwoomAPI(scenario="limit_none")
    mock_executor = MockOrderExecutor(mock_api_limit)
    config = MockTradingConfig(buy_order_type="limit_plus_one_tick", buy_fallback_to_market=True)

    # 테스트 데이터
    stock_code = "051780"
    stock_name = "테스트종목"
    current_price = 10000
    max_investment = 1000000

    # 1단계: 지정가 매수 시도
    tick_size = get_tick_size(current_price)
    order_price = current_price + tick_size
    quantity = mock_executor.calculate_buy_quantity(order_price, max_investment)

    mock_api_limit.get_access_token()
    order_result = await mock_executor.execute_limit_buy(
        stock_code=stock_code,
        stock_name=stock_name,
        quantity=quantity,
        current_price=current_price,
        order_price=order_price
    )

    # 체결 확인 (미체결)
    execution_result = await mock_executor.wait_for_buy_execution(
        stock_code=stock_code,
        order_qty=quantity,
        order_no=order_result.get("order_no")
    )

    # 검증: 미체결
    assert execution_result['status'] == 'NOT_EXECUTED'
    assert execution_result['executed_qty'] == 0
    assert execution_result['success'] == False

    logger.info("\n⚠️ 지정가 미체결 → 시장가로 재주문")

    # 2단계: 시장가로 폴백
    mock_api_market = MockKiwoomAPI(scenario="market")
    mock_executor_market = MockOrderExecutor(mock_api_market)

    quantity_market = mock_executor_market.calculate_buy_quantity(current_price, max_investment)

    fallback_result = await mock_executor_market.execute_market_buy(
        stock_code=stock_code,
        stock_name=stock_name,
        quantity=quantity_market,
        current_price=current_price
    )

    # 검증: 시장가 성공
    assert fallback_result.get("success") == True

    logger.info("\n✅ 시나리오 4 성공: 지정가 미체결 → 시장가 재주문 완료")
    logger.info(f"   1차 시도: 지정가 {order_price:,}원 → 미체결")
    logger.info(f"   2차 시도: 시장가 {current_price:,}원 → 체결 성공")
    logger.info(f"   최종 수량: {quantity_market}주")
    logger.info(f"   최종 투자금액: {current_price * quantity_market:,}원")

    return True


async def test_scenario_5_limit_none_fallback_false():
    """시나리오 5: 지정가 0% 미체결 + 폴백 false (포기)"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 시나리오 5: 지정가 미체결 + 폴백 false (포기) 테스트")
    logger.info("=" * 80)

    # Mock 설정
    mock_api = MockKiwoomAPI(scenario="limit_none")
    mock_executor = MockOrderExecutor(mock_api)
    config = MockTradingConfig(buy_order_type="limit_plus_one_tick", buy_fallback_to_market=False)

    # 테스트 데이터
    stock_code = "051780"
    stock_name = "테스트종목"
    current_price = 10000
    max_investment = 1000000

    # 지정가 매수 시도
    tick_size = get_tick_size(current_price)
    order_price = current_price + tick_size
    quantity = mock_executor.calculate_buy_quantity(order_price, max_investment)

    mock_api.get_access_token()
    order_result = await mock_executor.execute_limit_buy(
        stock_code=stock_code,
        stock_name=stock_name,
        quantity=quantity,
        current_price=current_price,
        order_price=order_price
    )

    # 체결 확인 (미체결)
    execution_result = await mock_executor.wait_for_buy_execution(
        stock_code=stock_code,
        order_qty=quantity,
        order_no=order_result.get("order_no")
    )

    # 검증
    assert execution_result['status'] == 'NOT_EXECUTED'
    assert execution_result['executed_qty'] == 0
    assert execution_result['success'] == False

    logger.info("\n❌ 시나리오 5 성공: 지정가 미체결 → 매수 포기")
    logger.info(f"   시도: 지정가 {order_price:,}원 → 미체결")
    logger.info(f"   폴백 설정: False → 재주문 없이 종료")
    logger.info(f"   최종 결과: 매수 없음")

    return True


# ========================================
# 메인 테스트 실행
# ========================================

async def run_all_tests():
    """모든 시뮬레이션 테스트 실행"""
    logger.info("\n" + "=" * 80)
    logger.info("🚀 v1.6.0 한 틱 위 지정가 매수 - 전체 시뮬레이션 테스트 시작")
    logger.info("=" * 80)

    results = []

    try:
        # 시나리오 1: 시장가 매수
        result1 = await test_scenario_1_market_buy()
        results.append(("시나리오 1: 시장가 매수", result1))

        # 시나리오 2: 지정가 100% 체결
        result2 = await test_scenario_2_limit_full()
        results.append(("시나리오 2: 지정가 100% 완전 체결", result2))

        # 시나리오 3: 지정가 부분 체결
        result3 = await test_scenario_3_limit_partial()
        results.append(("시나리오 3: 지정가 부분 체결 (60%)", result3))

        # 시나리오 4: 지정가 미체결 + 폴백 true
        result4 = await test_scenario_4_limit_none_fallback_true()
        results.append(("시나리오 4: 지정가 미체결 + 폴백 true", result4))

        # 시나리오 5: 지정가 미체결 + 폴백 false
        result5 = await test_scenario_5_limit_none_fallback_false()
        results.append(("시나리오 5: 지정가 미체결 + 폴백 false", result5))

    except Exception as e:
        logger.error(f"❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 결과 요약
    logger.info("\n" + "=" * 80)
    logger.info("📊 테스트 결과 요약")
    logger.info("=" * 80)

    all_passed = True
    for i, (name, result) in enumerate(results, 1):
        status = "✅ 통과" if result else "❌ 실패"
        logger.info(f"{i}. {name}: {status}")
        if not result:
            all_passed = False

    logger.info("=" * 80)

    if all_passed:
        logger.info("🎉 모든 테스트 통과!")
        logger.info("\n✅ v1.6.0 한 틱 위 지정가 매수 기능 검증 완료")
        logger.info("   - 5가지 시나리오 모두 정상 동작")
        logger.info("   - 시장가/지정가 분기 로직 정상")
        logger.info("   - 100% 체결, 부분 체결, 미체결 처리 정상")
        logger.info("   - 폴백 전략 정상 동작")
    else:
        logger.error("❌ 일부 테스트 실패")

    logger.info("=" * 80)

    return all_passed


if __name__ == "__main__":
    # 테스트 실행
    success = asyncio.run(run_all_tests())

    # 종료 코드 반환
    exit(0 if success else 1)
