"""
텔레그램 채널 기반 실시간 자동매매 시스템

텔레그램 채널에서 매수 신호를 받아 키움 API로 자동 매수하고,
WebSocket으로 실시간 시세를 모니터링하여 자동 익절/손절합니다.
"""

import asyncio
import logging
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telethon import TelegramClient, events
from logging.handlers import RotatingFileHandler

from config import TradingConfig
from trading_system_base import TradingSystemBase

# 환경변수 로드
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 로그 포맷 설정
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 콘솔 핸들러
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 파일 핸들러 (안전하게 추가)
try:
    log_dir = os.path.dirname('auto_trading.log')
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        'auto_trading.log',
        maxBytes=200 * 1024 * 1024,  # 200MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

except Exception as e:
    print(f"⚠️ 로그 파일 생성 실패: {e}")
    print(f"📝 콘솔 전용 모드로 실행됩니다.")


class TelegramTradingSystem(TradingSystemBase):
    """텔레그램 채널 기반 자동매매 시스템"""

    def __init__(self, config: TradingConfig):
        """
        Args:
            config: 자동매매 설정
        """
        super().__init__(config)

        # Telegram 설정 검증
        if not config.api_id or not config.api_hash:
            raise ValueError("Telegram API 설정이 필요합니다 (API_ID, API_HASH)")

        # Telegram 설정
        self.api_id = config.api_id
        self.api_hash = config.api_hash
        self.session_name = config.session_name
        self.source_channel = config.source_channel
        self.target_channel = config.target_channel

        # Telegram 클라이언트
        self.telegram_client = TelegramClient(
            self.session_name,
            self.api_id,
            self.api_hash
        )

        logger.info("✅ TelegramTradingSystem 초기화 완료")

    @staticmethod
    def to_kst(utc_datetime):
        """
        UTC 시간을 한국 시간(KST, UTC+9)으로 변환

        Args:
            utc_datetime: UTC datetime 객체

        Returns:
            한국 시간으로 변환된 datetime 객체
        """
        if utc_datetime.tzinfo is None:
            # timezone 정보가 없으면 UTC로 가정
            utc_datetime = utc_datetime.replace(tzinfo=ZoneInfo("UTC"))
        return utc_datetime.astimezone(ZoneInfo("Asia/Seoul"))

    def parse_stock_signal(self, message_text: str) -> dict:
        """
        텔레그램 메시지에서 종목 정보 파싱

        **새 로직 (B안 - 유연성 우선):**
        괄호 안 6자리 숫자를 종목코드로 인식하여 시그널 처리
        키워드 검증 없이 모든 형식의 메시지 지원

        지원 형식 예시:
        - ⭐️ Ai 종목포착 시그널\n포착 종목명 : 유일에너테크 (340930)
        - ✅ #매수신호\n종목명 👉 벨로크 (424760)
        - ✅ #알림\n종목명 : 아미노로직스 (074430)
        - 급등주 추천: 테스트종목 (123456)
        - 종목명이 없어도 OK:  (051980)

        Returns:
            {
                "stock_name": "벨로크",
                "stock_code": "424760",
                "target_price": 1458,
                "current_price": 1426
            }
        """
        try:
            # 1. 괄호 안의 6자리 숫자 추출 (종목코드)
            stock_code_pattern = r'\((\d{6})\)'
            match = re.search(stock_code_pattern, message_text)

            if not match:
                logger.debug("ℹ️ 괄호 안의 6자리 숫자를 찾을 수 없습니다")
                return None

            stock_code = match.group(1)

            # 2. 종목코드 유효성 검증 (3단계 검증 + 캐싱)
            logger.info(f"🔍 종목코드 유효성 검증 시작: {stock_code}")
            validation_result = self.kiwoom_api.validate_stock_code(stock_code)

            if not validation_result["valid"]:
                reason = validation_result["reason"]
                logger.warning(f"❌ 유효하지 않은 종목코드: {stock_code} - {reason}")
                return None

            # 검증 성공 - API에서 받은 종목명 사용 (더 정확함)
            validated_stock_name = validation_result["stock_name"]
            cached_info = " (캐시됨)" if validation_result["cached"] else ""
            logger.info(f"✅ 종목코드 검증 성공: {stock_code} ({validated_stock_name}){cached_info}")

            # 3. 종목명 추출 (괄호 앞의 텍스트에서)
            stock_name = self._extract_stock_name(message_text, stock_code)

            # 메시지에서 종목명을 찾지 못했으면 API에서 받은 종목명 사용
            if not stock_name:
                stock_name = validated_stock_name
                logger.info(f"ℹ️ 메시지에서 종목명을 찾지 못해 API 종목명 사용: {stock_name}")

            # 4. 가격 정보 추출
            prices = self._extract_prices(message_text)

            result = {
                "stock_name": stock_name,
                "stock_code": stock_code,
                "target_price": prices.get("target"),
                "current_price": prices.get("current")
            }

            logger.info(f"✅ 신호 파싱 완료 (6자리 숫자 기반 + 검증): {result}")
            return result

        except Exception as e:
            logger.error(f"❌ 신호 파싱 실패: {e}")
            import traceback
            logger.debug(traceback.format_exc())
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

    async def handle_telegram_signal(self, event):
        """텔레그램 신호 처리 (이벤트 핸들러)"""
        msg = event.message
        logger.info("🔔 이벤트 핸들러 호출됨! (새 메시지 감지)")

        try:
            # 0. TARGET_CHANNEL이 설정되어 있으면 모든 메시지를 TARGET 채널로 복사
            if self.target_channel and self.target_channel.strip():
                try:
                    if msg.media:
                        await self.telegram_client.send_file(
                            self.target_channel,
                            msg.media,
                            caption=msg.text
                        )
                        logger.info(f"📤 메시지 복사 완료 (미디어 포함, TARGET: {self.target_channel})")
                    elif msg.text:
                        await self.telegram_client.send_message(self.target_channel, msg.text)
                        logger.info(f"📤 메시지 복사 완료 (텍스트, TARGET: {self.target_channel})")
                    else:
                        logger.info("ℹ️ 복사할 내용이 없는 메시지입니다")
                except Exception as e:
                    logger.error(f"❌ 메시지 복사 실패: {e}")
            else:
                logger.debug("ℹ️ TARGET_CHANNEL이 설정되지 않아 메시지 복사를 건너뜁니다")

            # 1. 텍스트 메시지가 아니면 매수 로직 스킵
            if not msg.text:
                logger.info("ℹ️ 텍스트 메시지가 아니므로 매수 처리를 건너뜁니다")
                return

            logger.info("=" * 80)
            logger.info("📨 텔레그램 메시지 수신")
            logger.info(f"💬 내용: {msg.text[:100]}...")
            logger.info("=" * 80)

            # 2. 메시지 파싱
            signal = self.parse_stock_signal(msg.text)

            if not signal:
                logger.info("ℹ️ 매수 신호가 아니거나 파싱 실패")
                return

            logger.info(f"✅ 신호 파싱 완료: {signal}")

            # 3. 오늘 이미 매수했는지 확인
            if self.check_today_trading_done():
                logger.info("⏹️  오늘 이미 매수를 실행했습니다. 추가 매수를 건너뜁니다.")
                return

            # 4. 이미 매수 주문을 실행했는지 확인
            if self.order_executed:
                logger.info("⏹️  이미 매수 주문을 실행했습니다. 추가 매수를 건너뜁니다.")
                return

            # 5. 매수 가능 시간 확인
            if not self.is_buy_time_allowed():
                now = datetime.now()
                logger.warning(f"⏰ 매수 가능 시간이 아닙니다. (현재: {now.strftime('%H:%M')}, 허용: {self.config.buy_start_time} ~ {self.config.buy_end_time})")
                return

            # 6. 자동 매수 실행
            self.order_executed = True  # 즉시 플래그 설정 (중복 방지)

            order_result = await self.execute_auto_buy(
                stock_code=signal["stock_code"],
                stock_name=signal["stock_name"],
                current_price=signal.get("current_price")
            )

            # 7. 10초 후 미체결 주문 자동 취소 백그라운드 태스크 시작
            asyncio.create_task(self.cancel_outstanding_orders_after_delay(delay_seconds=10))

            if order_result and order_result.get("success"):
                # 매수 기록 저장
                self.record_today_trading(
                    stock_code=signal["stock_code"],
                    stock_name=signal["stock_name"],
                    buy_price=self.buy_info["buy_price"],
                    quantity=self.buy_info["quantity"],
                    buy_time=self.buy_info["buy_time"]
                )

                # WebSocket 실시간 시세 모니터링 시작
                if self.config.enable_sell_monitoring:
                    logger.info(f"📈 WebSocket 실시간 시세 모니터링 시작 (목표: {self.config.target_profit_rate*100:.2f}%)")
                    await self.start_websocket_monitoring()

                    # REST API 폴링 태스크 추가 (백업)
                    asyncio.create_task(self.price_polling_loop())
                else:
                    logger.info("⏸️  매도 모니터링이 비활성화되어 있습니다.")
            else:
                logger.error("❌ 자동 매수 실패")
                self.order_executed = False  # 실패 시 플래그 해제

        except Exception as e:
            logger.error(f"❌ Telegram 신호 처리 중 오류: {e}")
            self.order_executed = False

    async def cancel_outstanding_orders_after_delay(self, delay_seconds: int = 10):
        """
        지정된 시간(기본 10초) 후 모든 미체결 주문을 자동 취소

        Args:
            delay_seconds: 대기 시간 (초)
        """
        try:
            logger.info(f"⏰ {delay_seconds}초 후 미체결 주문 자동 취소 예약됨")

            # 지정된 시간만큼 대기
            await asyncio.sleep(delay_seconds)

            logger.info(f"🔍 {delay_seconds}초 경과 - 미체결 주문 확인 중...")

            # 미체결 주문 조회
            outstanding_result = self.order_api.get_outstanding_orders()

            if not outstanding_result or not outstanding_result.get("success"):
                logger.warning("⚠️ 미체결 주문 조회 실패")
                return

            outstanding_orders = outstanding_result.get("outstanding_orders", [])

            if not outstanding_orders:
                logger.info("✅ 미체결 주문이 없습니다 (모두 체결 완료)")
                return

            # 모든 미체결 주문 취소
            logger.warning(f"🚨 미체결 주문 {len(outstanding_orders)}건 발견 - 자동 취소 시작")

            for order in outstanding_orders:
                try:
                    ord_no = order.get("ord_no", "")
                    stock_code = order.get("stk_cd", "")
                    stock_name = order.get("stk_nm", "")
                    rmndr_qty = order.get("rmndr_qty", order.get("ord_qty", "0"))

                    if not ord_no or not stock_code:
                        logger.warning(f"⚠️ 주문정보 불완전 - 건너뜀: {order}")
                        continue

                    # 미체결 수량 전부 취소 (0 입력 시 잔량 전부 취소)
                    cancel_qty = int(rmndr_qty) if rmndr_qty else 0

                    logger.info(f"🗑️ 주문 취소 시도: {stock_name}({stock_code}) - 주문번호: {ord_no}, 수량: {cancel_qty}주")

                    cancel_result = self.order_api.cancel_order(
                        order_no=ord_no,
                        stock_code=stock_code,
                        quantity=cancel_qty
                    )

                    if cancel_result and cancel_result.get("success"):
                        logger.info(f"✅ 주문 취소 성공: {stock_name}({stock_code})")
                    else:
                        logger.error(f"❌ 주문 취소 실패: {stock_name}({stock_code}) - {cancel_result.get('message', '알 수 없는 오류')}")

                except Exception as e:
                    logger.error(f"❌ 주문 취소 중 오류: {e}")
                    continue

            logger.info("✅ 미체결 주문 자동 취소 완료")

        except Exception as e:
            logger.error(f"❌ 미체결 주문 자동 취소 프로세스 오류: {e}")

    async def price_polling_loop(self):
        """REST API로 10초마다 현재가 조회 (WebSocket 백업)"""
        from rich.live import Live

        logger.info("🔄 REST API 백업 폴링 시작 (10초 간격)")
        await asyncio.sleep(10)

        # 콘솔 클리어
        self.console.clear()

        # 초기 테이블 생성
        initial_table = self.create_price_table(0, self.buy_info["buy_price"], 0.0, "대기 중")

        # Rich Live 디스플레이 시작
        with Live(
            initial_table,
            console=self.console,
            refresh_per_second=4,
            screen=True
        ) as live:
            self.live_display = live

            while not self.sell_executed:
                try:
                    # REST API로 현재가 조회
                    result = self.kiwoom_api.get_current_price(self.buy_info["stock_code"])

                    if result.get("success"):
                        current_price = result.get("current_price", 0)

                        if current_price > 0:
                            buy_price = self.buy_info["buy_price"]
                            profit_rate = (current_price - buy_price) / buy_price

                            # Rich 테이블로 화면 갱신
                            table = self.create_price_table(current_price, buy_price, profit_rate, "REST API")
                            live.update(table)

                            # 목표 수익률 도달 확인
                            if profit_rate >= self.buy_info["target_profit_rate"]:
                                logger.info("🎯 REST API로 목표 수익률 도달 확인!")
                                await self.execute_auto_sell(current_price, profit_rate)
                                break
                        else:
                            logger.warning(f"⚠️ REST API 현재가가 0입니다: {result}")
                    else:
                        logger.error(f"❌ REST API 현재가 조회 실패: {result}")

                except Exception as e:
                    logger.error(f"❌ 현재가 조회 중 오류: {e}")

                # 10초 대기
                await asyncio.sleep(10)

            self.live_display = None

    async def start_monitoring(self):
        """
        자동매매 시작 (Telegram 모니터링)

        Telegram 채널에서 매수 신호를 모니터링하고,
        신호 감지 시 자동으로 매수합니다.
        """
        try:
            # 먼저 계좌 잔고 조회
            trading_info = self.load_today_trading_info()

            # 보유 종목 여부 확인
            has_holdings = trading_info is not None

            if has_holdings:
                if self.target_channel and self.target_channel.strip():
                    logger.info("✅ 보유 종목이 있습니다. 매도 모니터링과 메시지 복사를 시작합니다.")
                else:
                    logger.info("✅ 보유 종목이 있습니다. 매도 모니터링을 시작합니다.")
                logger.info("📊 브라우저 없이 WebSocket 매도 모니터링을 진행합니다.")
                self.order_executed = True

                # 매수 정보 복원
                self.buy_info["stock_code"] = trading_info.get("stock_code")
                self.buy_info["stock_name"] = trading_info.get("stock_name")
                self.buy_info["buy_price"] = trading_info.get("buy_price", 0)
                self.buy_info["quantity"] = trading_info.get("quantity", 0)
                self.buy_info["buy_time"] = trading_info.get("buy_time")

                logger.info("=" * 60)
                logger.info(f"📥 매수 정보 복원 완료")
                logger.info(f"종목명: {self.buy_info['stock_name']}")
                logger.info(f"종목코드: {self.buy_info['stock_code']}")
                logger.info(f"매수가: {self.buy_info['buy_price']:,}원")
                logger.info(f"수량: {self.buy_info['quantity']}주")
                logger.info("=" * 60)

                # WebSocket 실시간 시세 모니터링 시작
                if self.config.enable_sell_monitoring:
                    logger.info(f"📈 WebSocket 매도 모니터링 시작 (목표: {self.buy_info['target_profit_rate']*100:.2f}%)")
                    await self.start_websocket_monitoring()

                    # REST API 폴링 태스크 추가
                    polling_task = asyncio.create_task(self.price_polling_loop())
                else:
                    logger.info("⏸️  매도 모니터링이 비활성화되어 있습니다.")

            # Telegram 클라이언트 시작
            logger.info("=" * 80)
            logger.info("🚀 텔레그램 자동매매 시스템 시작")
            logger.info("=" * 80)

            # 타이밍 측정
            import time
            start_time = time.time()

            # Telegram 클라이언트 시작
            logger.info("⏱️ Telegram 클라이언트 연결 시작...")
            connect_start = time.time()
            await self.telegram_client.start()
            connect_time = time.time() - connect_start
            logger.info(f"✅ Telegram 연결 완료 (소요 시간: {connect_time:.3f}초)")

            # 사용자 정보 조회
            me = await self.telegram_client.get_me()
            logger.info(f"✅ Telegram 로그인: {me.first_name} (@{me.username})")
            logger.info(f"📥 매수 신호 모니터링 채널 (SOURCE_CHANNEL): {self.source_channel}")
            if self.target_channel and self.target_channel.strip():
                logger.info(f"📤 알림 전송 채널 (TARGET_CHANNEL): {self.target_channel}")
            else:
                logger.info("📤 알림 전송 채널 (TARGET_CHANNEL): 비활성화 (메시지 복사 안함)")
            logger.info(f"💰 최대 투자금액: {self.max_investment:,}원")
            logger.info(f"⏰ 매수 가능 시간: {self.config.buy_start_time} ~ {self.config.buy_end_time}")
            logger.info("=" * 80)

            # 채널 엔티티 정보 확인
            logger.info("🔍 SOURCE_CHANNEL 엔티티 정보를 확인합니다...")
            source_entity = None
            try:
                source_entity = await self.telegram_client.get_entity(self.source_channel)
                logger.info(f"📊 채널 정보:")
                logger.info(f"   - 채널명: {getattr(source_entity, 'title', 'N/A')}")
                logger.info(f"   - 채널 ID: {source_entity.id}")
                logger.info(f"   - Username: @{getattr(source_entity, 'username', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ 채널 엔티티 조회 실패: {e}")
                logger.error(f"💡 .env의 SOURCE_CHANNEL 설정을 확인하세요!")
                return

            # 최근 메시지 확인 (로그 확인용)
            logger.info("🔍 채널의 최근 메시지를 확인합니다... (로그 확인용)")
            try:
                messages = await self.telegram_client.get_messages(self.source_channel, limit=5)
                logger.info(f"✅ 메시지 조회 완료 ({len(messages)}개 조회)")

                if messages:
                    logger.info("📋 최근 메시지:")
                    for i, msg in enumerate(messages[:3], 1):
                        if msg.text:
                            kst_time = self.to_kst(msg.date)
                            logger.info(f"   [{i}] {kst_time.strftime('%H:%M:%S')} (KST) - {msg.text[:50]}...")

                logger.info("💡 놓친 메시지는 자동 매수하지 않습니다. 실시간 메시지만 처리합니다.")

            except Exception as e:
                logger.error(f"❌ 최근 메시지 조회 중 오류: {e}")
                logger.info("📡 실시간 모니터링을 계속합니다...")

            # 이벤트 핸들러 등록
            @self.telegram_client.on(events.NewMessage(chats=source_entity))
            async def handler(event):
                await self.handle_telegram_signal(event)

            logger.info(f"✅ 이벤트 핸들러 등록 완료 (채널 ID: {source_entity.id})")

            total_time = time.time() - start_time
            logger.info("=" * 80)
            logger.info(f"⏱️ 초기화 완료! 총 소요 시간: {total_time:.3f}초")
            logger.info("=" * 80)

            logger.info("👀 매수 신호 모니터링 시작... (Ctrl+C로 종료)")
            logger.info("=" * 80)

            # 보유 종목이 있으면 WebSocket과 Telegram을 병렬 실행
            if has_holdings and self.config.enable_sell_monitoring:
                if self.target_channel and self.target_channel.strip():
                    logger.info("🔄 WebSocket 시세 모니터링과 Telegram 메시지 복사를 동시에 실행합니다.")
                else:
                    logger.info("🔄 WebSocket 시세 모니터링과 Telegram 신호 감지를 동시에 실행합니다.")

                try:
                    await asyncio.gather(
                        self.ws_receive_task,
                        self.telegram_client.run_until_disconnected()
                    )
                except asyncio.CancelledError:
                    logger.info("✅ WebSocket 모니터링이 정상 종료되었습니다.")
                    if 'polling_task' in locals():
                        polling_task.cancel()
            else:
                # 보유 종목이 없으면 Telegram만 실행
                await self.telegram_client.run_until_disconnected()

        except Exception as e:
            logger.error(f"오류 발생: {e}")
            raise

        finally:
            await self.cleanup_telegram()

    async def cleanup_telegram(self):
        """Telegram 전용 정리"""
        logger.info("=" * 80)
        logger.info("🔍 종료 전 미체결 주문 확인 중...")

        # 미체결 주문 확인
        outstanding_result = self.kiwoom_api.get_outstanding_orders()

        if outstanding_result.get("success"):
            outstanding_orders = outstanding_result.get("outstanding_orders", [])

            if outstanding_orders:
                logger.warning(f"⚠️ 미체결 주문이 {len(outstanding_orders)}건 존재합니다!")
                logger.warning("⚠️ 시스템을 종료하지 않고 계속 모니터링합니다.")
                return
            else:
                logger.info("✅ 미체결 주문이 없습니다. 안전하게 종료합니다.")
        else:
            logger.warning("⚠️ 미체결 주문 확인 실패. 강제 종료합니다.")

        logger.info("=" * 80)
        logger.info("리소스 정리 중...")

        # 기반 클래스 cleanup 호출
        await self.cleanup()

        # Telegram 클라이언트 종료
        if self.telegram_client and self.telegram_client.is_connected():
            await self.telegram_client.disconnect()
            logger.info("✅ Telegram 클라이언트 종료")

        logger.info("✅ 자동매매 시스템 종료")


async def main():
    """메인 실행 함수"""
    # 설정 로드
    config = TradingConfig.from_env()
    config.validate()

    logger.info(config)

    # 자동매매 시스템 생성
    trading_system = TelegramTradingSystem(config)

    # Telegram 신호 모니터링 및 자동매매 시작
    await trading_system.start_monitoring()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"프로그램 오류: {e}")
