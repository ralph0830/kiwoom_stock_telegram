# 빌드 검증 체크리스트

Portable 패키지 빌드 후 배포 전 필수 검증 항목입니다.

---

## 📋 빌드 전 체크리스트

### 소스 코드 준비

- [ ] 최신 코드가 커밋되었는가?
- [ ] `.env` 파일이 gitignore에 포함되었는가?
- [ ] `daily_trading_lock.json`이 포함되지 않았는가?
- [ ] `trading_results/` 디렉토리가 비어있는가?
- [ ] 로그 파일(`*.log`)이 포함되지 않았는가?

### 의존성 확인

- [ ] `pyproject.toml`에 모든 의존성이 명시되었는가?
- [ ] 버전 충돌이 없는가?
- [ ] Python 3.11.8 embedded 다운로드 완료?

---

## 🔨 빌드 과정 검증

### 1. 빌드 스크립트 실행

```bash
cd portable
build_portable.bat
```

**예상 소요 시간**: 5-10분

### 2. 각 단계 확인

#### Step 1: Python Embedded 확인
```bash
dir build\stock_trading_portable\python\python.exe
```
- [ ] `python.exe` 파일 존재
- [ ] 크기: 약 50MB

#### Step 2: pip 설치 확인
```bash
build\stock_trading_portable\python\python.exe -m pip --version
```
- [ ] pip 버전 출력 (예: pip 24.0)

#### Step 3: 의존성 설치 확인
```bash
build\stock_trading_portable\python\python.exe -m pip list
```

**필수 패키지 확인**:
- [ ] streamlit >= 1.29.0
- [ ] telethon >= 1.36.0
- [ ] websockets >= 12.0
- [ ] requests >= 2.31.0
- [ ] python-dotenv >= 1.0.1
- [ ] plotly >= 5.18.0
- [ ] pandas >= 2.1.4
- [ ] watchdog >= 3.0.0

#### Step 4: 파일 복사 확인

**애플리케이션 코드**:
- [ ] `build\stock_trading_portable\app\auto_trading.py`
- [ ] `build\stock_trading_portable\app\kiwoom_order.py`
- [ ] `build\stock_trading_portable\app\kiwoom_websocket.py`
- [ ] `build\stock_trading_portable\app\gui\app.py`
- [ ] `build\stock_trading_portable\app\gui\utils\telegram_auth.py`
- [ ] `build\stock_trading_portable\app\gui\utils\process_monitor.py`
- [ ] `build\stock_trading_portable\app\scripts\telegram_auth.py`

**설정 파일**:
- [ ] `build\stock_trading_portable\setup_gui.py`
- [ ] `build\stock_trading_portable\launcher.py`
- [ ] `build\stock_trading_portable\app\.env.example`

**실행 스크립트**:
- [ ] `build\stock_trading_portable\scripts\start.bat`
- [ ] `build\stock_trading_portable\scripts\stop.bat`
- [ ] `build\stock_trading_portable\scripts\setup.bat`

**문서**:
- [ ] `build\stock_trading_portable\사용설명서.txt`
- [ ] `build\stock_trading_portable\README.txt`

**템플릿**:
- [ ] `build\stock_trading_portable\data\.env.template`

#### Step 5: 바로가기 확인
- [ ] `build\stock_trading_portable\설정하기.lnk` 존재
- [ ] `build\stock_trading_portable\자동매매 시작.lnk` 존재

---

## ✅ 기능 테스트

### 1. 설정 GUI 테스트

```bash
cd build\stock_trading_portable
설정하기.lnk
```

**테스트 항목**:
- [ ] GUI 창이 정상적으로 열리는가?
- [ ] 3개 탭 (Telegram, 키움증권, 매매전략)이 표시되는가?
- [ ] 입력 필드가 모두 정상 작동하는가?
- [ ] "저장" 버튼 클릭 시 `data/.env` 파일이 생성되는가?
- [ ] 저장 완료 메시지가 표시되는가?
- [ ] 기존 설정 불러오기가 정상 작동하는가?

### 2. 자동매매 시작 테스트

```bash
자동매매 시작.lnk
```

