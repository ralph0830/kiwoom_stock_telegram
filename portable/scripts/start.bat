@echo off
chcp 65001 >nul
title 📈 자동매매 시스템 시작

echo ========================================
echo   📈 자동매매 시스템을 시작합니다
echo ========================================
echo.

REM 현재 디렉토리를 배치 파일 위치로 변경
cd /d "%~dp0\.."

REM 설정 파일 확인
if not exist "data\.env" (
    echo ❌ 설정 파일이 없습니다!
    echo.
    echo    "설정하기.exe"를 먼저 실행하세요.
    echo.
    pause
    exit /b 1
)

REM Python 경로 설정
set PYTHONPATH=%~dp0..\app
set PYTHONHOME=%~dp0..\python
set PATH=%~dp0..\python;%~dp0..\python\Scripts;%PATH%

REM .env 파일 복사
if exist "data\.env" (
    copy /Y "data\.env" "app\.env" >nul 2>&1
)

REM 세션 파일 확인
set SESSION_NAME=channel_copier
for /f "tokens=2 delims==" %%a in ('findstr /i "SESSION_NAME" data\.env 2^>nul') do set SESSION_NAME=%%a

if not exist "data\%SESSION_NAME%.session" (
    echo.
    echo ⚠️  Telegram 인증이 필요합니다.
    echo.
    echo    처음 실행 시 Telegram 전화번호 인증을 진행합니다.
    echo    준비가 되면 아무 키나 누르세요...
    echo.
    pause

    REM Telegram 인증 실행
    echo.
    echo 📱 Telegram 인증을 시작합니다...
    echo.
    python\python.exe app\scripts\telegram_auth.py

    if errorlevel 1 (
        echo.
        echo ❌ Telegram 인증 실패!
        echo.
        pause
        exit /b 1
    )

    REM 세션 파일 이동
    if exist "%SESSION_NAME%.session" (
        move "%SESSION_NAME%.session" "data\%SESSION_NAME%.session" >nul 2>&1
    )
)

REM 세션 파일을 app 디렉토리로 복사
if exist "data\%SESSION_NAME%.session" (
    copy /Y "data\%SESSION_NAME%.session" "app\%SESSION_NAME%.session" >nul 2>&1
)

echo.
echo ✅ 설정 확인 완료
echo.
echo 🌐 웹 브라우저가 자동으로 열립니다...
echo    (자동으로 열리지 않으면 http://localhost:8501 로 접속하세요)
echo.
echo ⚠️  이 창을 닫으면 자동매매가 중지됩니다!
echo.

REM 브라우저 자동 실행 (3초 후)
timeout /t 3 /nobreak >nul
start http://localhost:8501

REM Streamlit 실행
python\python.exe python\Scripts\streamlit run app\gui\app.py

echo.
echo 📋 자동매매 시스템이 종료되었습니다.
echo.
pause
