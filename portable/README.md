# Portable 패키지 빌드 시스템

Python 설치 없이 실행 가능한 자동매매 시스템 Portable 패키지를 빌드하는 도구입니다.

---

## 📦 개요

이 디렉토리는 **비전문가도 쉽게 사용할 수 있는** 자동매매 시스템 배포 패키지를 생성합니다.

### 주요 특징

✅ **Python 설치 불필요** - Python embedded 사용
✅ **GUI 설정 도구** - Tkinter 기반 직관적 설정
✅ **원클릭 실행** - 바로가기로 간편 실행
✅ **완전 독립 실행** - 모든 의존성 포함
✅ **크로스 플랫폼** - Windows 10+ 지원

### 배포 대상

- Python을 설치할 수 없는 사용자
- 터미널 사용이 어려운 사용자
- 간편한 설치를 원하는 사용자

---

## 📁 디렉토리 구조

```
portable/
├── build_portable.bat          # 빌드 자동화 스크립트
├── setup_gui.py                # Tkinter 설정 GUI
├── launcher.py                 # 통합 런처 스크립트
├── setup_gui.spec              # PyInstaller 설정 (선택)
│
├── scripts/                    # 실행 배치 스크립트
│   ├── start.bat               # 자동매매 시작
│   ├── stop.bat                # 자동매매 중지
│   └── setup.bat               # 설정 GUI 실행
│
├── templates/                  # 템플릿 파일
│   └── .env.template           # 환경 변수 템플릿
│
├── docs/                       # 문서
│   ├── DEPLOY.md               # 배포 가이드 (개발자용)
│   └── USER_GUIDE.md           # 사용설명서 (사용자용)
│
├── BUILD_VERIFICATION.md       # 빌드 검증 체크리스트
├── QUICK_START.md              # 빠른 시작 가이드
└── README.md                   # 본 문서

build/                          # 빌드 결과물 (자동 생성)
└── stock_trading_portable/     # 배포 패키지
    ├── 설정하기.lnk
    ├── 자동매매 시작.lnk
    ├── python/
    ├── app/
    ├── data/
    ├── scripts/
    └── docs/
```

---

## 🚀 빠른 시작

### 1. Python Embedded 다운로드

```
URL: https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-amd64.zip
위치: portable/build/stock_trading_portable/python/
```

### 2. 빌드 실행

```bash
cd portable
build_portable.bat
```

### 3. 테스트

```bash
cd build\stock_trading_portable
설정하기.lnk
```

**상세 가이드**: [QUICK_START.md](QUICK_START.md)

---

## 📚 문서

### 개발자용

- **[QUICK_START.md](QUICK_START.md)** - 3단계 빠른 빌드
- **[docs/DEPLOY.md](docs/DEPLOY.md)** - 전체 빌드 및 배포 가이드
- **[BUILD_VERIFICATION.md](BUILD_VERIFICATION.md)** - 빌드 검증 체크리스트

### 사용자용

- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** - 최종 사용자 매뉴얼

---

## 🔧 주요 컴포넌트

### 1. setup_gui.py

Tkinter 기반 설정 GUI

**기능**:
- Telegram API 설정 입력
- 키움증권 API 설정 입력
- 매매 전략 설정 입력
- .env 파일 자동 생성
- 기존 설정 불러오기

**실행**:
```bash
python setup_gui.py
# 또는
설정하기.lnk
```

### 2. launcher.py

통합 실행 런처

**명령어**:
```bash
# 설정 GUI 실행
python launcher.py setup

# 자동매매 시작
python launcher.py start

# 자동매매 중지
python launcher.py stop

# 도움말
python launcher.py help
```

### 3. build_portable.bat

자동 빌드 스크립트

**단계**:
1. Python Embedded 확인
2. pip 설치
3. 의존성 설치 (streamlit, telethon 등)
4. 애플리케이션 파일 복사
5. 문서 복사
6. 바로가기 생성
7. 빌드 검증

**출력**:
```
build/stock_trading_portable/ (약 300-400MB)
```

### 4. 실행 배치 스크립트

**start.bat**:
- .env 설정 확인
- Telegram 인증 (최초 1회)
- Streamlit 웹 대시보드 실행
- 브라우저 자동 실행

**stop.bat**:
- Python 프로세스 종료
- Streamlit 프로세스 종료

**setup.bat**:
- 설정 GUI 실행

---

## 🧪 테스트

