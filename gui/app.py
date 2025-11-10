"""
Telegram 자동매매 시스템 GUI

Streamlit 기반 웹 대시보드
"""

import streamlit as st
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import json

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경변수 로드
load_dotenv()

# GUI 유틸리티 임포트
from gui.utils.telegram_auth import TelegramAuthManager
from gui.utils.process_monitor import AutoTradingProcessMonitor

# Telegram 설정
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "channel_copier")

# 페이지 설정
st.set_page_config(
    page_title="📈 자동매매 시스템",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .status-active {
        color: #2ecc71;
        font-weight: bold;
    }
    .status-inactive {
        color: #e74c3c;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """세션 상태 초기화"""
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = TelegramAuthManager(
            int(API_ID) if API_ID else 0,
            API_HASH or "",
            SESSION_NAME
        )

    if 'process_monitor' not in st.session_state:
        st.session_state.process_monitor = AutoTradingProcessMonitor()

    if 'session_verified' not in st.session_state:
        st.session_state.session_verified = None


def verify_telegram_session():
    """Telegram 세션 검증"""
    if st.session_state.session_verified is None:
        with st.spinner("🔍 Telegram 세션 검증 중..."):
            is_valid, message = asyncio.run(
                st.session_state.auth_manager.verify_session()
            )
            st.session_state.session_verified = is_valid

            if is_valid:
                st.success(f"✅ {message}")
            else:
                st.warning(f"⚠️ {message}")

    return st.session_state.session_verified


def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.markdown('<p class="main-header">⚙️ 제어 패널</p>', unsafe_allow_html=True)

        # Telegram 세션 정보
        if st.session_state.session_verified:
            user_info = asyncio.run(st.session_state.auth_manager.get_user_info())
            if user_info:
                st.success(f"✅ Telegram: {user_info['first_name']}")
                with st.expander("📱 사용자 정보"):
                    st.write(f"**이름**: {user_info['first_name']} {user_info['last_name']}")
                    st.write(f"**Username**: @{user_info['username']}")
                    st.write(f"**전화번호**: {user_info['phone']}")

        st.divider()

        # 자동매매 제어
        st.subheader("🎛️ 자동매매 제어")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("▶️ 시작", type="primary", use_container_width=True):
                if st.session_state.process_monitor.start_trading_system():
                    st.success("자동매매 시작!")
                    st.rerun()
                else:
                    st.error("시작 실패")

        with col2:
            if st.button("⏹️ 중지", use_container_width=True):
                if st.session_state.process_monitor.stop_trading_system():
                    st.info("자동매매 중지")
                    st.rerun()
                else:
                    st.error("중지 실패")

        if st.button("🔄 재시작", use_container_width=True):
            with st.spinner("재시작 중..."):
                if st.session_state.process_monitor.restart_trading_system():
                    st.success("재시작 완료!")
                    st.rerun()
                else:
                    st.error("재시작 실패")

        st.divider()

        # 시스템 상태
        st.subheader("📊 시스템 상태")

        status = st.session_state.process_monitor.get_status()

        # 프로세스 상태
        if status['process_running']:
            st.markdown('<p class="status-active">🟢 실행중</p>', unsafe_allow_html=True)
            st.caption(f"PID: {status['process_pid']}")
        else:
            st.markdown('<p class="status-inactive">🔴 중지</p>', unsafe_allow_html=True)

        # Telegram 세션 상태
        session_status_map = {
            "ACTIVE": ("🟢", "활성"),
            "EXPIRED": ("🔴", "만료"),
            "STARTING": ("🟡", "시작중"),
            "STOPPED": ("⚪", "중지"),
            "ERROR": ("🔴", "오류"),
            "UNKNOWN": ("⚪", "알 수 없음")
        }

        icon, label = session_status_map.get(status['session_status'], ("⚪", "알 수 없음"))
        st.metric("Telegram 세션", f"{icon} {label}")

        if status['last_update']:
            update_time = datetime.fromisoformat(status['last_update'])
            st.caption(f"최근 업데이트: {update_time.strftime('%H:%M:%S')}")

        # 세션 만료 감지
        if status['session_status'] == "EXPIRED":
            st.error("🚨 세션 만료!")
            if st.button("🔄 재인증", type="primary"):
                st.session_state.session_verified = False
                st.rerun()

        if status['session_error']:
            with st.expander("⚠️ 에러 정보"):
                st.error(status['session_error'])

        st.divider()

        # 재인증 옵션
        if st.button("🔑 Telegram 재인증"):
            st.session_state.session_verified = False
            st.rerun()


def render_main_dashboard():
    """메인 대시보드 렌더링"""
    st.markdown('<p class="main-header">📊 실시간 모니터링 대시보드</p>', unsafe_allow_html=True)

    # 상태 요약
    status = st.session_state.process_monitor.get_status()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if status['process_running']:
            st.metric("프로세스 상태", "🟢 실행중")
        else:
            st.metric("프로세스 상태", "🔴 중지")

    with col2:
        st.metric("Telegram 세션", status['session_status'])

    with col3:
        # 매매 이력 체크
        lock_file = Path("daily_trading_lock.json")
        if lock_file.exists():
            try:
                with open(lock_file, 'r', encoding='utf-8') as f:
                    lock_data = json.load(f)
                    st.metric("오늘 매수", f"{lock_data.get('stock_name', 'N/A')}")
            except Exception:
                st.metric("오늘 매수", "없음")
        else:
            st.metric("오늘 매수", "없음")

    with col4:
        # 로그 파일 크기
        log_file = Path("auto_trading.log")
        if log_file.exists():
            log_size = log_file.stat().st_size / 1024  # KB
            st.metric("로그 크기", f"{log_size:.1f} KB")
        else:
            st.metric("로그 크기", "0 KB")

    st.divider()

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📜 실시간 로그", "📈 매매 내역", "⚙️ 시스템 정보"])

    with tab1:
        render_log_viewer()

    with tab2:
        render_trading_history()

    with tab3:
        render_system_info()


def render_log_viewer():
    """실시간 로그 뷰어"""
    st.subheader("📜 실시간 로그")

    col1, col2 = st.columns([3, 1])

    with col1:
        lines = st.number_input("표시할 라인 수", min_value=10, max_value=500, value=50, step=10)

    with col2:
        auto_refresh = st.checkbox("자동 새로고침", value=False)

    if auto_refresh:
        st.info("⏱️ 5초마다 자동 새로고침")

    # 로그 조회
    logs = st.session_state.process_monitor.get_recent_logs(lines=int(lines))

    if logs:
        # 로그 표시 (코드 블록)
        log_text = "".join(logs)
        st.code(log_text, language="log")
    else:
        st.info("로그가 없습니다")

    # 자동 새로고침
    if auto_refresh:
        import time
        time.sleep(5)
        st.rerun()


def render_trading_history():
    """매매 내역 조회"""
    st.subheader("📈 매매 내역")

    # trading_results 디렉토리 확인
    results_dir = Path("trading_results")

    if not results_dir.exists():
        st.info("매매 내역이 없습니다")
        return

    # 결과 파일 목록
    result_files = sorted(results_dir.glob("*.json"), reverse=True)

    if not result_files:
        st.info("매매 내역이 없습니다")
        return

    st.write(f"총 {len(result_files)}개의 매매 기록")

    # 최근 10개만 표시
    for result_file in result_files[:10]:
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 매매 유형 표시
            trade_type = "익절" if "익절" in result_file.name else "손절" if "손절" in result_file.name else "강제청산" if "강제청산" in result_file.name else "매매"

            with st.expander(f"{data.get('date', 'N/A')} - {data.get('stock_name', 'N/A')} ({trade_type})"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("종목명", data.get('stock_name', 'N/A'))
                    st.metric("매수가", f"{data.get('buy_price', 0):,}원")

                with col2:
                    st.metric("매도가", f"{data.get('sell_price', 0):,}원")
                    st.metric("수량", f"{data.get('quantity', 0)}주")

                with col3:
                    profit_rate = data.get('profit_rate', 0)
                    profit_amount = data.get('profit_amount', 0)

                    st.metric(
                        "수익률",
                        f"{profit_rate:+.2f}%",
                        delta=f"{profit_amount:+,}원"
                    )

                # 상세 정보
                st.json(data)

        except Exception as e:
            st.error(f"파일 읽기 오류: {result_file.name} - {e}")


def render_system_info():
    """시스템 정보"""
    st.subheader("⚙️ 시스템 정보")

    # 환경 변수 (민감 정보 제외)
    with st.expander("📋 환경 설정"):
        st.write("**모드**:", "모의투자" if os.getenv("USE_MOCK", "false").lower() == "true" else "실전투자")
        st.write("**디버그**:", os.getenv("DEBUG", "false"))
        st.write("**계좌번호**:", os.getenv("ACCOUNT_NO", "N/A")[:4] + "****")
        st.write("**최대 투자금액**:", f"{int(os.getenv('MAX_INVESTMENT', 0)):,}원")
        st.write("**목표 수익률**:", f"{float(os.getenv('TARGET_PROFIT_RATE', 1.0))}%")
        st.write("**손절 수익률**:", f"{float(os.getenv('STOP_LOSS_RATE', -2.5))}%")
        st.write("**매수 시간**:", f"{os.getenv('BUY_START_TIME', 'N/A')} ~ {os.getenv('BUY_END_TIME', 'N/A')}")
        st.write("**강제 청산 시간**:", os.getenv('DAILY_FORCE_SELL_TIME', 'N/A'))

    # 파일 정보
    with st.expander("📁 파일 정보"):
        files_to_check = [
            ("세션 파일", f"{SESSION_NAME}.session"),
            ("로그 파일", "auto_trading.log"),
            ("매수 이력", "daily_trading_lock.json"),
            ("세션 상태", ".telegram_status.json"),
        ]

        for name, filename in files_to_check:
            file_path = Path(filename)
            if file_path.exists():
                size = file_path.stat().st_size
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                st.write(f"✅ **{name}**: {size:,} bytes (수정: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
            else:
                st.write(f"❌ **{name}**: 없음")

    # 프로세스 정보
    status = st.session_state.process_monitor.get_status()
    with st.expander("🔧 프로세스 정보"):
        st.json(status)


def main():
    """메인 함수"""

    # 세션 상태 초기화
    initialize_session_state()

    # Telegram 세션 검증
    if not verify_telegram_session():
        # 재인증 UI 표시
        st.session_state.auth_manager.render_reauth_ui()
        return  # 재인증 완료 전까지 여기서 중단

    # 사이드바 렌더링
    render_sidebar()

    # 메인 대시보드 렌더링
    render_main_dashboard()

    # 푸터
    st.divider()
    st.caption("📈 Telegram 자동매매 시스템 v1.6.0 GUI | Powered by Streamlit")


if __name__ == "__main__":
    main()
