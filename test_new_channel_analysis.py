#!/usr/bin/env python3
"""
새 채널에서 최근 신호 10개 분석 테스트
"""

import asyncio
import os
import re
from datetime import datetime
from telethon import TelegramClient
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# Telegram 클라이언트 설정
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_NAME = os.getenv('SESSION_NAME', 'channel_copier')
SOURCE_CHANNEL = os.getenv('SOURCE_CHANNEL')

def parse_stock_signal_new(message_text: str) -> dict:
    """
    새 파싱 로직 (B안 - 괄호 안 6자리 숫자 기반)
    """
    try:
        # 1. 괄호 안의 6자리 숫자 추출 (종목코드)
        stock_code_pattern = r'\((\d{6})\)'
        match = re.search(stock_code_pattern, message_text)
        
        if not match:
            return None
        
        stock_code = match.group(1)
        
        # 2. 종목명 추출 (괄호 앞의 텍스트에서)
        stock_name = extract_stock_name(message_text, stock_code)
        
        # 3. 가격 정보 추출
        prices = extract_prices(message_text)
        
        return {
            "stock_name": stock_name,
            "stock_code": stock_code,
            "target_price": prices.get("target_price"),
            "current_price": prices.get("current_price")
        }
        
    except Exception as e:
        print(f"파싱 오류: {e}")
        return None

def extract_stock_name(message_text: str, stock_code: str) -> str:
    """괄호 앞의 텍스트에서 종목명 추출"""
    try:
        # 괄호와 종목코드 위치 찾기
        pattern = rf'\(({re.escape(stock_code)})\)'
        match = re.search(pattern, message_text)
        
        if not match:
            return ""
        
        # 괄호 앞의 텍스트 추출
        before_parentheses = message_text[:match.start()].strip()
        
        # 마지막 단어들을 종목명으로 추정 (최대 20자)
        lines = before_parentheses.split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith('=') and not line.startswith('-'):
                # 특수문자 제거하고 한글/영문/숫자만 추출
                cleaned = re.sub(r'[^\w가-힣\s]', '', line).strip()
                words = cleaned.split()
                if words:
                    # 마지막 몇 개 단어를 종목명으로 사용 (최대 20자)
                    stock_name = ' '.join(words[-3:])[:20]
                    if stock_name:
                        return stock_name
        
        return ""
        
    except Exception as e:
        print(f"종목명 추출 오류: {e}")
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
                break
        
    except Exception as e:
        print(f"가격 추출 오류: {e}")
    
    return prices

async def analyze_new_channel():
    """새 채널에서 최근 신호 10개 분석"""
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        print("🔗 Telegram 클라이언트 연결 중...")
        await client.start()
        
        print("📡 채널 정보 확인 중...")
        try:
            entity = await client.get_entity(SOURCE_CHANNEL)
            print(f"✅ 채널 연결 성공:")
            print(f"   - 채널명: {entity.title}")
            print(f"   - 채널 ID: {entity.id}")
            if hasattr(entity, 'username') and entity.username:
                print(f"   - Username: @{entity.username}")
        except Exception as e:
            print(f"❌ 채널 연결 실패: {e}")
            return
        
        print(f"\n📥 최근 메시지 50개 조회 중...")
        messages = []
        async for message in client.iter_messages(entity, limit=50):
            if message.text:
                messages.append({
                    'id': message.id,
                    'date': message.date,
                    'text': message.text
                })
        
        print(f"✅ {len(messages)}개 메시지 조회 완료")
        
        # 새 파싱 로직으로 신호 분석
        print(f"\n🔍 새 파싱 로직으로 종목 신호 분석 중...")
        detected_signals = []
        
        for msg in messages:
            result = parse_stock_signal_new(msg['text'])
            if result:
                detected_signals.append({
                    'message_id': msg['id'],
                    'date': msg['date'],
                    'signal': result,
                    'text': msg['text']
                })
        
        print(f"\n📊 **분석 결과 요약:**")
        print(f"   - 전체 메시지: {len(messages)}개")
        print(f"   - 감지된 신호: {len(detected_signals)}개")
        print(f"   - 신호 인식률: {len(detected_signals)/len(messages)*100:.1f}%")
        
        # 상위 10개 신호 상세 분석
        print(f"\n🎯 **최근 신호 10개 상세 분석:**")
        print("=" * 80)
        
        signals_to_show = detected_signals[:10]  # 최근 10개
        
        for i, signal_data in enumerate(signals_to_show, 1):
            signal = signal_data['signal']
            date = signal_data['date']
            
            print(f"\n[{i}] 감지 시간: {date.strftime('%m-%d %H:%M:%S')}")
            print(f"    종목명: {signal['stock_name'] or '(추출 실패)'}")
            print(f"    종목코드: {signal['stock_code']}")
            
            if signal['target_price']:
                print(f"    목표가: {signal['target_price']:,}원")
            if signal['current_price']:
                print(f"    현재가: {signal['current_price']:,}원")
            
            # 메시지 원문 일부 표시 (첫 2줄)
            text_lines = signal_data['text'].split('\n')[:2]
            preview = ' / '.join(line.strip() for line in text_lines if line.strip())
            print(f"    원문: {preview[:60]}{'...' if len(preview) > 60 else ''}")
        
        # 종목코드별 통계
        stock_codes = [s['signal']['stock_code'] for s in detected_signals]
        unique_codes = list(set(stock_codes))
        
        print(f"\n📈 **종목별 통계:**")
        print(f"   - 총 감지 종목 수: {len(unique_codes)}개")
        if len(unique_codes) > 0:
            print(f"   - 중복 신호 비율: {(len(stock_codes) - len(unique_codes))/len(stock_codes)*100:.1f}%")
        
        # 시간별 분포
        if detected_signals:
            hours = [s['date'].hour for s in detected_signals]
            hour_dist = {}
            for hour in hours:
                hour_dist[hour] = hour_dist.get(hour, 0) + 1
            
            print(f"\n⏰ **시간대별 신호 분포:**")
            for hour in sorted(hour_dist.keys()):
                print(f"   - {hour:02d}시: {hour_dist[hour]}개")
        
        print(f"\n" + "=" * 80)
        print(f"✅ 새 채널 분석 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(analyze_new_channel())