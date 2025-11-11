"""
안전 마진 필요 여부 분석
- 시장가 매수 vs 지정가 매수에서 안전 마진의 역할 검증
"""
import sys
sys.path.append('/home/ralph/work/python/stock_tel')

from kiwoom_order import get_tick_size


def test_market_buy():
    """시장가 매수에서 안전 마진의 필요성"""
    print("\n" + "=" * 80)
    print("📊 시장가 매수 - 안전 마진 필요성 분석")
    print("=" * 80)

    max_investment = 1000000
    current_price = 10000
    safety_margin = 0.02

    print(f"\n💰 설정:")
    print(f"   최대 투자금액: {max_investment:,}원")
    print(f"   현재가: {current_price:,}원")
    print(f"   안전 마진: {safety_margin * 100}%")

    # 안전 마진 적용 O
    adjusted_investment = int(max_investment * (1 - safety_margin))
    quantity_with_margin = adjusted_investment // current_price

    print(f"\n✅ 안전 마진 적용 O:")
    print(f"   조정 투자금액: {adjusted_investment:,}원")
    print(f"   수량: {quantity_with_margin}주")
    print(f"   예상 필요 금액: {quantity_with_margin * current_price:,}원")

    # 안전 마진 적용 X
    quantity_without_margin = max_investment // current_price

    print(f"\n❌ 안전 마진 적용 X:")
    print(f"   수량: {quantity_without_margin}주")
    print(f"   예상 필요 금액: {quantity_without_margin * current_price:,}원")

    # 시장가 슬리피지 시뮬레이션
    print(f"\n🔥 시장가 슬리피지 시나리오:")

    slippage_cases = [
        (0.005, "0.5% 상승"),
        (0.01, "1% 상승"),
        (0.02, "2% 상승"),
        (0.03, "3% 상승"),
    ]

    for slippage_rate, description in slippage_cases:
        actual_price = int(current_price * (1 + slippage_rate))

        # 안전 마진 O인 경우
        required_with_margin = quantity_with_margin * actual_price
        ok_with_margin = required_with_margin <= max_investment

        # 안전 마진 X인 경우
        required_without_margin = quantity_without_margin * actual_price
        ok_without_margin = required_without_margin <= max_investment

        print(f"\n   {description}: 체결가 {actual_price:,}원")
        print(f"      안전 마진 O: {required_with_margin:,}원 " +
              (f"✅ (OK)" if ok_with_margin else f"❌ (초과 {required_with_margin - max_investment:,}원)"))
        print(f"      안전 마진 X: {required_without_margin:,}원 " +
              (f"✅ (OK)" if ok_without_margin else f"❌ (초과 {required_without_margin - max_investment:,}원)"))

    print(f"\n📌 결론:")
    print(f"   - 시장가 매수는 체결가를 예측할 수 없음")
    print(f"   - 슬리피지로 인해 최대 투자금액 초과 가능")
    print(f"   - 안전 마진 필요함! ✅")


