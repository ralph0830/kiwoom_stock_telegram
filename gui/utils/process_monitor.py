"""
자동매매 프로세스 모니터

auto_trading.py 프로세스의 상태를 모니터링하고 제어합니다.
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import signal


class AutoTradingProcessMonitor:
    """auto_trading.py 프로세스 상태 모니터링 및 제어"""

    def __init__(self):
        """초기화"""
        self.process: Optional[subprocess.Popen] = None
        self.status_file = Path(".telegram_status.json")
        self.log_file = Path("auto_trading.log")

    def start_trading_system(self) -> bool:
        """
        자동매매 시스템 시작

        Returns:
            bool: 시작 성공 여부
        """
        # 이미 실행 중인지 확인
        if self.is_running():
            return False

        try:
            # auto_trading.py 실행
            self.process = subprocess.Popen(
                ["python", "auto_trading.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # 라인 버퍼링
                universal_newlines=True
            )

            # 상태 초기화
            self._update_status("STARTING", "프로세스 시작 중")

            return True

        except Exception as e:
            self._update_status("ERROR", f"시작 실패: {str(e)}")
            return False

    def stop_trading_system(self, force: bool = False) -> bool:
        """
        자동매매 시스템 중지

        Args:
            force: 강제 종료 여부

        Returns:
            bool: 중지 성공 여부
        """
        if not self.process:
            return True

        try:
            if force:
                # 강제 종료 (SIGKILL)
                self.process.kill()
            else:
                # 정상 종료 (SIGTERM)
                self.process.terminate()

            # 종료 대기 (최대 10초)
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # 타임아웃 시 강제 종료
                self.process.kill()
                self.process.wait()

            self._update_status("STOPPED", "프로세스 중지됨")
            self.process = None
            return True

        except Exception as e:
            self._update_status("ERROR", f"중지 실패: {str(e)}")
            return False

    def restart_trading_system(self) -> bool:
        """
        자동매매 시스템 재시작

        Returns:
            bool: 재시작 성공 여부
        """
        if not self.stop_trading_system():
            return False

        import time
        time.sleep(2)  # 2초 대기

        return self.start_trading_system()

    def is_running(self) -> bool:
        """
        프로세스 실행 중 여부 확인

        Returns:
            bool: 실행 중이면 True
        """
        if not self.process:
            return False

        # poll()이 None이면 실행 중
        return self.process.poll() is None

    def get_status(self) -> dict:
        """
        프로세스 및 세션 상태 확인

        Returns:
            dict: 상태 정보
                - process_running: 프로세스 실행 여부
                - process_pid: 프로세스 ID (실행 중일 때)
                - session_status: Telegram 세션 상태
                - session_error: 세션 에러 메시지
                - last_update: 마지막 업데이트 시간
        """
        status = {
            "process_running": self.is_running(),
            "process_pid": self.process.pid if self.process else None,
            "session_status": "UNKNOWN",
            "session_error": None,
            "last_update": None
        }

        # 세션 상태 파일 읽기
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    status["session_status"] = session_data.get("status", "UNKNOWN")
                    status["session_error"] = session_data.get("error")
                    status["last_update"] = session_data.get("timestamp")
            except Exception:
                pass

        return status

    def get_recent_logs(self, lines: int = 50) -> list[str]:
        """
        최근 로그 라인 조회

        Args:
            lines: 조회할 라인 수

        Returns:
            list: 로그 라인 리스트
        """
        if not self.log_file.exists():
            return []

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
        except Exception:
            return []

    def check_session_expired(self) -> bool:
        """
        Telegram 세션 만료 여부 확인

        Returns:
            bool: 만료되었으면 True
        """
        status = self.get_status()
        return status["session_status"] == "EXPIRED"

    def _update_status(self, status: str, error: str = None):
        """
        상태 파일 업데이트 (내부 사용)

        Args:
            status: 상태 코드
            error: 에러 메시지 (선택)
        """
        status_data = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "error": error
        }

        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get_process_output(self) -> tuple[str, str]:
        """
        프로세스 출력 조회 (stdout, stderr)

        Returns:
            tuple: (stdout, stderr)
        """
        if not self.process:
            return "", ""

        try:
            # 비블로킹 읽기
            stdout = self.process.stdout.read() if self.process.stdout else ""
            stderr = self.process.stderr.read() if self.process.stderr else ""
            return stdout, stderr
        except Exception:
            return "", ""

    def cleanup(self):
        """리소스 정리"""
        if self.process:
            self.stop_trading_system(force=True)

    def __del__(self):
        """소멸자"""
        self.cleanup()
