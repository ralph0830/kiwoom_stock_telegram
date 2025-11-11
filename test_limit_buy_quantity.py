"""
지정가 매수 시 매수 수량 계산 로직 검증
- 현재가 기준 수량으로 지정가 주문 시 금액 초과 여부 확인
"""
import sys
sys.path.append('/home/ralph/work/python/stock_tel')

from kiwoom_order import get_tick_size


def calculate_buy_quantity(current_price: int, max_investment: int, safety_margin: float = 0.02) -> int:
    """
    매수 수량 계산 (order_executor.py와 동일한 로직)

    Args:
        current_price: 현재가
        max_investment: 최대 투자금액
        safety_margin: 안전 마진 (기본 2%)

    Returns:
        int: 매수 수량
    """
    if current_price <= 0:
        return 0

    # 안전 마진 적용 (시장가 체결 시 가격 상승 대비)
    adjusted_investment = int(max_investment * (1 - safety_margin))
    quantity = adjusted_investment // current_price

    return quantity


def test_limit_buy_quantity():
    """지정가 매수 시 수량 계산 테스트"""
    print("\n" + "=" * 80)
    print("지정가 매수 시 매수 수량 계산 로직 검증")
    print("=" * 80)

    # 테스트 케이스
    test_cases = [
        # (최대 투자금액, 현재가, 설명)
        (1000000, 10000, "일반 케이스: 1백만원, 1만원 주식"),
        (1000000, 5000, "저가 주식: 1백만원, 5천원 주식"),
        (1000000, 50000, "고가 주식: 1백만원, 5만원 주식"),
        (1000000, 100000, "초고가 주식: 1백만원, 10만원 주식"),
        (500000, 10000, "소액 투자: 50만원, 1만원 주식"),
        (2000000, 10000, "대액 투자: 2백만원, 1만원 주식"),
    ]

    issues_found = []

    for max_investment, current_price, description in test_cases:
        print(f"\n" + "-" * 80)
        print(f"📊 {description}")
        print("-" * 80)

        # 안전 마진 2% 적용
        safety_margin = 0.02
        adjusted_investment = int(max_investment * (1 - safety_margin))

        # 현재가 기준 수량 계산 (현재 로직)
        quantity = calculate_buy_quantity(current_price, max_investment, safety_margin)

        # 지정가 계산 (현재가 + 1틱)
        tick_size = get_tick_size(current_price)
        order_price = current_price + tick_size

        # 현재가 기준 필요 금액
        required_amount_current = current_price * quantity

        # 지정가 기준 필요 금액
        required_amount_limit = order_price * quantity

        print(f"\n💰 투자 설정:")
        print(f"   최대 투자금액: {max_investment:,}원")
        print(f"   안전 마진: {safety_margin * 100}%")
        print(f"   조정 투자금액: {adjusted_investment:,}원")

        print(f"\n📈 가격 정보:")
        print(f"   현재가: {current_price:,}원")
        print(f"   틱 크기: {tick_size}원")
        print(f"   지정가: {order_price:,}원 (현재가 + {tick_size}원)")

        print(f"\n🔢 수량 계산 (현재 로직 - 현재가 기준):")
        print(f"   계산된 수량: {quantity}주")
        print(f"   현재가 기준 필요 금액: {required_amount_current:,}원")
        print(f"   지정가 기준 필요 금액: {required_amount_limit:,}원")

        # 검증
        current_price_ok = required_amount_current <= adjusted_investment
        limit_price_ok = required_amount_limit <= max_investment

        print(f"\n✅ 검증 결과:")

        # 현재가 기준 체크
        if current_price_ok:
            print(f"   ✅ 현재가 기준: {required_amount_current:,}원 <= {adjusted_investment:,}원 (OK)")
        else:
            print(f"   ❌ 현재가 기준: {required_amount_current:,}원 > {adjusted_investment:,}원 (초과!)")

        # 지정가 기준 체크 (실제 주문 금액)
        if limit_price_ok:
            print(f"   ✅ 지정가 기준: {required_amount_limit:,}원 <= {max_investment:,}원 (OK)")
        else:
            print(f"   ❌ 지정가 기준: {required_amount_limit:,}원 > {max_investment:,}원 (초과!)")
            issues_found.append({
                "description": description,
                "max_investment": max_investment,
                "current_price": current_price,
                "order_price": order_price,
                "quantity": quantity,
                "required_amount": required_amount_limit,
                "excess": required_amount_limit - max_investment
            })

        # 틱 크기 비율
        tick_ratio = (tick_size / current_price) * 100
        print(f"\n📊 틱 크기 비율: {tick_ratio:.2f}% (현재가 대비)")

        # 초과 금액 계산
        if not limit_price_ok:
            excess = required_amount_limit - max_investment
            excess_ratio = (excess / max_investment) * 100
            print(f"   ⚠️ 초과 금액: {excess:,}원 ({excess_ratio:.2f}%)")
            print(f"   ⚠️ 최대 가능 수량: {max_investment // order_price}주")

    # 최종 요약
    print("\n" + "=" * 80)
    print("📊 최종 검증 결과")
    print("=" * 80)

    if issues_found:
        print(f"\n❌ 문제 발견: {len(issues_found)}개 케이스에서 금액 초과")
        print("\n⚠️ 현재 로직의 문제점:")
        print("   - 현재가 기준으로 수량 계산")
        print("   - 지정가(현재가 + 1틱)로 주문")
        print("   - 지정가 기준 필요 금액이 최대 투자금액을 초과할 수 있음")

        print("\n🔧 해결 방법:")
        print("   1. 지정가 매수 시에는 지정가 기준으로 수량을 재계산")
        print("   2. 주문 전에 필요 금액을 검증하고 초과 시 수량 조정")
        print("   3. 주문 실패 시 수량을 줄여서 재주문하는 로직 추가")

        print("\n📋 문제 발생 케이스:")
        for i, issue in enumerate(issues_found, 1):
            print(f"\n   케이스 {i}: {issue['description']}")
            print(f"      현재가: {issue['current_price']:,}원")
            print(f"      지정가: {issue['order_price']:,}원")
            print(f"      수량: {issue['quantity']}주")
            print(f"      필요 금액: {issue['required_amount']:,}원")
            print(f"      최대 금액: {issue['max_investment']:,}원")
            print(f"      초과 금액: {issue['excess']:,}원")
            print(f"      → 수정 수량: {issue['max_investment'] // issue['order_price']}주")

        return False
    else:
        print("\n✅ 모든 테스트 케이스 통과!")
        print("   - 지정가 기준 필요 금액이 최대 투자금액을 초과하지 않음")
        print("   - 현재 로직으로 안전하게 주문 가능")
        return True


