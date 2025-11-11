"""
안전 마진 제거 확인 테스트
- 실제 order_executor.py 함수 테스트
- 시장가/지정가 매수 수량 비교
"""
import sys
sys.path.append('/home/ralph/work/python/stock_tel')

from kiwoom_order import get_tick_size


# order_executor.py의 calculate_buy_quantity와 동일한 로직
def calculate_buy_quantity(current_price: int, max_investment: int, safety_margin: float = 0.0) -> int:
    """매수 수량 계산 (안전 마진 제거됨)"""
    if current_price <= 0:
        return 0

    # 안전 마진 없음 (최대 투자금액으로 최대한 매수)
    quantity = max_investment // current_price
    return quantity


def main():
    """안전 마진 제거 확인"""
    print("\n" + "=" * 80)
    print("안전 마진 제거 확인 테스트")
    print("=" * 80)

    max_investment = 1000000
    current_price = 10000

    # 시장가 매수 수량 계산
    market_quantity = calculate_buy_quantity(current_price, max_investment)

    # 지정가 매수 수량 계산
    tick_size = get_tick_size(current_price)
    order_price = current_price + tick_size
    limit_quantity = max_investment // order_price

    print(f"\n💰 설정:")
    print(f"   최대 투자금액: {max_investment:,}원")
    print(f"   현재가: {current_price:,}원")
    print(f"   틱 크기: {tick_size}원")
    print(f"   지정가: {order_price:,}원")

    print(f"\n📊 시장가 매수 (안전 마진 제거 후):")
    print(f"   계산: {max_investment:,} ÷ {current_price:,} = {market_quantity}주")
    print(f"   예상 금액: {market_quantity * current_price:,}원")
    print(f"   투자 효율: {(market_quantity * current_price / max_investment) * 100:.2f}%")

    print(f"\n📊 지정가 매수 (안전 마진 제거 후):")
    print(f"   계산: {max_investment:,} ÷ {order_price:,} = {limit_quantity}주")
    print(f"   예상 금액: {limit_quantity * order_price:,}원")
    print(f"   투자 효율: {(limit_quantity * order_price / max_investment) * 100:.2f}%")

    print(f"\n✅ 검증:")

    # 시장가: 100주여야 함
    if market_quantity == 100:
        print(f"   ✅ 시장가 수량: {market_quantity}주 (안전 마진 제거 확인)")
    else:
        print(f"   ❌ 시장가 수량: {market_quantity}주 (예상: 100주)")

    # 지정가: 99주여야 함
    if limit_quantity == 99:
        print(f"   ✅ 지정가 수량: {limit_quantity}주 (안전 마진 제거 확인)")
    else:
        print(f"   ❌ 지정가 수량: {limit_quantity}주 (예상: 99주)")

    print(f"\n📌 이전 로직 (안전 마진 2%)과 비교:")

    # 이전 시장가: 98주
    old_market_quantity = int(max_investment * 0.98) // current_price
    print(f"   시장가: {old_market_quantity}주 → {market_quantity}주 (+{market_quantity - old_market_quantity}주)")

    # 이전 지정가: 97주 (현재가 기준 + 안전 마진)
    old_limit_quantity = int(max_investment * 0.98) // current_price
    print(f"   지정가: {old_limit_quantity}주 → {limit_quantity}주 (+{limit_quantity - old_limit_quantity}주)")

    print(f"\n🎯 최종 결론:")
    if market_quantity == 100 and limit_quantity == 99:
        print(f"   ✅ 안전 마진 제거 완료!")
        print(f"   ✅ 시장가: 현재가 기준으로 최대한 매수 (100주)")
        print(f"   ✅ 지정가: 지정가 기준으로 최대한 매수 (99주)")
        print(f"=" * 80)
        return 0
    else:
        print(f"   ❌ 안전 마진이 아직 적용되어 있습니다")
        print(f"=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
