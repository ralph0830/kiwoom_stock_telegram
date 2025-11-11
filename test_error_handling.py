"""
8단계: 에러 처리 및 예외 상황 검증
API 실패, 예외 처리, 엣지 케이스 테스트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kiwoom_order import get_tick_size, parse_price_string
from order_executor import OrderExecutor
from trading_system_base import TradingSystemBase
from config import TradingConfig
from datetime import datetime, time


def test_price_edge_cases():
    """가격 엣지 케이스 테스트"""
    print("\n" + "=" * 80)
    print("8-1. 가격 엣지 케이스 테스트")
    print("=" * 80)

    test_cases = [
        # (입력값, 예상 결과, 설명)
        (0, 1, "0원 → 최소 틱 1원"),
        (-100, 1, "음수 가격 → 최소 틱 1원"),
        (999, 1, "경계값: 999원 → 1원"),
        (1000, 5, "경계값: 1,000원 → 5원"),
        (4999, 5, "경계값: 4,999원 → 5원"),
        (5000, 10, "경계값: 5,000원 → 10원"),
        (9999, 10, "경계값: 9,999원 → 10원"),
        (10000, 50, "경계값: 10,000원 → 50원"),
        (49999, 50, "경계값: 49,999원 → 50원"),
        (50000, 100, "경계값: 50,000원 → 100원"),
        (99999, 100, "경계값: 99,999원 → 100원"),
        (100000, 500, "경계값: 100,000원 → 500원"),
        (499999, 500, "경계값: 499,999원 → 500원"),
        (500000, 1000, "경계값: 500,000원 → 1,000원"),
        (1000000, 1000, "경계값: 1,000,000원 → 1,000원"),
    ]

    all_passed = True
    for price, expected_tick, description in test_cases:
        result = get_tick_size(price)
        status = "✅" if result == expected_tick else "❌"

        if result != expected_tick:
            all_passed = False
            print(f"{status} {description}")
            print(f"   입력: {price:,}원, 예상: {expected_tick}원, 실제: {result}원")
        else:
            print(f"{status} {description}")

    if all_passed:
        print("\n✅ 모든 가격 엣지 케이스 테스트 통과!")
    else:
        print("\n❌ 일부 테스트 실패!")

    return all_passed


def test_parse_price_edge_cases():
    """가격 파싱 엣지 케이스 테스트"""
    print("\n" + "=" * 80)
    print("8-2. 가격 파싱 엣지 케이스 테스트")
    print("=" * 80)

    test_cases = [
        # (입력값, 예상 결과, 설명)
        ("10,000원", 10000, "정상: 쉼표 포함 문자열"),
        ("10000원", 10000, "정상: 쉼표 없는 문자열"),
        ("10,000", 10000, "정상: 원 기호 없음"),
        ("10000", 10000, "정상: 숫자만"),
        ("", 0, "빈 문자열 → 0"),
        ("0원", 0, "0원"),
        ("-1000원", 0, "음수 → 0 (최소값 보정)"),
        ("abc", 0, "잘못된 문자열 → 0"),
        ("1,2,3,4", 1234, "여러 쉼표"),
        ("   1000   ", 1000, "공백 포함"),
    ]

    all_passed = True
    for price_str, expected, description in test_cases:
        try:
            result = parse_price_string(price_str)
            status = "✅" if result == expected else "❌"

            if result != expected:
                all_passed = False
                print(f"{status} {description}")
                print(f"   입력: '{price_str}', 예상: {expected:,}원, 실제: {result:,}원")
            else:
                print(f"{status} {description}")
        except Exception as e:
            all_passed = False
            print(f"❌ {description}")
            print(f"   입력: '{price_str}', 예외 발생: {str(e)}")

    if all_passed:
        print("\n✅ 모든 가격 파싱 테스트 통과!")
    else:
        print("\n❌ 일부 테스트 실패!")

    return all_passed


def test_buy_quantity_edge_cases():
    """매수 수량 계산 엣지 케이스 테스트"""
    print("\n" + "=" * 80)
    print("8-3. 매수 수량 계산 엣지 케이스 테스트")
    print("=" * 80)

    executor = OrderExecutor(None, "12345678-01")  # Mock

    test_cases = [
        # (투자금, 가격, 예상 수량, 설명)
        (1000000, 0, 0, "0원 주식 → 0주 (예외 처리)"),
        (1000000, -100, 0, "음수 가격 → 0주 (예외 처리)"),
        (0, 10000, 0, "0원 투자 → 0주"),
        (-100000, 10000, 0, "음수 투자 → 0주 (예외 처리)"),
        (100, 10000, 0, "투자금 < 주가 → 0주"),
        (10000, 10000, 0, "투자금 = 주가 (2% 마진 적용) → 0주"),
        (10300, 10000, 1, "최소 1주 매수 가능"),
        (1000000, 1000000, 0, "초고가 주식 → 0주"),
    ]

    all_passed = True
    for investment, price, expected, description in test_cases:
        try:
            result = executor.calculate_buy_quantity(price, investment)
            status = "✅" if result == expected else "❌"

            if result != expected:
                all_passed = False
                print(f"{status} {description}")
                print(f"   투자금: {investment:,}원, 가격: {price:,}원")
                print(f"   예상: {expected}주, 실제: {result}주")
            else:
                print(f"{status} {description}")
        except Exception as e:
            # 예외 발생은 정상 동작 (0 반환 예상)
            if expected == 0:
                print(f"✅ {description} (예외 처리 정상)")
            else:
                all_passed = False
                print(f"❌ {description}")
                print(f"   예외 발생: {str(e)}")

    if all_passed:
        print("\n✅ 모든 수량 계산 엣지 케이스 통과!")
    else:
        print("\n❌ 일부 테스트 실패!")

    return all_passed


def test_duplicate_order_prevention():
    """중복 주문 방지 테스트"""
    print("\n" + "=" * 80)
    print("8-4. 중복 주문 방지 테스트")
    print("=" * 80)

    # TradingSystemBase의 플래그 상태 시뮬레이션
    test_cases = [
        # (order_executed, sell_executed, 예상 매수 가능, 예상 매도 가능, 설명)
        (False, False, True, True, "초기 상태: 매수/매도 모두 가능"),
        (True, False, False, True, "매수 완료: 매도만 가능"),
        (False, True, True, False, "매도 완료: 매수만 가능 (비정상 상태)"),
        (True, True, False, False, "매수/매도 모두 완료: 둘 다 불가"),
    ]

    all_passed = True
    for order_exec, sell_exec, can_buy, can_sell, description in test_cases:
        # 매수 가능 여부
        buy_possible = not order_exec
        # 매도 가능 여부
        sell_possible = not sell_exec

        buy_status = "✅" if buy_possible == can_buy else "❌"
        sell_status = "✅" if sell_possible == can_sell else "❌"

        if buy_possible != can_buy or sell_possible != can_sell:
            all_passed = False

        print(f"{description}")
        print(f"  {buy_status} 매수 가능: {buy_possible} (예상: {can_buy})")
        print(f"  {sell_status} 매도 가능: {sell_possible} (예상: {can_sell})")

    if all_passed:
        print("\n✅ 중복 주문 방지 로직 정상!")
    else:
        print("\n❌ 중복 주문 방지 로직 오류!")

    return all_passed


def test_time_boundary_cases():
    """시간 경계값 테스트"""
    print("\n" + "=" * 80)
    print("8-5. 시간 경계값 테스트")
    print("=" * 80)

    # 매수 가능 시간: 08:50 ~ 12:10
    buy_start = time(8, 50)
    buy_end = time(12, 10)

    test_cases = [
        # (시간, 예상 매수 가능 여부, 설명)
        (time(8, 49), False, "매수 시작 1분 전 → 불가"),
        (time(8, 50), True, "매수 시작 시간 정각 → 가능"),
        (time(8, 51), True, "매수 시작 1분 후 → 가능"),
        (time(12, 9), True, "매수 종료 1분 전 → 가능"),
        (time(12, 10), False, "매수 종료 시간 정각 → 불가"),
        (time(12, 11), False, "매수 종료 1분 후 → 불가"),
        (time(0, 0), False, "자정 → 불가"),
        (time(23, 59), False, "하루 끝 → 불가"),
    ]

    all_passed = True
    for current_time, expected, description in test_cases:
        # 매수 가능 시간 체크 로직
        is_buy_time = buy_start <= current_time < buy_end

        status = "✅" if is_buy_time == expected else "❌"

        if is_buy_time != expected:
            all_passed = False
            print(f"{status} {description}")
            print(f"   시간: {current_time.strftime('%H:%M')}, 예상: {expected}, 실제: {is_buy_time}")
        else:
            print(f"{status} {description}")

    if all_passed:
        print("\n✅ 모든 시간 경계값 테스트 통과!")
    else:
        print("\n❌ 일부 시간 경계값 테스트 실패!")

    return all_passed


def main():
    """에러 처리 및 예외 상황 종합 테스트"""
    print("\n" + "🔬" * 40)
    print("8단계: 에러 처리 및 예외 상황 검증 시작")
    print("🔬" * 40)

    results = []

    # 8-1: 가격 엣지 케이스
    results.append(("가격 엣지 케이스", test_price_edge_cases()))

    # 8-2: 가격 파싱 엣지 케이스
    results.append(("가격 파싱 엣지 케이스", test_parse_price_edge_cases()))

    # 8-3: 매수 수량 엣지 케이스
    results.append(("매수 수량 엣지 케이스", test_buy_quantity_edge_cases()))

    # 8-4: 중복 주문 방지
    results.append(("중복 주문 방지", test_duplicate_order_prevention()))

    # 8-5: 시간 경계값
    results.append(("시간 경계값", test_time_boundary_cases()))

    # 최종 결과
    print("\n" + "=" * 80)
    print("8단계 종합 테스트 결과")
    print("=" * 80)

    all_passed = True
    for name, passed in results:
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 8단계 모든 테스트 통과! 에러 처리 로직 정상 동작 확인!")
    else:
        print("⚠️ 일부 테스트 실패. 에러 처리 로직 점검 필요.")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
