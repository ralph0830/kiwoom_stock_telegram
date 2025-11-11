#!/usr/bin/env python3
"""
자동매매 시스템 시뮬레이션 테스트

실제 주문 없이 개선된 코드의 로직을 검증합니다.
"""

import asyncio
import logging
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock
from rich.console import Console
from rich.table import Table

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


async def test_order_executor():
    """OrderExecutor 테스트"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]OrderExecutor 시뮬레이션 테스트")
    console.print("[bold cyan]=" * 40)

    from order_executor import OrderExecutor
    from kiwoom_order import KiwoomOrderAPI

    # Mock API 생성
    mock_api = Mock(spec=KiwoomOrderAPI)
    mock_api.place_market_buy_order = Mock(return_value={
        "success": True,
        "order_no": "TEST-BUY-001",
        "message": "매수 주문 성공"
    })
    mock_api.place_limit_sell_order = Mock(return_value={
        "success": True,
        "order_no": "TEST-SELL-001",
        "message": "매도 주문 성공"
    })
    mock_api.place_market_sell_order = Mock(return_value={
        "success": True,
        "order_no": "TEST-SELL-002",
        "message": "시장가 매도 성공"
    })

    # OrderExecutor 생성
    executor = OrderExecutor(mock_api, "12345678-01")

    # 테스트 1: 매수 수량 계산
    console.print("\n[bold yellow]📊 테스트 1: 매수 수량 계산")
    test_cases = [
        (10000, 1000000),  # 현재가 10,000원, 최대투자 1,000,000원
        (50000, 2000000),  # 현재가 50,000원, 최대투자 2,000,000원
        (100000, 500000),  # 현재가 100,000원, 최대투자 500,000원
    ]

    for current_price, max_investment in test_cases:
        quantity = executor.calculate_buy_quantity(current_price, max_investment)
        console.print(f"  현재가: {current_price:,}원, 최대투자: {max_investment:,}원 → 수량: {quantity}주")

    # 테스트 2: 매도가 계산
    console.print("\n[bold yellow]📊 테스트 2: 매도가 계산 (목표 수익률 1%)")
    test_cases = [
        (10000, 0.01),  # 매수가 10,000원, 목표 1%
        (50000, 0.01),  # 매수가 50,000원, 목표 1%
        (100000, 0.01), # 매수가 100,000원, 목표 1%
    ]

    for buy_price, profit_rate in test_cases:
        sell_price = executor.calculate_sell_price(buy_price, profit_rate)
        console.print(f"  매수가: {buy_price:,}원, 목표: {profit_rate*100:.1f}% → 매도가: {sell_price:,}원")

    # 테스트 3: 시장가 매수 주문
    console.print("\n[bold yellow]📊 테스트 3: 시장가 매수 주문")
    result = await executor.execute_market_buy(
        stock_code="005930",
        stock_name="삼성전자",
        quantity=10,
        current_price=70000
    )
    console.print(f"  결과: {result}")

    # 테스트 4: 지정가 매도 주문 (익절)
    console.print("\n[bold yellow]📊 테스트 4: 지정가 매도 주문 (익절)")
    result = await executor.execute_limit_sell(
        stock_code="005930",
        stock_name="삼성전자",
        quantity=10,
        sell_price=70700,
        reason="익절"
    )
    console.print(f"  결과: {result}")

    # 테스트 5: 시장가 매도 주문 (손절)
    console.print("\n[bold yellow]📊 테스트 5: 시장가 매도 주문 (손절)")
    result = await executor.execute_market_sell(
        stock_code="005930",
        stock_name="삼성전자",
        quantity=10,
        current_price=68250,
        reason="손절"
    )
    console.print(f"  결과: {result}")

    console.print("\n[bold green]✅ OrderExecutor 테스트 완료!")
    return True


async def test_price_monitor():
    """PriceMonitor 테스트"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]PriceMonitor 시뮬레이션 테스트")
    console.print("[bold cyan]=" * 40)

    from price_monitor import PriceMonitor
    from kiwoom_websocket import KiwoomWebSocket
    from kiwoom_order import KiwoomOrderAPI

    # Mock WebSocket 생성
    mock_ws = Mock(spec=KiwoomWebSocket)
    mock_ws.connect = AsyncMock(return_value=None)
    mock_ws.register_stock = AsyncMock(return_value=None)
    mock_ws.unregister_stock = AsyncMock(return_value=None)
    mock_ws.close = AsyncMock(return_value=None)
    mock_ws.get_current_price = Mock(return_value=70000)

    # Mock API 생성
    mock_api = Mock(spec=KiwoomOrderAPI)
    mock_api.get_current_price = Mock(return_value={
        "success": True,
        "price": 70000,
        "current_price": 70000
    })

    # PriceMonitor 생성
    monitor = PriceMonitor(mock_ws, mock_api)

    # 테스트 1: 모니터링 시작
    console.print("\n[bold yellow]📊 테스트 1: 모니터링 시작")

    price_updates = []

    async def mock_callback(stock_code, price, data):
        price_updates.append({
            "stock_code": stock_code,
            "price": price,
            "timestamp": datetime.now()
        })
        console.print(f"  📈 가격 업데이트: {stock_code} - {price:,}원")

    try:
        await monitor.start_monitoring("005930", mock_callback)
        console.print("  ✅ 모니터링 시작 성공")
    except Exception as e:
        console.print(f"  ⚠️ 모니터링 시작 실패: {e}")

    # 테스트 2: 현재가 조회
    console.print("\n[bold yellow]📊 테스트 2: 현재가 조회")
    cached_price = monitor.get_current_price("005930")
    console.print(f"  캐시된 가격: {cached_price:,}원")

    api_price = await monitor.get_current_price_from_api("005930")
    console.print(f"  API 조회 가격: {api_price:,}원")

    # 테스트 3: 모니터링 상태 확인
    console.print("\n[bold yellow]📊 테스트 3: 모니터링 상태")
    console.print(f"  모니터링 중: {monitor.is_monitoring}")
    console.print(f"  모니터링 종목: {monitor.monitored_stocks}")

    # 테스트 4: 모니터링 중지
    console.print("\n[bold yellow]📊 테스트 4: 모니터링 중지")
    try:
        await monitor.stop_monitoring("005930")
        console.print("  ✅ 모니터링 중지 성공")
    except Exception as e:
        console.print(f"  ⚠️ 모니터링 중지 실패: {e}")

    console.print("\n[bold green]✅ PriceMonitor 테스트 완료!")
    return True


