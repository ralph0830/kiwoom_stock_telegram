"""
일일 강제 청산 로직 시뮬레이션 테스트

목적:
- ENABLE_DAILY_FORCE_SELL 설정 확인
- DAILY_FORCE_SELL_TIME 시간 도달 확인
- is_force_sell_time() 메서드 동작 확인
- execute_daily_force_sell() 호출 확인
- 우선순위: 강제청산 > 손절 > 익절 검증
"""

import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from config import TradingConfig
from trading_system_base import TradingSystemBase

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockTradingSystem(TradingSystemBase):
    """테스트용 TradingSystemBase Mock 클래스"""

    async def start_monitoring(self):
        """추상 메서드 구현 (사용 안 함)"""
        pass


async def test_force_sell_time_detection():
    """강제 청산 시간 감지 테스트"""
    logger.info("=" * 80)
    logger.info("🧪 테스트 1: 강제 청산 시간 감지")
    logger.info("=" * 80)

    # Config 생성 (강제 청산 활성화)
    config = TradingConfig.from_env()
    config.enable_daily_force_sell = True
    config.daily_force_sell_time = "15:19"

    # Mock 시스템 생성
    system = MockTradingSystem(config)

    # 현재 시간 확인
    now = datetime.now()
    current_time_str = now.strftime("%H:%M")

    logger.info(f"✅ 현재 시간: {current_time_str}")
    logger.info(f"✅ 강제 청산 설정 시간: {config.daily_force_sell_time}")
    logger.info(f"✅ 강제 청산 활성화 여부: {config.enable_daily_force_sell}")

    # is_force_sell_time() 메서드 테스트
    is_time = system.is_force_sell_time()

    if is_time:
        logger.info(f"🎯 강제 청산 시간 도달! (현재: {current_time_str} >= 설정: {config.daily_force_sell_time})")
    else:
        logger.info(f"⏰ 강제 청산 시간 미도달 (현재: {current_time_str} < 설정: {config.daily_force_sell_time})")

    logger.info("")
    return is_time


