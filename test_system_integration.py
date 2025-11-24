"""
시스템 통합 테스트

목적:
- TradingSystemBase + Config 통합 테스트
- 모든 컴포넌트가 정상적으로 초기화되는지 확인
- 매수/매도 플로우가 문제없이 구동되는지 검증
"""

import asyncio
import logging
from datetime import datetime
from unittest.mock import Mock, AsyncMock
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
        """추상 메서드 구현"""
        pass


async def test_system_initialization():
    """시스템 초기화 테스트"""
    logger.info("=" * 80)
    logger.info("🧪 테스트 1: 시스템 초기화")
    logger.info("=" * 80)

    try:
        # Config 로드
        config = TradingConfig.from_env()
        config.validate()
        logger.info("✅ Config 로드 및 검증 완료")

        # TradingSystemBase 초기화
        system = MockTradingSystem(config)
        logger.info("✅ TradingSystemBase 초기화 완료")

        # 주요 속성 확인
        logger.info("\n📋 시스템 주요 속성:")
        logger.info(f"   account_no: {system.account_no}")
        logger.info(f"   max_investment: {system.max_investment:,}원")
        logger.info(f"   order_executed: {system.order_executed}")
        logger.info(f"   sell_executed: {system.sell_executed}")
        logger.info(f"   kiwoom_api: {type(system.kiwoom_api).__name__}")
        logger.info(f"   order_executor: {type(system.order_executor).__name__}")
        logger.info(f"   buy_info: {system.buy_info}")

        # Config 확인
        logger.info("\n📋 Config 주요 설정:")
        logger.info(f"   target_profit_rate: {system.config.target_profit_rate*100:.2f}%")
        logger.info(f"   stop_loss_rate: {system.config.stop_loss_rate*100:.2f}%")
        logger.info(f"   enable_daily_force_sell: {system.config.enable_daily_force_sell}")
        logger.info(f"   daily_force_sell_time: {system.config.daily_force_sell_time}")

        return True

    except Exception as e:
        logger.error(f"❌ 시스템 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_buy_flow():
    """매수 플로우 테스트"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 테스트 2: 매수 플로우")
    logger.info("=" * 80)

    try:
        config = TradingConfig.from_env()
        system = MockTradingSystem(config)

        # kiwoom_api Mock
        system.kiwoom_api = Mock()
        system.kiwoom_api.get_access_token = Mock()
        system.kiwoom_api.get_current_price = Mock(return_value={
            "success": True,
            "current_price": 10000
        })

        # order_executor Mock
        system.order_executor = Mock()
        system.order_executor.execute_market_buy = AsyncMock(return_value={
            "success": True,
            "order_no": "TEST12345",
            "buy_price": 10000,
            "quantity": 100
        })

        # save_trading_result Mock
        system.save_trading_result = AsyncMock()

        logger.info("📊 매수 주문 실행...")
        result = await system.execute_auto_buy(
            stock_code="000000",
            stock_name="테스트종목",
            current_price=10000
        )

        if result and result.get("success"):
            logger.info("✅ 매수 주문 성공")
            logger.info(f"   종목코드: {system.buy_info['stock_code']}")
            logger.info(f"   종목명: {system.buy_info['stock_name']}")
            logger.info(f"   매수가: {system.buy_info['buy_price']:,}원")
            logger.info(f"   수량: {system.buy_info['quantity']}주")
            logger.info(f"   매수 시간: {system.buy_info['buy_time']}")
            return True
        else:
            logger.error("❌ 매수 주문 실패")
            return False

    except Exception as e:
        logger.error(f"❌ 매수 플로우 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sell_flow():
    """매도 플로우 테스트 (익절)"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 테스트 3: 익절 매도 플로우")
    logger.info("=" * 80)

    try:
        config = TradingConfig.from_env()
        system = MockTradingSystem(config)

        # 매수 정보 설정
        system.buy_info = {
            "stock_code": "000000",
            "stock_name": "테스트종목",
            "buy_price": 10000,
            "quantity": 100,
            "buy_time": datetime.now(),
            "target_profit_rate": 0.03  # 3%
        }

        # kiwoom_api Mock
        system.kiwoom_api = Mock()
        system.kiwoom_api.place_limit_sell_order = Mock(return_value={
            "success": True,
            "order_no": "SELL12345"
        })

        # wait_for_sell_execution Mock
        system.wait_for_sell_execution = AsyncMock(return_value=True)

        # cancel_outstanding_buy_orders Mock
        system.cancel_outstanding_buy_orders = AsyncMock()

        # websocket Mock
        system.websocket = Mock()
        system.websocket.unregister_stock = AsyncMock()
        system.ws_receive_task = Mock()
        system.ws_receive_task.cancel = Mock()

        # save_sell_result_ws Mock
        system.save_sell_result_ws = AsyncMock()

        logger.info("📊 익절 매도 실행...")
        logger.info(f"   매수가: {system.buy_info['buy_price']:,}원")
        logger.info(f"   목표 수익률: {system.buy_info['target_profit_rate']*100:.2f}%")

        current_price = 10300  # +3%
        profit_rate = (current_price - system.buy_info['buy_price']) / system.buy_info['buy_price']

        logger.info(f"   현재가: {current_price:,}원")
        logger.info(f"   수익률: {profit_rate*100:.2f}%")

        await system.execute_auto_sell(current_price, profit_rate)

        if system.sell_executed:
            logger.info("✅ 익절 매도 성공")
            logger.info(f"   sell_executed: {system.sell_executed}")

            if system.kiwoom_api.place_limit_sell_order.called:
                logger.info("   ✅ kiwoom_api.place_limit_sell_order 호출됨")
                call_args = system.kiwoom_api.place_limit_sell_order.call_args
                logger.info(f"      - stock_code: {call_args.kwargs.get('stock_code')}")
                logger.info(f"      - quantity: {call_args.kwargs.get('quantity')}")
                logger.info(f"      - price: {call_args.kwargs.get('price')}")
                logger.info(f"      - account_no: {call_args.kwargs.get('account_no')}")
            else:
                logger.error("   ❌ kiwoom_api.place_limit_sell_order 호출 안됨")
                return False

            return True
        else:
            logger.error("❌ 익절 매도 실패")
            return False

    except Exception as e:
        logger.error(f"❌ 익절 플로우 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stop_loss_flow():
    """손절 매도 플로우 테스트"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 테스트 4: 손절 매도 플로우")
    logger.info("=" * 80)

    try:
        config = TradingConfig.from_env()
        system = MockTradingSystem(config)

        # 매수 정보 설정
        system.buy_info = {
            "stock_code": "000000",
            "stock_name": "테스트종목",
            "buy_price": 10000,
            "quantity": 100,
            "buy_time": datetime.now(),
            "target_profit_rate": 0.03
        }

        # kiwoom_api Mock
        system.kiwoom_api = Mock()
        system.kiwoom_api.place_market_sell_order = Mock(return_value={
            "success": True,
            "order_no": "STOPLOSS12345"
        })

        # cancel_outstanding_buy_orders Mock
        system.cancel_outstanding_buy_orders = AsyncMock()

        # websocket Mock
        system.websocket = Mock()
        system.websocket.unregister_stock = AsyncMock()
        system.ws_receive_task = Mock()
        system.ws_receive_task.cancel = Mock()

        # save_stop_loss_result Mock
        system.save_stop_loss_result = AsyncMock()

        logger.info("📊 손절 매도 실행...")
        logger.info(f"   매수가: {system.buy_info['buy_price']:,}원")
        logger.info(f"   손절 수익률: {system.config.stop_loss_rate*100:.2f}%")

        current_price = 9700  # -3%
        profit_rate = (current_price - system.buy_info['buy_price']) / system.buy_info['buy_price']

        logger.info(f"   현재가: {current_price:,}원")
        logger.info(f"   수익률: {profit_rate*100:.2f}%")

        await system.execute_stop_loss(current_price, profit_rate)

        if system.sell_executed:
            logger.info("✅ 손절 매도 성공")
            logger.info(f"   sell_executed: {system.sell_executed}")

            if system.kiwoom_api.place_market_sell_order.called:
                logger.info("   ✅ kiwoom_api.place_market_sell_order 호출됨")
                call_args = system.kiwoom_api.place_market_sell_order.call_args
                logger.info(f"      - stock_code: {call_args.kwargs.get('stock_code')}")
                logger.info(f"      - quantity: {call_args.kwargs.get('quantity')}")
                logger.info(f"      - account_no: {call_args.kwargs.get('account_no')}")
            else:
                logger.error("   ❌ kiwoom_api.place_market_sell_order 호출 안됨")
                return False

            return True
        else:
            logger.error("❌ 손절 매도 실패")
            return False

    except Exception as e:
        logger.error(f"❌ 손절 플로우 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_force_sell_flow():
    """강제 청산 플로우 테스트"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 테스트 5: 강제 청산 플로우")
    logger.info("=" * 80)

    try:
        config = TradingConfig.from_env()
        system = MockTradingSystem(config)

        # 매수 정보 설정
        system.buy_info = {
            "stock_code": "000000",
            "stock_name": "테스트종목",
            "buy_price": 10000,
            "quantity": 100,
            "buy_time": datetime.now(),
            "target_profit_rate": 0.03
        }

        # kiwoom_api Mock
        system.kiwoom_api = Mock()
        system.kiwoom_api.get_outstanding_orders = Mock(return_value={
            "success": True,
            "outstanding_orders": []
        })
        system.kiwoom_api.place_market_sell_order = Mock(return_value={
            "success": True,
            "order_no": "FORCE12345"
        })
        system.kiwoom_api.get_current_price = Mock(return_value={
            "success": True,
            "current_price": 10050
        })

        # websocket Mock
        system.websocket = Mock()
        system.websocket.unregister_stock = AsyncMock()
        system.ws_receive_task = Mock()
        system.ws_receive_task.cancel = Mock()

        # save_force_sell_result Mock
        system.save_force_sell_result = AsyncMock()

        logger.info("📊 강제 청산 실행...")
        logger.info(f"   강제 청산 시간: {system.config.daily_force_sell_time}")

        await system.execute_daily_force_sell()

        if system.sell_executed:
            logger.info("✅ 강제 청산 성공")
            logger.info(f"   sell_executed: {system.sell_executed}")

            if system.kiwoom_api.place_market_sell_order.called:
                logger.info("   ✅ kiwoom_api.place_market_sell_order 호출됨")
                call_args = system.kiwoom_api.place_market_sell_order.call_args
                logger.info(f"      - stock_code: {call_args.kwargs.get('stock_code')}")
                logger.info(f"      - quantity: {call_args.kwargs.get('quantity')}")
                logger.info(f"      - account_no: {call_args.kwargs.get('account_no')}")
            else:
                logger.error("   ❌ kiwoom_api.place_market_sell_order 호출 안됨")
                return False

            return True
        else:
            logger.error("❌ 강제 청산 실패")
            return False

    except Exception as e:
        logger.error(f"❌ 강제 청산 플로우 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 테스트 실행"""
    logger.info("=" * 80)
    logger.info("🧪 시스템 통합 테스트 시작")
    logger.info("=" * 80)
    logger.info("")

    results = []

    # 테스트 1: 시스템 초기화
    results.append(("시스템 초기화", await test_system_initialization()))

    # 테스트 2: 매수 플로우
    results.append(("매수 플로우", await test_buy_flow()))

    # 테스트 3: 익절 매도 플로우
    results.append(("익절 매도 플로우", await test_sell_flow()))

    # 테스트 4: 손절 매도 플로우
    results.append(("손절 매도 플로우", await test_stop_loss_flow()))

    # 테스트 5: 강제 청산 플로우
    results.append(("강제 청산 플로우", await test_force_sell_flow()))

    # 결과 요약
    logger.info("\n" + "=" * 80)
    logger.info("📊 테스트 결과 요약")
    logger.info("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {status} | {test_name}")

    logger.info("\n" + "=" * 80)
    if passed == total:
        logger.info(f"✅ 모든 테스트 통과! ({passed}/{total})")
        logger.info("✅ 시스템이 정상적으로 구동됩니다!")
    else:
        logger.error(f"❌ 일부 테스트 실패 ({passed}/{total})")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
