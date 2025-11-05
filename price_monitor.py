"""
실시간 시세 모니터링 클래스

역할: WebSocket을 통한 실시간 가격 모니터링
- WebSocket 연결 관리
- 실시간 시세 등록/해지
- 가격 변동 콜백 호출
- REST API 백업 폴링
"""

import asyncio
import logging
from typing import Callable, Optional
from datetime import datetime

from kiwoom_websocket import KiwoomWebSocket
from kiwoom_order import KiwoomOrderAPI

logger = logging.getLogger(__name__)


class PriceMonitor:
    """실시간 시세 모니터링 클래스"""

    def __init__(
        self,
        websocket: KiwoomWebSocket,
        api: KiwoomOrderAPI
    ):
        """
        Args:
            websocket: KiwoomWebSocket 인스턴스
            api: KiwoomOrderAPI 인스턴스 (REST API 백업용)
        """
        self.websocket = websocket
        self.api = api
        self.callbacks = {}  # {stock_code: callback}
        self.monitoring = False
        self.polling_task: Optional[asyncio.Task] = None

    async def start_monitoring(
        self,
        stock_code: str,
        callback: Callable[[str, int, dict], None]
    ):
        """
        실시간 시세 모니터링 시작

        Args:
            stock_code: 종목코드
            callback: 가격 변동 콜백 함수
                Args: (stock_code: str, current_price: int, data: dict)
        """
        logger.info("=" * 80)
        logger.info("📈 실시간 시세 모니터링 시작")
        logger.info("=" * 80)
        logger.info(f"종목코드: {stock_code}")

        # 콜백 함수 등록
        self.callbacks[stock_code] = callback
        self.monitoring = True

        # WebSocket 연결
        try:
            await self.websocket.connect()
            logger.info("✅ WebSocket 연결 성공")
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {e}")
            raise

        # 실시간 시세 등록
        try:
            await self.websocket.register_stock(
                stock_code=stock_code,
                callback=self._handle_price_update
            )
            logger.info(f"✅ 실시간 시세 등록 완료 (종목코드: {stock_code})")
        except Exception as e:
            logger.error(f"❌ 실시간 시세 등록 실패: {e}")
            raise

        logger.info("📊 실시간 시세 수신 대기 중...")

    async def stop_monitoring(self, stock_code: Optional[str] = None):
        """
        실시간 시세 모니터링 중지

        Args:
            stock_code: 종목코드 (None이면 모든 종목)
        """
        logger.info("=" * 80)
        logger.info("⏹️ 실시간 시세 모니터링 중지")
        logger.info("=" * 80)

        self.monitoring = False

        # 폴링 태스크 종료
        if self.polling_task and not self.polling_task.done():
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                logger.info("✅ 폴링 태스크 종료 완료")

        # 실시간 시세 해지
        if stock_code:
            logger.info(f"종목코드: {stock_code}")
            try:
                await self.websocket.unregister_stock(stock_code)
                del self.callbacks[stock_code]
                logger.info(f"✅ 실시간 시세 해지 완료 (종목코드: {stock_code})")
            except Exception as e:
                logger.error(f"❌ 실시간 시세 해지 실패: {e}")
        else:
            logger.info("모든 종목")
            try:
                for code in list(self.callbacks.keys()):
                    await self.websocket.unregister_stock(code)
                self.callbacks.clear()
                logger.info("✅ 모든 실시간 시세 해지 완료")
            except Exception as e:
                logger.error(f"❌ 실시간 시세 해지 실패: {e}")

        # WebSocket 종료
        try:
            await self.websocket.close()
            logger.info("✅ WebSocket 연결 종료 완료")
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 종료 실패: {e}")

    async def _handle_price_update(self, stock_code: str, current_price: int, data: dict):
        """
        실시간 가격 변동 핸들러 (내부용)

        Args:
            stock_code: 종목코드
            current_price: 현재가
            data: 실시간 데이터
        """
        if not self.monitoring:
            return

        # 등록된 콜백 호출
        callback = self.callbacks.get(stock_code)
        if callback:
            try:
                await callback(stock_code, current_price, data)
            except Exception as e:
                logger.error(f"❌ 콜백 함수 실행 중 오류: {e}", exc_info=True)

    async def start_backup_polling(
        self,
        stock_code: str,
        interval: int = 10,
        callback: Optional[Callable[[str, int, dict], None]] = None
    ):
        """
        REST API를 이용한 백업 폴링 시작 (WebSocket 백업용)

        Args:
            stock_code: 종목코드
            interval: 조회 주기 (초)
            callback: 가격 변동 콜백 함수 (None이면 등록된 콜백 사용)
        """
        logger.info("=" * 80)
        logger.info("🔄 REST API 백업 폴링 시작")
        logger.info("=" * 80)
        logger.info(f"종목코드: {stock_code}")
        logger.info(f"조회 주기: {interval}초")

        async def polling_loop():
            """폴링 루프"""
            last_log_time = datetime.now()

            while self.monitoring:
                try:
                    # 현재가 조회
                    result = self.api.get_current_price(stock_code)

                    if result.get("success"):
                        current_price = result.get("price", 0)

                        # 10초마다 한 번만 로그 출력
                        now = datetime.now()
                        if (now - last_log_time).total_seconds() >= 10:
                            logger.info(f"📊 현재가 조회 (REST API): {current_price:,}원")
                            last_log_time = now

                        # 콜백 호출
                        target_callback = callback or self.callbacks.get(stock_code)
                        if target_callback and current_price > 0:
                            await target_callback(stock_code, current_price, {
                                "source": "REST_API",
                                "timestamp": datetime.now().isoformat()
                            })
                    else:
                        logger.error(f"❌ 현재가 조회 실패: {result.get('message')}")

                except Exception as e:
                    logger.error(f"❌ 폴링 중 오류 발생: {e}", exc_info=True)

                # 다음 조회까지 대기
                await asyncio.sleep(interval)

        # 폴링 태스크 시작
        self.polling_task = asyncio.create_task(polling_loop())
        logger.info("✅ 백업 폴링 태스크 시작됨")

    def get_current_price(self, stock_code: str) -> Optional[int]:
        """
        캐시된 현재가 조회 (WebSocket)

        Args:
            stock_code: 종목코드

        Returns:
            int: 현재가 (캐시에 없으면 None)
        """
        return self.websocket.get_current_price(stock_code)

    async def get_current_price_from_api(self, stock_code: str) -> Optional[int]:
        """
        REST API로 현재가 조회 (즉시 조회)

        Args:
            stock_code: 종목코드

        Returns:
            int: 현재가 (실패 시 None)
        """
        result = self.api.get_current_price(stock_code)

        if result.get("success"):
            return result.get("price", 0)
        else:
            logger.error(f"❌ 현재가 조회 실패: {result.get('message')}")
            return None

    @property
    def is_monitoring(self) -> bool:
        """모니터링 중 여부"""
        return self.monitoring

    @property
    def monitored_stocks(self) -> list[str]:
        """모니터링 중인 종목 목록"""
        return list(self.callbacks.keys())

    def __repr__(self) -> str:
        return (
            f"PriceMonitor("
            f"monitoring={self.monitoring}, "
            f"stocks={self.monitored_stocks})"
        )
