"""
종목명이 정상적으로 있는 실제 메시지 파싱 테스트
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


def main():
    """종목명이 정상적으로 있는 실제 메시지 테스트"""
    print("\n" + "=" * 80)
    print("종목명이 정상적으로 있는 실제 메시지 파싱 테스트")
    print("=" * 80)

    # 사용자가 제공한 실제 메시지
    test_message = """⭐️ Ai 종목포착 시그널
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
포착 종목명 : 중앙첨단소재 (051980)
적정 매수가 : 3,430원 👉 7.36%
포착 현재가 : 3,395원 👉 6.26%"""

    print("\n📨 테스트 메시지:")
    print(test_message)
    print("\n" + "-" * 80)
    print("🔍 메시지 구조 분석:")
    print("-" * 80)

    # 메시지 라인별로 분석
    for i, line in enumerate(test_message.split('\n'), 1):
        print(f"   Line {i}: {repr(line)}")

    print("\n" + "=" * 80)

    # 파싱 실행
    result = parse_stock_signal(test_message)

    # 결과 검증
    print("\n" + "=" * 80)
    print("📊 파싱 결과 검증")
    print("=" * 80)

    if result:
        print(f"\n✅ 파싱 성공!")
        print(f"\n   📌 종목명: {result['stock_name']}")
        print(f"   📌 종목코드: {result['stock_code']}")
        print(f"   📌 적정 매수가: {result['target_price']:,}원" if result['target_price'] else "   📌 적정 매수가: None")
        print(f"   📌 현재가: {result['current_price']:,}원" if result['current_price'] else "   📌 현재가: None")

        print("\n" + "-" * 80)
        print("🔎 기대값과 비교:")
        print("-" * 80)

        # 기대값 검증
        checks = []

        # 1. 종목명 검증
        if result['stock_name'] == '중앙첨단소재':
            print("   ✅ 종목명: '중앙첨단소재' (정확히 일치)")
            checks.append(True)
        else:
            print(f"   ❌ 종목명: 예상 '중앙첨단소재', 실제 '{result['stock_name']}'")
            checks.append(False)

        # 2. 종목코드 검증
        if result['stock_code'] == '051980':
            print("   ✅ 종목코드: '051980' (정확히 일치)")
            checks.append(True)
        else:
            print(f"   ❌ 종목코드: 예상 '051980', 실제 '{result['stock_code']}'")
            checks.append(False)

        # 3. 적정 매수가 검증
        if result['target_price'] == 3430:
            print("   ✅ 적정 매수가: 3,430원 (정확히 일치)")
            checks.append(True)
        else:
            print(f"   ❌ 적정 매수가: 예상 3,430원, 실제 {result['target_price']}원")
            checks.append(False)

        # 4. 현재가 검증
        if result['current_price'] == 3395:
            print("   ✅ 현재가: 3,395원 (정확히 일치)")
            checks.append(True)
        else:
            print(f"   ❌ 현재가: 예상 3,395원, 실제 {result['current_price']}원")
            checks.append(False)

        print("\n" + "=" * 80)

        # 최종 결과
        if all(checks):
            print("🎉 모든 검증 항목 통과!")
            print("=" * 80)
            print("\n✅ 종목명이 정상적으로 있는 메시지 파싱 완벽하게 동작합니다")
            print("   - 종목명 '중앙첨단소재' 추출: OK")
            print("   - 종목코드 '051980' 추출: OK")
            print("   - 적정 매수가 3,430원 추출: OK")
            print("   - 현재가 3,395원 추출: OK")
            return 0
        else:
            print("❌ 일부 검증 항목 실패!")
            print("=" * 80)
            return 1

    else:
        print("\n❌ 파싱 실패!")
        print("=" * 80)
        print("\n메시지가 올바르게 파싱되지 않았습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
