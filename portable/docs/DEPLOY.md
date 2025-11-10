# 배포 가이드

개발자를 위한 Portable 패키지 빌드 및 배포 가이드입니다.

---

## 📋 목차

1. [빌드 환경 준비](#빌드-환경-준비)
2. [Portable 패키지 빌드](#portable-패키지-빌드)
3. [EXE 변환 (선택)](#exe-변환-선택)
4. [배포 패키지 구성](#배포-패키지-구성)
5. [테스트 및 검증](#테스트-및-검증)
6. [배포 방법](#배포-방법)
7. [문제 해결](#문제-해결)

---

## 빌드 환경 준비

### 필수 요구사항

- **OS**: Windows 10 이상 (64비트)
- **Python**: 3.11 이상
- **디스크 공간**: 최소 2GB (빌드 + 결과물)
- **네트워크**: Python embedded 다운로드 및 pip 패키지 설치 필요

### 빌드 도구 설치

```bash
# 프로젝트 루트에서
cd portable

# PyInstaller 설치 (EXE 변환용, 선택)
pip install pyinstaller
```

---

## Portable 패키지 빌드

### 1. Python Embedded 다운로드

**수동 다운로드 필요**:
- URL: https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-amd64.zip
- 다운로드 후 압축 해제: `build/stock_trading_portable/python/` 폴더에 복사

**이유**:
- 자동 다운로드 시 방화벽/보안 이슈 발생 가능
- 오프라인 빌드 환경 지원
- 안정적인 버전 관리

### 2. 빌드 스크립트 실행

```bash
# portable 디렉토리에서
build_portable.bat
```

**빌드 과정** (약 5-10분 소요):

```
Step 1: Python Embedded 다운로드 (수동)
  ↓
Step 2: pip 설치
  ↓
Step 3: 의존성 설치 (streamlit, telethon, websockets 등)
  ↓
Step 4: 애플리케이션 파일 복사
  ↓
Step 5: 문서 복사
  ↓
Step 6: 바로가기 생성
  ↓
✅ 빌드 완료
```

### 3. 빌드 결과 확인

```
build/stock_trading_portable/
├── python/                    # Python embedded (약 50MB)
├── app/                       # 애플리케이션 코드
├── data/                      # 사용자 설정 디렉토리 (비어있음)
├── scripts/                   # 실행 배치 스크립트
├── setup_gui.py               # 설정 GUI
├── launcher.py                # 통합 런처
├── 설정하기.lnk               # 바로가기
├── 자동매매 시작.lnk          # 바로가기
├── 사용설명서.txt             # 사용자 가이드
└── README.txt                 # 프로젝트 설명
```

**총 용량**: 약 300~400MB (Python + 의존성 포함)

---

## EXE 변환 (선택)

설정 GUI를 단독 실행 파일로 변환하려면:

### 1. PyInstaller로 EXE 빌드

```bash
# portable 디렉토리에서
pyinstaller setup_gui.spec

# 결과물
dist/설정하기.exe  (약 15MB)
```

### 2. EXE 파일 복사

```bash
# EXE를 빌드 디렉토리로 복사
copy dist\설정하기.exe build\stock_trading_portable\
```

### 3. 배치 스크립트 수정

`scripts/setup.bat` 파일 수정:

```batch
REM 기존
python\python.exe setup_gui.py

REM 변경
설정하기.exe
```

**장점**:
- Python 설치 없이 설정 가능
- 더 네이티브한 사용자 경험

**단점**:
- 파일 크기 증가 (약 15MB)
- 빌드 과정 복잡도 증가

---

## 배포 패키지 구성

### ZIP 압축

```bash
# build 디렉토리에서
cd build
powershell Compress-Archive -Path stock_trading_portable -DestinationPath stock_trading_v1.6.0_portable.zip
```

### 배포 파일 목록

```
stock_trading_v1.6.0_portable.zip  (약 300~400MB)
├── 📁 stock_trading_portable/
│   ├── 설정하기.lnk               # 더블클릭 → 설정 GUI
│   ├── 자동매매 시작.lnk          # 더블클릭 → 자동매매 시작
│   ├── 사용설명서.txt             # 필독!
│   ├── README.txt
│   ├── python/                    # Python 런타임 (수정 금지)
│   ├── app/                       # 애플리케이션 코드 (수정 금지)
│   ├── data/                      # 사용자 설정 (자동 생성)
│   └── scripts/                   # 실행 스크립트 (수정 금지)
```

---

## 테스트 및 검증

### 배포 전 체크리스트

**1. 기능 테스트**:
```bash
# 설정 GUI 실행 확인
설정하기.lnk

# 자동매매 시작 확인
자동매매 시작.lnk

# Telegram 인증 확인
# Streamlit 웹 브라우저 자동 실행 확인
```

**2. 환경 테스트**:
- [ ] 깨끗한 Windows 환경 (Python 미설치)
- [ ] Python 설치된 환경 (충돌 확인)
- [ ] 다른 계정으로 실행 (권한 확인)
- [ ] 바이러스 백신 환경 (오탐 확인)

**3. 파일 구조 확인**:
```bash
# 필수 파일 존재 확인
dir python\python.exe
dir app\auto_trading.py
dir app\gui\app.py
dir scripts\start.bat
```

**4. 의존성 확인**:
```bash
# Python 패키지 목록 확인
python\python.exe -m pip list

# 필수 패키지 확인
# - streamlit
# - telethon
# - websockets
# - requests
# - python-dotenv
# - plotly
# - pandas
# - watchdog
```

---

## 배포 방법

### 방법 1: 직접 다운로드

**파일 공유 서비스 이용**:
- Google Drive
- Dropbox
- OneDrive
- 네이버 클라우드

**예시**:
```
1. stock_trading_v1.6.0_portable.zip 업로드
2. 공유 링크 생성
3. 사용자에게 링크 전달
4. 사용자가 다운로드 → 압축 해제 → 실행
```

### 방법 2: 설치 프로그램 (고급)

**NSIS (Nullsoft Scriptable Install System) 사용**:
- 전문적인 설치 경험 제공
- 레지스트리 등록, 바로가기 생성 자동화
- 언인스톨러 제공

**단점**:
- 복잡도 증가
- 코드 서명 인증서 필요 (SmartScreen 경고 방지)

### 방법 3: 업데이트 전략

**버전 관리**:
```
stock_trading_v1.6.0_portable.zip
stock_trading_v1.7.0_portable.zip
stock_trading_v2.0.0_portable.zip
```

**업데이트 방법**:
1. 기존 `data/` 폴더 백업 (설정, 세션 파일)
2. 새 버전 압축 해제
3. 백업한 `data/` 폴더 복사
4. 실행

---

## 문제 해결

### 빌드 실패

**Python embedded 없음**:
```
❌ Python이 설치되지 않았습니다!
```
→ 해결: Step 1에서 Python embedded 수동 다운로드 및 압축 해제

**pip 설치 실패**:
```
❌ pip 설치 실패
```
→ 해결: 네트워크 연결 확인, 방화벽 해제

**의존성 설치 실패**:
```
ERROR: Could not find a version that satisfies the requirement...
```
→ 해결: Python 버전 확인 (>=3.10), pip 업그레이드 (`python -m pip install --upgrade pip`)

### 실행 문제

**설정하기.lnk 실행 안됨**:
→ 해결: `scripts/setup.bat` 직접 실행

**브라우저 자동 실행 안됨**:
→ 해결: 수동으로 http://localhost:8501 접속

**Telegram 인증 실패**:
→ 해결:
1. API_ID, API_HASH 확인
2. 전화번호 형식 확인 (+8210...)
3. SMS 인증 코드 재전송

### 바이러스 백신 오탐

**SmartScreen 경고**:
```
Windows의 PC 보호
Microsoft Defender SmartScreen에서 인식할 수 없는 앱의 시작을 차단했습니다.
```

→ 해결:
1. "추가 정보" 클릭
2. "실행" 버튼 클릭

**백신 프로그램 차단**:
→ 해결:
1. 예외 목록에 `stock_trading_portable` 폴더 추가
2. 또는 백신 프로그램 일시 중지 후 실행

---

## 보안 고려사항

### 배포 시 주의

**절대 포함하지 말 것**:
- [ ] `.env` 파일 (API 키 포함)
- [ ] `*.session` 파일 (Telegram 세션)
- [ ] `daily_trading_lock.json` (거래 이력)
- [ ] `trading_results/` (매매 기록)
- [ ] `*.log` 파일 (로그)

**깨끗한 상태로 배포**:
```bash
# data 디렉토리는 비어있어야 함
dir data\
# 결과: 파일 없음 또는 .env.template만 존재
```

### 사용자 교육

**필수 안내사항**:
1. `.env` 파일에 API 키 절대 공유 금지
2. `*.session` 파일 백업 권장
3. `trading_results/` 주기적 백업
4. 프로그램 실행 시 공용 컴퓨터 사용 금지

---

## 라이선스 및 법적 고지

**배포 시 포함할 문서**:
- LICENSE 파일 (오픈소스 라이선스)
- 키움증권 OpenAPI 이용약관 안내
- Telegram API 이용약관 안내
- 투자 손실 책임 면책 조항

**예시 면책 조항**:
```
본 소프트웨어는 투자 판단을 돕기 위한 도구이며,
투자로 인한 모든 손실은 사용자 본인의 책임입니다.
개발자는 투자 결과에 대해 어떠한 책임도 지지 않습니다.
```

---

## 추가 리소스

- **프로젝트 저장소**: [GitHub URL]
- **이슈 트래커**: [GitHub Issues URL]
- **사용자 커뮤니티**: [디스코드/텔레그램 그룹]
- **키움증권 OpenAPI 문서**: 프로젝트 루트의 `키움 REST API 문서.xlsx`

---

**작성일**: 2025-11-10
**버전**: v1.6.0
**작성자**: Ralph