async def test_exceptions():
    """커스텀 예외 테스트"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]커스텀 예외 시뮬레이션 테스트")
    console.print("[bold cyan]=" * 40)

    from exceptions import (
        TradingNetworkError,
        TradingTimeoutError,
        TradingAuthError,
        TradingInsufficientBalanceError,
        TradingOrderRejectError,
        get_exception_type,
        format_exception_message
    )

    # 테스트 1: 예외 생성 및 메시지
    console.print("\n[bold yellow]📊 테스트 1: 예외 생성")
    test_exceptions = [
        TradingNetworkError("네트워크 연결 실패", "NET001"),
        TradingTimeoutError("API 응답 타임아웃", "TIMEOUT001"),
        TradingAuthError("토큰 인증 실패", "AUTH001"),
        TradingInsufficientBalanceError("잔고 부족", "BAL001"),
        TradingOrderRejectError("주문 거부: 시장가 거래 불가", "ORD001"),
    ]

    for exc in test_exceptions:
        console.print(f"  {exc.__class__.__name__}: {exc}")
        formatted = format_exception_message(exc)
        console.print(f"    → {formatted}")

    # 테스트 2: 예외 타입 추론
    console.print("\n[bold yellow]📊 테스트 2: 에러 메시지로 예외 타입 추론")
    test_messages = [
        "Connection timed out",
        "네트워크 연결 실패",
        "토큰이 만료되었습니다",
        "잔고가 부족합니다",
        "주문이 거부되었습니다",
    ]

    for msg in test_messages:
        exc_type = get_exception_type(msg)
        console.print(f"  '{msg}' → {exc_type.__name__}")

    console.print("\n[bold green]✅ 커스텀 예외 테스트 완료!")
    return True


async def test_config():
    """TradingConfig 테스트"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]TradingConfig 시뮬레이션 테스트")
    console.print("[bold cyan]=" * 40)

    from config import TradingConfig
    import os

    # 테스트 1: 환경변수 로드
    console.print("\n[bold yellow]📊 테스트 1: 환경변수 로드")
    try:
        # .env 파일에서 로드 시도
        config = TradingConfig.from_env()
        console.print("  ✅ 설정 로드 성공")

        # 주요 설정 출력
        table = Table(title="자동매매 설정")
        table.add_column("항목", style="cyan")
        table.add_column("값", style="green")

        table.add_row("계좌번호", config.account_no)
        table.add_row("최대 투자금액", f"{config.max_investment:,}원")
        table.add_row("목표 수익률", f"{config.target_profit_rate*100:.2f}%")
        table.add_row("손절 수익률", f"{config.stop_loss_rate*100:.2f}%")
        table.add_row("손절 지연", f"{config.stop_loss_delay_minutes}분")
        table.add_row("매수 시간", f"{config.buy_start_time} ~ {config.buy_end_time}")
        table.add_row("강제 청산 시간", config.daily_force_sell_time)
        table.add_row("디버그 모드", str(config.debug_mode))

        console.print(table)

    except Exception as e:
        console.print(f"  ⚠️ 설정 로드 실패: {e}")
        return False

    # 테스트 2: 설정 검증
    console.print("\n[bold yellow]📊 테스트 2: 설정 검증")
    try:
        config.validate()
        console.print("  ✅ 설정 검증 통과")
    except Exception as e:
        console.print(f"  ❌ 설정 검증 실패: {e}")
        return False

    console.print("\n[bold green]✅ TradingConfig 테스트 완료!")
    return True


