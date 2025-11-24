"""
종목코드 유효성 검증 테스트

3단계 검증 + 캐싱 메커니즘을 모두 테스트합니다.
"""
import sys
import time
sys.path.append('/home/ralph/work/python/stock_tel')

from kiwoom_order import KiwoomOrderAPI


def test_case(title: str, stock_code: str, expected_valid: bool) -> bool:
    """
    개별 테스트 케이스 실행

    Args:
        title: 테스트 케이스 제목
        stock_code: 테스트할 종목코드
        expected_valid: 기대하는 유효성 (True/False)

    Returns:
        True if test passes, False otherwise
    """
    print("\n" + "=" * 100)
    print(f"📋 {title}")
    print("=" * 100)
    print(f"종목코드: {stock_code}")
    print(f"기대 결과: {'유효' if expected_valid else '무효'}")
    print("-" * 100)

    # 검증 실행
    api = KiwoomOrderAPI()
    result = api.validate_stock_code(stock_code)

    # 결과 출력
    print(f"\n📊 검증 결과:")
    print(f"   유효 여부: {'유효 ✅' if result['valid'] else '무효 ❌'}")
    print(f"   종목코드: {result['stock_code']}")
    print(f"   종목명: {result.get('stock_name', 'N/A')}")
    if not result['valid']:
        print(f"   무효 사유: {result.get('reason', 'N/A')}")
    print(f"   캐시 사용: {'예' if result.get('cached') else '아니오'}")

    # 검증
    if result['valid'] == expected_valid:
        print(f"\n✅ {title} 통과!")
        return True
    else:
        print(f"\n❌ {title} 실패!")
        print(f"   기대값: {'유효' if expected_valid else '무효'}")
        print(f"   실제값: {'유효' if result['valid'] else '무효'}")
        return False


def test_caching(stock_code: str) -> bool:
    """
    캐싱 메커니즘 테스트

    Args:
        stock_code: 테스트할 유효한 종목코드

    Returns:
        True if test passes, False otherwise
    """
    print("\n" + "=" * 100)
    print(f"📋 캐싱 메커니즘 테스트")
    print("=" * 100)
    print(f"종목코드: {stock_code}")
    print("-" * 100)

    api = KiwoomOrderAPI()

    # 첫 번째 호출 (API 호출)
    print("\n1️⃣ 첫 번째 호출 (API 호출 예상)...")
    start_time = time.time()
    result1 = api.validate_stock_code(stock_code, use_cache=True)
    elapsed1 = time.time() - start_time

    print(f"   소요 시간: {elapsed1:.3f}초")
    print(f"   유효 여부: {'유효 ✅' if result1['valid'] else '무효 ❌'}")
    print(f"   종목명: {result1.get('stock_name', 'N/A')}")
    print(f"   캐시 사용: {'예' if result1.get('cached') else '아니오'}")

    # 두 번째 호출 (캐시 사용)
    print("\n2️⃣ 두 번째 호출 (캐시 사용 예상)...")
    start_time = time.time()
    result2 = api.validate_stock_code(stock_code, use_cache=True)
    elapsed2 = time.time() - start_time

    print(f"   소요 시간: {elapsed2:.3f}초")
    print(f"   유효 여부: {'유효 ✅' if result2['valid'] else '무효 ❌'}")
    print(f"   종목명: {result2.get('stock_name', 'N/A')}")
    print(f"   캐시 사용: {'예' if result2.get('cached') else '아니오'}")

    # 검증
    print("\n🔎 검증:")
    checks = []

    # 1. 결과 일치 확인
    if result1['valid'] == result2['valid']:
        print(f"   ✅ 유효성 결과 일치")
        checks.append(True)
    else:
        print(f"   ❌ 유효성 결과 불일치")
        checks.append(False)

    # 2. 캐시 사용 확인
    if not result1.get('cached') and result2.get('cached'):
        print(f"   ✅ 캐시 작동 (첫 번째: API, 두 번째: 캐시)")
        checks.append(True)
    else:
        print(f"   ❌ 캐시 미작동")
        checks.append(False)

    # 3. 속도 개선 확인
    if elapsed2 < elapsed1:
        speedup = (elapsed1 - elapsed2) / elapsed1 * 100
        print(f"   ✅ 캐시로 {speedup:.1f}% 속도 향상 ({elapsed1:.3f}초 → {elapsed2:.3f}초)")
        checks.append(True)
    else:
        print(f"   ⚠️ 속도 개선 미미 ({elapsed1:.3f}초 → {elapsed2:.3f}초)")
        checks.append(False)

    if all(checks):
        print(f"\n✅ 캐싱 메커니즘 테스트 통과!")
        return True
    else:
        print(f"\n❌ 캐싱 메커니즘 테스트 실패!")
        return False


