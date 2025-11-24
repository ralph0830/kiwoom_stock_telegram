"""
새로운 파싱 로직 (B안 - 유연성 우선) 테스트

괄호 안 6자리 숫자 기반 시그널 인식 테스트
"""
import sys
sys.path.append('/home/ralph/work/python/stock_tel')

from config import TradingConfig
from auto_trading import TelegramTradingSystem


def test_case(title: str, message: str, expected: dict) -> bool:
    """
    개별 테스트 케이스 실행

    Args:
        title: 테스트 케이스 제목
        message: 테스트할 메시지
        expected: 기대값 딕셔너리

    Returns:
        True if all checks pass, False otherwise
    """
    print("\n" + "=" * 100)
    print(f"📋 {title}")
    print("=" * 100)
    print("\n📨 테스트 메시지:")
    lines = message.split('\n')
    for line in lines[:7]:  # 처음 7줄만 출력
        print(f"   {line}")
    if len(lines) > 7:
        print(f"   ... (총 {len(lines)}줄)")
    print("\n" + "-" * 100)

    # 설정 생성 (더미 - 최소한의 필수 파라미터만)
    config = TradingConfig(
        account_no="12345678-01",
        max_investment=1000000,
        target_profit_rate=0.01,
        stop_loss_rate=-0.025,
        stop_loss_delay_minutes=1,
        buy_start_time="09:00",
        buy_end_time="15:30",
        enable_sell_monitoring=True,
        enable_stop_loss=True,
        enable_daily_force_sell=True,
        daily_force_sell_time="15:19",
        cancel_outstanding_on_failure=True,
        outstanding_check_timeout=30,
        outstanding_check_interval=5,
        enable_lazy_verification=False,
        balance_check_interval=0,
        buy_order_type="market",
        buy_execution_timeout=30,
        buy_execution_check_interval=5,
        buy_fallback_to_market=True,
        debug_mode=False,
        ws_ping_interval=None,
        ws_ping_timeout=None,
        ws_recv_timeout=60,
        api_id=12345,
        api_hash="test",
        session_name="test",
        source_channel="test",
        target_channel="test"
    )

    # 시스템 생성
    system = TelegramTradingSystem(config)

    # 파싱 실행
    result = system.parse_stock_signal(message)

    if not result:
        print("❌ 파싱 실패!")
        if expected:
            print(f"   기대값: {expected}")
            return False
        else:
            print("   기대값도 None이므로 통과")
            return True

    # 결과 출력
    print(f"\n📊 파싱 결과:")
    print(f"   종목명: {result['stock_name']}")
    print(f"   종목코드: {result['stock_code']}")
    print(f"   적정매수가: {result['target_price']}")
    print(f"   현재가: {result['current_price']}")

    # 검증
    print(f"\n🔎 검증:")
    checks = []

    for key, expected_value in expected.items():
        actual_value = result.get(key)
        if actual_value == expected_value:
            print(f"   ✅ {key}: {actual_value} (일치)")
            checks.append(True)
        else:
            print(f"   ❌ {key}: 예상 {expected_value}, 실제 {actual_value}")
            checks.append(False)

    if all(checks):
        print(f"\n✅ {title} 통과!")
        return True
    else:
        print(f"\n❌ {title} 실패!")
        return False


