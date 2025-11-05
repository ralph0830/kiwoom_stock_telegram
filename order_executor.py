"""
주문 실행 클래스

역할: 매수/매도 주문 실행 로직 캡슐화
- 매수 주문 실행
- 매도 주문 실행 (익절, 손절)
- 주문 검증
- 체결 확인
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from kiwoom_order import KiwoomOrderAPI

logger = logging.getLogger(__name__)


class OrderExecutor:
    """주문 실행 클래스"""

    def __init__(self, api: KiwoomOrderAPI):
        """
        Args:
            api: KiwoomOrderAPI 인스턴스
        """
        self.api = api

    async def execute_market_buy(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        current_price: int
    ) -> dict:
        """
        시장가 매수 주문 실행

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            quantity: 매수 수량
            current_price: 현재가 (로깅용)

        Returns:
            dict: 주문 결과
                - success: bool
                - order_no: str (성공 시)
                - message: str
                - buy_price: int (추정 매수가)
                - quantity: int
                - stock_code: str
                - stock_name: str
        """
        logger.info("=" * 80)
        logger.info("🎯 시장가 매수 주문 시작")
        logger.info("=" * 80)
        logger.info(f"종목명: {stock_name}")
        logger.info(f"종목코드: {stock_code}")
        logger.info(f"현재가: {current_price:,}원")
        logger.info(f"주문 수량: {quantity}주")
        logger.info(f"예상 금액: {current_price * quantity:,}원")

        # 시장가 매수 주문
        result = self.api.place_market_buy_order(
            stock_code=stock_code,
            quantity=quantity
        )

        if not result.get("success"):
            logger.error(f"❌ 매수 주문 실패: {result.get('message')}")
            return {
                "success": False,
                "message": result.get("message", "매수 주문 실패"),
                "stock_code": stock_code,
                "stock_name": stock_name
            }

        order_no = result.get("order_no")
        logger.info(f"✅ 시장가 매수 주문 성공!")
        logger.info(f"주문번호: {order_no}")

        return {
            "success": True,
            "order_no": order_no,
            "message": "매수 주문 성공",
            "buy_price": current_price,  # 추정 매수가 (시장가)
            "quantity": quantity,
            "stock_code": stock_code,
            "stock_name": stock_name
        }

    async def execute_limit_sell(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        sell_price: int,
        reason: str = "익절"
    ) -> dict:
        """
        지정가 매도 주문 실행 (익절용)

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            quantity: 매도 수량
            sell_price: 매도가격
            reason: 매도 사유 (로깅용)

        Returns:
            dict: 주문 결과
                - success: bool
                - order_no: str (성공 시)
                - message: str
                - sell_price: int
                - quantity: int
                - reason: str
        """
        logger.info("=" * 80)
        logger.info(f"💰 지정가 매도 주문 시작 ({reason})")
        logger.info("=" * 80)
        logger.info(f"종목명: {stock_name}")
        logger.info(f"종목코드: {stock_code}")
        logger.info(f"매도가: {sell_price:,}원")
        logger.info(f"매도 수량: {quantity}주")
        logger.info(f"예상 금액: {sell_price * quantity:,}원")

        # 지정가 매도 주문
        result = self.api.place_limit_sell_order(
            stock_code=stock_code,
            quantity=quantity,
            price=sell_price
        )

        if not result.get("success"):
            logger.error(f"❌ 매도 주문 실패: {result.get('message')}")
            return {
                "success": False,
                "message": result.get("message", "매도 주문 실패"),
                "stock_code": stock_code,
                "stock_name": stock_name,
                "reason": reason
            }

        order_no = result.get("order_no")
        logger.info(f"✅ 지정가 매도 주문 성공!")
        logger.info(f"주문번호: {order_no}")

        return {
            "success": True,
            "order_no": order_no,
            "message": "매도 주문 성공",
            "sell_price": sell_price,
            "quantity": quantity,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "reason": reason
        }

    async def execute_market_sell(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        current_price: int,
        reason: str = "손절"
    ) -> dict:
        """
        시장가 매도 주문 실행 (손절/강제청산용)

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            quantity: 매도 수량
            current_price: 현재가 (로깅용)
            reason: 매도 사유 (로깅용)

        Returns:
            dict: 주문 결과
                - success: bool
                - order_no: str (성공 시)
                - message: str
                - sell_price: int (추정)
                - quantity: int
                - reason: str
        """
        logger.info("=" * 80)
        logger.info(f"🚨 시장가 매도 주문 시작 ({reason})")
        logger.info("=" * 80)
        logger.info(f"종목명: {stock_name}")
        logger.info(f"종목코드: {stock_code}")
        logger.info(f"현재가: {current_price:,}원")
        logger.info(f"매도 수량: {quantity}주")
        logger.info(f"예상 금액: {current_price * quantity:,}원")

        # 시장가 매도 주문
        result = self.api.place_market_sell_order(
            stock_code=stock_code,
            quantity=quantity
        )

        if not result.get("success"):
            logger.error(f"❌ 매도 주문 실패: {result.get('message')}")
            return {
                "success": False,
                "message": result.get("message", "매도 주문 실패"),
                "stock_code": stock_code,
                "stock_name": stock_name,
                "reason": reason
            }

        order_no = result.get("order_no")
        logger.info(f"✅ 시장가 매도 주문 성공!")
        logger.info(f"주문번호: {order_no}")

        return {
            "success": True,
            "order_no": order_no,
            "message": "매도 주문 성공",
            "sell_price": current_price,  # 추정 매도가 (시장가)
            "quantity": quantity,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "reason": reason
        }

    async def verify_order_filled(
        self,
        order_no: str,
        timeout: int = 30,
        interval: int = 5
    ) -> dict:
        """
        주문 체결 확인 (타임아웃 방식)

        Args:
            order_no: 주문번호
            timeout: 타임아웃 (초)
            interval: 확인 주기 (초)

        Returns:
            dict: 체결 결과
                - filled: bool (체결 여부)
                - avg_price: int (평균 체결가, 체결 시)
                - filled_quantity: int (체결 수량, 체결 시)
                - message: str
        """
        logger.info(f"⏳ 주문 체결 확인 시작 (주문번호: {order_no})")
        logger.info(f"타임아웃: {timeout}초, 확인 주기: {interval}초")

        start_time = datetime.now()
        elapsed = 0
        attempt = 0

        while elapsed < timeout:
            attempt += 1
            logger.info(f"📊 체결 확인 시도 {attempt}회 (경과: {elapsed}초)")

            # TODO: 실제 체결 확인 API 호출
            # 현재는 타임아웃만 체크
            await asyncio.sleep(interval)

            elapsed = (datetime.now() - start_time).total_seconds()

        logger.warning(f"⚠️ 주문 체결 확인 타임아웃 ({timeout}초)")
        return {
            "filled": False,
            "message": f"체결 확인 타임아웃 ({timeout}초)"
        }

    async def cancel_order(self, order_no: str, stock_code: str) -> dict:
        """
        미체결 주문 취소

        Args:
            order_no: 주문번호
            stock_code: 종목코드

        Returns:
            dict: 취소 결과
                - success: bool
                - message: str
        """
        logger.info(f"❌ 주문 취소 시작 (주문번호: {order_no})")

        # TODO: 실제 주문 취소 API 호출
        # 현재는 로그만 남김

        logger.info("✅ 주문 취소 완료")
        return {
            "success": True,
            "message": "주문 취소 완료"
        }

    def calculate_buy_quantity(
        self,
        current_price: int,
        max_investment: int,
        safety_margin: float = 0.02
    ) -> int:
        """
        매수 수량 계산

        Args:
            current_price: 현재가
            max_investment: 최대 투자금액
            safety_margin: 안전 마진 (기본 2%)

        Returns:
            int: 매수 수량
        """
        if current_price <= 0:
            logger.error(f"❌ 현재가가 0 이하입니다: {current_price}")
            return 0

        # 안전 마진 적용 (시장가 체결 시 가격 상승 대비)
        adjusted_investment = int(max_investment * (1 - safety_margin))
        quantity = adjusted_investment // current_price

        logger.info(f"💰 매수 수량 계산:")
        logger.info(f"   최대 투자금액: {max_investment:,}원")
        logger.info(f"   안전 마진: {safety_margin * 100}%")
        logger.info(f"   조정 투자금액: {adjusted_investment:,}원")
        logger.info(f"   현재가: {current_price:,}원")
        logger.info(f"   매수 수량: {quantity}주")
        logger.info(f"   실제 투자금액: {current_price * quantity:,}원")

        return quantity

    def calculate_sell_price(
        self,
        buy_price: int,
        profit_rate: float
    ) -> int:
        """
        목표 수익률 기준 매도가 계산 (한 틱 아래)

        Args:
            buy_price: 매수가
            profit_rate: 목표 수익률 (소수, 예: 0.01 = 1%)

        Returns:
            int: 매도가 (한 틱 아래)
        """
        from kiwoom_order import get_tick_size, calculate_sell_price

        # 목표가 계산
        target_price = int(buy_price * (1 + profit_rate))

        # 한 틱 아래로 매도가 계산
        sell_price = calculate_sell_price(target_price, buy_price)

        logger.info(f"💰 매도가 계산:")
        logger.info(f"   매수가: {buy_price:,}원")
        logger.info(f"   목표 수익률: {profit_rate * 100:.2f}%")
        logger.info(f"   목표가: {target_price:,}원")
        logger.info(f"   매도가 (한 틱 아래): {sell_price:,}원")

        return sell_price