def test_limit_buy():
    """지정가 매수에서 안전 마진의 필요성"""
    print("\n" + "=" * 80)
    print("📊 지정가 매수 - 안전 마진 필요성 분석")
    print("=" * 80)

    max_investment = 1000000
    current_price = 10000
    safety_margin = 0.02
    tick_size = get_tick_size(current_price)
    order_price = current_price + tick_size

    print(f"\n💰 설정:")
    print(f"   최대 투자금액: {max_investment:,}원")
    print(f"   현재가: {current_price:,}원")
    print(f"   틱 크기: {tick_size}원")
    print(f"   지정가: {order_price:,}원")

    # 현재 로직: 현재가 기준 + 안전 마진
    adjusted_investment = int(max_investment * (1 - safety_margin))
    quantity_current_logic = adjusted_investment // current_price
    required_current_logic = quantity_current_logic * order_price

    print(f"\n❌ 현재 로직 (현재가 기준 + 안전 마진):")
    print(f"   조정 투자금액: {adjusted_investment:,}원")
    print(f"   수량 계산: {adjusted_investment:,} ÷ {current_price:,} = {quantity_current_logic}주")
    print(f"   실제 필요 금액: {quantity_current_logic}주 × {order_price:,}원 = {required_current_logic:,}원")
    print(f"   남는 금액: {max_investment - required_current_logic:,}원")
    print(f"   투자 효율: {(required_current_logic / max_investment) * 100:.2f}%")

    # 개선 로직 1: 지정가 기준 (안전 마진 없음)
    quantity_improved = max_investment // order_price
    required_improved = quantity_improved * order_price

    print(f"\n✅ 개선 로직 (지정가 기준, 안전 마진 없음):")
    print(f"   수량 계산: {max_investment:,} ÷ {order_price:,} = {quantity_improved}주")
    print(f"   실제 필요 금액: {quantity_improved}주 × {order_price:,}원 = {required_improved:,}원")
    print(f"   남는 금액: {max_investment - required_improved:,}원")
    print(f"   투자 효율: {(required_improved / max_investment) * 100:.2f}%")

    # 비교
    print(f"\n📊 비교:")
    print(f"   수량 차이: {quantity_improved - quantity_current_logic}주 더 매수 가능")
    print(f"   투자 금액 차이: {required_improved - required_current_logic:,}원 더 투자 가능")
    print(f"   투자 효율 개선: {((required_improved / max_investment) - (required_current_logic / max_investment)) * 100:.2f}%p")

    # 지정가의 안정성 검증
    print(f"\n🔒 지정가의 안정성:")
    print(f"   - 지정가: {order_price:,}원 (고정)")
    print(f"   - 이 가격 이상으로는 절대 체결되지 않음 (보장)")
    print(f"   - 최악의 경우: {quantity_improved}주 × {order_price:,}원 = {required_improved:,}원")
    print(f"   - 최대 투자금액: {max_investment:,}원")
    print(f"   - 초과 여부: {'❌ 초과' if required_improved > max_investment else '✅ 안전'}")

    print(f"\n📌 결론:")
    print(f"   - 지정가 매수는 체결가가 지정가 이하로 고정됨")
    print(f"   - 최대 투자금액 초과 불가능")
    print(f"   - 안전 마진 불필요! ❌")
    print(f"   - 지정가 기준으로 수량 계산하면 더 많이 매수 가능")


def test_extreme_cases():
    """극단적인 케이스에서 안전 마진 검증"""
    print("\n" + "=" * 80)
    print("🔥 극단적인 케이스 - 안전 마진 영향")
    print("=" * 80)

    test_cases = [
        (1000000, 10000, "일반: 1백만원, 1만원 주식"),
        (1000000, 100000, "고가: 1백만원, 10만원 주식"),
        (1000000, 500000, "초고가: 1백만원, 50만원 주식"),
        (500000, 10000, "소액: 50만원, 1만원 주식"),
    ]

    for max_investment, current_price, description in test_cases:
        tick_size = get_tick_size(current_price)
        order_price = current_price + tick_size
        safety_margin = 0.02

        # 현재 로직
        adjusted_investment = int(max_investment * (1 - safety_margin))
        quantity_current = adjusted_investment // current_price

        # 개선 로직
        quantity_improved = max_investment // order_price

        print(f"\n{description}:")
        print(f"   현재가: {current_price:,}원, 지정가: {order_price:,}원")
        print(f"   현재 로직: {quantity_current}주 (효율: {(quantity_current * order_price / max_investment) * 100:.1f}%)")
        print(f"   개선 로직: {quantity_improved}주 (효율: {(quantity_improved * order_price / max_investment) * 100:.1f}%)")

        diff = quantity_improved - quantity_current
        if diff > 0:
            print(f"   ➡️ {diff}주 더 매수 가능 (+{(diff / quantity_current) * 100:.1f}%)")


def main():
    """안전 마진 필요 여부 종합 분석"""
    print("\n" + "🔬" * 40)
    print("안전 마진 필요 여부 종합 분석")
    print("🔬" * 40)

    # 시장가 매수 분석
    test_market_buy()

    # 지정가 매수 분석
    test_limit_buy()

    # 극단적인 케이스
    test_extreme_cases()

    # 최종 결론
    print("\n" + "=" * 80)
    print("🎯 최종 결론")
    print("=" * 80)
    print("\n✅ 시장가 매수:")
    print("   - 안전 마진 2% 필요 (체결가 예측 불가)")
    print("   - 슬리피지로 인한 금액 초과 방지")
    print("\n❌ 지정가 매수:")
    print("   - 안전 마진 불필요 (지정가 이하로만 체결 보장)")
    print("   - 지정가 기준으로 수량 계산 권장")
    print("   - 투자 효율 향상 (더 많은 수량 매수 가능)")

    print("\n🔧 권장 수정 사항:")
    print("   1. 시장가 매수: 현재가 기준 + 안전 마진 2% (유지)")
    print("   2. 지정가 매수: 지정가 기준 + 안전 마진 0% (수정 필요)")
    print("=" * 80)


if __name__ == "__main__":
    main()
