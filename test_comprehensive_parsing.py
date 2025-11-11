"""
종목명 파싱 종합 테스트
- 정상적인 메시지 (종목명 있음)
- 오류 메시지 (종목명 비어있음)
"""
import re
import sys
sys.path.append('/home/ralph/work/python/stock_tel')


def parse_stock_signal(message_text: str) -> dict:
    """
    테스트용 파싱 함수 (auto_trading.py와 동일한 로직)
    """
    try:
        # 매수 신호인지 확인
        if "Ai 종목포착 시그널" not in message_text and "종목포착" not in message_text:
            return None

        # 종목명과 종목코드 추출
        # 종목명이 비어있어도 종목코드만 있으면 매수 가능하도록 *? 사용 (0개 이상)
        stock_pattern = r'(?:포착\s*)?종목명\s*[:：]\s*([가-힣a-zA-Z0-9＆&\s]*?)\s*\((\d{6})\)'
        stock_match = re.search(stock_pattern, message_text)

        if not stock_match:
            print("⚠️ 종목명/종목코드를 찾을 수 없습니다")
            return None

        stock_name = stock_match.group(1).strip()
        stock_code = stock_match.group(2).strip()

        # 종목명이 비어있으면 종목코드를 종목명으로 사용
        if not stock_name:
            stock_name = stock_code
            print(f"⚠️ 종목명이 비어있어 종목코드({stock_code})를 종목명으로 사용합니다")

        # 적정 매수가 추출 (선택)
        target_price = None
        target_pattern = r'적정\s*매수가?\s*[:：]\s*([\d,]+)원?'
        target_match = re.search(target_pattern, message_text)
        if target_match:
            target_price = int(target_match.group(1).replace(',', ''))

        # 현재가 추출 (선택)
        current_price = None
        current_pattern = r'(?:포착\s*)?현재가\s*[:：]\s*([\d,]+)원?'
        current_match = re.search(current_pattern, message_text)
        if current_match:
            current_price = int(current_match.group(1).replace(',', ''))

        result = {
            "stock_name": stock_name,
            "stock_code": stock_code,
            "target_price": target_price,
            "current_price": current_price
        }

        print(f"✅ 신호 파싱 완료: {result}")
        return result

    except Exception as e:
        print(f"❌ 신호 파싱 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


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
    print("\n" + "=" * 80)
    print(f"📋 {title}")
    print("=" * 80)
    print("\n📨 테스트 메시지:")
    for line in message.split('\n'):
        print(f"   {line}")
    print("\n" + "-" * 80)

    # 파싱 실행
    result = parse_stock_signal(message)

    if not result:
        print("❌ 파싱 실패!")
        return False

    # 결과 출력
    print(f"\n📊 파싱 결과:")
    print(f"   종목명: {result['stock_name']}")
    print(f"   종목코드: {result['stock_code']}")
    print(f"   적정 매수가: {result['target_price']}")
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
    print("\n" + "🔬" * 40)
    print("종목명 파싱 종합 테스트")
    print("🔬" * 40)

    test_results = []

    # 테스트 1: 정상적인 메시지 (종목명 있음)
    message1 = """⭐️ Ai 종목포착 시그널
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
포착 종목명 : 중앙첨단소재 (051980)
적정 매수가 : 3,430원 👉 7.36%
포착 현재가 : 3,395원 👉 6.26%"""

    expected1 = {
        "stock_name": "중앙첨단소재",
        "stock_code": "051980",
        "target_price": 3430,
        "current_price": 3395
    }

    result1 = test_case("테스트 1: 정상 메시지 (종목명 있음)", message1, expected1)
    test_results.append(("정상 메시지", result1))

    # 테스트 2: 종목명 비어있는 메시지
    message2 = """■ Ai 종목포착 시그널
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
포착 종목명 :  (051980)
적정 매수가 : 원 👉 %
포착 현재가 : 3,395원 👉 6.26%"""

    expected2 = {
        "stock_name": "051980",  # 종목코드로 대체됨
        "stock_code": "051980",
        "target_price": None,    # 빈 값은 None
        "current_price": 3395
    }

    result2 = test_case("테스트 2: 오류 메시지 (종목명 비어있음)", message2, expected2)
    test_results.append(("오류 메시지", result2))

    # 테스트 3: 다른 정상 메시지
    message3 = """⭐️ Ai 종목포착 시그널
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
포착 종목명 : 유일에너테크 (340930)
적정 매수가 : 2,870원 👉 6.49%
포착 현재가 : 2,860원 👉 6.12%"""

    expected3 = {
        "stock_name": "유일에너테크",
        "stock_code": "340930",
        "target_price": 2870,
        "current_price": 2860
    }

    result3 = test_case("테스트 3: 정상 메시지 (다른 종목)", message3, expected3)
    test_results.append(("다른 종목", result3))

    # 최종 결과 요약
    print("\n" + "=" * 80)
    print("📊 최종 테스트 결과 요약")
    print("=" * 80)

    for test_name, passed in test_results:
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"   {status}: {test_name}")

    total_passed = sum(1 for _, passed in test_results if passed)
    total_tests = len(test_results)

    print("\n" + "-" * 80)
    print(f"   총 {total_tests}개 테스트 중 {total_passed}개 통과")
    print("-" * 80)

    if total_passed == total_tests:
        print("\n🎉 모든 테스트 통과!")
        print("\n✅ 종목명이 있는 정상 메시지: 완벽히 파싱됨")
        print("✅ 종목명이 비어있는 오류 메시지: 종목코드로 대체하여 매수 가능")
        print("✅ 여러 종목의 정상 메시지: 모두 정확히 파싱됨")
        print("\n" + "=" * 80)
        return 0
    else:
        print("\n❌ 일부 테스트 실패!")
        print("\n" + "=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
