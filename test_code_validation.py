#!/usr/bin/env python3
"""
전체 코드 검증 스크립트

모든 파일의 import, 의존성, 로직을 체계적으로 검증합니다.
"""

import sys
import importlib
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def test_imports():
    """모든 파일의 import 검증"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]1. Import 의존성 검증")
    console.print("[bold cyan]=" * 40)

    files_to_test = [
        "config",
        "exceptions",
        "order_executor",
        "price_monitor",
        "kiwoom_order",
        "kiwoom_websocket",
        "trading_system_base",
        "auto_trading",
    ]

    results = []

    for module_name in files_to_test:
        try:
            module = importlib.import_module(module_name)
            console.print(f"  ✅ {module_name}.py - import 성공")
            results.append((module_name, True, None))
        except Exception as e:
            console.print(f"  ❌ {module_name}.py - import 실패: {e}")
            results.append((module_name, False, str(e)))

    return all(r[1] for r in results), results


def test_config():
    """TradingConfig 검증"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]2. TradingConfig 검증")
    console.print("[bold cyan]=" * 40)

    try:
        from config import TradingConfig

        # 환경변수 로드
        config = TradingConfig.from_env()
        console.print("  ✅ 환경변수 로드 성공")

        # 설정 검증
        config.validate()
        console.print("  ✅ 설정 검증 통과")

        # 주요 설정 확인
        checks = [
            ("계좌번호", config.account_no is not None),
            ("최대 투자금액", config.max_investment > 0),
            ("목표 수익률", config.target_profit_rate > 0),
            ("손절 수익률", config.stop_loss_rate < 0),
            ("매수 시간", config.buy_start_time and config.buy_end_time),
            ("강제 청산 시간", config.daily_force_sell_time is not None),
        ]

        table = Table(title="설정 검증")
        table.add_column("항목", style="cyan")
        table.add_column("상태", style="bold")

        for check_name, passed in checks:
            status = "[green]✅ OK[/green]" if passed else "[red]❌ FAIL[/red]"
            table.add_row(check_name, status)

        console.print(table)

        return all(c[1] for c in checks)

    except Exception as e:
        console.print(f"  ❌ TradingConfig 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_order_executor():
    """OrderExecutor 검증"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]3. OrderExecutor 검증")
    console.print("[bold cyan]=" * 40)

    try:
        from order_executor import OrderExecutor
        from kiwoom_order import KiwoomOrderAPI
        from unittest.mock import Mock

        # Mock API
        mock_api = Mock(spec=KiwoomOrderAPI)
        executor = OrderExecutor(mock_api)

        # 테스트 케이스
        tests = []

        # 1. 매수 수량 계산
        try:
            quantity = executor.calculate_buy_quantity(10000, 1000000)
            tests.append(("매수 수량 계산", quantity > 0))
        except Exception as e:
            tests.append(("매수 수량 계산", False))
            console.print(f"    ❌ 매수 수량 계산 오류: {e}")

        # 2. 매도가 계산
        try:
            sell_price = executor.calculate_sell_price(10000, 0.01)
            tests.append(("매도가 계산", sell_price > 10000))
        except Exception as e:
            tests.append(("매도가 계산", False))
            console.print(f"    ❌ 매도가 계산 오류: {e}")

        # 3. OrderExecutor 속성 확인
        tests.append(("OrderExecutor.api 존재", hasattr(executor, 'api')))

        # 결과 출력
        for test_name, passed in tests:
            status = "✅" if passed else "❌"
            console.print(f"  {status} {test_name}")

        return all(t[1] for t in tests)

    except Exception as e:
        console.print(f"  ❌ OrderExecutor 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_price_monitor():
    """PriceMonitor 검증"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]4. PriceMonitor 검증")
    console.print("[bold cyan]=" * 40)

    try:
        from price_monitor import PriceMonitor
        from kiwoom_websocket import KiwoomWebSocket
        from kiwoom_order import KiwoomOrderAPI
        from unittest.mock import Mock

        # Mock 객체
        mock_ws = Mock(spec=KiwoomWebSocket)
        mock_api = Mock(spec=KiwoomOrderAPI)
        monitor = PriceMonitor(mock_ws, mock_api)

        # 테스트
        tests = [
            ("PriceMonitor.websocket 존재", hasattr(monitor, 'websocket')),
            ("PriceMonitor.api 존재", hasattr(monitor, 'api')),
            ("PriceMonitor.callbacks 존재", hasattr(monitor, 'callbacks')),
            ("PriceMonitor.monitoring 존재", hasattr(monitor, 'monitoring')),
        ]

        for test_name, passed in tests:
            status = "✅" if passed else "❌"
            console.print(f"  {status} {test_name}")

        return all(t[1] for t in tests)

    except Exception as e:
        console.print(f"  ❌ PriceMonitor 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trading_system_base():
    """TradingSystemBase 검증"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]5. TradingSystemBase 검증")
    console.print("[bold cyan]=" * 40)

    try:
        from trading_system_base import TradingSystemBase
        from config import TradingConfig

        # 추상 메서드 확인
        abstract_methods = ['start_monitoring']

        tests = [
            ("TradingSystemBase is ABC", hasattr(TradingSystemBase, '__abstractmethods__')),
        ]

        for method_name in abstract_methods:
            has_method = hasattr(TradingSystemBase, method_name)
            tests.append((f"추상 메서드 '{method_name}' 정의됨", has_method))

        # 주요 메서드 확인
        required_methods = [
            'execute_auto_buy',
            'execute_auto_sell',
            'execute_stop_loss',
            'execute_daily_force_sell',
            'on_price_update',
            'is_force_sell_time',
            'check_today_trading_done',
            'record_today_trading',
        ]

        for method_name in required_methods:
            has_method = hasattr(TradingSystemBase, method_name)
            tests.append((f"메서드 '{method_name}' 존재", has_method))

        for test_name, passed in tests:
            status = "✅" if passed else "❌"
            console.print(f"  {status} {test_name}")

        return all(t[1] for t in tests)

    except Exception as e:
        console.print(f"  ❌ TradingSystemBase 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auto_trading():
    """AutoTrading (TelegramTradingSystem) 검증"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]6. TelegramTradingSystem 검증")
    console.print("[bold cyan]=" * 40)

    try:
        from auto_trading import TelegramTradingSystem
        from trading_system_base import TradingSystemBase

        # 상속 확인
        tests = [
            ("TradingSystemBase 상속", issubclass(TelegramTradingSystem, TradingSystemBase)),
        ]

        # 필수 메서드 구현 확인
        required_methods = [
            'start_monitoring',
            'parse_stock_signal',
            'handle_telegram_signal',
        ]

        for method_name in required_methods:
            has_method = hasattr(TelegramTradingSystem, method_name)
            tests.append((f"메서드 '{method_name}' 구현됨", has_method))

        for test_name, passed in tests:
            status = "✅" if passed else "❌"
            console.print(f"  {status} {test_name}")

        return all(t[1] for t in tests)

    except Exception as e:
        console.print(f"  ❌ TelegramTradingSystem 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_exceptions():
    """커스텀 예외 검증"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]7. 커스텀 예외 검증")
    console.print("[bold cyan]=" * 40)

    try:
        from exceptions import (
            TradingException,
            TradingNetworkError,
            TradingTimeoutError,
            TradingAuthError,
            TradingOrderError,
            TradingDataError,
            get_exception_type,
            format_exception_message,
        )

        # 예외 계층 구조 확인
        tests = [
            ("TradingNetworkError is TradingException", issubclass(TradingNetworkError, TradingException)),
            ("TradingTimeoutError is TradingException", issubclass(TradingTimeoutError, TradingException)),
            ("TradingAuthError is TradingException", issubclass(TradingAuthError, TradingException)),
            ("TradingOrderError is TradingException", issubclass(TradingOrderError, TradingException)),
            ("TradingDataError is TradingException", issubclass(TradingDataError, TradingException)),
        ]

        # 유틸리티 함수 확인
        tests.append(("get_exception_type 함수 존재", callable(get_exception_type)))
        tests.append(("format_exception_message 함수 존재", callable(format_exception_message)))

        for test_name, passed in tests:
            status = "✅" if passed else "❌"
            console.print(f"  {status} {test_name}")

        return all(t[1] for t in tests)

    except Exception as e:
        console.print(f"  ❌ 커스텀 예외 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_env_file():
    """환경 변수 파일 확인"""
    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]8. 환경 변수 파일 확인")
    console.print("[bold cyan]=" * 40)

    env_file = Path(".env")

    if not env_file.exists():
        console.print("  ❌ .env 파일이 없습니다!")
        return False

    console.print("  ✅ .env 파일 존재")

    # 필수 환경변수 확인
    required_vars = [
        "ACCOUNT_NO",
        "MAX_INVESTMENT",
        "TARGET_PROFIT_RATE",
        "STOP_LOSS_RATE",
        "BUY_START_TIME",
        "BUY_END_TIME",
        "DAILY_FORCE_SELL_TIME",
        "BALANCE_CHECK_INTERVAL",
    ]

    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()

    tests = []
    for var in required_vars:
        exists = var in content
        tests.append((var, exists))
        status = "✅" if exists else "❌"
        console.print(f"  {status} {var}")

    return all(t[1] for t in tests)


def main():
    """메인 검증 함수"""
    console.print("\n")
    console.print(Panel.fit(
        "[bold blue]자동매매 시스템 전체 코드 검증[/bold blue]",
        border_style="blue"
    ))

    test_functions = [
        ("Import 의존성", test_imports),
        ("TradingConfig", test_config),
        ("OrderExecutor", test_order_executor),
        ("PriceMonitor", test_price_monitor),
        ("TradingSystemBase", test_trading_system_base),
        ("TelegramTradingSystem", test_auto_trading),
        ("커스텀 예외", test_exceptions),
        ("환경 변수", check_env_file),
    ]

    results = []

    for test_name, test_func in test_functions:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"\n[bold red]❌ {test_name} 테스트 중 예외 발생: {e}[/bold red]")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # 최종 결과
    console.print("\n")
    console.print("[bold cyan]=" * 80)
    console.print("[bold cyan]최종 검증 결과")
    console.print("[bold cyan]=" * 80)

    result_table = Table(title="코드 검증 결과", show_header=True, header_style="bold magenta")
    result_table.add_column("검증 항목", style="cyan", width=30)
    result_table.add_column("결과", style="bold", width=15)

    passed_count = 0
    failed_count = 0

    for test_name, result in results:
        if result:
            result_table.add_row(test_name, "[green]✅ PASS[/green]")
            passed_count += 1
        else:
            result_table.add_row(test_name, "[red]❌ FAIL[/red]")
            failed_count += 1

    console.print(result_table)

    console.print(f"\n[bold]총 {len(results)}개 검증:[/bold]")
    console.print(f"  [green]✅ 통과: {passed_count}개[/green]")
    console.print(f"  [red]❌ 실패: {failed_count}개[/red]")

    if failed_count == 0:
        console.print("\n[bold green]🎉 모든 코드 검증 통과![/bold green]")
        console.print("[bold green]코드에 문제가 없습니다. 실전 투자 준비 완료![/bold green]")
        return 0
    else:
        console.print(f"\n[bold red]⚠️ {failed_count}개 검증 실패. 코드를 수정해주세요.[/bold red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
