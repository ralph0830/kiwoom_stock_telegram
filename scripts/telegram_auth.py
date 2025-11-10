"""
Telegram 초기 인증 스크립트

GUI 실행 전 1회만 실행하여 Telegram 세션 파일을 생성합니다.
세션 파일이 생성되면 이후 GUI에서 자동으로 재사용됩니다.

사용법:
    uv run python scripts/telegram_auth.py
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경변수 로드
load_dotenv()


async def authenticate():
    """Telegram 인증 프로세스"""

    # 환경 변수 확인
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    session_name = os.getenv("SESSION_NAME", "channel_copier")

    if not api_id or not api_hash:
        print("❌ .env 파일에 API_ID와 API_HASH를 설정하세요")
        print("   https://my.telegram.org/auth 에서 발급 가능")
        return False

    try:
        api_id = int(api_id)
    except ValueError:
        print("❌ API_ID는 숫자여야 합니다")
        return False

    print("=" * 60)
    print("📱 Telegram 인증 시작")
    print("=" * 60)
    print(f"세션 이름: {session_name}")
    print(f"API ID: {api_id}")
    print()

    # 기존 세션 파일 확인
    session_file = Path(f"{session_name}.session")
    if session_file.exists():
        print(f"⚠️  기존 세션 파일이 있습니다: {session_file}")
        response = input("   기존 세션을 삭제하고 재인증하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("✅ 기존 세션을 유지합니다")
            return True
        else:
            # 백업 후 삭제
            backup_file = session_file.with_suffix('.session.backup')
            session_file.rename(backup_file)
            print(f"   백업 완료: {backup_file}")

    # Telegram 클라이언트 생성
    client = TelegramClient(session_name, api_id, api_hash)

    try:
        await client.start()

        # 인증 성공 - 사용자 정보 조회
        me = await client.get_me()

        print()
        print("=" * 60)
        print("✅ Telegram 인증 완료!")
        print("=" * 60)
        print(f"사용자: {me.first_name} {me.last_name or ''}")
        print(f"Username: @{me.username}")
        print(f"전화번호: {me.phone}")
        print(f"세션 파일: {session_file.absolute()}")
        print()
        print("💡 이제 GUI를 실행할 수 있습니다:")
        print("   streamlit run gui/app.py")
        print("=" * 60)

        await client.disconnect()
        return True

    except SessionPasswordNeededError:
        print("❌ 2단계 인증 비밀번호가 필요합니다")
        password = input("2단계 인증 비밀번호를 입력하세요: ")

        try:
            await client.sign_in(password=password)
            me = await client.get_me()

            print()
            print("=" * 60)
            print("✅ Telegram 인증 완료!")
            print("=" * 60)
            print(f"사용자: {me.first_name} {me.last_name or ''}")
            print(f"Username: @{me.username}")
            print(f"세션 파일: {session_file.absolute()}")
            print("=" * 60)

            await client.disconnect()
            return True

        except Exception as e:
            print(f"❌ 비밀번호 인증 실패: {e}")
            await client.disconnect()
            return False

    except KeyboardInterrupt:
        print("\n⚠️  인증이 취소되었습니다")
        await client.disconnect()
        return False

    except Exception as e:
        print(f"❌ 인증 실패: {e}")
        await client.disconnect()
        return False


def main():
    """메인 함수"""
    success = asyncio.run(authenticate())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
