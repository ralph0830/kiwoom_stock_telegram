"""
자동매매 시스템 설정 GUI

사용자 친화적인 설정 인터페이스를 제공합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from pathlib import Path


class SetupGUI:
    """설정 GUI 메인 클래스"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("📈 자동매매 시스템 설정")
        self.window.geometry("700x800")
        self.window.resizable(False, False)

        # 데이터 디렉토리 설정
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # 기존 설정 로드
        self.load_existing_config()

        # UI 생성
        self.create_widgets()

    def load_existing_config(self):
        """기존 .env 파일에서 설정 로드"""
        self.config = {}
        env_file = self.data_dir / ".env"

        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            self.config[key] = value
            except Exception:
                pass

    def create_widgets(self):
        """UI 위젯 생성"""

        # 메인 프레임
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill='both', expand=True)

        # 제목
        title = tk.Label(
            main_frame,
            text="📈 자동매매 시스템 설정",
            font=("맑은 고딕", 20, "bold"),
            fg="#1f77b4"
        )
        title.pack(pady=(0, 20))

        # 탭 구성
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)

        # 탭 1: Telegram 설정
        telegram_frame = self.create_scrollable_frame(notebook)
        notebook.add(telegram_frame, text="📱 Telegram")
        self.create_telegram_tab(telegram_frame)

        # 탭 2: 키움증권 설정
        kiwoom_frame = self.create_scrollable_frame(notebook)
        notebook.add(kiwoom_frame, text="💰 키움증권")
        self.create_kiwoom_tab(kiwoom_frame)

        # 탭 3: 매매 전략
        strategy_frame = self.create_scrollable_frame(notebook)
        notebook.add(strategy_frame, text="📊 매매 전략")
        self.create_strategy_tab(strategy_frame)

        # 하단 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(20, 0))

        # 저장 버튼
        save_btn = tk.Button(
            button_frame,
            text="💾 설정 저장 후 종료",
            font=("맑은 고딕", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.save_config,
            height=2,
            cursor="hand2"
        )
        save_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))

        # 취소 버튼
        cancel_btn = tk.Button(
            button_frame,
            text="❌ 취소",
            font=("맑은 고딕", 12),
            bg="#f44336",
            fg="white",
            command=self.window.destroy,
            height=2,
            cursor="hand2"
        )
        cancel_btn.pack(side='right', fill='x', expand=True, padx=(5, 0))

    def create_scrollable_frame(self, parent):
        """스크롤 가능한 프레임 생성"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return scrollable_frame

    def create_telegram_tab(self, parent):
        """Telegram 설정 탭"""

        # 안내 메시지
        info = tk.Label(
            parent,
            text="Telegram API는 https://my.telegram.org/auth 에서 발급받으세요.",
            font=("맑은 고딕", 9),
            fg="#666",
            justify='left'
        )
        info.pack(pady=(10, 20), padx=20, anchor='w')

        # API ID
        self.create_input_field(
            parent,
            "API ID *",
            "API_ID",
            "예: 12345678",
            is_password=False
        )

        # API Hash
        self.create_input_field(
            parent,
            "API Hash *",
            "API_HASH",
            "예: abc123def456...",
            is_password=False
        )

        # Session Name
        self.create_input_field(
            parent,
            "세션 이름",
            "SESSION_NAME",
            "예: my_trader (기본값: channel_copier)",
            default="channel_copier"
        )

        # Source Channel
        self.create_input_field(
            parent,
            "매수 신호 채널 *",
            "SOURCE_CHANNEL",
            "예: https://t.me/signal_channel 또는 @channel_name"
        )

        # Target Channel
        self.create_input_field(
            parent,
            "알림 전송 채널 (선택)",
            "TARGET_CHANNEL",
            "예: @my_channel (비워두면 알림 없음)"
        )

    def create_kiwoom_tab(self, parent):
        """키움증권 설정 탭"""

        # 거래 모드
        mode_frame = ttk.LabelFrame(parent, text="거래 모드", padding=10)
        mode_frame.pack(fill='x', padx=20, pady=10)

        self.use_mock = tk.BooleanVar(
            value=self.config.get('USE_MOCK', 'true').lower() == 'true'
        )

        ttk.Radiobutton(
            mode_frame,
            text="🔧 모의투자 (추천)",
            variable=self.use_mock,
            value=True
        ).pack(anchor='w', pady=2)

        ttk.Radiobutton(
            mode_frame,
            text="💰 실전투자",
            variable=self.use_mock,
            value=False
        ).pack(anchor='w', pady=2)

        # 계좌번호
        self.create_input_field(
            parent,
            "계좌번호 *",
            "ACCOUNT_NO",
            "예: 12345678-01"
        )

        # APP KEY
        self.create_input_field(
            parent,
            "APP KEY *",
            "KIWOOM_APP_KEY",
            "키움증권에서 발급받은 APP KEY"
        )

        # SECRET KEY
        self.create_input_field(
            parent,
            "SECRET KEY *",
            "KIWOOM_SECRET_KEY",
            "키움증권에서 발급받은 SECRET KEY",
            is_password=True
        )

        # 모의투자 키 (선택)
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill='x', padx=20, pady=20)

        mock_label = tk.Label(
            parent,
            text="모의투자용 별도 키 (선택사항)",
            font=("맑은 고딕", 10, "bold")
        )
        mock_label.pack(padx=20, anchor='w')

        self.create_input_field(
            parent,
            "모의투자 APP KEY",
            "KIWOOM_MOCK_APP_KEY",
            "모의투자 전용 키 (비워두면 실전 키 사용)"
        )

        self.create_input_field(
            parent,
            "모의투자 SECRET KEY",
            "KIWOOM_MOCK_SECRET_KEY",
            "모의투자 전용 키 (비워두면 실전 키 사용)",
            is_password=True
        )

    def create_strategy_tab(self, parent):
        """매매 전략 탭"""

        # 투자 설정
        invest_frame = ttk.LabelFrame(parent, text="투자 설정", padding=10)
        invest_frame.pack(fill='x', padx=20, pady=10)

        self.create_input_field(
            invest_frame,
            "최대 투자금액 (원) *",
            "MAX_INVESTMENT",
            "예: 2000000",
            default="2000000"
        )

        # 매수 설정
        buy_frame = ttk.LabelFrame(parent, text="매수 설정", padding=10)
        buy_frame.pack(fill='x', padx=20, pady=10)

        self.create_input_field(
            buy_frame,
            "매수 시작 시간",
            "BUY_START_TIME",
            "예: 08:50",
            default="08:50"
        )

        self.create_input_field(
            buy_frame,
            "매수 종료 시간",
            "BUY_END_TIME",
            "예: 12:10",
            default="12:10"
        )

        # 매수 타입
        buy_type_label = tk.Label(
            buy_frame,
            text="매수 주문 타입",
            font=("맑은 고딕", 9, "bold")
        )
        buy_type_label.pack(anchor='w', padx=5, pady=(10, 5))

        self.buy_type = tk.StringVar(
            value=self.config.get('BUY_ORDER_TYPE', 'market')
        )

        ttk.Radiobutton(
            buy_frame,
            text="시장가 (빠른 체결, 슬리피지 있음)",
            variable=self.buy_type,
            value='market'
        ).pack(anchor='w', padx=5)

        ttk.Radiobutton(
            buy_frame,
            text="지정가 +1틱 (유리한 가격, 미체결 가능)",
            variable=self.buy_type,
            value='limit_plus_one_tick'
        ).pack(anchor='w', padx=5)

        # 수익 설정
        profit_frame = ttk.LabelFrame(parent, text="수익/손실 설정", padding=10)
        profit_frame.pack(fill='x', padx=20, pady=10)

        self.create_input_field(
            profit_frame,
            "목표 수익률 (%)",
            "TARGET_PROFIT_RATE",
            "예: 1.0",
            default="1.0"
        )

        self.create_input_field(
            profit_frame,
            "손절 수익률 (%)",
            "STOP_LOSS_RATE",
            "예: -2.5 (마이너스 값)",
            default="-2.5"
        )

        self.create_input_field(
            profit_frame,
            "강제 청산 시간",
            "DAILY_FORCE_SELL_TIME",
            "예: 15:19 (장마감 11분 전)",
            default="15:19"
        )

    def create_input_field(self, parent, label, key, placeholder, default="", is_password=False):
        """입력 필드 생성 헬퍼"""

        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=20, pady=8)

        # 라벨
        lbl = tk.Label(
            frame,
            text=label,
            font=("맑은 고딕", 9, "bold"),
            anchor='w'
        )
        lbl.pack(anchor='w')

        # 입력 필드
        entry = ttk.Entry(
            frame,
            font=("맑은 고딕", 9),
            show="*" if is_password else ""
        )
        entry.pack(fill='x', pady=(3, 0))

        # 기존 값 또는 기본값 로드
        value = self.config.get(key, default)
        if value:
            entry.insert(0, value)

        # placeholder 표시
        if placeholder:
            entry.configure(foreground='gray')
            entry.insert(0, placeholder) if not value else None

            def on_focus_in(event):
                if entry.get() == placeholder:
                    entry.delete(0, 'end')
                    entry.configure(foreground='black')

            def on_focus_out(event):
                if not entry.get():
                    entry.insert(0, placeholder)
                    entry.configure(foreground='gray')

            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)

        # 위젯 저장
        setattr(self, f'entry_{key}', entry)

    def get_entry_value(self, key):
        """입력 필드 값 가져오기"""
        entry = getattr(self, f'entry_{key}', None)
        if entry:
            value = entry.get().strip()
            # placeholder 제거
            if value.startswith('예:'):
                return ""
            return value
        return ""

    def save_config(self):
        """설정 저장"""

        # 필수 항목 검증
        required = {
            'API_ID': 'Telegram API ID',
            'API_HASH': 'Telegram API Hash',
            'SOURCE_CHANNEL': '매수 신호 채널',
            'ACCOUNT_NO': '계좌번호',
            'KIWOOM_APP_KEY': 'APP KEY',
            'KIWOOM_SECRET_KEY': 'SECRET KEY',
            'MAX_INVESTMENT': '최대 투자금액'
        }

        for key, name in required.items():
            value = self.get_entry_value(key)
            if not value or value.startswith('예:'):
                messagebox.showerror("오류", f"{name}을(를) 입력하세요")
                return

        # .env 파일 생성
        env_content = self.generate_env_content()

        try:
            # 저장
            env_file = self.data_dir / ".env"
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(env_content)

            messagebox.showinfo(
                "성공",
                "설정이 저장되었습니다!\n\n"
                "이제 '자동매매 시작'을 실행하세요.\n\n"
                "주의: 처음 실행 시 Telegram 전화번호 인증이 필요합니다."
            )
            self.window.destroy()

        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 실패:\n{e}")

    def generate_env_content(self):
        """env 파일 내용 생성"""

        use_mock = 'true' if self.use_mock.get() else 'false'

        content = f"""# ====================================