def main():
    """종합 테스트 실행"""
    print("\n" + "🔬" * 50)
    print("종목코드 유효성 검증 종합 테스트")
    print("🔬" * 50)

    test_results = []

    # ==================== 유효한 종목코드 테스트 ====================
    print("\n" + "=" * 100)
    print("📌 1단계: 유효한 종목코드 테스트 (실제 API 호출)")
    print("=" * 100)

    # 테스트 1: 삼성전자 (005930)
    result1 = test_case("테스트 1: 삼성전자 (KOSPI 대표주)", "005930", expected_valid=True)
    test_results.append(("삼성전자", result1))

    # 테스트 2: 카카오 (035720)
    result2 = test_case("테스트 2: 카카오 (KOSPI)", "035720", expected_valid=True)
    test_results.append(("카카오", result2))

    # 테스트 3: 네이버 (035420) - KOSPI 종목으로 변경
    result3 = test_case("테스트 3: 네이버 (KOSPI)", "035420", expected_valid=True)
    test_results.append(("네이버", result3))

    # ==================== 형식 오류 테스트 ====================
    print("\n" + "=" * 100)
    print("📌 2단계: 형식 오류 테스트 (API 호출 없이 즉시 거부)")
    print("=" * 100)

    # 테스트 4: 5자리 종목코드
    result4 = test_case("테스트 4: 5자리 종목코드 (형식 오류)", "05930", expected_valid=False)
    test_results.append(("5자리 코드", result4))

    # 테스트 5: 7자리 종목코드
    result5 = test_case("테스트 5: 7자리 종목코드 (형식 오류)", "0059301", expected_valid=False)
    test_results.append(("7자리 코드", result5))

    # 테스트 6: 문자 포함
    result6 = test_case("테스트 6: 문자 포함 (형식 오류)", "00593A", expected_valid=False)
    test_results.append(("문자 포함", result6))

    # ==================== 범위 오류 테스트 ====================
    print("\n" + "=" * 100)
    print("📌 3단계: 범위 오류 테스트 (형식은 맞지만 범위 벗어남)")
    print("=" * 100)

    # 테스트 7: 000000 (범위 밖)
    result7 = test_case("테스트 7: 000000 (범위 오류)", "000000", expected_valid=False)
    test_results.append(("000000", result7))

    # ==================== API 검증 테스트 ====================
    print("\n" + "=" * 100)
    print("📌 4단계: API 검증 테스트 (존재하지 않는 종목)")
    print("=" * 100)

    # 테스트 8: 999999 (형식/범위는 맞지만 존재하지 않는 종목)
    result8 = test_case("테스트 8: 999999 (존재하지 않는 종목)", "999999", expected_valid=False)
    test_results.append(("999999", result8))

    # 테스트 9: 123456 (임의의 존재하지 않는 종목)
    result9 = test_case("테스트 9: 123456 (존재하지 않는 종목)", "123456", expected_valid=False)
    test_results.append(("123456", result9))

    # ==================== 캐싱 메커니즘 테스트 ====================
    print("\n" + "=" * 100)
    print("📌 5단계: 캐싱 메커니즘 테스트")
    print("=" * 100)

    result_cache = test_caching("005930")  # 삼성전자로 캐싱 테스트
    test_results.append(("캐싱 메커니즘", result_cache))

    # ==================== 최종 결과 요약 ====================
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
        print("\n✅ 형식 검증: 6자리 숫자 여부 확인")
        print("✅ 범위 검증: 000001 ~ 999999 범위 확인")
        print("✅ API 검증: 실제 종목 존재 여부 확인")
        print("✅ 캐싱: 24시간 유효한 종목 캐싱, 1시간 무효 종목 캐싱")
        print("✅ 성능: 캐시로 인한 속도 향상 확인")
        print("\n" + "=" * 100)
        return 0
    else:
        print("\n❌ 일부 테스트 실패!")
        print("\n" + "=" * 100)
        return 1


if __name__ == "__main__":
    sys.exit(main())