**테스트 항목**:
- [ ] 설정 파일 존재 확인 메시지가 표시되는가?
- [ ] Telegram 인증 프롬프트가 표시되는가?
- [ ] 전화번호 입력이 정상 작동하는가?
- [ ] SMS 코드 입력이 정상 작동하는가?
- [ ] 2FA 비밀번호 입력이 정상 작동하는가? (해당하는 경우)
- [ ] 인증 완료 후 세션 파일이 생성되는가?
- [ ] 웹 브라우저가 자동으로 열리는가?
- [ ] Streamlit 대시보드가 정상 표시되는가?

### 3. Streamlit 대시보드 테스트

**URL**: http://localhost:8501

**테스트 항목**:
- [ ] 페이지가 정상적으로 로드되는가?
- [ ] 3개 탭 (실시간 로그, 매매 기록, 시스템 정보)이 표시되는가?
- [ ] "자동매매 시스템이 실행 중입니다" 메시지가 표시되는가?
- [ ] 실시간 로그가 업데이트되는가?
- [ ] 시스템 정보 탭에 설정값이 표시되는가?

### 4. Telegram 연결 테스트

**테스트 항목**:
- [ ] SOURCE 채널 연결 확인 메시지가 표시되는가?
- [ ] "매수 신호 모니터링 시작..." 메시지가 표시되는가?
- [ ] 로그에 채널 정보가 출력되는가?
- [ ] 테스트 메시지 전송 시 감지되는가?

### 5. 중지 기능 테스트

**방법 1**: Ctrl+C (터미널)
- [ ] 프로그램이 정상 종료되는가?
- [ ] 리소스 정리 메시지가 표시되는가?

**방법 2**: 작업 관리자
- [ ] python.exe 프로세스가 종료되는가?
- [ ] streamlit 프로세스가 종료되는가?

### 6. 세션 복원 테스트

**시나리오**: 매수 후 프로그램 재시작

1. 수동으로 키움증권 HTS에서 종목 매수 (또는 매수 신호 대기)
2. 프로그램 종료 (Ctrl+C)
3. 프로그램 재시작 (`자동매매 시작.lnk`)
4. 로그 확인:
   - [ ] "보유 종목이 있습니다" 메시지 표시
   - [ ] "매도 모니터링만 시작합니다" 메시지 표시
   - [ ] 보유 종목 정보 출력 (종목명, 코드, 수량, 평균단가)
   - [ ] WebSocket 실시간 시세 수신 시작

---

## 🔍 상세 검증

### 파일 크기 확인

```bash
dir /s build\stock_trading_portable
```

**예상 크기**:
- `python/`: 약 50MB
- `python/Lib/site-packages/`: 약 200-300MB
- `app/`: 약 1-2MB
- **총계**: 약 300-400MB

### 실행 파일 권한 확인

- [ ] `python\python.exe` 실행 가능
- [ ] `scripts\*.bat` 실행 가능
- [ ] `setup_gui.py` 읽기 가능
- [ ] `launcher.py` 읽기 가능

### 환경 변수 테스트

**data/.env 파일 생성 테스트**:
1. 설정 GUI에서 모든 필드 입력
2. "저장" 버튼 클릭
3. `data/.env` 파일 열기
4. 확인 사항:
   - [ ] 모든 환경 변수가 저장되었는가?
   - [ ] 값이 올바르게 인코딩되었는가? (특수문자 포함)
   - [ ] 주석이 제거되었는가?

### 로그 파일 생성 확인

프로그램 실행 후:
- [ ] `app/auto_trading.log` 파일 생성
- [ ] 로그 내용이 정상적으로 기록되는가?
- [ ] 에러 메시지가 명확하게 기록되는가?

---

## 🧪 엣지 케이스 테스트

### 1. 설정 파일 없이 실행

```bash
자동매매 시작.lnk
```

**예상 결과**:
- [ ] "설정 파일이 없습니다!" 에러 메시지
- [ ] "설정하기.exe를 먼저 실행하세요" 안내
- [ ] 프로그램 종료

### 2. 잘못된 API 키

설정 GUI에서 잘못된 API 키 입력 후 실행

**예상 결과**:
- [ ] "Access Token 발급 실패" 에러 메시지
- [ ] 명확한 에러 원인 표시
- [ ] 프로그램 정상 종료 (크래시 없음)

### 3. Telegram 세션 만료

`data/*.session` 파일 삭제 후 실행

