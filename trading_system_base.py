"""
자동매매 시스템 기반 클래스

모든 자동매매 시스템의 공통 로직을 포함하는 추상 기반 클래스
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import box

from config import TradingConfig
from kiwoom_order import KiwoomOrderAPI, calculate_sell_price
from kiwoom_websocket import KiwoomWebSocket
from order_executor import OrderExecutor
from price_monitor import PriceMonitor

logger = logging.getLogger(__name__)


class TradingSystemBase(ABC):
    """자동매매 시스템 기반 클래스 (추상)"""

    def __init__(self, config: TradingConfig):
        """
        Args:
            config: 자동매매 설정 (TradingConfig 인스턴스)
        """
        self.config = config

        # 기본 설정
        self.account_no = config.account_no
        self.max_investment = config.max_investment
        self.order_executed = False
        self.sell_executed = False  # 매도 실행 플래그 (중복 방지)
        self.sell_monitoring = False
        self.sell_order_no = None  # 매도 주문번호 저장

        # 매수 정보 저장
        self.buy_info = {
            "stock_code": None,
            "stock_name": None,
            "buy_price": 0,
            "quantity": 0,
            "buy_time": None,  # 매수 시간 (손절 지연용)
            "target_profit_rate": config.target_profit_rate
        }

        # 키움 API 초기화
        self.kiwoom_api = KiwoomOrderAPI()

        # WebSocket 초기화
        self.websocket: Optional[KiwoomWebSocket] = None
        self.ws_receive_task: Optional[asyncio.Task] = None

        # 주문 실행기 초기화 (OrderExecutor 사용)
        self.order_executor = OrderExecutor(self.kiwoom_api)

        # 가격 모니터 초기화 (나중에 WebSocket 설정 후 생성)
        self.price_monitor: Optional[PriceMonitor] = None

        # 결과 저장 디렉토리 생성
        self.result_dir = Path("./trading_results")
        self.result_dir.mkdir(exist_ok=True)

        # 하루 1회 매수 제한 파일
        self.trading_lock_file = Path("./daily_trading_lock.json")

        # Rich Console 초기화
        self.console = Console()
        self.live_display = None  # Live 디스플레이 객체

        # 주기적 계좌 조회 설정
        self._last_balance_check = None  # 마지막 계좌 조회 시간

        # 로깅
        if config.debug_mode:
            logger.info("🐛 DEBUG 모드 활성화: 실시간 시세를 계속 출력합니다")

        if config.enable_stop_loss:
            logger.info(f"🛡️  손절 모니터링 활성화: {config.stop_loss_rate*100:.2f}% 이하 시 시장가 매도")
            if config.stop_loss_delay_minutes > 0:
                logger.info(f"⏱️  손절 지연 설정: 매수 후 {config.stop_loss_delay_minutes}분 이후부터 손절 가능")
            else:
                logger.info("⏱️  손절 지연 없음: 즉시 손절 가능")
        else:
            logger.info("⏸️  손절 모니터링이 비활성화되었습니다")

        if config.enable_daily_force_sell:
            logger.info(f"⏰ 일일 강제 청산 활성화: {config.daily_force_sell_time}에 100% 전량 시장가 매도")
        else:
            logger.info("⏸️  일일 강제 청산이 비활성화되었습니다")

        if config.balance_check_interval > 0:
            logger.info(f"🔄 주기적 평균단가 업데이트: {config.balance_check_interval}초마다 계좌 조회")
        else:
            logger.info("⏸️  주기적 평균단가 업데이트 비활성화")

    # ========================================
    # 추상 메서드 (하위 클래스에서 구현 필수)
    # ========================================

    @abstractmethod
    async def start_monitoring(self):
        """매수 신호 모니터링 (하위 클래스에서 구현)"""
        pass

    # ========================================
    # 매수 및 WebSocket 모니터링
    # ========================================

    async def execute_auto_buy(self, stock_code: str, stock_name: str, current_price: int = None) -> dict | None:
        """
        자동 매수 실행 (시장가 주문)

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            current_price: 현재가 (선택, None이면 API로 조회)

        Returns:
            주문 결과 또는 None
        """
        if not stock_code:
            logger.error("❌ 종목코드를 찾을 수 없습니다.")
            return None

        # 현재가 조회 (제공되지 않은 경우)
        if current_price is None:
            logger.info("📊 현재가 조회 중...")
            price_result = self.kiwoom_api.get_current_price(stock_code)

            if not price_result.get("success"):
                logger.error(f"❌ 현재가 조회 실패: {price_result.get('message')}")
                return None

            current_price = price_result["current_price"]
            logger.info(f"💰 현재가: {current_price:,}원")

        # 매수 수량 계산 (OrderExecutor 사용)
        quantity = self.order_executor.calculate_buy_quantity(
            current_price=current_price,
            max_investment=self.max_investment
        )

        if quantity <= 0:
            logger.error("❌ 매수 가능 수량이 0입니다.")
            return None

        try:
            # Access Token 발급
            self.kiwoom_api.get_access_token()

            # ========================================
            # 매수 타입에 따라 분기 (v1.6.0)
            # ========================================

            if self.config.buy_order_type == "limit_plus_one_tick":
                # ========================================
                # 지정가 매수 (현재가 + 1틱)
                # ========================================
                from kiwoom_order import get_tick_size

                tick_size = get_tick_size(current_price)
                order_price = current_price + tick_size

                logger.info(f"📊 매수 타입: 지정가 (한 틱 위)")
                logger.info(f"   현재가: {current_price:,}원")
                logger.info(f"   틱 크기: {tick_size}원")
                logger.info(f"   주문가: {order_price:,}원")

                # 지정가 매수 주문
                order_result = await self.order_executor.execute_limit_buy(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    quantity=quantity,
                    current_price=current_price,
                    order_price=order_price
                )

                if not order_result.get("success"):
                    return None

                order_no = order_result.get("order_no")

                # 체결 확인 (부분 체결 처리 포함)
                execution_result = await self.order_executor.wait_for_buy_execution(
                    stock_code=stock_code,
                    order_qty=quantity,
                    order_no=order_no,
                    timeout=self.config.buy_execution_timeout,
                    interval=self.config.buy_execution_check_interval
                )

                # ========================================
                # 체결 결과에 따라 처리
                # ========================================

                if execution_result['status'] == 'FULLY_EXECUTED':
                    # 100% 체결 → 정상 완료
                    buy_time = datetime.now()
                    self.buy_info = {
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "buy_price": execution_result['avg_buy_price'],
                        "quantity": execution_result['executed_qty'],
                        "buy_time": buy_time,
                        "target_profit_rate": self.buy_info["target_profit_rate"],
                        "is_verified": True  # 계좌 조회로 확인된 값
                    }

                    result_data = {
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "current_price": current_price,
                        "quantity": execution_result['executed_qty']
                    }
                    await self.save_trading_result(result_data, order_result)
                    logger.info("✅ 지정가 매수 완료!")
                    return order_result

                elif execution_result['status'] == 'PARTIALLY_EXECUTED':
                    # 부분 체결 → 체결분만 수용
                    buy_time = datetime.now()
                    self.buy_info = {
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "buy_price": execution_result['avg_buy_price'],
                        "quantity": execution_result['executed_qty'],  # 실제 체결 수량만
                        "buy_time": buy_time,
                        "target_profit_rate": self.buy_info["target_profit_rate"],
                        "is_verified": True,
                        "buy_order_no": order_no  # 미체결 주문 취소용
                    }

                    result_data = {
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "current_price": current_price,
                        "quantity": execution_result['executed_qty']
                    }
                    await self.save_trading_result(result_data, order_result)
                    logger.info("✅ 부분 체결 매수 완료!")
                    logger.info(f"⚠️ 미체결 매수 주문이 남아있습니다 (주문번호: {order_no})")
                    logger.info("💡 익절 완료 시 미체결 주문이 자동으로 취소됩니다")
                    return order_result

                else:  # NOT_EXECUTED
                    # 0% 미체결 → 폴백 전략
                    if self.config.buy_fallback_to_market:
                        logger.warning("⚠️ 지정가 미체결 → 시장가로 재주문합니다")
                        # 시장가로 폴백 (재귀 호출)
                        original_type = self.config.buy_order_type
                        self.config.buy_order_type = "market"  # 임시로 시장가로 변경
                        result = await self.execute_auto_buy(stock_code, stock_name, current_price)
                        self.config.buy_order_type = original_type  # 원복
                        return result
                    else:
                        logger.error("❌ 지정가 미체결 → 매수를 포기합니다")
                        return None

            else:  # market (기본값)
                # ========================================
                # 시장가 매수 (기존 로직 유지)
                # ========================================
                logger.info("📊 매수 타입: 시장가 (즉시 체결)")

                order_result = await self.order_executor.execute_market_buy(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    quantity=quantity,
                    current_price=current_price
                )

                if not order_result.get("success"):
                    return None

                # 매수 정보 저장
                buy_time = datetime.now()
                self.buy_info = {
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "buy_price": current_price,  # 추정값
                    "quantity": quantity,
                    "buy_time": buy_time,
                    "target_profit_rate": self.buy_info["target_profit_rate"],
                    "is_verified": not self.config.enable_lazy_verification
                }

                # 결과 저장
                result_data = {
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "current_price": current_price,
                    "quantity": quantity
                }
                await self.save_trading_result(result_data, order_result)

                logger.info("✅ 시장가 매수 완료!")

                if self.config.enable_lazy_verification:
                    logger.info("⚡ 즉시 매도 모니터링을 시작합니다 (추정 매수가 기준)")
                    logger.info("   첫 번째 실시간 시세 수신 시 실제 체결 정보를 자동으로 확인합니다")
                else:
                    logger.info("📝 추정 매수가로 매도 모니터링을 시작합니다")

                return order_result

        except Exception as e:
            logger.error(f"❌ 매수 주문 실행 중 오류: {e}")
            return None

    async def start_websocket_monitoring(self):
        """WebSocket 실시간 시세 모니터링 시작"""
        try:
            # WebSocket 생성 및 연결
            self.websocket = KiwoomWebSocket(
                self.kiwoom_api,
                debug_mode=self.config.debug_mode
            )
            await self.websocket.connect()

            # 실시간 시세 등록
            await self.websocket.register_stock(
                self.buy_info["stock_code"],
                self.on_price_update
            )

            # 실시간 수신 태스크 시작
            self.ws_receive_task = asyncio.create_task(self.websocket.receive_loop())

            logger.info(f"✅ 실시간 시세 모니터링 시작: {self.buy_info['stock_name']} ({self.buy_info['stock_code']})")

        except Exception as e:
            logger.error(f"❌ WebSocket 모니터링 시작 실패: {e}")

    # ========================================
    # 일일 매수 제한 관리
    # ========================================

    def check_today_trading_done(self) -> bool:
        """
        오늘 이미 매수했는지 확인

        Returns:
            True: 오늘 이미 매수함, False: 매수 안 함
        """
        if not self.trading_lock_file.exists():
            return False

        try:
            with open(self.trading_lock_file, 'r', encoding='utf-8') as f:
                lock_data = json.load(f)

            last_trading_date = lock_data.get("last_trading_date")
            today = datetime.now().strftime("%Y%m%d")

            if last_trading_date == today:
                logger.info(f"⏹️  오늘({today}) 이미 매수를 실행했습니다.")
                logger.info(f"📝 매수 정보: {lock_data.get('stock_name')} ({lock_data.get('stock_code')})")
                logger.info(f"⏰ 매수 시각: {lock_data.get('trading_time')}")
                return True

            return False

        except Exception as e:
            logger.error(f"매수 이력 확인 중 오류: {e}")
            return False

    def record_today_trading(
        self,
        stock_code: str,
        stock_name: str,
        buy_price: int,
        quantity: int,
        buy_time: datetime = None
    ):
        """
        오늘 매수 기록 저장

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            buy_price: 매수가
            quantity: 매수 수량
            buy_time: 매수 시간 (선택적, 자동 매수만 전달)
        """
        try:
            lock_data = {
                "last_trading_date": datetime.now().strftime("%Y%m%d"),
                "stock_code": stock_code,
                "stock_name": stock_name,
                "buy_price": buy_price,
                "quantity": quantity
            }

            # buy_time이 있을 때만 trading_time 필드 추가 (자동 매수만)
            if buy_time is not None:
                lock_data["trading_time"] = buy_time.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"✅ 오늘 매수 기록 저장 완료 (매수 시간: {lock_data['trading_time']})")
            else:
                logger.info(f"✅ 오늘 매수 기록 저장 완료 (수동 매수 - 손절 지연 없음)")

            with open(self.trading_lock_file, 'w', encoding='utf-8') as f:
                json.dump(lock_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"매수 기록 저장 중 오류: {e}")

    def load_today_trading_info(self) -> dict | None:
        """
        오늘 매수 정보 로드 (실제 계좌 잔고 조회)

        Returns:
            실제 계좌의 보유 종목 정보 또는 None
        """
        try:
            # 실제 계좌 잔고 조회
            logger.info("📊 실제 계좌 잔고 조회 중...")
            balance_result = self.kiwoom_api.get_account_balance()

            if not balance_result.get("success"):
                logger.warning("⚠️ 계좌 잔고 조회 실패")
                return None

            holdings = balance_result.get("holdings", [])

            if not holdings:
                logger.info("ℹ️ 보유 종목이 없습니다.")
                return None

            # 첫 번째 보유 종목 반환 (자동매매 시스템은 1종목만 관리)
            first_holding = holdings[0]

            trading_info = {
                "stock_code": first_holding.get("stk_cd", ""),
                "stock_name": first_holding.get("stk_nm", ""),
                "buy_price": int(first_holding.get("buy_uv", 0)),
                "quantity": int(first_holding.get("rmnd_qty", 0)),  # 보유수량
                "current_price": int(first_holding.get("cur_prc", 0)),  # 현재가
                "buy_time": None  # 기본값
            }

            # daily_trading_lock.json에서 매수 시간 로드 시도
            if self.trading_lock_file.exists():
                try:
                    with open(self.trading_lock_file, 'r', encoding='utf-8') as f:
                        lock_data = json.load(f)

                    # 날짜가 오늘인지 확인
                    if lock_data.get("last_trading_date") == datetime.now().strftime("%Y%m%d"):
                        # trading_time이 있으면 파싱
                        trading_time_str = lock_data.get("trading_time")
                        if trading_time_str:
                            trading_info["buy_time"] = datetime.strptime(trading_time_str, "%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    logger.warning(f"⚠️ daily_trading_lock.json에서 매수 시간 로드 실패: {e}")

            logger.info("=" * 80)
            logger.info("📥 실제 계좌 보유 종목 확인")
            logger.info(f"   종목명: {trading_info['stock_name']}")
            logger.info(f"   종목코드: {trading_info['stock_code']}")
            logger.info(f"   매입단가: {trading_info['buy_price']:,}원")
            logger.info(f"   보유수량: {trading_info['quantity']}주")
            if trading_info['buy_time']:
                logger.info(f"   매수 시간: {trading_info['buy_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 80)

            return trading_info

        except Exception as e:
            logger.error(f"매수 정보 로드 중 오류: {e}")
            return None

    # ========================================
    # 실시간 시세 모니터링
    # ========================================

    async def on_price_update(self, stock_code: str, current_price: int, data: dict):
        """
        실시간 시세 업데이트 콜백 함수

        Args:
            stock_code: 종목코드
            current_price: 현재가
            data: 전체 실시간 데이터
        """
        if current_price <= 0:
            return

        # Lazy Verification: 첫 시세 수신 시 실제 체결 정보 확인
        if self.config.enable_lazy_verification and not self.buy_info.get("is_verified", False):
            logger.info("🔄 실제 체결 정보를 확인합니다...")

            try:
                balance_result = self.kiwoom_api.get_account_balance()

                if balance_result.get("success"):
                    holdings = balance_result.get("holdings", [])

                    # 해당 종목 찾기
                    for holding in holdings:
                        if holding.get("stk_cd") == stock_code:
                            actual_price = int(holding.get("buy_uv") or 0)  # 평균 매입단가
                            actual_quantity = int(holding.get("rmnd_qty") or 0)  # 보유 수량

                            if actual_price > 0 and actual_quantity > 0:
                                # 추정값과 비교
                                price_diff = actual_price - self.buy_info["buy_price"]
                                quantity_diff = actual_quantity - self.buy_info["quantity"]

                                # 실제 체결 정보로 업데이트
                                self.buy_info["buy_price"] = actual_price
                                self.buy_info["quantity"] = actual_quantity
                                self.buy_info["is_verified"] = True

                                # 파일에도 실제값 저장
                                self.record_today_trading(
                                    stock_code=stock_code,
                                    stock_name=self.buy_info["stock_name"],
                                    buy_price=actual_price,
                                    quantity=actual_quantity,
                                    buy_time=self.buy_info.get("buy_time")
                                )

                                logger.info("✅ 실제 체결 정보 확인 완료!")
                                logger.info(f"   실제 평균 매입단가: {actual_price:,}원 (예상 대비 {price_diff:+,}원)")
                                logger.info(f"   실제 체결 수량: {actual_quantity:,}주 (예상 대비 {quantity_diff:+,}주)")
                                logger.info(f"   실제 투자금액: {actual_price * actual_quantity:,}원")
                            break
                    else:
                        logger.warning("⚠️ 계좌에서 해당 종목을 찾을 수 없습니다. 추정값으로 계속 진행합니다.")
                        self.buy_info["is_verified"] = True  # 재시도 방지
                else:
                    logger.warning("⚠️ 계좌 조회 실패! 추정값으로 계속 진행합니다.")
                    self.buy_info["is_verified"] = True  # 재시도 방지

            except Exception as e:
                logger.error(f"❌ 체결 정보 확인 중 오류: {e}")
                self.buy_info["is_verified"] = True  # 실패 시에도 플래그 설정

        buy_price = self.buy_info["buy_price"]
        if buy_price <= 0:
            return

        # 주기적 계좌 조회 (수동 매수 대응)
        if self.config.balance_check_interval > 0:
            now = datetime.now()
            should_check_balance = (
                self._last_balance_check is None or
                (now - self._last_balance_check).total_seconds() >= self.config.balance_check_interval
            )

            if should_check_balance:
                try:
                    balance_result = self.kiwoom_api.get_account_balance()

                    if balance_result.get("success"):
                        holdings = balance_result.get("holdings", [])

                        for holding in holdings:
                            if holding.get("stk_cd") == stock_code:
                                actual_buy_price = int(holding.get("buy_uv") or 0)
                                actual_quantity = int(holding.get("rmnd_qty") or 0)

                                # 평균 매입단가 또는 수량 변경 감지
                                if actual_buy_price > 0 and (
                                    actual_buy_price != self.buy_info["buy_price"] or
                                    actual_quantity != self.buy_info["quantity"]
                                ):
                                    old_price = self.buy_info["buy_price"]
                                    old_quantity = self.buy_info["quantity"]

                                    # 업데이트
                                    self.buy_info["buy_price"] = actual_buy_price
                                    self.buy_info["quantity"] = actual_quantity

                                    # 파일에도 저장
                                    self.record_today_trading(
                                        stock_code=stock_code,
                                        stock_name=self.buy_info["stock_name"],
                                        buy_price=actual_buy_price,
                                        quantity=actual_quantity,
                                        buy_time=self.buy_info.get("buy_time")
                                    )

                                    logger.warning("=" * 80)
                                    logger.warning("🔄 수동 매수 감지! 평균 매입단가 업데이트")
                                    logger.warning(f"   평균 매입단가: {old_price:,}원 → {actual_buy_price:,}원")
                                    logger.warning(f"   보유 수량: {old_quantity:,}주 → {actual_quantity:,}주")
                                    logger.warning("=" * 80)

                                    # buy_price 재설정
                                    buy_price = actual_buy_price
                                break

                    self._last_balance_check = now

                except Exception as e:
                    logger.error(f"❌ 주기적 계좌 조회 중 오류: {e}")
                    self._last_balance_check = now

        # 현재 수익률 계산
        profit_rate = (current_price - buy_price) / buy_price

        # DEBUG 모드일 때만 실시간 시세 출력
        if self.config.debug_mode:
            if not hasattr(self, '_last_profit_log') or \
               (datetime.now() - self._last_profit_log).total_seconds() >= 1:
                if self.live_display:
                    table = self.create_price_table(current_price, buy_price, profit_rate, "WebSocket")
                    self.live_display.update(table)

                self._last_profit_log = datetime.now()

        # 강제 청산 시간 체크 (최우선)
        if self.config.enable_daily_force_sell and self.is_force_sell_time() and not self.sell_executed:
            await self.execute_daily_force_sell()
            return

        # 손절 조건 체크 (손절이 목표 수익률보다 우선)
        if self.config.enable_stop_loss and profit_rate <= self.config.stop_loss_rate and not self.sell_executed:
            # 매수 후 경과 시간 체크 (손절 지연 설정)
            buy_time = self.buy_info.get("buy_time")
            if buy_time and self.config.stop_loss_delay_minutes > 0:
                elapsed_minutes = (datetime.now() - buy_time).total_seconds() / 60
                if elapsed_minutes < self.config.stop_loss_delay_minutes:
                    if self.config.debug_mode:
                        logger.debug(f"⏱️  손절 지연: 매수 후 {elapsed_minutes:.1f}분 경과")
                    return

            # 캐시된 평균단가로 즉시 손절 실행
            await self.execute_stop_loss(current_price, profit_rate)
            return

        # 목표 수익률 도달 확인
        if profit_rate >= self.buy_info["target_profit_rate"] and not self.sell_executed:
            await self.execute_auto_sell(current_price, profit_rate)

    # ========================================
    # 자동 매도 (익절)
    # ========================================

    async def execute_auto_sell(self, current_price: int, profit_rate: float):
        """자동 매도 실행 (100% 전량 매도)"""
        # 중복 매도 방지
        if self.sell_executed:
            logger.warning("⚠️ 이미 매도 주문을 실행했습니다. 중복 실행 방지")
            return

        self.sell_executed = True  # 즉시 플래그 설정

        logger.info("=" * 60)
        logger.info(f"🎯 목표 수익률 {self.buy_info['target_profit_rate']*100:.2f}% 도달! 자동 매도를 시작합니다")
        logger.info(f"매수가: {self.buy_info['buy_price']:,}원")
        logger.info(f"현재가: {current_price:,}원")
        logger.info(f"수익률: {profit_rate*100:.2f}%")
        logger.info("=" * 60)

        # 캐시된 보유 정보 사용
        actual_quantity = self.buy_info["quantity"]
        actual_buy_price = self.buy_info["buy_price"]

        logger.info(f"💰 매도 수량: {actual_quantity}주 (캐시 기반 100% 전량)")
        logger.info(f"💰 평균 매입단가: {actual_buy_price:,}원 (캐시 기반)")

        if actual_quantity <= 0:
            logger.error("❌ 매도할 수량이 0입니다. 매도를 중단합니다.")
            return

        # 매도가 계산 (목표 수익률 기준, OrderExecutor 사용)
        sell_price = self.order_executor.calculate_sell_price(
            buy_price=actual_buy_price,
            profit_rate=profit_rate
        )

        try:
            # 지정가 매도 주문 (OrderExecutor 사용)
            sell_result = await self.order_executor.execute_limit_sell(
                stock_code=self.buy_info["stock_code"],
                stock_name=self.buy_info["stock_name"],
                quantity=actual_quantity,
                sell_price=sell_price,
                reason="익절"
            )

            if sell_result and sell_result.get("success"):
                # 주문번호 저장
                self.sell_order_no = sell_result.get("order_no")
                logger.info(f"✅ 지정가 매도 주문 접수! 주문번호: {self.sell_order_no}")
                logger.info(f"⏳ 체결 확인 중... (최대 {self.config.outstanding_check_timeout}초 대기)")

                # 체결 확인 대기
                is_executed = await self.wait_for_sell_execution(
                    order_no=self.sell_order_no,
                    current_price=current_price,
                    profit_rate=profit_rate,
                    actual_quantity=actual_quantity,
                    actual_buy_price=actual_buy_price
                )

                if is_executed:
                    logger.info("✅ 자동 매도 완료!")

                    # WebSocket 모니터링 중지
                    if self.websocket:
                        await self.websocket.unregister_stock(self.buy_info["stock_code"])
                        if self.ws_receive_task:
                            self.ws_receive_task.cancel()

                    # 매도 결과 저장
                    await self.save_sell_result_ws(
                        current_price, sell_result, profit_rate, actual_quantity, actual_buy_price
                    )
                else:
                    # 미체결 시 처리
                    await self.handle_outstanding_order(
                        order_no=self.sell_order_no,
                        stock_code=self.buy_info["stock_code"],
                        quantity=actual_quantity
                    )
            else:
                logger.error("❌ 자동 매도 실패")
                self.sell_executed = False

        except Exception as e:
            logger.error(f"❌ 매도 주문 실행 중 오류: {e}")
            self.sell_executed = False

    async def wait_for_sell_execution(
        self,
        order_no: str,
        current_price: int,
        profit_rate: float,
        actual_quantity: int,
        actual_buy_price: int
    ) -> bool:
        """
        매도 주문 체결 대기 및 확인

        Returns:
            체결 완료 여부
        """
        elapsed_time = 0
        check_count = 0

        while elapsed_time < self.config.outstanding_check_timeout:
            await asyncio.sleep(self.config.outstanding_check_interval)
            elapsed_time += self.config.outstanding_check_interval
            check_count += 1

            logger.info(f"🔍 체결 확인 {check_count}회차 (경과: {elapsed_time}초/{self.config.outstanding_check_timeout}초)")

            # 체결 여부 확인
            execution_result = self.kiwoom_api.check_order_execution(order_no)

            if not execution_result.get("success"):
                logger.warning(f"⚠️ 체결 확인 실패: {execution_result.get('message', '알 수 없는 오류')}")
                continue

            if execution_result.get("is_executed"):
                logger.info(f"✅ 매도 주문 체결 완료! (소요 시간: {elapsed_time}초)")
                return True
            else:
                remaining_qty = execution_result.get("remaining_qty", 0)
                logger.info(f"⏳ 아직 미체결 상태입니다 (미체결 수량: {remaining_qty}주)")

        # 타임아웃
        logger.warning(f"⚠️ 체결 확인 타임아웃 ({self.config.outstanding_check_timeout}초 경과)")
        return False

    async def handle_outstanding_order(
        self,
        order_no: str,
        stock_code: str,
        quantity: int
    ):
        """미체결 주문 처리 (취소 또는 유지)"""
        logger.info("=" * 80)
        logger.info("⚠️ 매도 주문이 체결되지 않았습니다!")
        logger.info(f"주문번호: {order_no}")
        logger.info(f"종목코드: {stock_code}")
        logger.info(f"주문수량: {quantity}주")

        if self.config.cancel_outstanding_on_failure:
            logger.info("🔄 미체결 주문 취소 후 재모니터링을 시작합니다...")

            # 주문 취소
            cancel_result = self.kiwoom_api.cancel_order(
                order_no=order_no,
                stock_code=stock_code,
                quantity=quantity
            )

            if cancel_result.get("success"):
                logger.info("✅ 미체결 주문 취소 완료!")
                logger.info("📈 실시간 시세 모니터링을 계속합니다...")

                # 플래그 해제
                self.sell_executed = False
                self.sell_order_no = None
            else:
                logger.error(f"❌ 주문 취소 실패: {cancel_result.get('message', '알 수 없는 오류')}")
                logger.info("📈 주문은 유지되며, 실시간 시세 모니터링을 계속합니다...")
        else:
            logger.info("📌 미체결 주문을 유지하고 실시간 시세 모니터링을 계속합니다...")

        logger.info("=" * 80)

    # ========================================
    # 손절 매도
    # ========================================

    async def execute_stop_loss(self, current_price: int, profit_rate: float):
        """손절 실행 (시장가 즉시 매도)"""
        # 중복 매도 방지
        if self.sell_executed:
            logger.warning("⚠️ 이미 매도 주문을 실행했습니다. 중복 실행 방지")
            return

        self.sell_executed = True  # 즉시 플래그 설정

        logger.info("=" * 60)
        logger.info(f"🚨 손절 조건 도달! ({self.config.stop_loss_rate*100:.2f}% 이하)")
        logger.info(f"매수가: {self.buy_info['buy_price']:,}원")
        logger.info(f"현재가: {current_price:,}원")
        logger.info(f"손실률: {profit_rate*100:.2f}%")
        logger.info("=" * 60)

        # 캐시된 보유 정보 사용
        actual_quantity = self.buy_info["quantity"]
        actual_buy_price = self.buy_info["buy_price"]

        logger.info(f"💰 손절 수량: {actual_quantity}주 (캐시 기반 100% 전량)")
        logger.info(f"💰 평균 매입단가: {actual_buy_price:,}원 (캐시 기반)")

        if actual_quantity <= 0:
            logger.error("❌ 매도할 수량이 0입니다. 손절을 중단합니다.")
            return

        try:
            # 시장가 매도 주문 (OrderExecutor 사용)
            sell_result = await self.order_executor.execute_market_sell(
                stock_code=self.buy_info["stock_code"],
                stock_name=self.buy_info["stock_name"],
                quantity=actual_quantity,
                current_price=current_price,
                reason="손절"
            )

            if sell_result and sell_result.get("success"):
                logger.info("✅ 손절 매도 완료!")

                # WebSocket 모니터링 중지
                if self.websocket:
                    await self.websocket.unregister_stock(self.buy_info["stock_code"])
                    if self.ws_receive_task:
                        self.ws_receive_task.cancel()

                # 손절 결과 저장
                await self.save_stop_loss_result(
                    current_price, sell_result, profit_rate, actual_quantity, actual_buy_price
                )
            else:
                logger.error("❌ 손절 매도 실패")

        except Exception as e:
            logger.error(f"❌ 손절 주문 실행 중 오류: {e}")

    # ========================================
    # 일일 강제 청산
    # ========================================

    async def execute_daily_force_sell(self):
        """일일 강제 청산 실행 (100% 전량 시장가 매도)"""
        # 중복 매도 방지
        if self.sell_executed:
            logger.warning("⚠️ 이미 매도 주문을 실행했습니다. 중복 실행 방지")
            return

        self.sell_executed = True

        logger.info("=" * 80)
        logger.info(f"⏰ 강제 청산 시간 도달! ({self.config.daily_force_sell_time})")
        logger.info(f"💰 보유 종목을 100% 전량 시장가 매도합니다")
        logger.info("=" * 80)

        # 미체결 주문 확인 및 취소
        logger.info("🔍 강제 청산 전 미체결 주문 확인 중...")
        outstanding_result = self.kiwoom_api.get_outstanding_orders()

        if outstanding_result.get("success"):
            outstanding_orders = outstanding_result.get("outstanding_orders", [])

            if outstanding_orders:
                logger.warning(f"⚠️ 미체결 주문 {len(outstanding_orders)}건 발견!")
                logger.info("🔄 강제 청산을 위해 모든 미체결 주문을 취소합니다...")

                for order in outstanding_orders:
                    order_no = order.get("ord_no", "")
                    stock_code = order.get("stk_cd", "")
                    remaining_qty = int(order.get("rmnd_qty", order.get("ord_qty", "0")))

                    logger.info(f"  ❌ 미체결 주문 취소 중: 주문번호={order_no}, 종목={stock_code}, 수량={remaining_qty}주")

                    cancel_result = self.kiwoom_api.cancel_order(
                        order_no=order_no,
                        stock_code=stock_code,
                        quantity=remaining_qty
                    )

                    if cancel_result.get("success"):
                        logger.info(f"  ✅ 주문 취소 완료: {order_no}")
                    else:
                        logger.error(f"  ❌ 주문 취소 실패: {order_no}")

                logger.info("✅ 미체결 주문 취소 처리 완료")
            else:
                logger.info("✅ 미체결 주문이 없습니다")
        else:
            logger.warning("⚠️ 미체결 주문 확인 실패. 강제 청산을 계속 진행합니다.")

        logger.info("=" * 80)

        # 캐시된 보유 정보 사용
        actual_quantity = self.buy_info["quantity"]
        actual_buy_price = self.buy_info["buy_price"]

        logger.info(f"💰 강제 청산 수량: {actual_quantity}주 (캐시 기반 100% 전량)")
        logger.info(f"💰 평균 매입단가: {actual_buy_price:,}원 (캐시 기반)")

        try:
            # 시장가 매도 주문 (OrderExecutor 사용)
            sell_result = await self.order_executor.execute_market_sell(
                stock_code=self.buy_info["stock_code"],
                stock_name=self.buy_info["stock_name"],
                quantity=actual_quantity,
                current_price=0,  # 강제 청산 시 정확한 가격은 나중에 조회
                reason="강제청산"
            )

            if sell_result and sell_result.get("success"):
                logger.info("✅ 강제 청산 완료!")

                # WebSocket 모니터링 중지
                if self.websocket:
                    await self.websocket.unregister_stock(self.buy_info["stock_code"])
                    if self.ws_receive_task:
                        self.ws_receive_task.cancel()

                # 현재가 조회 (수익률 계산용)
                current_price = 0
                price_result = self.kiwoom_api.get_current_price(self.buy_info["stock_code"])
                if price_result.get("success"):
                    current_price = price_result.get("current_price", 0)

                profit_rate = 0
                if actual_buy_price > 0 and current_price > 0:
                    profit_rate = (current_price - actual_buy_price) / actual_buy_price

                # 강제 청산 결과 저장
                await self.save_force_sell_result(
                    current_price, sell_result, profit_rate, actual_quantity, actual_buy_price
                )
            else:
                logger.error("❌ 강제 청산 실패")

        except Exception as e:
            logger.error(f"❌ 강제 청산 주문 실행 중 오류: {e}")

    # ========================================
    # 결과 저장
    # ========================================

    async def save_trading_result(self, stock_data: dict, order_result: dict):
        """매매 결과 저장 (매수)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stock_name = stock_data.get("stock_name", "unknown").replace("/", "_")

        result = {
            "timestamp": timestamp,
            "action": "BUY",
            "stock_info": stock_data,
            "order_result": order_result,
            "source": "Auto Trading System"
        }

        filename = self.result_dir / f"{timestamp}_{stock_name}_매수결과.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 매수 결과 저장: {filename}")

    async def save_sell_result_ws(
        self,
        current_price: int,
        order_result: dict,
        profit_rate: float,
        actual_quantity: int = None,
        actual_buy_price: int = None
    ):
        """매도 결과 저장 (WebSocket 기반)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stock_name = self.buy_info["stock_name"].replace("/", "_")

        sell_quantity = actual_quantity if actual_quantity is not None else self.buy_info["quantity"]
        avg_buy_price = actual_buy_price if actual_buy_price is not None else self.buy_info["buy_price"]

        result = {
            "timestamp": timestamp,
            "action": "SELL",
            "buy_info": self.buy_info,
            "actual_avg_buy_price": avg_buy_price,
            "sell_quantity": sell_quantity,
            "current_price": current_price,
            "profit_rate": f"{profit_rate*100:.2f}%",
            "order_result": order_result,
            "source": "WebSocket 실시간 시세"
        }

        filename = self.result_dir / f"{timestamp}_{stock_name}_매도결과.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 매도 결과 저장: {filename}")

    async def save_stop_loss_result(
        self,
        current_price: int,
        order_result: dict,
        profit_rate: float,
        actual_quantity: int = None,
        actual_buy_price: int = None
    ):
        """손절 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stock_name = self.buy_info["stock_name"].replace("/", "_")

        sell_quantity = actual_quantity if actual_quantity is not None else self.buy_info["quantity"]
        avg_buy_price = actual_buy_price if actual_buy_price is not None else self.buy_info["buy_price"]

        result = {
            "timestamp": timestamp,
            "action": "STOP_LOSS",
            "buy_info": self.buy_info,
            "actual_avg_buy_price": avg_buy_price,
            "sell_quantity": sell_quantity,
            "current_price": current_price,
            "profit_rate": f"{profit_rate*100:.2f}%",
            "stop_loss_rate": f"{self.config.stop_loss_rate*100:.2f}%",
            "order_result": order_result,
            "source": "WebSocket 실시간 시세 (손절)"
        }

        filename = self.result_dir / f"{timestamp}_{stock_name}_손절결과.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 손절 결과 저장: {filename}")

    async def save_force_sell_result(
        self,
        current_price: int,
        order_result: dict,
        profit_rate: float,
        actual_quantity: int = None,
        actual_buy_price: int = None
    ):
        """강제 청산 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stock_name = self.buy_info["stock_name"].replace("/", "_")

        sell_quantity = actual_quantity if actual_quantity is not None else self.buy_info["quantity"]
        avg_buy_price = actual_buy_price if actual_buy_price is not None else self.buy_info["buy_price"]

        result = {
            "timestamp": timestamp,
            "action": "DAILY_FORCE_SELL",
            "buy_info": self.buy_info,
            "actual_avg_buy_price": avg_buy_price,
            "sell_quantity": sell_quantity,
            "current_price": current_price,
            "profit_rate": f"{profit_rate*100:.2f}%",
            "force_sell_time": self.config.daily_force_sell_time,
            "order_result": order_result,
            "source": "일일 강제 청산"
        }

        filename = self.result_dir / f"{timestamp}_{stock_name}_강제청산결과.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 강제 청산 결과 저장: {filename}")

    # ========================================
    # 유틸리티 메서드
    # ========================================

    def is_buy_time_allowed(self) -> bool:
        """
        매수 가능 시간인지 확인

        Returns:
            True: 매수 가능 시간, False: 매수 불가 시간
        """
        from datetime import datetime as dt

        now = datetime.now()
        current_time_str = now.strftime("%H:%M")

        try:
            current_time = dt.strptime(current_time_str, "%H:%M").time()
            start_time = dt.strptime(self.config.buy_start_time, "%H:%M").time()
            end_time = dt.strptime(self.config.buy_end_time, "%H:%M").time()

            return start_time <= current_time < end_time
        except ValueError as e:
            logger.error(f"❌ 시간 형식 오류: {e}")
            return False

    def is_force_sell_time(self) -> bool:
        """
        강제 청산 시간인지 확인

        Returns:
            True: 강제 청산 시간 도달, False: 아직 도달 안함
        """
        from datetime import datetime as dt

        now = datetime.now()
        current_time_str = now.strftime("%H:%M")

        try:
            current_time = dt.strptime(current_time_str, "%H:%M").time()
            force_sell_time = dt.strptime(self.config.daily_force_sell_time, "%H:%M").time()

            return current_time >= force_sell_time
        except ValueError as e:
            logger.error(f"❌ 강제 청산 시간 형식 오류: {e}")
            return False

    def create_price_table(
        self,
        current_price: int,
        buy_price: int,
        profit_rate: float,
        source: str = "REST API"
    ) -> Table:
        """실시간 시세 정보 테이블 생성"""
        table = Table(title=f"📊 실시간 시세 정보 ({source})", box=box.ROUNDED, show_header=False)
        table.add_column("항목", style="cyan", width=15)
        table.add_column("값", style="white")

        # 수익률에 따른 색상 결정
        profit_color = "red" if profit_rate >= 0 else "blue"
        profit_sign = "+" if profit_rate >= 0 else ""

        table.add_row("종목명", self.buy_info['stock_name'])
        table.add_row("종목코드", self.buy_info['stock_code'])
        table.add_row("평균 매수가", f"{buy_price:,}원")
        table.add_row("현재가", f"{current_price:,}원")
        table.add_row(
            "수익률",
            f"[{profit_color}]{profit_sign}{profit_rate*100:.2f}%[/{profit_color}] (목표: +{self.buy_info['target_profit_rate']*100:.2f}%)"
        )
        table.add_row(
            "수익금",
            f"[{profit_color}]{profit_sign}{(current_price - buy_price) * self.buy_info['quantity']:,}원[/{profit_color}]"
        )
        table.add_row("보유수량", f"{self.buy_info['quantity']:,}주")
        table.add_row("업데이트", datetime.now().strftime("%H:%M:%S"))

        return table

    async def cleanup(self):
        """리소스 정리"""
        try:
            # WebSocket 연결 종료
            if self.websocket:
                await self.websocket.close()
                logger.info("✅ WebSocket 연결 종료")

            # 백그라운드 태스크 취소
            if self.ws_receive_task and not self.ws_receive_task.done():
                self.ws_receive_task.cancel()
                try:
                    await self.ws_receive_task
                except asyncio.CancelledError:
                    pass

            logger.info("✅ 리소스 정리 완료")

        except Exception as e:
            logger.error(f"❌ 리소스 정리 중 오류: {e}")
