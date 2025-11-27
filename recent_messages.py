#!/usr/bin/env python3
"""
텔레그램 채널 최근 메시지 조회 및 매수신호 분석

auto_trading.py의 parse_stock_signal 로직을 사용하여
최근 메시지 중 매수신호로 인정될 만한 것을 리스트업합니다.
"""

import asyncio
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telethon import TelegramClient

# 환경변수 로드
load_dotenv()

class MessageAnalyzer:
    """메시지 분석기"""
    
    def __init__(self):
        # Telegram 설정
        self.api_id = int(os.getenv('API_ID'))
        self.api_hash = os.getenv('API_HASH')
        self.session_name = os.getenv('SESSION_NAME', 'channel_copier')
        self.source_channel = os.getenv('SOURCE_CHANNEL')
        
        # Telegram 클라이언트
        self.telegram_client = TelegramClient(
            self.session_name,
            self.api_id,
            self.api_hash
        )

    @staticmethod
    def to_kst(utc_datetime):
        """UTC 시간을 한국 시간(KST, UTC+9)으로 변환"""
        if utc_datetime.tzinfo is None:
            utc_datetime = utc_datetime.replace(tzinfo=ZoneInfo("UTC"))
        return utc_datetime.astimezone(ZoneInfo("Asia/Seoul"))

    def parse_stock_signal(self, message_text: str) -> dict:
        """
        텔레그램 메시지에서 종목 정보 파싱 (auto_trading.py와 동일한 로직)
        
        괄호 안 6자리 숫자를 종목코드로 인식하여 시그널 처리
        
        Returns:
            {
                "stock_name": "벨로크",
                "stock_code": "424760", 
                "target_price": 1458,
                "current_price": 1426
            } or None
        """
        try:
            # 1. 괄호 안의 6자리 숫자 추출 (종목코드)
            stock_code_pattern = r'\((\d{6})\)'
            match = re.search(stock_code_pattern, message_text)
            
            if not match:
                return None
                
            stock_code = match.group(1)
            
            # 2. 종목명 추출 (괄호 앞의 텍스트에서)
            stock_name = self._extract_stock_name(message_text, stock_code)
            
            # 3. 가격 정보 추출  
            prices = self._extract_prices(message_text)
            
            result = {
                "stock_name": stock_name,
                "stock_code": stock_code,
                "target_price": prices.get("target"),
                "current_price": prices.get("current")
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 신호 파싱 실패: {e}")
            return None

    def _extract_stock_name(self, message_text: str, stock_code: str) -> str:
        """
        괄호 앞에서 종목명 추출
        
        예:
        "포착 종목명 : 벨로크 (424760)" → "벨로크"
        "종목명 👉 유일에너테크 (340930)" → "유일에너테크" 
        "종목명 : 아미노로직스 (074430)" → "아미노로직스"
        "종목코드 (123456)" → ""
        """
        # 괄호 앞의 텍스트 패턴 (한글, 영문, 숫자, &, ＆)
        pattern = r'([가-힣a-zA-Z0-9＆&]+)\s*\(' + re.escape(stock_code) + r'\)'
        match = re.search(pattern, message_text)
        
        if not match:
            return ""
            
        stock_name = match.group(1).strip()
        
        # 불필요한 접두사 제거
        # "포착 종목명 : 벨로크" → "벨로크" 
        # "종목명 👉 유일에너테크" → "유일에너테크"
        stock_name = re.sub(r'.*[:：]\s*', '', stock_name).strip()
        stock_name = re.sub(r'.*👉\s*', '', stock_name).strip()
        
        return stock_name

    def _extract_prices(self, message_text: str) -> dict:
        """
        메시지에서 가격 정보 추출
        
        Returns:
            {"target": int or None, "current": int or None}
        """
        prices = {"target": None, "current": None}
        
        # 1. 적정 매수가, 매도가, 목표가 → target_price
        target_patterns = [
            r'적정\s*매수가?\s*[:：]\s*([\d,]+)원?',
            r'매도가\s*[:：👉]\s*([\d,]+)원?', 
            r'목표가\s*[:：👉]\s*([\d,]+)원?'
        ]
        
        for pattern in target_patterns:
            match = re.search(pattern, message_text)
            if match:
                try:
                    prices["target"] = int(match.group(1).replace(',', ''))
                    break
                except (ValueError, AttributeError):
                    continue
        
        # 2. 현재가, 매수가, 포착 현재가 → current_price  
        current_patterns = [
            r'(?:포착\s*)?현재가\s*[:：]\s*([\d,]+)원?',
            r'매수가\s*[:：👉]\s*([\d,]+)원?'
        ]
        
        for pattern in current_patterns:
            match = re.search(pattern, message_text)
            if match:
                try:
                    prices["current"] = int(match.group(1).replace(',', ''))
                    break
                except (ValueError, AttributeError):
                    continue
                    
        return prices

    async def get_recent_messages(self, limit: int = 10):
        """최근 메시지 조회 및 매수신호 분석"""
        
        try:
            print("🚀 텔레그램 클라이언트 연결 중...")
            await self.telegram_client.start()
            
            me = await self.telegram_client.get_me()
            print(f"✅ 로그인: {me.first_name} (@{me.username})")
            print(f"📥 채널: {self.source_channel}")
            print(f"🔍 최근 {limit}개 메시지 조회 중... (DSC 인베스트먼트 검색)")
            print("=" * 80)
            
            # 채널 엔티티 정보 확인
            source_entity = await self.telegram_client.get_entity(self.source_channel)
            print(f"📊 채널명: {getattr(source_entity, 'title', 'N/A')}")
            print(f"📊 채널 ID: {source_entity.id}")
            print("=" * 80)
            
            # 최근 메시지 조회
            messages = await self.telegram_client.get_messages(self.source_channel, limit=limit)
            
            # DSC 인베스트먼트 메시지 특별 검색
            print("🔍 'DSC' 또는 '241520' 포함 메시지 특별 검색 중...")
            dsc_messages = []
            for msg in messages:
                if msg.text and ('DSC' in msg.text or '241520' in msg.text):
                    dsc_messages.append(msg)
            
            if dsc_messages:
                print(f"📋 DSC 관련 메시지 {len(dsc_messages)}건 발견!")
            else:
                print("❌ DSC 또는 241520 관련 메시지를 찾을 수 없습니다.")
            
            print(f"✅ {len(messages)}개 메시지 조회 완료")
            print("=" * 80)
            
            # DSC 메시지 상세 분석
            print("\n🔍 DSC 관련 메시지 상세 분석:")
            for i, msg in enumerate(dsc_messages, 1):
                print(f"\n📨 DSC 메시지 {i}")
                kst_time = self.to_kst(msg.date)
                print(f"⏰ 시간: {kst_time.strftime('%Y-%m-%d %H:%M:%S')} (KST)")
                print(f"💬 전체 내용:\n{msg.text}")
                
                # 6자리 숫자 찾기
                stock_codes = re.findall(r'\((\d{6})\)', msg.text)
                if stock_codes:
                    print(f"🎯 발견된 종목코드: {stock_codes}")
                else:
                    print("❌ 6자리 종목코드를 찾을 수 없음")
                    
                # 신호 파싱 시도
                signal = self.parse_stock_signal(msg.text)
                if signal:
                    print(f"✅ 파싱 성공: {signal}")
                else:
                    print("❌ 파싱 실패")
                    
                print("=" * 60)
            
            # 매수신호 분석
            signals = []
            
            for i, msg in enumerate(messages, 1):
                if not msg.text:
                    continue
                
                # DSC 메시지는 건너뛰고 (이미 위에서 분석함)
                if 'DSC' in msg.text:
                    continue

                print(f"\n📨 메시지 {i}")
                kst_time = self.to_kst(msg.date)
                print(f"⏰ 시간: {kst_time.strftime('%Y-%m-%d %H:%M:%S')} (KST)")
                print(f"💬 내용: {msg.text[:100]}...")
                
                # 신고 파싱 시도
                signal = self.parse_stock_signal(msg.text)
                
                if signal:
                    print(f"✅ 매수신호 감지!")
                    print(f"   종목명: {signal['stock_name']}")
                    print(f"   종목코드: {signal['stock_code']}")
                    if signal['target_price']:
                        print(f"   목표가: {signal['target_price']:,}원")
                    if signal['current_price']:
                        print(f"   현재가: {signal['current_price']:,}원")
                    
                    signals.append({
                        "message_id": msg.id,
                        "date": msg.date,
                        "text": msg.text,
                        "signal": signal
                    })
                else:
                    print("ℹ️  매수신호 아님")
                    
                print("-" * 40)
            
            # 결과 요약
            print("\n" + "=" * 80)
            print("📋 매수신호 요약")
            print("=" * 80)
            
            if signals:
                print(f"✅ 총 {len(signals)}개의 매수신호를 발견했습니다:")
                print()
                
                for i, item in enumerate(signals, 1):
                    signal = item['signal']
                    date_str = item['date'].strftime('%Y-%m-%d %H:%M:%S')
                    
                    print(f"{i}. [{date_str}] {signal['stock_name']} ({signal['stock_code']})")
                    if signal['target_price']:
                        print(f"   목표가: {signal['target_price']:,}원")
                    if signal['current_price']:
                        print(f"   현재가: {signal['current_price']:,}원")
                    print()
                    
            else:
                print("❌ 매수신호가 발견되지 않았습니다.")
                print("💡 6자리 숫자가 괄호 안에 있는 메시지를 찾습니다.")
                print("💡 예: '종목명 : 테스트종목 (123456)'")
            
            print("=" * 80)
            
            return signals
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            return []
            
        finally:
            if self.telegram_client.is_connected():
                await self.telegram_client.disconnect()
                print("✅ 텔레그램 클라이언트 종료")


async def main():
    """메인 실행 함수"""
    analyzer = MessageAnalyzer()
    
    # 최근 100개 메시지 분석 (DSC 인베스트먼트 찾기 위해 확장)
    signals = await analyzer.get_recent_messages(limit=100)
    
    print(f"\n🎯 분석 완료: {len(signals)}개 매수신호 발견")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"프로그램 오류: {e}")