### 기본 테스트

```bash
# 빌드 디렉토리로 이동
cd build\stock_trading_portable

# 설정 GUI 테스트
설정하기.lnk

# 자동매매 시작 테스트 (Telegram 인증 필요)
자동매매 시작.lnk
```

### 전체 검증

**체크리스트**: [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md)

---

## 📦 배포

### ZIP 압축

```bash
cd build
powershell Compress-Archive -Path stock_trading_portable -DestinationPath stock_trading_v1.6.0_portable.zip
```

**결과**:
- `stock_trading_v1.6.0_portable.zip` (약 150-200MB)

### 배포 방법

1. **파일 공유 서비스**
   - Google Drive, Dropbox, OneDrive 등
   - 공유 링크 생성 후 전달

2. **설치 프로그램** (고급)
   - NSIS를 사용한 인스톨러 생성
   - 코드 서명 인증서 필요 (SmartScreen 경고 방지)

**상세 가이드**: [docs/DEPLOY.md](docs/DEPLOY.md)

---

## 🔒 보안 주의사항

### 배포 시 절대 포함하지 말 것

- [ ] `.env` 파일 (API 키 포함)
- [ ] `*.session` 파일 (Telegram 세션)
- [ ] `daily_trading_lock.json` (거래 이력)
- [ ] `trading_results/` (매매 기록)
- [ ] `*.log` 파일 (로그)

### 검증 방법

```bash
findstr /s /i "API_KEY SECRET password" build\stock_trading_portable\*
# 결과: 아무것도 나오지 않아야 함
```

---

## 🛠️ 문제 해결

### 빌드 실패

**증상**: "Python이 설치되지 않았습니다!"

**해결**:
1. Python embedded 다운로드 완료 확인
2. 압축 해제 위치 확인: `build/stock_trading_portable/python/`
3. `python.exe` 파일 존재 확인

---

**증상**: "pip 설치 실패"

**해결**:
1. 인터넷 연결 확인
2. 방화벽 설정 확인
3. PowerShell 권한 확인

---

**증상**: "라이브러리 설치 실패"

**해결**:
```bash
# pip 업그레이드
build\stock_trading_portable\python\python.exe -m pip install --upgrade pip

# 재시도
build_portable.bat
```

### 실행 문제

**증상**: 바로가기가 작동하지 않음

**해결**: `scripts/setup.bat` 또는 `scripts/start.bat` 직접 실행

---

**증상**: Telegram 인증 실패

**해결**:
1. API_ID, API_HASH 재확인
2. 전화번호 형식 확인 (+8210...)
3. SMS 코드 재전송

---

## 📊 시스템 요구사항

### 빌드 환경

- **OS**: Windows 10+ (64비트)
- **Python**: 3.11+ (빌드 시에만)
- **디스크**: 최소 2GB
- **네트워크**: 인터넷 연결 필수

### 최종 사용자 환경

- **OS**: Windows 10+ (64비트)
- **RAM**: 최소 4GB
- **디스크**: 약 500MB
- **네트워크**: 인터넷 연결 필수
- **Python**: 설치 불필요 ✅

---

## 🔄 업데이트 전략

### 버전 관리

```
v1.6.0 → v1.7.0 업데이트 시:

1. 사용자에게 data/ 폴더 백업 안내
2. 새 버전 배포 (stock_trading_v1.7.0_portable.zip)
3. 압축 해제 후 백업한 data/ 폴더 복사
4. 실행
```

### 호환성

- `data/.env` 파일 형식 변경 시 마이그레이션 스크립트 제공
- `data/*.session` 파일은 하위 호환 유지

---

## 📈 개선 계획

### v1.7.0 (예정)

- [ ] PyInstaller EXE 변환 자동화
- [ ] 자동 업데이트 기능
- [ ] 다국어 지원 (영어)
- [ ] macOS/Linux 지원

### v2.0.0 (검토 중)

- [ ] NSIS 인스톨러 생성
- [ ] 코드 서명 인증서 적용
- [ ] 클라우드 설정 동기화

---

## 🤝 기여

버그 리포트, 기능 제안, 문서 개선은 언제나 환영합니다!

**GitHub Issues**: [프로젝트 URL]

---

## 📄 라이선스

본 프로젝트의 라이선스를 따릅니다.

---

**작성일**: 2025-11-10
**버전**: v1.6.0
**작성자**: Ralph
**최종 수정**: 2025-11-10
