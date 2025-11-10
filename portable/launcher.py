"""
간편 실행 런처 - 자동매매 시스템 통합 관리

사용법:
    python launcher.py [명령어]

명령어:
    setup   - 설정 GUI 실행
    start   - 자동매매 시스템 시작
    stop    - 자동매매 시스템 중지
    help    - 도움말 표시
"""

import sys
import os
import subprocess
from pathlib import Path

# 현재 스크립트 위치 기준 경로 설정
BASE_DIR = Path(__file__).parent.resolve()
PYTHON_EXE = BASE_DIR / "python" / "python.exe"
APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = BASE_DIR / "scripts"


def setup():
    """설정 GUI 실행"""
    print("⚙️ 설정 화면을 여는 중...")
    setup_bat = SCRIPTS_DIR / "setup.bat"
    subprocess.run([str(setup_bat)], shell=True)


def start():
    """자동매매 시스템 시작"""
    # 설정 파일 확인
    env_file = DATA_DIR / ".env"
    if not env_file.exists():
        print("❌ 설정 파일이 없습니다!")
        print()
        print("   먼저 'launcher.py setup' 명령으로 설정을 완료하세요.")
        print()
        return False

    print("📈 자동매매 시스템을 시작합니다...")
    start_bat = SCRIPTS_DIR / "start.bat"
    subprocess.run([str(start_bat)], shell=True)


def stop():
    """자동매매 시스템 중지"""
    print("⏹️ 자동매매 시스템을 중지합니다...")
    stop_bat = SCRIPTS_DIR / "stop.bat"
    subprocess.run([str(stop_bat)], shell=True)


def show_help():
    """도움말 표시"""
    help_text = """
================================================================================
  📈 자동매매 시스템 런처
================================================================================

사용법:
  launcher.py [명령어]

명령어:
  setup   - 설정 GUI 실행 (최초 설정 또는 설정 변경)
  start   - 자동매매 시스템 시작 (웹 브라우저 자동 실행)
  stop    - 자동매매 시스템 중지
  help    - 이 도움말 표시

예시:
  # 처음 사용 시
  launcher.py setup
  launcher.py start

  # 시스템 중지
  launcher.py stop

참고:
  - 설정 파일 위치: data/.env
  - 세션 파일 위치: data/[SESSION_NAME].session
  - 로그 파일: app/auto_trading.log

================================================================================
    """
    print(help_text)


def main():
    """메인 진입점"""
    # 명령어 파싱
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    # 명령어 실행
    commands = {
        'setup': setup,
        'start': start,
        'stop': stop,
        'help': show_help,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"❌ 알 수 없는 명령어: {command}")
        print()
        show_help()


if __name__ == "__main__":
    main()
