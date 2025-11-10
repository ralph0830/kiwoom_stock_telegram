@echo off
chcp 65001 >nul
title ⚙️ 자동매매 시스템 설정

echo ========================================
echo   ⚙️ 자동매매 시스템 설정
echo ========================================
echo.

REM 현재 디렉토리를 배치 파일 위치로 변경
cd /d "%~dp0\.."

REM Python 경로 설정
set PYTHONPATH=%~dp0..
set PYTHONHOME=%~dp0..\python
set PATH=%~dp0..\python;%~dp0..\python\Scripts;%PATH%

REM 설정 GUI 실행
echo 📝 설정 창을 여는 중...
echo.

python\python.exe setup_gui.py

if errorlevel 1 (
    echo.
    echo ❌ 설정 실행 실패!
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 설정 완료!
echo.
timeout /t 2 /nobreak >nul