# 자동매매 시스템 설정
# ====================================

# 모의투자/실전투자 선택
USE_MOCK={use_mock}

# 디버그 모드
DEBUG=true

# ====================================
# Telegram API 설정
# ====================================
API_ID={self.get_entry_value('API_ID')}
API_HASH={self.get_entry_value('API_HASH')}
SESSION_NAME={self.get_entry_value('SESSION_NAME') or 'channel_copier'}

# Telegram 채널
SOURCE_CHANNEL={self.get_entry_value('SOURCE_CHANNEL')}
TARGET_CHANNEL={self.get_entry_value('TARGET_CHANNEL')}

# ====================================
# 키움증권 API 설정
# ====================================
ACCOUNT_NO={self.get_entry_value('ACCOUNT_NO')}

# 실전투자 키
KIWOOM_APP_KEY={self.get_entry_value('KIWOOM_APP_KEY')}
KIWOOM_SECRET_KEY={self.get_entry_value('KIWOOM_SECRET_KEY')}

# 모의투자 키 (선택)
KIWOOM_MOCK_APP_KEY={self.get_entry_value('KIWOOM_MOCK_APP_KEY') or self.get_entry_value('KIWOOM_APP_KEY')}
KIWOOM_MOCK_SECRET_KEY={self.get_entry_value('KIWOOM_MOCK_SECRET_KEY') or self.get_entry_value('KIWOOM_SECRET_KEY')}

