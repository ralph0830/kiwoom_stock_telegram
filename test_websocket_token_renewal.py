"""
WebSocket Token 자동 재발급 테스트

Token 만료 시 자동 재발급 및 로그인 재시도 로직을 검증합니다.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_token_expiry_check():
    """테스트 1: Token 만료 체크 및 자동 재발급"""
    print("\n" + "=" * 80)
    print("테스트 1: Token 만료 체크 및 자동 재발급")
    print("=" * 80)

    from kiwoom_order import KiwoomOrderAPI

    # Mock 환경 설정
    with patch.dict('os.environ', {
        'USE_MOCK': 'true',
        'KIWOOM_MOCK_APP_KEY': 'test_app_key',
        'KIWOOM_MOCK_SECRET_KEY': 'test_secret_key'
    }):
        # API 인스턴스 생성
        api = KiwoomOrderAPI()

        # 시나리오 1: Token이 없는 경우
        print("\n[시나리오 1] Token이 없는 경우")
        api.access_token = None
        api._token_expiry = None

        is_expired = api._is_token_expired()
        print(f"Token 만료 여부: {is_expired}")
        assert is_expired == True, "Token이 없으면 만료로 판단해야 함"
        print("✅ 통과: Token이 없으면 만료로 판단")

        # 시나리오 2: Token이 유효한 경우
        print("\n[시나리오 2] Token이 유효한 경우 (1시간 후 만료)")
        api.access_token = "valid_token_12345"
        api._token_expiry = datetime.now() + timedelta(hours=1)

        is_expired = api._is_token_expired()
        print(f"Token 만료 여부: {is_expired}")
        assert is_expired == False, "Token이 유효하면 만료되지 않음"
        print("✅ 통과: Token이 유효하면 만료되지 않음")

        # 시나리오 3: Token이 만료된 경우
        print("\n[시나리오 3] Token이 만료된 경우 (1시간 전 만료)")
        api.access_token = "expired_token_12345"
        api._token_expiry = datetime.now() - timedelta(hours=1)

        is_expired = api._is_token_expired()
        print(f"Token 만료 여부: {is_expired}")
        assert is_expired == True, "Token이 만료되었으면 만료로 판단"
        print("✅ 통과: Token이 만료되었으면 만료로 판단")

    print("\n" + "=" * 80)
    print("✅ 테스트 1 완료: Token 만료 체크 로직 정상 작동")
    print("=" * 80)


async def test_websocket_connect_with_valid_token():
    """테스트 2: WebSocket connect() - Token 유효 시 정상 연결"""
    print("\n" + "=" * 80)
    print("테스트 2: WebSocket connect() - Token 유효 시 정상 연결")
    print("=" * 80)

    from kiwoom_order import KiwoomOrderAPI
    from kiwoom_websocket import KiwoomWebSocket

    # Mock 환경 설정
    with patch.dict('os.environ', {
        'USE_MOCK': 'true',
        'KIWOOM_MOCK_APP_KEY': 'test_app_key',
        'KIWOOM_MOCK_SECRET_KEY': 'test_secret_key'
    }):
        # API 인스턴스 생성
        api = KiwoomOrderAPI()

        # 유효한 Token 설정
        api.access_token = "valid_token_12345"
        api._token_expiry = datetime.now() + timedelta(hours=1)

        # WebSocket 인스턴스 생성
        ws = KiwoomWebSocket(api, debug_mode=True)

        # websockets.connect를 Mock으로 대체
        mock_websocket = AsyncMock()
        mock_websocket.recv = AsyncMock(return_value='{"trnm": "LOGIN", "return_code": 0}')
        mock_websocket.send = AsyncMock()
        mock_websocket.close = AsyncMock()

        # AsyncMock을 async function으로 래핑
        async def mock_connect(*args, **kwargs):
            return mock_websocket

        with patch('websockets.connect', side_effect=mock_connect):
            # get_access_token을 Mock으로 대체 (호출 확인용)
            with patch.object(api, 'get_access_token', wraps=api.get_access_token) as mock_get_token:
                try:
                    # WebSocket 연결 시도
                    await ws.connect()

                    # 검증
                    print(f"\n[검증] Token 유효성 체크")
                    print(f"- get_access_token() 호출 횟수: {mock_get_token.call_count}")
                    print(f"- WebSocket 연결 상태: {ws.is_connected}")

                    assert mock_get_token.call_count == 1, "get_access_token()이 1회 호출되어야 함"
                    assert ws.is_connected == True, "WebSocket이 연결되어야 함"

                    print("✅ 통과: Token이 유효하면 재발급 없이 정상 연결")

                except Exception as e:
                    print(f"❌ 오류 발생: {e}")
                    raise

    print("\n" + "=" * 80)
    print("✅ 테스트 2 완료: Token 유효 시 정상 연결")
    print("=" * 80)


async def test_websocket_connect_with_expired_token():
    """테스트 3: WebSocket connect() - Token 만료 시 자동 재발급"""
    print("\n" + "=" * 80)
    print("테스트 3: WebSocket connect() - Token 만료 시 자동 재발급")
    print("=" * 80)

    from kiwoom_order import KiwoomOrderAPI
    from kiwoom_websocket import KiwoomWebSocket

    # Mock 환경 설정
    with patch.dict('os.environ', {
        'USE_MOCK': 'true',
        'KIWOOM_MOCK_APP_KEY': 'test_app_key',
        'KIWOOM_MOCK_SECRET_KEY': 'test_secret_key'
    }):
        # API 인스턴스 생성
        api = KiwoomOrderAPI()

        # 만료된 Token 설정
        api.access_token = "expired_token_12345"
        api._token_expiry = datetime.now() - timedelta(hours=1)

        print(f"\n[초기 상태]")
        print(f"- Token: {api.access_token}")
        print(f"- 만료 여부: {api._is_token_expired()}")

        # WebSocket 인스턴스 생성
        ws = KiwoomWebSocket(api, debug_mode=True)

        # Mock requests.post (Token 재발급 API)
        mock_response = Mock()
        mock_response.json.return_value = {
            "token": "new_token_67890",
            "expires_dt": (datetime.now() + timedelta(hours=23)).strftime("%Y%m%d%H%M%S")
        }
        mock_response.raise_for_status = Mock()

        # websockets.connect를 Mock으로 대체
        mock_websocket = AsyncMock()
        mock_websocket.recv = AsyncMock(return_value='{"trnm": "LOGIN", "return_code": 0}')
        mock_websocket.send = AsyncMock()
        mock_websocket.close = AsyncMock()

        # AsyncMock을 async function으로 래핑
        async def mock_connect(*args, **kwargs):
            return mock_websocket

        with patch('requests.post', return_value=mock_response):
            with patch('websockets.connect', side_effect=mock_connect):
                try:
                    # WebSocket 연결 시도
                    await ws.connect()

                    # 검증
                    print(f"\n[최종 상태]")
                    print(f"- Token: {api.access_token}")
                    print(f"- 만료 여부: {api._is_token_expired()}")
                    print(f"- WebSocket 연결: {ws.is_connected}")

                    assert api.access_token == "new_token_67890", "Token이 재발급되어야 함"
                    assert api._is_token_expired() == False, "새 Token은 유효해야 함"
                    assert ws.is_connected == True, "WebSocket이 연결되어야 함"

                    print("✅ 통과: Token 만료 시 자동 재발급 후 연결 성공")

                except Exception as e:
                    print(f"❌ 오류 발생: {e}")
                    raise

    print("\n" + "=" * 80)
    print("✅ 테스트 3 완료: Token 만료 시 자동 재발급")
    print("=" * 80)


async def test_websocket_login_failure_retry():
    """테스트 4: WebSocket 로그인 실패 시 Token 재발급 후 재시도"""
    print("\n" + "=" * 80)
    print("테스트 4: WebSocket 로그인 실패 시 Token 재발급 후 재시도")
    print("=" * 80)

    from kiwoom_order import KiwoomOrderAPI
    from kiwoom_websocket import KiwoomWebSocket

    # Mock 환경 설정
    with patch.dict('os.environ', {
        'USE_MOCK': 'true',
        'KIWOOM_MOCK_APP_KEY': 'test_app_key',
        'KIWOOM_MOCK_SECRET_KEY': 'test_secret_key'
    }):
        # API 인스턴스 생성
        api = KiwoomOrderAPI()

        # 유효한 Token 설정 (하지만 서버에서는 거부)
        api.access_token = "valid_but_rejected_token"
        api._token_expiry = datetime.now() + timedelta(hours=1)

        # WebSocket 인스턴스 생성
        ws = KiwoomWebSocket(api, debug_mode=True)

        # Mock requests.post (Token 재발급 API)
        mock_response = Mock()
        mock_response.json.return_value = {
            "token": "new_refreshed_token_99999",
            "expires_dt": (datetime.now() + timedelta(hours=23)).strftime("%Y%m%d%H%M%S")
        }
        mock_response.raise_for_status = Mock()

        # websockets.connect를 Mock으로 대체
        mock_websocket = AsyncMock()

        # 첫 번째 로그인 실패, 두 번째 로그인 성공 시뮬레이션
        login_responses = [
            '{"trnm": "LOGIN", "return_code": 1, "message": "Token 인증 실패"}',  # 첫 시도 실패
            '{"trnm": "LOGIN", "return_code": 0}'  # 재시도 성공
        ]
        mock_websocket.recv = AsyncMock(side_effect=login_responses)
        mock_websocket.send = AsyncMock()
        mock_websocket.close = AsyncMock()

        # AsyncMock을 async function으로 래핑
        async def mock_connect(*args, **kwargs):
            return mock_websocket

        with patch('requests.post', return_value=mock_response):
            with patch('websockets.connect', side_effect=mock_connect):
                try:
                    print(f"\n[초기 Token]: {api.access_token}")

                    # WebSocket 연결 시도
                    await ws.connect()

                    # 검증
                    print(f"\n[최종 Token]: {api.access_token}")
                    print(f"- WebSocket 연결: {ws.is_connected}")
                    print(f"- recv() 호출 횟수: {mock_websocket.recv.call_count}")

                    assert api.access_token == "new_refreshed_token_99999", "Token이 재발급되어야 함"
                    assert ws.is_connected == True, "재시도 후 WebSocket이 연결되어야 함"
                    assert mock_websocket.recv.call_count == 2, "로그인 응답을 2회 받아야 함 (실패 + 성공)"

                    print("✅ 통과: 로그인 실패 시 Token 재발급 후 재시도 성공")

                except Exception as e:
                    print(f"❌ 오류 발생: {e}")
                    raise

    print("\n" + "=" * 80)
    print("✅ 테스트 4 완료: 로그인 실패 시 Token 재발급 후 재시도")
    print("=" * 80)


async def main():
    """전체 테스트 실행"""
    print("=" * 80)
    print("🧪 WebSocket Token 자동 재발급 테스트 시작")
    print("=" * 80)

    try:
        # 테스트 1: Token 만료 체크
        await test_token_expiry_check()

        # 테스트 2: Token 유효 시 정상 연결
        await test_websocket_connect_with_valid_token()

        # 테스트 3: Token 만료 시 자동 재발급
        await test_websocket_connect_with_expired_token()

        # 테스트 4: 로그인 실패 시 재시도
        await test_websocket_login_failure_retry()

        # 최종 결과
        print("\n" + "=" * 80)
        print("✅ 모든 테스트 통과!")
        print("=" * 80)
        print("\n📊 테스트 결과 요약:")
        print("  ✅ Token 만료 체크 로직: 정상")
        print("  ✅ Token 유효 시 정상 연결: 정상")
        print("  ✅ Token 만료 시 자동 재발급: 정상")
        print("  ✅ 로그인 실패 시 재시도: 정상")
        print("\n💡 WebSocket Token 자동 재발급 기능이 정상적으로 작동합니다!")
        print("=" * 80)

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