async def test_force_sell_time_with_mocking():
    """시간 Mocking을 통한 강제 청산 시간 테스트"""
    logger.info("=" * 80)
    logger.info("🧪 테스트 2: 강제 청산 시간 Mocking 테스트")
    logger.info("=" * 80)

    # Config 생성
    config = TradingConfig.from_env()
    config.enable_daily_force_sell = True
    config.daily_force_sell_time = "15:19"

    # Mock 시스템 생성
    system = MockTradingSystem(config)

    # 테스트 시나리오
    test_cases = [
        ("15:18", False, "1분 전"),
        ("15:19", True, "정확히 청산 시간"),
        ("15:20", True, "1분 후"),
        ("15:30", True, "11분 후"),
    ]

    for test_time, expected, description in test_cases:
        # datetime.now() Mock
        mock_time = datetime.strptime(f"2025-01-14 {test_time}", "%Y-%m-%d %H:%M")

        with patch('trading_system_base.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_time
            mock_datetime.strptime = datetime.strptime  # strptime은 실제 함수 사용

            is_time = system.is_force_sell_time()

            status = "✅ PASS" if is_time == expected else "❌ FAIL"
            logger.info(f"{status} | 시간: {test_time} | 예상: {expected} | 실제: {is_time} | {description}")

    logger.info("")


async def test_force_sell_priority():
    """강제 청산 우선순위 테스트 (강제청산 > 손절 > 익절)"""
    logger.info("=" * 80)
    logger.info("🧪 테스트 3: 강제 청산 우선순위 검증")
    logger.info("=" * 80)

    # Config 생성
    config = TradingConfig.from_env()
    config.enable_daily_force_sell = True
    config.daily_force_sell_time = "15:19"
    config.enable_stop_loss = True
    config.stop_loss_rate = -0.025  # -2.5%
    config.target_profit_rate = 0.01  # 1%

    # Mock 시스템 생성
    system = MockTradingSystem(config)

    # 매수 정보 설정
    system.buy_info = {
        "stock_code": "000000",
        "stock_name": "테스트종목",
        "buy_price": 10000,
        "quantity": 100,
        "buy_time": datetime.now() - timedelta(minutes=10),
        "target_profit_rate": 0.01
    }

    # Mock 함수 설정
    system.execute_daily_force_sell = AsyncMock()
    system.execute_stop_loss = AsyncMock()
    system.execute_auto_sell = AsyncMock()

    # 시나리오 1: 강제청산 시간 + 익절 조건 + 손절 조건 모두 만족
    logger.info("📋 시나리오 1: 강제청산 시간 + 익절 조건 + 손절 조건 모두 만족")

    # 강제 청산 시간으로 Mock
    mock_time = datetime.strptime("2025-01-14 15:19", "%Y-%m-%d %H:%M")

    with patch('trading_system_base.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_time
        mock_datetime.strptime = datetime.strptime

        # 익절 조건 만족하는 가격 (10,100원 = +1%)
        current_price = 10100
        profit_rate = (current_price - system.buy_info["buy_price"]) / system.buy_info["buy_price"]

        logger.info(f"   현재가: {current_price:,}원")
        logger.info(f"   수익률: {profit_rate*100:.2f}%")
        logger.info(f"   강제청산 시간: {system.is_force_sell_time()}")
        logger.info(f"   익절 조건: {profit_rate >= config.target_profit_rate}")
        logger.info(f"   손절 조건: {profit_rate <= config.stop_loss_rate}")

        # on_price_update 호출
        await system.on_price_update("000000", current_price, {})

        # 검증
        if system.execute_daily_force_sell.called:
            logger.info("   ✅ 강제 청산이 최우선으로 실행됨")
        else:
            logger.error("   ❌ 강제 청산이 실행되지 않음")

        if not system.execute_auto_sell.called and not system.execute_stop_loss.called:
            logger.info("   ✅ 익절/손절이 실행되지 않음 (올바른 우선순위)")
        else:
            logger.error("   ❌ 익절/손절이 실행됨 (잘못된 우선순위)")

    logger.info("")

    # 초기화
    system.execute_daily_force_sell.reset_mock()
    system.execute_stop_loss.reset_mock()
    system.execute_auto_sell.reset_mock()
    system.sell_executed = False

    # 시나리오 2: 강제청산 시간 아님 + 손절 조건 + 익절 조건 만족
    logger.info("📋 시나리오 2: 강제청산 시간 아님 + 손절 조건 + 익절 조건 만족")

    mock_time = datetime.strptime("2025-01-14 14:00", "%Y-%m-%d %H:%M")

    with patch('trading_system_base.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_time
        mock_datetime.strptime = datetime.strptime

        # 손절 조건 만족하는 가격 (9,700원 = -3%)
        current_price = 9700
        profit_rate = (current_price - system.buy_info["buy_price"]) / system.buy_info["buy_price"]

        logger.info(f"   현재가: {current_price:,}원")
        logger.info(f"   수익률: {profit_rate*100:.2f}%")
        logger.info(f"   강제청산 시간: {system.is_force_sell_time()}")
        logger.info(f"   익절 조건: {profit_rate >= config.target_profit_rate}")
        logger.info(f"   손절 조건: {profit_rate <= config.stop_loss_rate}")

        # on_price_update 호출
        await system.on_price_update("000000", current_price, {})

        # 검증
        if not system.execute_daily_force_sell.called:
            logger.info("   ✅ 강제 청산이 실행되지 않음 (시간 미도달)")
        else:
            logger.error("   ❌ 강제 청산이 실행됨 (시간 미도달인데 실행)")

        if system.execute_stop_loss.called:
            logger.info("   ✅ 손절이 실행됨 (강제청산 다음 우선순위)")
        else:
            logger.error("   ❌ 손절이 실행되지 않음")

        if not system.execute_auto_sell.called:
            logger.info("   ✅ 익절이 실행되지 않음 (손절 우선)")
        else:
            logger.error("   ❌ 익절이 실행됨 (손절보다 우선 실행됨)")

    logger.info("")


async def test_force_sell_execution_logic():
    """강제 청산 실행 로직 테스트"""
    logger.info("=" * 80)
    logger.info("🧪 테스트 4: 강제 청산 실행 로직")
    logger.info("=" * 80)

    # Config 생성
    config = TradingConfig.from_env()
    config.enable_daily_force_sell = True
    config.daily_force_sell_time = "15:19"

    # Mock 시스템 생성
    system = MockTradingSystem(config)

    # 매수 정보 설정
    system.buy_info = {
        "stock_code": "000000",
        "stock_name": "테스트종목",
        "buy_price": 10000,
        "quantity": 100,
        "buy_time": datetime.now() - timedelta(minutes=10),
        "target_profit_rate": 0.01
    }

    # kiwoom_api Mock
    system.kiwoom_api = Mock()
    system.kiwoom_api.get_outstanding_orders = Mock(return_value={
        "success": True,
        "outstanding_orders": []
    })
    system.kiwoom_api.place_market_sell_order = Mock(return_value={
        "success": True,
        "order_no": "TEST12345"
    })
    system.kiwoom_api.get_current_price = Mock(return_value={
        "success": True,
        "current_price": 10050
    })

    # WebSocket Mock
    system.websocket = Mock()
    system.websocket.unregister_stock = AsyncMock()
    system.ws_receive_task = Mock()
    system.ws_receive_task.cancel = Mock()

    # save_force_sell_result Mock
    system.save_force_sell_result = AsyncMock()

    logger.info("📊 초기 상태:")
    logger.info(f"   종목코드: {system.buy_info['stock_code']}")
    logger.info(f"   종목명: {system.buy_info['stock_name']}")
    logger.info(f"   매수가: {system.buy_info['buy_price']:,}원")
    logger.info(f"   보유 수량: {system.buy_info['quantity']}주")
    logger.info("")

    # 강제 청산 실행
    logger.info("🚀 강제 청산 실행...")
    await system.execute_daily_force_sell()

    # 검증
    logger.info("")
    logger.info("📋 실행 결과:")

    if system.sell_executed:
        logger.info("   ✅ sell_executed 플래그 설정됨")
    else:
        logger.error("   ❌ sell_executed 플래그 설정 안됨")

    if system.kiwoom_api.place_market_sell_order.called:
        logger.info("   ✅ 시장가 매도 주문 호출됨")
        call_args = system.kiwoom_api.place_market_sell_order.call_args
        logger.info(f"      - 종목코드: {call_args.kwargs.get('stock_code')}")
        logger.info(f"      - 수량: {call_args.kwargs.get('quantity')}주")
        logger.info(f"      - 계좌번호: {call_args.kwargs.get('account_no')}")
    else:
        logger.error("   ❌ 시장가 매도 주문 호출 안됨")

    if system.websocket.unregister_stock.called:
        logger.info("   ✅ WebSocket 시세 등록 해제됨")
    else:
        logger.error("   ❌ WebSocket 시세 등록 해제 안됨")

    if system.save_force_sell_result.called:
        logger.info("   ✅ 강제 청산 결과 저장됨")
    else:
        logger.error("   ❌ 강제 청산 결과 저장 안됨")

    logger.info("")


async def main():
    """메인 테스트 실행 함수"""
    logger.info("=" * 80)
    logger.info("🧪 일일 강제 청산 로직 시뮬레이션 테스트 시작")
    logger.info("=" * 80)
    logger.info("")

    try:
        # 테스트 1: 실제 시간 기반 강제 청산 시간 감지
        await test_force_sell_time_detection()

        # 테스트 2: Mocking을 통한 강제 청산 시간 테스트
        await test_force_sell_time_with_mocking()

        # 테스트 3: 강제 청산 우선순위 검증
        await test_force_sell_priority()

        # 테스트 4: 강제 청산 실행 로직
        await test_force_sell_execution_logic()

        logger.info("=" * 80)
        logger.info("✅ 모든 테스트 완료!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
