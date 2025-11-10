# ⚡ 빠른 시작 가이드

개발자를 위한 Portable 패키지 빌드 빠른 가이드

---

## 🚀 3단계로 빌드하기

### 1단계: Python Embedded 다운로드

**다운로드 URL**:
```
https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-amd64.zip
```

**압축 해제 위치**:
```
portable/build/stock_trading_portable/python/
```

### 2단계: 빌드 스크립트 실행

```bash
cd portable
build_portable.bat
```

**예상 소요 시간**: 5-10분

### 3단계: 테스트 및 배포

```bash
# 기능 테스트
cd build\stock_trading_portable
설정하기.lnk

# ZIP 압축
cd ..
powershell Compress-Archive -Path stock_trading_portable -DestinationPath stock_trading_v1.6.0_portable.zip
```

---

## 📂 빌드 결과 구조

```
build/stock_trading_portable/
├── 설정하기.lnk               # 더블클릭 → 설정 GUI
├── 자동매매 시작.lnk          # 더블클릭 → 자동매매 시작
├── 사용설명서.txt
├── README.txt
├── setup_gui.py
├── launcher.py
├── python/                    # Python 3.11.8 embedded (~50MB)
├── app/                       # 애플리케이션 소스
│   ├── auto_trading.py
│   ├── kiwoom_order.py
│   ├── kiwoom_websocket.py
│   ├── gui/
│   └── scripts/
├── data/                      # 사용자 설정 (비어있음)
│   └── .env.template
├── scripts/                   # 실행 배치 스크립트
│   ├── start.bat
│   ├── stop.bat
│   └── setup.bat
└── docs/                      # 문서
    ├── DEPLOY.md
    └── BUILD_VERIFICATION.md
```

---

## ✅ 빠른 검증

```bash
# 필수 파일 확인
dir build\stock_trading_portable\python\python.exe
dir build\stock_trading_portable\setup_gui.py
dir build\stock_trading_portable\scripts\start.bat
dir build\stock_trading_portable\app\auto_trading.py

# Python 버전 확인
build\stock_trading_portable\python\python.exe --version
# 출력: Python 3.11.8

# 설치된 패키지 확인
build\stock_trading_portable\python\python.exe -m pip list
# streamlit, telethon, websockets 등 확인
```

---

## 🔥 문제 해결

### Python embedded 다운로드 실패
→ 해결: VPN 사용 또는 미러 사이트에서 다운로드

### pip 설치 실패
→ 해결: 인터넷 연결 확인, 방화벽 해제

### 의존성 설치 실패
→ 해결: `python -m pip install --upgrade pip` 후 재시도

### 바로가기 생성 실패
→ 해결: 수동으로 `scripts\setup.bat`, `scripts\start.bat` 실행

---

## 📚 상세 문서

- **배포 가이드**: `docs/DEPLOY.md` - 전체 빌드 프로세스 상세 설명
- **빌드 검증**: `BUILD_VERIFICATION.md` - 배포 전 검증 체크리스트
- **사용설명서**: `docs/USER_GUIDE.md` - 최종 사용자 가이드

---

## 🎯 다음 단계

1. **빌드 검증**: `BUILD_VERIFICATION.md` 체크리스트 확인
2. **기능 테스트**: 설정 GUI, Telegram 인증, 자동매매 테스트
3. **ZIP 압축**: 배포 패키지 생성
4. **배포**: 사용자에게 전달

---

**작성일**: 2025-11-10
**버전**: v1.6.0
**빌드 시간**: 약 5-10분