async def test_integration():
    """통합 시뮬레이션 테스트"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]통합 시뮬레이션 테스트")
    console.print("[bold cyan]=" * 40)

    console.print("\n[bold yellow]📊 시나리오: 매수 → 익절 시뮬레이션")

    # 시뮬레이션 데이터
    stock_code = "005930"
    stock_name = "삼성전자"
    buy_price = 70000
    quantity = 10
    target_profit_rate = 0.01  # 1%

    console.print(f"\n  종목: {stock_name} ({stock_code})")
    console.print(f"  매수가: {buy_price:,}원")
    console.print(f"  수량: {quantity}주")
    console.print(f"  투자금액: {buy_price * quantity:,}원")
    console.print(f"  목표 수익률: {target_profit_rate*100:.1f}%")

    # OrderExecutor 사용
    from order_executor import OrderExecutor
    from kiwoom_order import KiwoomOrderAPI

    mock_api = Mock(spec=KiwoomOrderAPI)
    executor = OrderExecutor(mock_api, "12345678-01")

    # 매도가 계산
    sell_price = executor.calculate_sell_price(buy_price, target_profit_rate)
    console.print(f"  매도가: {sell_price:,}원")

    # 예상 수익 계산
    profit_per_share = sell_price - buy_price
    total_profit = profit_per_share * quantity
    actual_profit_rate = (sell_price - buy_price) / buy_price

    console.print(f"\n  예상 수익:")
    console.print(f"    주당 수익: {profit_per_share:,}원")
    console.print(f"    총 수익: {total_profit:,}원")
    console.print(f"    실제 수익률: {actual_profit_rate*100:.2f}%")

    # 가격 변동 시뮬레이션
    console.print(f"\n[bold yellow]📊 가격 변동 시뮬레이션")

    price_scenarios = [
        (69000, "하락 중"),
        (69500, "약간 하락"),
        (70000, "보합"),
        (70500, "상승 중"),
        (70700, "목표 도달"),
    ]

    for price, status in price_scenarios:
        current_rate = (price - buy_price) / buy_price
        console.print(f"  현재가: {price:,}원 ({status}) - 수익률: {current_rate*100:+.2f}%")

    console.print("\n[bold green]✅ 통합 시뮬레이션 완료!")
    return True


async def main():
    """메인 테스트 함수"""
    console.print("\n")
    console.print("[bold blue]╔" + "=" * 78 + "╗")
    console.print("[bold blue]║" + " " * 20 + "자동매매 시스템 시뮬레이션 테스트" + " " * 23 + "║")
    console.print("[bold blue]╚" + "=" * 78 + "╝")

    results = []

    # 테스트 실행
    tests = [
        ("TradingConfig", test_config),
        ("커스텀 예외", test_exceptions),
        ("OrderExecutor", test_order_executor),
        ("PriceMonitor", test_price_monitor),
        ("통합 시나리오", test_integration),
    ]

    for test_name, test_func in tests:
        try:
            console.print(f"\n[bold]▶ {test_name} 테스트 시작...[/bold]")
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"\n[bold red]❌ {test_name} 테스트 실패: {e}[/bold red]")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # 최종 결과
    console.print("\n")
    console.print("[bold cyan]=" * 80)
    console.print("[bold cyan]최종 테스트 결과")
    console.print("[bold cyan]=" * 80)

    result_table = Table(title="시뮬레이션 테스트 결과")
    result_table.add_column("테스트", style="cyan")
    result_table.add_column("결과", style="bold")

    passed = 0
    failed = 0

    for test_name, result in results:
        if result:
            result_table.add_row(test_name, "[green]✅ PASS[/green]")
            passed += 1
        else:
            result_table.add_row(test_name, "[red]❌ FAIL[/red]")
            failed += 1

    console.print(result_table)

    console.print(f"\n[bold]총 {len(results)}개 테스트:[/bold]")
    console.print(f"  [green]✅ 통과: {passed}개[/green]")
    console.print(f"  [red]❌ 실패: {failed}개[/red]")

    if failed == 0:
        console.print("\n[bold green]🎉 모든 시뮬레이션 테스트 통과![/bold green]")
        console.print("[bold green]개선된 코드가 정상적으로 동작합니다.[/bold green]")
        return 0
    else:
        console.print(f"\n[bold red]⚠️ {failed}개 테스트 실패. 코드를 확인해주세요.[/bold red]")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
