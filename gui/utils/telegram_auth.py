"""
Telegram 인증 관리자 (GUI용)

세션 검증 및 GUI에서 재인증 처리를 담당합니다.
"""

import streamlit as st
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    FloodWaitError
)
import asyncio
import os
from pathlib import Path
import time


class TelegramAuthManager:
    """Telegram 인증 관리자 (GUI 재인증 지원)"""

    def __init__(self, api_id: int, api_hash: str, session_name: str):
        """
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_name: 세션 파일 이름
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = None

    async def verify_session(self) -> tuple[bool, str]:
        """
        세션 검증

        Returns:
            (is_valid, message): 검증 결과 및 메시지
        """
        session_file = Path(f"{self.session_name}.session")

        # 세션 파일 존재 확인
        if not session_file.exists():
            return False, "세션 파일이 없습니다"

        try:
            # Telegram 클라이언트 생성 및 연결
            self.client = TelegramClient(
                self.session_name,
                self.api_id,
                self.api_hash
            )
            await self.client.connect()

            # 인증 상태 확인
            if not await self.client.is_user_authorized():
                await self.client.disconnect()
                return False, "세션이 만료되었습니다"

            # 실제 API 호출 테스트
            me = await self.client.get_me()
            if not me:
                await self.client.disconnect()
                return False, "사용자 정보 조회 실패"

            # 검증 성공
            user_info = f"{me.first_name} (@{me.username})"
            await self.client.disconnect()
            return True, f"세션 유효: {user_info}"

        except Exception as e:
            if self.client:
                await self.client.disconnect()
            return False, f"세션 검증 오류: {str(e)}"

    def render_reauth_ui(self):
        """GUI 재인증 UI 렌더링"""

        st.warning("🔐 Telegram 재인증이 필요합니다")

        # 세션 상태 초기화
        if 'auth_step' not in st.session_state:
            st.session_state.auth_step = 'phone'
            st.session_state.auth_phone = None
            st.session_state.phone_code_hash = None
            st.session_state.auth_error = None

        # 에러 메시지 표시
        if st.session_state.auth_error:
            st.error(f"❌ {st.session_state.auth_error}")
            st.session_state.auth_error = None

        # 단계별 UI 렌더링
        if st.session_state.auth_step == 'phone':
            self._render_phone_input()

        elif st.session_state.auth_step == 'code':
            self._render_code_input()

        elif st.session_state.auth_step == 'password':
            self._render_password_input()

        elif st.session_state.auth_step == 'complete':
            st.success("✅ 인증 완료!")
            st.balloons()
            # 초기화 및 페이지 새로고침
            st.session_state.auth_step = 'phone'
            st.session_state.session_verified = True
            time.sleep(1)
            st.rerun()

    def _render_phone_input(self):
        """전화번호 입력 UI"""

        st.info("📱 전화번호를 입력하세요")

        with st.form("phone_form"):
            phone = st.text_input(
                "전화번호",
                placeholder="+821012345678",
                help="국제 형식으로 입력 (예: +82 10-1234-5678)"
            )

            submitted = st.form_submit_button("📤 인증 코드 전송", type="primary")

            if submitted:
                if not phone:
                    st.session_state.auth_error = "전화번호를 입력하세요"
                    st.rerun()
                elif not phone.startswith('+'):
                    st.session_state.auth_error = "전화번호는 + 로 시작해야 합니다 (예: +821012345678)"
                    st.rerun()
                else:
                    # 인증 코드 전송
                    with st.spinner("인증 코드 전송 중..."):
                        result = asyncio.run(self._send_code(phone))
                        if result:
                            st.rerun()

    async def _send_code(self, phone: str) -> bool:
        """인증 코드 전송"""
        try:
            # 클라이언트 생성
            self.client = TelegramClient(
                self.session_name,
                self.api_id,
                self.api_hash
            )
            await self.client.connect()

            # 기존 세션 파일 백업 및 삭제
            session_file = Path(f"{self.session_name}.session")
            if session_file.exists():
                backup_file = session_file.with_suffix('.session.backup')
                session_file.rename(backup_file)

            # 인증 코드 요청
            result = await self.client.send_code_request(phone)

            # 상태 저장
            st.session_state.auth_phone = phone
            st.session_state.phone_code_hash = result.phone_code_hash
            st.session_state.auth_step = 'code'

            await self.client.disconnect()
            return True

        except FloodWaitError as e:
            st.session_state.auth_error = f"너무 많은 요청. {e.seconds}초 후 다시 시도하세요"
            return False

        except Exception as e:
            st.session_state.auth_error = f"인증 코드 전송 실패: {str(e)}"
            return False

    def _render_code_input(self):
        """SMS 코드 입력 UI"""

        st.info(f"📱 {st.session_state.auth_phone}로 전송된 인증 코드를 입력하세요")

        with st.form("code_form"):
            code = st.text_input(
                "인증 코드",
                placeholder="12345",
                max_chars=5,
                help="Telegram에서 받은 5자리 코드"
            )

            col1, col2 = st.columns([1, 3])

            with col1:
                submitted = st.form_submit_button("✅ 인증", type="primary")
            with col2:
                cancel = st.form_submit_button("← 다시 시작")

            if cancel:
                st.session_state.auth_step = 'phone'
                st.rerun()

            if submitted:
                if not code:
                    st.session_state.auth_error = "인증 코드를 입력하세요"
                    st.rerun()
                elif len(code) != 5:
                    st.session_state.auth_error = "인증 코드는 5자리입니다"
                    st.rerun()
                else:
                    # 인증 코드 검증
                    with st.spinner("인증 중..."):
                        result = asyncio.run(self._verify_code(code))
                        if result:
                            st.rerun()

    async def _verify_code(self, code: str) -> bool:
        """인증 코드 검증"""
        try:
            await self.client.connect()

            try:
                # 코드로 로그인
                await self.client.sign_in(
                    st.session_state.auth_phone,
                    code,
                    phone_code_hash=st.session_state.phone_code_hash
                )

                # 성공 - 세션 파일 생성됨
                st.session_state.auth_step = 'complete'
                await self.client.disconnect()
                return True

            except SessionPasswordNeededError:
                # 2단계 비밀번호 필요
                st.session_state.auth_step = 'password'
                return True

            except PhoneCodeInvalidError:
                st.session_state.auth_error = "잘못된 인증 코드입니다"
                return False

            except PhoneCodeExpiredError:
                st.session_state.auth_error = "인증 코드가 만료되었습니다. 처음부터 다시 시작하세요"
                st.session_state.auth_step = 'phone'
                return False

        except Exception as e:
            st.session_state.auth_error = f"인증 실패: {str(e)}"
            return False

    def _render_password_input(self):
        """2단계 비밀번호 입력 UI"""

        st.info("🔒 2단계 인증 비밀번호를 입력하세요")

        with st.form("password_form"):
            password = st.text_input(
                "비밀번호",
                type="password",
                help="Telegram 2단계 인증 비밀번호"
            )

            col1, col2 = st.columns([1, 3])

            with col1:
                submitted = st.form_submit_button("🔓 로그인", type="primary")
            with col2:
                cancel = st.form_submit_button("← 다시 시작")

            if cancel:
                st.session_state.auth_step = 'phone'
                st.rerun()

            if submitted:
                if not password:
                    st.session_state.auth_error = "비밀번호를 입력하세요"
                    st.rerun()
                else:
                    # 비밀번호 검증
                    with st.spinner("로그인 중..."):
                        result = asyncio.run(self._verify_password(password))
                        if result:
                            st.rerun()

    async def _verify_password(self, password: str) -> bool:
        """2단계 비밀번호 검증"""
        try:
            await self.client.connect()
            await self.client.sign_in(password=password)

            # 성공
            st.session_state.auth_step = 'complete'
            await self.client.disconnect()
            return True

        except Exception as e:
            st.session_state.auth_error = f"로그인 실패: {str(e)}"
            return False

    async def get_user_info(self) -> dict:
        """현재 인증된 사용자 정보 조회"""
        try:
            client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await client.connect()

            me = await client.get_me()

            user_info = {
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name or "",
                "username": me.username or "",
                "phone": me.phone or ""
            }

            await client.disconnect()
            return user_info

        except Exception:
            return None