def test_extreme_cases():
    """극단적인 케이스 테스트"""
    print("\n" + "=" * 80)
    print("🔥 극단적인 케이스 테스트")
    print("=" * 80)

    # 틱 크기가 큰 케이스 (고가 주식)
    extreme_cases = [
        (1000000, 499999, "경계값: 500원 틱 직전"),
        (1000000, 500000, "경계값: 1000원 틱 시작"),
        (1000000, 1000000, "극단: 초고가 주식"),
    ]

    for max_investment, current_price, description in extreme_cases:
        print(f"\n" + "-" * 80)
        print(f"📊 {description}")
        print("-" * 80)

        safety_margin = 0.02
        adjusted_investment = int(max_investment * (1 - safety_margin))

        quantity = calculate_buy_quantity(current_price, max_investment, safety_margin)
        tick_size = get_tick_size(current_price)
        order_price = current_price + tick_size

        required_amount_limit = order_price * quantity

        print(f"   현재가: {current_price:,}원")
        print(f"   틱 크기: {tick_size}원")
        print(f"   지정가: {order_price:,}원")
        print(f"   수량: {quantity}주")
        print(f"   필요 금액: {required_amount_limit:,}원")
        print(f"   최대 금액: {max_investment:,}원")

        if required_amount_limit > max_investment:
            excess = required_amount_limit - max_investment
            print(f"   ❌ 초과: {excess:,}원")
        else:
            print(f"   ✅ 안전")


if __name__ == "__main__":
    # 일반 케이스 테스트
    result = test_limit_buy_quantity()

    # 극단적인 케이스 테스트
    test_extreme_cases()

    # 종료 코드
    sys.exit(0 if result else 1)