# ====================================
# 매매 설정
# ====================================
MAX_INVESTMENT={self.get_entry_value('MAX_INVESTMENT')}
TARGET_PROFIT_RATE={self.get_entry_value('TARGET_PROFIT_RATE') or '1.0'}

# 매수 시간
BUY_START_TIME={self.get_entry_value('BUY_START_TIME') or '08:50'}
BUY_END_TIME={self.get_entry_value('BUY_END_TIME') or '12:10'}

# 매수 타입
BUY_ORDER_TYPE={self.buy_type.get()}
BUY_EXECUTION_TIMEOUT=30
BUY_EXECUTION_CHECK_INTERVAL=5
BUY_FALLBACK_TO_MARKET=true

# 매도 모니터링
ENABLE_SELL_MONITORING=true

# 손절 설정
ENABLE_STOP_LOSS=true
STOP_LOSS_RATE={self.get_entry_value('STOP_LOSS_RATE') or '-2.5'}

# 일일 강제 청산
ENABLE_DAILY_FORCE_SELL=true
DAILY_FORCE_SELL_TIME={self.get_entry_value('DAILY_FORCE_SELL_TIME') or '15:19'}

# 미체결 주문 처리
CANCEL_OUTSTANDING_ON_FAILURE=true
OUTSTANDING_CHECK_TIMEOUT=30
OUTSTANDING_CHECK_INTERVAL=5

# 실시간 체결 정보 검증
ENABLE_LAZY_VERIFICATION=true

# 주기적 평균단가 업데이트
BALANCE_CHECK_INTERVAL=0
"""
        return content

    def run(self):
        """GUI 실행"""
        # 창 중앙 배치
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

        self.window.mainloop()


if __name__ == "__main__":
    app = SetupGUI()
    app.run()