**예상 결과**:
- [ ] Telegram 재인증 프롬프트 표시
- [ ] 인증 후 새 세션 파일 생성
- [ ] 정상 실행

### 4. 포트 충돌 (8501)

다른 프로그램이 8501 포트를 사용 중일 때

**예상 결과**:
- [ ] "포트가 사용 중입니다" 에러 메시지
- [ ] 대체 포트 안내 또는 자동 선택
- [ ] 정상 종료

### 5. 인터넷 연결 끊김

실행 중 인터넷 연결 해제

**예상 결과**:
- [ ] WebSocket 연결 끊김 감지
- [ ] 자동 재연결 시도 (2초마다)
- [ ] 재연결 성공 시 정상 복구

---

## 📊 성능 테스트

### 리소스 사용량 확인

**작업 관리자에서 확인**:
- [ ] CPU 사용률: < 5% (대기 중)
- [ ] 메모리 사용량: < 250MB
- [ ] 디스크 I/O: 최소
- [ ] 네트워크 사용량: < 1MB/min (WebSocket)

### 응답 속도 테스트

- [ ] Telegram 메시지 감지: < 0.5초
- [ ] 매수 주문 실행: < 1초
- [ ] 실시간 시세 수신: < 1초 지연
- [ ] 웹 대시보드 로딩: < 3초

---

## 🔒 보안 검증

### 민감 정보 누출 확인

**배포 패키지 검사**:
```bash
findstr /s /i "API_KEY SECRET password" build\stock_trading_portable\*
```

- [ ] `.env` 파일이 포함되지 않았는가?
- [ ] 세션 파일(`.session`)이 포함되지 않았는가?
- [ ] 로그 파일에 민감 정보가 기록되지 않는가?
- [ ] 소스 코드에 하드코딩된 키가 없는가?

### 파일 권한 확인

- [ ] `data/` 폴더 권한: 사용자 전용
- [ ] `.env` 파일 권한: 읽기/쓰기만 허용
- [ ] 세션 파일 권한: 읽기/쓰기만 허용

---

## 📦 최종 패키징 검증

### ZIP 압축 확인

```bash
powershell Compress-Archive -Path build\stock_trading_portable -DestinationPath stock_trading_v1.6.0_portable.zip
```

**확인 사항**:
- [ ] ZIP 파일 크기: 약 150-200MB (압축 후)
- [ ] 압축 해제 후 파일 구조 정상
- [ ] 실행 파일 권한 유지
- [ ] 한글 파일명 정상 표시

### 배포 파일 목록 확인

- [ ] `stock_trading_v1.6.0_portable.zip`
- [ ] `README.txt` (사용 방법 안내)
- [ ] `사용설명서.txt` (USER_GUIDE.md 복사본)
- [ ] `CHANGELOG.txt` (선택)

---

## ✅ 최종 승인 체크리스트

**배포 전 필수 확인**:

- [ ] 모든 기능 테스트 통과
- [ ] 성능 테스트 통과
- [ ] 보안 검증 통과
- [ ] 엣지 케이스 테스트 통과
- [ ] 문서 완성 (DEPLOY.md, USER_GUIDE.md)
- [ ] 버전 번호 확인 (v1.6.0)
- [ ] 릴리스 노트 작성
- [ ] 배포 링크 생성

**승인자 서명**:
- 개발자: _________________ 날짜: _________
- 테스터: _________________ 날짜: _________
- 배포 책임자: _________________ 날짜: _________

---

## 📝 테스트 결과 기록

### 테스트 환경

- **OS**: Windows ___ (버전: _________)
- **Python**: 설치 여부 (Yes/No): _____
- **바이러스 백신**: __________________
- **테스트 날짜**: _______________
- **테스터**: ___________________

### 발견된 이슈

| # | 이슈 설명 | 심각도 | 상태 | 비고 |
|---|----------|-------|------|------|
| 1 |          |       |      |      |
| 2 |          |       |      |      |
| 3 |          |       |      |      |

### 전체 평가

- **빌드 품질**: ⭐⭐⭐⭐⭐ (5점 만점)
- **배포 준비도**: 준비됨 / 미준비 / 보류
- **추가 작업 필요**: Yes / No

**비고**:
```
(여기에 추가 의견 작성)
```

---

**작성일**: 2025-11-10
**버전**: v1.6.0
**작성자**: Ralph
