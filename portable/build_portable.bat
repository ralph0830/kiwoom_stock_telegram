@echo off
chcp 65001 >nul
title 📦 Portable 패키지 빌드

echo ========================================
echo   📦 Portable 패키지 빌드 시작
echo   버전: v1.6.0
echo ========================================
echo.

REM 시작 시간 기록
set START_TIME=%TIME%

REM 빌드 디렉토리 설정
set BUILD_DIR=build\stock_trading_portable
set PYTHON_URL=https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-amd64.zip

REM 기존 빌드 디렉토리 정리
if exist "%BUILD_DIR%" (
    echo 🗑️  기존 빌드 디렉토리 삭제 중...
    rmdir /s /q "%BUILD_DIR%" 2>nul
    if errorlevel 1 (
        echo ❌ 기존 디렉토리 삭제 실패! 파일이 사용 중일 수 있습니다.
        pause
        exit /b 1
    )
)

echo 📁 빌드 디렉토리 구조 생성 중...
mkdir "%BUILD_DIR%" 2>nul
mkdir "%BUILD_DIR%\python" 2>nul
mkdir "%BUILD_DIR%\app" 2>nul
mkdir "%BUILD_DIR%\data" 2>nul
mkdir "%BUILD_DIR%\scripts" 2>nul
mkdir "%BUILD_DIR%\docs" 2>nul

if not exist "%BUILD_DIR%" (
    echo ❌ 빌드 디렉토리 생성 실패!
    pause
    exit /b 1
)

echo ✅ 디렉토리 구조 생성 완료
echo.

echo ========================================
echo   Step 1: Python Embedded 다운로드
echo ========================================
echo.
echo Python Embedded 3.11.8이 필요합니다.
echo.
echo 수동 다운로드 방법:
echo   1. 아래 URL을 브라우저에서 열기
echo   2. %PYTHON_URL%
echo   3. 다운로드 완료 후 "%BUILD_DIR%\python" 폴더에 압축 해제
echo.
echo 💡 팁: 7-Zip 또는 WinRAR 사용 권장
echo.
pause

REM Python 설치 확인
if not exist "%BUILD_DIR%\python\python.exe" (
    echo.
    echo ❌ Python이 설치되지 않았습니다!
    echo.
    echo 확인 사항:
    echo   1. Python embedded 다운로드 완료 여부
    echo   2. 압축 해제 위치: %BUILD_DIR%\python\
    echo   3. python.exe 파일 존재 여부
    echo.
    pause
    exit /b 1
)

echo ✅ Python Embedded 확인 완료
set PYTHON_EXE=%BUILD_DIR%\python\python.exe
%PYTHON_EXE% --version
echo.

echo ========================================
echo   Step 2: pip 설치
echo ========================================
echo.

REM get-pip.py 다운로드
echo 📥 get-pip.py 다운로드 중...
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%BUILD_DIR%\python\get-pip.py'" 2>nul

if not exist "%BUILD_DIR%\python\get-pip.py" (
    echo ❌ get-pip.py 다운로드 실패!
    echo.
    echo 가능한 원인:
    echo   1. 인터넷 연결 끊김
    echo   2. 방화벽 차단
    echo   3. PowerShell 권한 부족
    echo.
    pause
    exit /b 1
)

echo ✅ get-pip.py 다운로드 완료
echo.

REM pip 설치
echo 📦 pip 설치 중...
%PYTHON_EXE% %BUILD_DIR%\python\get-pip.py --no-warn-script-location

if errorlevel 1 (
    echo ❌ pip 설치 실패!
    pause
    exit /b 1
)

echo ✅ pip 설치 완료
%PYTHON_EXE% -m pip --version
echo.

echo ========================================
echo   Step 3: 의존성 설치
echo ========================================
echo.
echo 다음 패키지를 설치합니다:
echo   - streamlit (웹 대시보드)
echo   - telethon (Telegram API)
echo   - websockets (실시간 통신)
echo   - requests (HTTP 클라이언트)
echo   - python-dotenv (환경 변수)
echo   - plotly (차트)
echo   - pandas (데이터 처리)
echo   - watchdog (파일 감시)
echo.
echo ⏱️  예상 소요 시간: 5-10분
echo 📡 인터넷 연결이 필요합니다
echo.

