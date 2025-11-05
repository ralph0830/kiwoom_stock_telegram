"""
자동매매 시스템 커스텀 예외

역할: 도메인별 예외 타입 정의
- 명확한 에러 분류
- 구체적인 에러 메시지
- 에러 핸들링 최적화
"""


class TradingException(Exception):
    """자동매매 시스템 기본 예외"""
    def __init__(self, message: str, error_code: str = None):
        """
        Args:
            message: 에러 메시지
            error_code: 에러 코드 (선택)
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


# ========================================
# 네트워크 및 API 관련 예외
# ========================================

class TradingNetworkError(TradingException):
    """네트워크 연결 오류"""
    pass


class TradingTimeoutError(TradingException):
    """API 호출 타임아웃"""
    pass


class TradingAPIError(TradingException):
    """API 응답 오류"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        """
        Args:
            message: 에러 메시지
            status_code: HTTP 상태 코드
            response_data: API 응답 데이터
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

    def __str__(self):
        if self.status_code:
            return f"[API ERROR {self.status_code}] {self.message}"
        return self.message


# ========================================
# 인증 관련 예외
# ========================================

class TradingAuthError(TradingException):
    """인증 실패 (토큰 발급 실패, 권한 없음 등)"""
    pass


class TradingTokenExpiredError(TradingAuthError):
    """Access Token 만료"""
    pass


# ========================================
# 주문 관련 예외
# ========================================

class TradingOrderError(TradingException):
    """주문 실행 오류"""
    pass


class TradingInsufficientBalanceError(TradingOrderError):
    """잔고 부족"""
    pass


class TradingInvalidQuantityError(TradingOrderError):
    """주문 수량 오류 (0 이하, 최소 수량 미달 등)"""
    pass


class TradingOrderRejectError(TradingOrderError):
    """주문 거부 (시장가 거래 불가, 호가 단위 오류 등)"""
    pass


class TradingOrderCancelError(TradingOrderError):
    """주문 취소 실패"""
    pass


# ========================================
# 데이터 관련 예외
# ========================================

class TradingDataError(TradingException):
    """데이터 파싱/검증 오류"""
    pass


class TradingInvalidPriceError(TradingDataError):
    """가격 데이터 오류 (0 이하, 형식 오류 등)"""
    pass


class TradingInvalidStockCodeError(TradingDataError):
    """종목코드 형식 오류"""
    pass


class TradingDataParsingError(TradingDataError):
    """응답 데이터 파싱 실패"""
    pass


# ========================================
# 설정 관련 예외
# ========================================

class TradingConfigError(TradingException):
    """설정 오류"""
    pass


class TradingMissingConfigError(TradingConfigError):
    """필수 설정 누락"""
    pass


class TradingInvalidConfigError(TradingConfigError):
    """설정값 유효성 검증 실패"""
    pass


# ========================================
# 시스템 상태 관련 예외
# ========================================

class TradingStateError(TradingException):
    """시스템 상태 오류"""
    pass


class TradingAlreadyExecutedError(TradingStateError):
    """이미 실행된 작업 (중복 매수/매도 등)"""
    pass


class TradingMarketClosedError(TradingStateError):
    """장 마감 시간"""
    pass


class TradingTradingLockError(TradingStateError):
    """일일 매수 제한 (오늘 이미 매수함)"""
    pass


# ========================================
# WebSocket 관련 예외
# ========================================

class TradingWebSocketError(TradingException):
    """WebSocket 연결/통신 오류"""
    pass


class TradingWebSocketConnectionError(TradingWebSocketError):
    """WebSocket 연결 실패"""
    pass


class TradingWebSocketDisconnectError(TradingWebSocketError):
    """WebSocket 연결 끊김"""
    pass


class TradingWebSocketTimeoutError(TradingWebSocketError):
    """WebSocket 응답 타임아웃"""
    pass


# ========================================
# 파일 시스템 관련 예외
# ========================================

class TradingFileError(TradingException):
    """파일 읽기/쓰기 오류"""
    pass


class TradingFilePermissionError(TradingFileError):
    """파일 권한 오류"""
    pass


class TradingFileNotFoundError(TradingFileError):
    """파일을 찾을 수 없음"""
    pass


# ========================================
# Telegram 관련 예외
# ========================================

class TradingTelegramError(TradingException):
    """Telegram API 오류"""
    pass


class TradingTelegramConnectionError(TradingTelegramError):
    """Telegram 연결 실패"""
    pass


class TradingTelegramAuthError(TradingTelegramError):
    """Telegram 인증 실패"""
    pass


# ========================================
# 유틸리티 함수
# ========================================

def get_exception_type(error_message: str) -> type[TradingException]:
    """
    에러 메시지로부터 적절한 예외 타입 추론

    Args:
        error_message: 에러 메시지

    Returns:
        TradingException의 하위 클래스
    """
    error_lower = error_message.lower()

    # 네트워크 관련
    if any(keyword in error_lower for keyword in ["connection", "network", "연결"]):
        return TradingNetworkError

    # 타임아웃
    if any(keyword in error_lower for keyword in ["timeout", "시간초과", "타임아웃"]):
        return TradingTimeoutError

    # 인증
    if any(keyword in error_lower for keyword in ["auth", "token", "인증", "토큰"]):
        return TradingAuthError

    # 잔고 부족
    if any(keyword in error_lower for keyword in ["balance", "잔고", "부족"]):
        return TradingInsufficientBalanceError

    # 주문 거부
    if any(keyword in error_lower for keyword in ["reject", "거부", "불가"]):
        return TradingOrderRejectError

    # 기본값
    return TradingException


def format_exception_message(exc: Exception) -> str:
    """
    예외를 사용자 친화적 메시지로 변환

    Args:
        exc: 예외 객체

    Returns:
        포맷된 에러 메시지
    """
    if isinstance(exc, TradingNetworkError):
        return f"🌐 네트워크 오류: {exc.message}"

    if isinstance(exc, TradingTimeoutError):
        return f"⏱️ 타임아웃: {exc.message}"

    if isinstance(exc, TradingAuthError):
        return f"🔐 인증 오류: {exc.message}"

    if isinstance(exc, TradingOrderError):
        return f"📋 주문 오류: {exc.message}"

    if isinstance(exc, TradingDataError):
        return f"📊 데이터 오류: {exc.message}"

    if isinstance(exc, TradingWebSocketError):
        return f"🔌 WebSocket 오류: {exc.message}"

    if isinstance(exc, TradingException):
        return f"❌ 시스템 오류: {exc.message}"

    return f"❌ 알 수 없는 오류: {str(exc)}"
