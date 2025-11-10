@echo off
REM Simple build script (English only, no encoding issues)
REM For Korean messages, use build_portable.ps1 instead

echo ========================================
echo   Portable Package Build v1.6.0
echo ========================================
echo.

set BUILD_DIR=build\stock_trading_portable
set PYTHON_URL=https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-amd64.zip

REM Clean existing build
if exist "%BUILD_DIR%" (
    echo Removing existing build directory...
    rmdir /s /q "%BUILD_DIR%" 2>nul
)

REM Create directories
echo Creating build directory structure...
mkdir "%BUILD_DIR%" 2>nul
mkdir "%BUILD_DIR%\python" 2>nul
mkdir "%BUILD_DIR%\app" 2>nul
mkdir "%BUILD_DIR%\data" 2>nul
mkdir "%BUILD_DIR%\scripts" 2>nul
mkdir "%BUILD_DIR%\docs" 2>nul

echo.
echo ========================================
echo   Step 1: Python Embedded Required
echo ========================================
echo.
echo Please download Python Embedded manually:
echo URL: %PYTHON_URL%
echo.
echo Extract to: %BUILD_DIR%\python\
echo.
pause

REM Check Python
if not exist "%BUILD_DIR%\python\python.exe" (
    echo.
    echo ERROR: Python not found!
    echo Please extract python-3.11.8-embed-amd64.zip to %BUILD_DIR%\python\
    echo.
    pause
    exit /b 1
)

echo Python Embedded confirmed
set PYTHON_EXE=%BUILD_DIR%\python\python.exe
%PYTHON_EXE% --version
echo.

REM Install pip
echo ========================================
echo   Step 2: Installing pip
echo ========================================
echo.

echo Downloading get-pip.py...
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%BUILD_DIR%\python\get-pip.py'" 2>nul

if not exist "%BUILD_DIR%\python\get-pip.py" (
    echo ERROR: Failed to download get-pip.py
    pause
    exit /b 1
)

echo Installing pip...
%PYTHON_EXE% %BUILD_DIR%\python\get-pip.py --no-warn-script-location

if errorlevel 1 (
    echo ERROR: pip installation failed
    pause
    exit /b 1
)

echo pip installed successfully
%PYTHON_EXE% -m pip --version
echo.

REM Install dependencies
echo ========================================
echo   Step 3: Installing Dependencies
echo ========================================
echo.
echo This will take 5-10 minutes...
echo.

%PYTHON_EXE% -m pip install --no-warn-script-location streamlit telethon websockets requests python-dotenv plotly pandas watchdog

if errorlevel 1 (
    echo.
    echo ERROR: Package installation failed
    echo Try: %PYTHON_EXE% -m pip install --upgrade pip
    echo.
    pause
    exit /b 1
)

echo.
echo All packages installed successfully
echo.

REM Copy files
echo ========================================
echo   Step 4: Copying Application Files
echo ========================================
echo.

echo Copying source code...
xcopy /E /I /Y ..\*.py "%BUILD_DIR%\app\" >nul 2>&1
xcopy /E /I /Y ..\gui "%BUILD_DIR%\app\gui\" >nul 2>&1
xcopy /E /I /Y ..\scripts "%BUILD_DIR%\app\scripts\" >nul 2>&1

if exist "..\.env.example" (
    copy /Y "..\.env.example" "%BUILD_DIR%\app\.env.example" >nul 2>&1
)

echo Copying setup files...
copy /Y setup_gui.py "%BUILD_DIR%\" >nul 2>&1
copy /Y launcher.py "%BUILD_DIR%\" >nul 2>&1

echo Copying batch scripts...
xcopy /E /I /Y scripts "%BUILD_DIR%\scripts\" >nul 2>&1

if exist "templates\.env.template" (
    copy /Y templates\.env.template "%BUILD_DIR%\data\.env.template" >nul 2>&1
)

echo Application files copied
echo.

REM Copy documentation
echo ========================================
echo   Step 5: Copying Documentation
echo ========================================
echo.

if exist "docs\USER_GUIDE.md" (
    copy /Y "docs\USER_GUIDE.md" "%BUILD_DIR%\USER_GUIDE.txt" >nul 2>&1
)

if exist "..\README.md" (
    copy /Y "..\README.md" "%BUILD_DIR%\README.txt" >nul 2>&1
)

if exist "docs\DEPLOY.md" (
    copy /Y "docs\DEPLOY.md" "%BUILD_DIR%\docs\DEPLOY.md" >nul 2>&1
)

if exist "BUILD_VERIFICATION.md" (
    copy /Y "BUILD_VERIFICATION.md" "%BUILD_DIR%\docs\BUILD_VERIFICATION.md" >nul 2>&1
)

echo Documentation copied
echo.

REM Create shortcuts
echo ========================================
echo   Step 6: Creating Shortcuts
echo ========================================
echo.

echo Creating shortcuts...
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%CD%\%BUILD_DIR%\Setup.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%CD%\%BUILD_DIR%\scripts\setup.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CD%\%BUILD_DIR%" >> CreateShortcut.vbs
echo oLink.IconLocation = "%CD%\%BUILD_DIR%\python\python.exe, 0" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs >nul 2>&1
del CreateShortcut.vbs >nul 2>&1

echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%CD%\%BUILD_DIR%\Start.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%CD%\%BUILD_DIR%\scripts\start.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CD%\%BUILD_DIR%" >> CreateShortcut.vbs
echo oLink.IconLocation = "%CD%\%BUILD_DIR%\python\python.exe, 0" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs >nul 2>&1
del CreateShortcut.vbs >nul 2>&1

echo Shortcuts created
echo.

REM Validation
echo ========================================
echo   Validation
echo ========================================
echo.

set VALIDATION_FAILED=0

if not exist "%BUILD_DIR%\python\python.exe" (
    echo ERROR: python.exe missing
    set VALIDATION_FAILED=1
)
if not exist "%BUILD_DIR%\setup_gui.py" (
    echo ERROR: setup_gui.py missing
    set VALIDATION_FAILED=1
)
if not exist "%BUILD_DIR%\scripts\start.bat" (
    echo ERROR: start.bat missing
    set VALIDATION_FAILED=1
)
if not exist "%BUILD_DIR%\app\auto_trading.py" (
    echo ERROR: auto_trading.py missing
    set VALIDATION_FAILED=1
)

if %VALIDATION_FAILED%==1 (
    echo.
    echo BUILD VALIDATION FAILED!
    pause
    exit /b 1
)

echo All required files confirmed
echo.

REM Complete
echo.
echo ========================================
echo   Build Completed Successfully!
echo ========================================
echo.
echo Build directory: %BUILD_DIR%
echo Build size: ~300-400MB
echo.
echo Next steps:
echo   1. Test: run Setup.lnk
echo   2. Compress: ZIP the directory
echo   3. Deploy to users
echo.
echo Documentation:
echo   - Deployment: %BUILD_DIR%\docs\DEPLOY.md
echo   - Verification: %BUILD_DIR%\docs\BUILD_VERIFICATION.md
echo   - User guide: %BUILD_DIR%\USER_GUIDE.txt
echo.
pause
