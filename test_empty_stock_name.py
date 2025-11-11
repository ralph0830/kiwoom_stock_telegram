"""
종목명이 비어있는 경우 파싱 테스트
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
        return None


def main():
    """종목명 비어있는 케이스 테스트"""
    print("\n" + "=" * 80)
    print("종목명이 비어있는 경우 파싱 테스트")
    print("=" * 80)

    # 사용자가 제공한 실제 메시지
    test_message = """■ Ai 종목포착 시그널
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
포착 종목명 :  (051980)
적정 매수가 : 원 👉 %
포착 현재가 : 3,395원 👉 6.26%"""

    print("\n📨 테스트 메시지:")
    print(test_message)
    print("\n" + "=" * 80)

    # 파싱 실행
    result = parse_stock_signal(test_message)

    # 결과 검증
    print("\n" + "=" * 80)
    print("📊 파싱 결과 검증")
    print("=" * 80)

    if result:
        print(f"✅ 파싱 성공!")
        print(f"   종목명: {result['stock_name']}")
        print(f"   종목코드: {result['stock_code']}")
        print(f"   적정 매수가: {result['target_price']}")
        print(f"   현재가: {result['current_price']}")

        # 기대값 검증
        assert result['stock_code'] == '051980', "종목코드가 일치하지 않습니다"
        assert result['stock_name'] == '051980', "종목명이 종목코드로 대체되지 않았습니다"
        assert result['current_price'] == 3395, "현재가가 일치하지 않습니다"
        assert result['target_price'] is None, "비어있는 적정 매수가가 None이 아닙니다"

        print("\n✅ 모든 검증 통과!")
        print("   - 종목코드 추출: OK")
        print("   - 종목명 자동 대체: OK (종목코드로 대체)")
        print("   - 현재가 추출: OK")
        print("   - 빈 적정 매수가 처리: OK (None)")
    else:
        print("❌ 파싱 실패!")
        sys.exit(1)


    # 추가 테스트 케이스
    print("\n" + "=" * 80)
    print("추가 테스트: 정상적인 메시지")
    print("=" * 80)

    normal_message = """⭐️ Ai 종목포착 시그널
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
포착 종목명 : 유일에너테크 (340930)
적정 매수가 : 2,870원 👉 6.49%
포착 현재가 : 2,860원 👉 6.12%"""

    print("\n📨 테스트 메시지:")
    print(normal_message)
    print("\n" + "=" * 80)

    result2 = parse_stock_signal(normal_message)

    if result2:
        print(f"✅ 파싱 성공!")
        print(f"   종목명: {result2['stock_name']}")
        print(f"   종목코드: {result2['stock_code']}")
        print(f"   적정 매수가: {result2['target_price']}")
        print(f"   현재가: {result2['current_price']}")

        assert result2['stock_name'] == '유일에너테크', "종목명이 일치하지 않습니다"
        assert result2['stock_code'] == '340930', "종목코드가 일치하지 않습니다"
        assert result2['target_price'] == 2870, "적정 매수가가 일치하지 않습니다"
        assert result2['current_price'] == 2860, "현재가가 일치하지 않습니다"

        print("\n✅ 정상 메시지 검증 통과!")
    else:
        print("❌ 정상 메시지 파싱 실패!")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("🎉 모든 테스트 통과!")
    print("=" * 80)
    print("\n✅ 종목명이 비어있어도 종목코드만으로 매수 가능합니다")
    print("✅ 정상적인 메시지도 문제없이 처리됩니다")


if __name__ == "__main__":
    main()
