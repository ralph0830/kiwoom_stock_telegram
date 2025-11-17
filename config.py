"""
자동매매 시스템 설정 관리

환경변수로부터 설정을 로드하고 검증하는 TradingConfig 클래스
"""

import os
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


@dataclass
class TradingConfig:
    """자동매매 시스템 설정"""

    # 계좌 정보
    account_no: str
    max_investment: int

    # 수익률 설정
    target_profit_rate: float  # 목표 수익률 (소수, 예: 0.01 = 1%)
    stop_loss_rate: float      # 손절 수익률 (소수, 예: -0.025 = -2.5%)
    stop_loss_delay_minutes: int  # 손절 지연 시간 (분)

    # 매수 시간 설정
    buy_start_time: str  # "HH:MM" 형식
    buy_end_time: str    # "HH:MM" 형식

    # 매도 설정
    enable_sell_monitoring: bool
    enable_stop_loss: bool
    enable_daily_force_sell: bool
    daily_force_sell_time: str  # "HH:MM" 형식

    # 미체결 처리 설정
    cancel_outstanding_on_failure: bool
    outstanding_check_timeout: int  # 초
    outstanding_check_interval: int  # 초

    # 체결 검증 설정
    enable_lazy_verification: bool

    # 주기적 계좌 조회 설정
    balance_check_interval: int  # 초 (0=비활성화)

    # 매수 주문 타입 설정 (v1.6.0)
    buy_order_type: str  # "market" | "limit_plus_one_tick"
    buy_execution_timeout: int  # 초 (지정가 체결 확인 타임아웃)
    buy_execution_check_interval: int  # 초 (지정가 체결 확인 주기)
    buy_fallback_to_market: bool  # 지정가 미체결 시 시장가 재주문 여부

    # 디버그 모드
    debug_mode: bool

    # WebSocket 설정
    ws_ping_interval: Optional[int]  # WebSocket ping 간격 (초, None=비활성화)
    ws_ping_timeout: Optional[int]   # WebSocket ping 타임아웃 (초, None=비활성화)
    ws_recv_timeout: int             # WebSocket 메시지 수신 타임아웃 (초)

    # Telegram 설정 (선택적)
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    session_name: Optional[str] = None
    source_channel: Optional[str] = None
    target_channel: Optional[str] = None

    @classmethod
    def from_env(cls, load_dotenv_first: bool = True) -> 'TradingConfig':
        """
        환경변수에서 설정 로드

        Args:
            load_dotenv_first: .env 파일을 먼저 로드할지 여부 (기본: True)

        Returns:
            TradingConfig 인스턴스

        Raises:
            ValueError: 필수 환경변수가 없거나 형식이 잘못된 경우
        """
        if load_dotenv_first:
            load_dotenv()

        # 필수 환경변수 확인
        account_no = os.getenv("ACCOUNT_NO")
        if not account_no:
            raise ValueError("환경변수 ACCOUNT_NO가 설정되지 않았습니다")

        # 수익률 설정 (퍼센트 → 소수 변환)
        target_profit_rate_percent = float(os.getenv("TARGET_PROFIT_RATE", "1.0"))
        target_profit_rate = target_profit_rate_percent / 100

        stop_loss_rate_percent = float(os.getenv("STOP_LOSS_RATE", "-2.5"))
        stop_loss_rate = stop_loss_rate_percent / 100

        # Telegram 설정 (선택적)
        api_id = None
        api_hash = None
        if os.getenv("API_ID"):
            try:
                api_id = int(os.getenv("API_ID"))
            except ValueError:
                pass

        api_hash = os.getenv("API_HASH")

        return cls(
            # 계좌 정보
            account_no=account_no,
            max_investment=int(os.getenv("MAX_INVESTMENT", "1000000")),

            # 수익률 설정
            target_profit_rate=target_profit_rate,
            stop_loss_rate=stop_loss_rate,
            stop_loss_delay_minutes=int(os.getenv("STOP_LOSS_DELAY_MINUTES", "1")),

            # 매수 시간 설정
            buy_start_time=os.getenv("BUY_START_TIME", "09:00"),
            buy_end_time=os.getenv("BUY_END_TIME", "09:10"),

            # 매도 설정
            enable_sell_monitoring=os.getenv("ENABLE_SELL_MONITORING", "true").lower() == "true",
            enable_stop_loss=os.getenv("ENABLE_STOP_LOSS", "true").lower() == "true",
            enable_daily_force_sell=os.getenv("ENABLE_DAILY_FORCE_SELL", "true").lower() == "true",
            daily_force_sell_time=os.getenv("DAILY_FORCE_SELL_TIME", "15:19"),

            # 미체결 처리 설정
            cancel_outstanding_on_failure=os.getenv("CANCEL_OUTSTANDING_ON_FAILURE", "true").lower() == "true",
            outstanding_check_timeout=int(os.getenv("OUTSTANDING_CHECK_TIMEOUT", "30")),
            outstanding_check_interval=int(os.getenv("OUTSTANDING_CHECK_INTERVAL", "5")),

            # 체결 검증 설정
            enable_lazy_verification=os.getenv("ENABLE_LAZY_VERIFICATION", "false").lower() == "true",

            # 주기적 계좌 조회 설정
            balance_check_interval=int(os.getenv("BALANCE_CHECK_INTERVAL", "0")),

            # 매수 주문 타입 설정 (v1.6.0)
            buy_order_type=os.getenv("BUY_ORDER_TYPE", "market"),
            buy_execution_timeout=int(os.getenv("BUY_EXECUTION_TIMEOUT", "30")),
            buy_execution_check_interval=int(os.getenv("BUY_EXECUTION_CHECK_INTERVAL", "5")),
            buy_fallback_to_market=os.getenv("BUY_FALLBACK_TO_MARKET", "true").lower() == "true",

            # 디버그 모드
            debug_mode=os.getenv("DEBUG", "false").lower() == "true",

            # WebSocket 설정
            ws_ping_interval=None if os.getenv("WS_PING_INTERVAL", "").lower() == "none" else int(os.getenv("WS_PING_INTERVAL", "0")) or None,
            ws_ping_timeout=None if os.getenv("WS_PING_TIMEOUT", "").lower() == "none" else int(os.getenv("WS_PING_TIMEOUT", "0")) or None,
            ws_recv_timeout=int(os.getenv("WS_RECV_TIMEOUT", "60")),

            # Telegram 설정 (선택적)
            api_id=api_id,
            api_hash=api_hash,
            session_name=os.getenv("SESSION_NAME", "telegram_trading_session"),
            source_channel=os.getenv("SOURCE_CHANNEL"),
            target_channel=os.getenv("TARGET_CHANNEL"),
        )

    def validate(self) -> None:
        """
        설정값 검증

        Raises:
            ValueError: 설정값이 유효하지 않은 경우
        """
        # 계좌번호 형식 검증 (예: 12345678-01)
        if not self.account_no or "-" not in self.account_no:
            raise ValueError(f"계좌번호 형식이 올바르지 않습니다: {self.account_no}")

        # 투자금액 검증
        if self.max_investment <= 0:
            raise ValueError(f"최대 투자금액은 0보다 커야 합니다: {self.max_investment}")

        # 수익률 검증
        if self.target_profit_rate <= 0:
            raise ValueError(f"목표 수익률은 0보다 커야 합니다: {self.target_profit_rate}")

        if self.stop_loss_rate >= 0:
            raise ValueError(f"손절 수익률은 0보다 작아야 합니다: {self.stop_loss_rate}")

        # 시간 형식 검증 (HH:MM)
        self._validate_time_format(self.buy_start_time, "BUY_START_TIME")
        self._validate_time_format(self.buy_end_time, "BUY_END_TIME")
        self._validate_time_format(self.daily_force_sell_time, "DAILY_FORCE_SELL_TIME")

        # 타임아웃 검증
        if self.outstanding_check_timeout <= 0:
            raise ValueError(f"타임아웃은 0보다 커야 합니다: {self.outstanding_check_timeout}")

        if self.outstanding_check_interval <= 0:
            raise ValueError(f"체크 주기는 0보다 커야 합니다: {self.outstanding_check_interval}")

        # 매수 주문 타입 검증 (v1.6.0)
        if self.buy_order_type not in ["market", "limit_plus_one_tick"]:
            raise ValueError(f"BUY_ORDER_TYPE은 'market' 또는 'limit_plus_one_tick'이어야 합니다: {self.buy_order_type}")

        if self.buy_execution_timeout <= 0:
            raise ValueError(f"매수 체결 확인 타임아웃은 0보다 커야 합니다: {self.buy_execution_timeout}")

        if self.buy_execution_check_interval <= 0:
            raise ValueError(f"매수 체결 확인 주기는 0보다 커야 합니다: {self.buy_execution_check_interval}")

    def _validate_time_format(self, time_str: str, field_name: str) -> None:
        """
        시간 형식 검증 (HH:MM)

        Args:
            time_str: 검증할 시간 문자열
            field_name: 필드 이름 (에러 메시지용)

        Raises:
            ValueError: 시간 형식이 올바르지 않은 경우
        """
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                raise ValueError()

            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except (ValueError, AttributeError):
            raise ValueError(f"{field_name} 형식이 올바르지 않습니다: {time_str} (HH:MM 형식이어야 함)")

    def __str__(self) -> str:
        """설정 요약 문자열"""
        return f"""
자동매매 시스템 설정:
  계좌번호: {self.account_no}
  최대 투자금액: {self.max_investment:,}원
  목표 수익률: {self.target_profit_rate*100:.2f}%
  손절 수익률: {self.stop_loss_rate*100:.2f}%
  손절 지연: {self.stop_loss_delay_minutes}분
  매수 시간: {self.buy_start_time} ~ {self.buy_end_time}
  강제 청산: {self.daily_force_sell_time}
  디버그 모드: {self.debug_mode}
"""