def main():
    """종합 테스트 실행"""
    print("\n" + "🔬" * 50)
    print("새로운 파싱 로직 (B안) 종합 테스트")
    print("🔬" * 50)

    test_results = []

    # 테스트 1: 기존 "Ai 종목포착 시그널" 메시지
    message1 = """⭐️ Ai 종목포착 시그널
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
포착 종목명 : 유일에너테크 (340930)
적정 매수가 : 2,870원 👉 6.49%
포착 현재가 : 2,860원 👉 6.12%"""

    expected1 = {
        "stock_name": "유일에너테크",
        "stock_code": "340930",
        "target_price": 2870,
        "current_price": 2860
    }

    result1 = test_case("테스트 1: Ai 종목포착 시그널 (기존 형식)", message1, expected1)
    test_results.append(("Ai 종목포착 시그널", result1))

    # 테스트 2: #매수신호 메시지
    message2 = """✅ #매수신호
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
종목명 👉 벨로크 (424760)
매수가 👉 1,426원
등락률 👉 6.58%
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
매도가 👉 1,458원"""

    expected2 = {
        "stock_name": "벨로크",
        "stock_code": "424760",
        "target_price": 1458,
        "current_price": 1426
    }

    result2 = test_case("테스트 2: #매수신호 (기존 형식)", message2, expected2)
    test_results.append(("#매수신호", result2))

    # 테스트 3: 종목명 비어있는 경우
    message3 = """■ Ai 종목포착 시그널
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
포착 종목명 :  (051980)
적정 매수가 : 원 👉 %
포착 현재가 : 3,395원 👉 6.26%"""

    expected3 = {
        "stock_name": "051980",  # 종목코드로 대체
        "stock_code": "051980",
        "target_price": None,
        "current_price": 3395
    }

    result3 = test_case("테스트 3: 종목명 비어있음 (엣지 케이스)", message3, expected3)
    test_results.append(("종목명 비어있음", result3))

    # 테스트 4: #알림 메시지 (새로 감지되는 케이스)
    message4 = """✅ #알림
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
종목명 : 아미노로직스 (074430)
───────────────

✅ 매도 (06%)"""

    expected4 = {
        "stock_name": "아미노로직스",
        "stock_code": "074430",
        "target_price": None,
        "current_price": None
    }

    result4 = test_case("테스트 4: #알림 (새로 지원되는 형식)", message4, expected4)
    test_results.append(("#알림 메시지", result4))

    # 테스트 5: 완전히 다른 형식 (유연성 테스트)
    message5 = """🚀 급등주 추천

종목: 테스트종목 (123456)
현재가: 10,000원
목표가: 11,000원"""

    expected5 = {
        "stock_name": "테스트종목",
        "stock_code": "123456",
        "target_price": 11000,
        "current_price": 10000
    }

    result5 = test_case("테스트 5: 완전히 다른 형식 (유연성 테스트)", message5, expected5)
    test_results.append(("새로운 형식", result5))

    # 테스트 6: 괄호 없는 메시지 (감지되지 말아야 함)
    message6 = """오늘의 추천 종목
051980 급등 예상
매수가: 3,400원"""

    expected6 = None  # 감지되지 말아야 함

    result6 = test_case("테스트 6: 괄호 없음 (미감지 예상)", message6, expected6)
    test_results.append(("괄호 없음", result6))

    # 테스트 7: 실제 채널 메시지 1 (코닉오토메이션)
    message7 = """✅ #매수신호
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
종목명 👉 코닉오토메이션 (391710)
매수가 👉 2,370원
등락률 👉 4.89%
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
매도가 👉 2,420원"""

    expected7 = {
        "stock_name": "코닉오토메이션",
        "stock_code": "391710",
        "target_price": 2420,
        "current_price": 2370
    }

    result7 = test_case("테스트 7: 실제 채널 메시지 (코닉오토메이션)", message7, expected7)
    test_results.append(("실제 메시지 1", result7))

    # 최종 결과 요약
    print("\n" + "=" * 100)
    print("📊 최종 테스트 결과 요약")
    print("=" * 100)

    for test_name, passed in test_results:
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"   {status}: {test_name}")

    total_passed = sum(1 for _, passed in test_results if passed)
    total_tests = len(test_results)

    print("\n" + "-" * 100)
    print(f"   총 {total_tests}개 테스트 중 {total_passed}개 통과")
    print("-" * 100)

    if total_passed == total_tests:
        print("\n🎉 모든 테스트 통과!")
        print("\n✅ 기존 형식 완벽 지원")
        print("✅ 새로운 형식 (#알림 등) 지원")
        print("✅ 종목명 비어있는 케이스 처리")
        print("✅ 괄호 없는 메시지는 올바르게 무시")
        print("✅ 완전히 다른 형식도 유연하게 처리")
        print("\n" + "=" * 100)
        return 0
    else:
        print("\n❌ 일부 테스트 실패!")
        print("\n" + "=" * 100)
        return 1


if __name__ == "__main__":
    sys.exit(main())