REM 필요한 라이브러리 설치
echo 📦 라이브러리 설치 시작...
%PYTHON_EXE% -m pip install --no-warn-script-location streamlit telethon websockets requests python-dotenv plotly pandas watchdog

if errorlevel 1 (
    echo.
    echo ❌ 라이브러리 설치 실패!
    echo.
    echo 가능한 원인:
    echo   1. 인터넷 연결 불안정
    echo   2. 디스크 공간 부족
    echo   3. 패키지 버전 충돌
    echo.
    echo 해결 방법:
    echo   - pip 업그레이드: %PYTHON_EXE% -m pip install --upgrade pip
    echo   - 재시도
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 모든 라이브러리 설치 완료
echo.
echo 설치된 패키지 확인:
%PYTHON_EXE% -m pip list | findstr /i "streamlit telethon websockets requests dotenv plotly pandas watchdog"
echo.

echo ========================================
echo   Step 4: 애플리케이션 파일 복사
echo ========================================
echo.

REM 메인 소스 코드 복사
echo 📄 메인 소스 코드 복사 중...
xcopy /E /I /Y ..\*.py "%BUILD_DIR%\app\" >nul 2>&1
if errorlevel 1 (
    echo ❌ 소스 코드 복사 실패!
    pause
    exit /b 1
)

REM GUI 디렉토리 복사
echo 📱 GUI 디렉토리 복사 중...
xcopy /E /I /Y ..\gui "%BUILD_DIR%\app\gui\" >nul 2>&1

REM 스크립트 디렉토리 복사
echo 📜 스크립트 디렉토리 복사 중...
xcopy /E /I /Y ..\scripts "%BUILD_DIR%\app\scripts\" >nul 2>&1

REM .env 예제 파일 복사
if exist "..\.env.example" (
    echo 📋 .env.example 파일 복사 중...
    copy /Y "..\.env.example" "%BUILD_DIR%\app\.env.example" >nul 2>&1
)

echo ✅ 애플리케이션 소스 복사 완료
echo.

REM 설정 GUI 복사
echo 📋 설정 GUI 복사 중...
copy /Y setup_gui.py "%BUILD_DIR%\" >nul 2>&1
if not exist "%BUILD_DIR%\setup_gui.py" (
    echo ❌ setup_gui.py 복사 실패!
    pause
    exit /b 1
)

REM 런처 복사
echo 🚀 런처 스크립트 복사 중...
copy /Y launcher.py "%BUILD_DIR%\" >nul 2>&1

REM 배치 스크립트 복사
echo 📝 배치 스크립트 복사 중...
xcopy /E /I /Y scripts "%BUILD_DIR%\scripts\" >nul 2>&1
if not exist "%BUILD_DIR%\scripts\start.bat" (
    echo ❌ 배치 스크립트 복사 실패!
    pause
    exit /b 1
)

REM 템플릿 파일 복사
echo 📄 템플릿 파일 복사 중...
if exist "templates\.env.template" (
    copy /Y templates\.env.template "%BUILD_DIR%\data\.env.template" >nul 2>&1
)

echo ✅ 설정 및 스크립트 복사 완료
echo.

echo ========================================
echo   Step 5: 문서 복사
echo ========================================
echo.

REM 사용설명서 복사
echo 📚 사용설명서 복사 중...
if exist "docs\USER_GUIDE.md" (
    copy /Y docs\USER_GUIDE.md "%BUILD_DIR%\사용설명서.txt" >nul 2>&1
)

REM README 복사
echo 📖 README 복사 중...
if exist "..\README.md" (
    copy /Y ..\README.md "%BUILD_DIR%\README.txt" >nul 2>&1
)

REM 배포 가이드 복사
echo 📋 배포 가이드 복사 중...
if exist "docs\DEPLOY.md" (
    copy /Y docs\DEPLOY.md "%BUILD_DIR%\docs\DEPLOY.md" >nul 2>&1
)

REM 빌드 검증 문서 복사
echo 📋 빌드 검증 문서 복사 중...
if exist "BUILD_VERIFICATION.md" (
    copy /Y BUILD_VERIFICATION.md "%BUILD_DIR%\docs\BUILD_VERIFICATION.md" >nul 2>&1
)

echo ✅ 문서 복사 완료
echo.

echo ========================================
echo   Step 6: 바로가기 생성
echo ========================================
echo.

REM 바로가기 생성 (VBS 스크립트 사용)
echo 🔗 "설정하기" 바로가기 생성 중...
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%CD%\%BUILD_DIR%\설정하기.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%CD%\%BUILD_DIR%\scripts\setup.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CD%\%BUILD_DIR%" >> CreateShortcut.vbs
echo oLink.IconLocation = "%CD%\%BUILD_DIR%\python\python.exe, 0" >> CreateShortcut.vbs
echo oLink.Description = "자동매매 시스템 설정" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript //nologo CreateShortcut.vbs >nul 2>&1
if errorlevel 1 (
    echo ⚠️  "설정하기" 바로가기 생성 실패 (수동으로 setup.bat 실행 가능)
) else (
    echo ✅ "설정하기" 바로가기 생성 완료
)
del CreateShortcut.vbs >nul 2>&1

echo 🔗 "자동매매 시작" 바로가기 생성 중...
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%CD%\%BUILD_DIR%\자동매매 시작.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%CD%\%BUILD_DIR%\scripts\start.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CD%\%BUILD_DIR%" >> CreateShortcut.vbs
echo oLink.IconLocation = "%CD%\%BUILD_DIR%\python\python.exe, 0" >> CreateShortcut.vbs
echo oLink.Description = "자동매매 시스템 시작" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript //nologo CreateShortcut.vbs >nul 2>&1
if errorlevel 1 (
    echo ⚠️  "자동매매 시작" 바로가기 생성 실패 (수동으로 start.bat 실행 가능)
) else (
    echo ✅ "자동매매 시작" 바로가기 생성 완료
)
del CreateShortcut.vbs >nul 2>&1

echo.

REM 최종 검증
echo ========================================
echo   🔍 빌드 검증
echo ========================================
echo.

set VALIDATION_FAILED=0

REM 필수 파일 확인
if not exist "%BUILD_DIR%\python\python.exe" (
    echo ❌ python.exe 없음
    set VALIDATION_FAILED=1
)
if not exist "%BUILD_DIR%\setup_gui.py" (
    echo ❌ setup_gui.py 없음
    set VALIDATION_FAILED=1
)
if not exist "%BUILD_DIR%\scripts\start.bat" (
    echo ❌ start.bat 없음
    set VALIDATION_FAILED=1
)
if not exist "%BUILD_DIR%\scripts\stop.bat" (
    echo ❌ stop.bat 없음
    set VALIDATION_FAILED=1
)
if not exist "%BUILD_DIR%\app\auto_trading.py" (
    echo ❌ auto_trading.py 없음
    set VALIDATION_FAILED=1
)

if %VALIDATION_FAILED%==1 (
    echo.
    echo ❌ 빌드 검증 실패! 필수 파일이 누락되었습니다.
    pause
    exit /b 1
)

echo ✅ 모든 필수 파일 확인 완료
echo.

REM 빌드 완료 시간 계산
set END_TIME=%TIME%

echo.
echo ========================================
echo   🎉 빌드 완료!
echo ========================================
echo.
echo 📦 빌드 디렉토리: %BUILD_DIR%
echo 📁 빌드 크기: 약 300-400MB
echo.
echo ⏱️  빌드 시작: %START_TIME%
echo ⏱️  빌드 완료: %END_TIME%
echo.
echo 📋 다음 단계:
echo   1. 빌드 검증 (BUILD_VERIFICATION.md 참고)
echo   2. 기능 테스트 (설정하기.lnk 실행)
echo   3. ZIP 압축 (powershell Compress-Archive ...)
echo   4. 사용자에게 배포
echo.
echo 📚 참고 문서:
echo   - 배포 가이드: %BUILD_DIR%\docs\DEPLOY.md
echo   - 빌드 검증: %BUILD_DIR%\docs\BUILD_VERIFICATION.md
echo   - 사용설명서: %BUILD_DIR%\사용설명서.txt
echo.
echo 🚀 빌드가 성공적으로 완료되었습니다!
echo.
pause
