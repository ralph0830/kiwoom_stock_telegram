#!/usr/bin/env python3
"""
실제 매수 신호 파싱 실패 디버깅
"""

import re

def parse_stock_signal_current(message_text: str) -> dict:
    """
    현재 auto_trading.py의 파싱 로직 (실패한 로직)
    """
    try:
        # 1. 괄호 안의 6자리 숫자 추출 (종목코드)
        stock_code_pattern = r'\((\d{6})\)'
        match = re.search(stock_code_pattern, message_text)
        
        if not match:
            print("❌ 괄호 안의 6자리 숫자를 찾을 수 없습니다")
            return None
        
        stock_code = match.group(1)
        print(f"✅ 종목코드 추출 성공: {stock_code}")
        
        # 2. 종목명 추출 (괄호 앞의 텍스트에서)
        stock_name = extract_stock_name(message_text, stock_code)
        print(f"✅ 종목명 추출: '{stock_name}'")
        
        # 3. 가격 정보 추출
        prices = extract_prices(message_text)
        print(f"✅ 가격 정보: {prices}")
        
        return {
            "stock_name": stock_name,
            "stock_code": stock_code,
            "target_price": prices.get("target_price"),
            "current_price": prices.get("current_price")
        }
        
    except Exception as e:
        print(f"❌ 파싱 오류: {e}")
        return None

def extract_stock_name(message_text: str, stock_code: str) -> str:
    """괄호 앞의 텍스트에서 종목명 추출"""
    try:
        # 괄호와 종목코드 위치 찾기
        pattern = rf'\(({re.escape(stock_code)})\)'
        match = re.search(pattern, message_text)
        
        if not match:
            print(f"❌ 종목코드 {stock_code} 패턴을 찾을 수 없음")
            return ""
        
        # 괄호 앞의 텍스트 추출
        before_parentheses = message_text[:match.start()].strip()
        print(f"🔍 괄호 앞 텍스트: '{before_parentheses}'")
        
        # 마지막 단어들을 종목명으로 추정 (최대 20자)
        lines = before_parentheses.split('\n')
        print(f"🔍 라인별 분석: {lines}")
        
        for line in reversed(lines):
            line = line.strip()
            print(f"🔍 라인 검사: '{line}'")
            if line and not line.startswith('=') and not line.startswith('-') and not line.startswith('￣'):
                # 특수문자 제거하고 한글/영문/숫자만 추출
                cleaned = re.sub(r'[^\w가-힣\s]', '', line).strip()
                print(f"🔍 정리된 라인: '{cleaned}'")
                words = cleaned.split()
                print(f"🔍 단어 분리: {words}")
                if words:
                    # 마지막 몇 개 단어를 종목명으로 사용 (최대 20자)
                    stock_name = ' '.join(words[-3:])[:20]
                    if stock_name:
                        print(f"✅ 종목명 추출 성공: '{stock_name}'")
                        return stock_name
        
        print(f"❌ 종목명을 찾을 수 없음")
        return ""
        
    except Exception as e:
        print(f"❌ 종목명 추출 오류: {e}")
        return ""

def extract_prices(message_text: str) -> dict:
    """메시지에서 가격 정보 추출"""
    prices = {"target_price": None, "current_price": None}
    
    try:
        # 목표가/적정매수가 패턴
        target_patterns = [
            r'목표가[:\s]*([\d,]+)원?',
            r'적정\s*매수가?[:\s]*([\d,]+)원?',
            r'매수가[:\s]*([\d,]+)원?'
        ]
        
        for pattern in target_patterns:
            match = re.search(pattern, message_text)
            if match:
                prices["target_price"] = int(match.group(1).replace(',', ''))
                print(f"✅ 매수가 추출: {prices['target_price']}")
                break
        
        # 현재가 패턴
        current_patterns = [
            r'현재가[:\s]*([\d,]+)원?',
            r'포착\s*현재가[:\s]*([\d,]+)원?'
        ]
        
        for pattern in current_patterns:
            match = re.search(pattern, message_text)
            if match:
                prices["current_price"] = int(match.group(1).replace(',', ''))
                print(f"✅ 현재가 추출: {prices['current_price']}")
                break
        
    except Exception as e:
        print(f"❌ 가격 추출 오류: {e}")
    
    return prices

# 실제 실패한 메시지 테스트
test_message = """✅ #매수신호
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
종목명 : 대원전선 (006340)
매수가 : 4,035원
등락률 : 6.35%
￣￣￣￣￣￣￣￣￣￣￣￣￣￣￣
매도가 : 4,125원"""

print("🔍 실제 실패한 메시지 디버깅")
print("=" * 60)
print("📨 원본 메시지:")
print(test_message)
print("=" * 60)

print("\n🧪 파싱 테스트 시작:")
result = parse_stock_signal_current(test_message)

print(f"\n📊 최종 결과:")
if result:
    print(f"✅ 파싱 성공!")
    for key, value in result.items():
        print(f"   - {key}: {value}")
else:
    print(f"❌ 파싱 실패")
    
print("\n" + "=" * 60)