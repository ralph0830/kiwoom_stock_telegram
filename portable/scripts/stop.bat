@echo off
chcp 65001 >nul
title ⏹️ 자동매매 시스템 중지

echo ========================================
echo   ⏹️ 자동매매 시스템을 중지합니다
echo ========================================
echo.

REM Python 프로세스 종료
taskkill /F /IM python.exe /T >nul 2>&1

REM Streamlit 프로세스 종료
taskkill /F /IM streamlit.exe /T >nul 2>&1

echo ✅ 자동매매 시스템이 중지되었습니다.
echo.

timeout /t 3 /nobreak >nul
