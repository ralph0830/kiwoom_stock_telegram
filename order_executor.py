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

    def __init__(self, api: KiwoomOrderAPI, account_no: str):
        """
        Args:
            api: KiwoomOrderAPI 인스턴스
            account_no: 계좌번호
        """
        self.api = api
        self.account_no = account_no

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
            quantity=quantity,
            account_no=self.account_no
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

    async def execute_limit_buy(
        self,
        stock_code: str,
        stock_name: str,
        quantity: int,
        current_price: int,
        order_price: int
    ) -> dict:
        """
        지정가 매수 주문 실행 (현재가 + 1틱)

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            quantity: 매수 수량
            current_price: 현재가 (로깅용)
            order_price: 주문가 (현재가 + 1틱)

        Returns:
            dict: 주문 결과
                - success: bool
                - order_no: str (성공 시)
                - message: str
                - buy_price: int (주문가, 체결 전 추정값)
                - quantity: int
                - stock_code: str
                - stock_name: str
        """
        logger.info("=" * 80)
        logger.info("🎯 지정가 매수 주문 시작 (한 틱 위)")
        logger.info("=" * 80)
        logger.info(f"종목명: {stock_name}")
        logger.info(f"종목코드: {stock_code}")
        logger.info(f"현재가: {current_price:,}원")
        logger.info(f"주문가: {order_price:,}원 (+{order_price - current_price}원 1틱 위)")
        logger.info(f"주문 수량: {quantity}주")
        logger.info(f"예상 금액: {order_price * quantity:,}원")

        # 지정가 매수 주문
        result = self.api.place_limit_buy_order(
            stock_code=stock_code,
            quantity=quantity,
            price=order_price,
            account_no=self.account_no
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
        logger.info(f"✅ 지정가 매수 주문 성공!")
        logger.info(f"주문번호: {order_no}")

        return {
            "success": True,
            "order_no": order_no,
            "message": "매수 주문 성공",
            "buy_price": order_price,  # 주문가 (추정 매수가)
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
            price=sell_price,
            account_no=self.account_no
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
            quantity=quantity,
            account_no=self.account_no
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

    async def wait_for_buy_execution(
        self,
        stock_code: str,
        order_qty: int,
        order_no: str,
        timeout: int = 30,
        interval: int = 5
    ) -> dict:
        """
        매수 체결 대기 및 확인 (부분 체결 처리 포함)

        Args:
            stock_code: 종목코드
            order_qty: 주문 수량
            order_no: 주문번호
            timeout: 타임아웃 (초)
            interval: 확인 주기 (초)

        Returns:
            dict: 체결 결과
                - status: str ('FULLY_EXECUTED' | 'PARTIALLY_EXECUTED' | 'NOT_EXECUTED')
                - executed_qty: int (실제 체결 수량)
                - remaining_qty: int (미체결 수량)
                - avg_buy_price: int (평균 매입단가, 실제 체결가)
                - success: bool (매도 모니터링 시작 여부)
        """
        elapsed = 0

        logger.info("⏳ 매수 체결 확인 시작")
        logger.info(f"타임아웃: {timeout}초, 주기: {interval}초")

        while elapsed < timeout:
            await asyncio.sleep(interval)
            elapsed += interval

            # ========================================
            # 1. 미체결 주문 조회
            # ========================================
            outstanding = self.api.get_outstanding_orders()

            order_found = False
            rmndr_qty = 0  # 미체결 수량

            if outstanding.get("success"):
                for order in outstanding.get("outstanding_orders", []):
                    if order.get("ord_no") == order_no:
                        order_found = True
                        rmndr_qty = int(order.get("rmndr_qty", 0))
                        logger.debug(f"📋 미체결 주문 확인: 미체결 {rmndr_qty}주")
                        break

            # 미체결 목록에 없으면 100% 체결된 것으로 판단
            if not order_found:
                logger.debug("✅ 미체결 목록에 없음 → 100% 체결 가능성")
                rmndr_qty = 0

            # ========================================
            # 2. 계좌 잔고 조회 (실제 보유 확인)
            # ========================================
            balance = self.api.get_account_balance()

            actual_qty = 0        # 실제 보유 수량
            avg_buy_price = 0     # 평균 매입단가

            if balance.get("success"):
                for holding in balance.get("holdings", []):
                    if holding.get("stk_cd") == stock_code:
                        actual_qty = int(holding.get("rmnd_qty", 0))
                        avg_buy_price = int(holding.get("buy_uv", 0))
                        logger.debug(f"📊 계좌 보유: {actual_qty}주, 평균단가: {avg_buy_price:,}원")
                        break

            # ========================================
            # 3. 체결 상태 판별
            # ========================================

            # 케이스 1: 100% 완전 체결
            if rmndr_qty == 0 and actual_qty >= order_qty:
                logger.info("=" * 80)
                logger.info(f"✅ 매수 100% 체결 완료! ({elapsed}초 소요)")
                logger.info(f"체결 수량: {actual_qty}주")
                logger.info(f"평균 매입단가: {avg_buy_price:,}원")
                logger.info("=" * 80)

                return {
                    'status': 'FULLY_EXECUTED',
                    'executed_qty': actual_qty,
                    'remaining_qty': 0,
                    'avg_buy_price': avg_buy_price,
                    'success': True
                }

            # 케이스 2: 부분 체결 (체결된 수량 > 0 AND 미체결 수량 > 0)
            elif actual_qty > 0 and rmndr_qty > 0:
                execution_rate = (actual_qty / order_qty) * 100

                logger.info("=" * 80)
                logger.warning(f"⚠️ 부분 체결 발생! ({elapsed}초 소요)")
                logger.info(f"주문 수량: {order_qty}주")
                logger.info(f"체결 수량: {actual_qty}주 ({execution_rate:.1f}%)")
                logger.info(f"미체결 수량: {rmndr_qty}주 ({100-execution_rate:.1f}%)")
                logger.info(f"평균 매입단가: {avg_buy_price:,}원")
                logger.info("=" * 80)

                # 미체결 주문 즉시 취소 (안전장치)
                logger.info(f"🔄 미체결 {rmndr_qty}주 주문을 취소합니다...")
                cancel_result = self.api.cancel_order(
                    order_no=order_no,
                    stock_code=stock_code,
                    quantity=rmndr_qty
                )

                if cancel_result.get("success"):
                    logger.info("✅ 미체결 주문 취소 완료")
                else:
                    logger.warning("⚠️ 미체결 주문 취소 실패 (수동 확인 필요)")

                logger.info(f"✅ 부분 체결 수용: {actual_qty}주로 매도 모니터링을 시작합니다")

                return {
                    'status': 'PARTIALLY_EXECUTED',
                    'executed_qty': actual_qty,
                    'remaining_qty': rmndr_qty,
                    'avg_buy_price': avg_buy_price,
                    'success': True  # 부분이라도 체결되었으므로 매도 모니터링 시작
                }

            # 아직 체결 중 (대기 계속)
            logger.info(f"⏳ 체결 대기 중... ({elapsed}/{timeout}초)")

        # ========================================
        # 케이스 3: 타임아웃 - 0% 미체결
        # ========================================
        logger.info("=" * 80)
        logger.warning(f"⚠️ 매수 미체결! (타임아웃: {timeout}초)")
        logger.info(f"주문 수량: {order_qty}주")
        logger.info("체결 수량: 0주")
        logger.info("=" * 80)

        # 미체결 주문 취소
        logger.info("🔄 미체결 주문을 취소합니다...")
        cancel_result = self.api.cancel_order(
            order_no=order_no,
            stock_code=stock_code,
            quantity=order_qty
        )

        if cancel_result.get("success"):
            logger.info("✅ 미체결 주문 취소 완료")
        else:
            logger.warning("⚠️ 미체결 주문 취소 실패 (수동 확인 필요)")

        return {
            'status': 'NOT_EXECUTED',
            'executed_qty': 0,
            'remaining_qty': order_qty,
            'avg_buy_price': 0,
            'success': False
        }

    async def verify_order_filled(
        self,
        order_no: str,
        timeout: int = 30,
        interval: int = 5
    ) -> dict:
        """
        주문 체결 확인 (타임아웃 방식) - 레거시 메서드

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
        safety_margin: float = 0.0
    ) -> int:
        """
        매수 수량 계산

        Args:
            current_price: 현재가
            max_investment: 최대 투자금액
            safety_margin: 안전 마진 (기본 0%, 사용 안 함)

        Returns:
            int: 매수 수량
        """
        if current_price <= 0:
            logger.error(f"❌ 현재가가 0 이하입니다: {current_price}")
            return 0

        # 안전 마진 없음 (최대 투자금액으로 최대한 매수)
        quantity = max_investment // current_price

        logger.info(f"💰 매수 수량 계산:")
        logger.info(f"   최대 투자금액: {max_investment:,}원")
        logger.info(f"   현재가: {current_price:,}원")
        logger.info(f"   매수 수량: {quantity}주")
        logger.info(f"   예상 투자금액: {current_price * quantity:,}원")

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
