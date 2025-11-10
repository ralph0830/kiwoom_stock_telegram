# Portable Package Build Script (PowerShell)
# Encoding: UTF-8 with BOM

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  📦 Portable Package Build" -ForegroundColor Cyan
Write-Host "  Version: v1.6.0" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$StartTime = Get-Date

# Build directory settings
$BUILD_DIR = "build\stock_trading_portable"
$PYTHON_URL = "https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-amd64.zip"

# Clean existing build directory
if (Test-Path $BUILD_DIR) {
    Write-Host "🗑️  Removing existing build directory..." -ForegroundColor Yellow
    Remove-Item -Path $BUILD_DIR -Recurse -Force -ErrorAction Stop
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to remove existing directory!" -ForegroundColor Red
        Write-Host "   Files may be in use." -ForegroundColor Red
        pause
        exit 1
    }
}

# Create build directory structure
Write-Host "📁 Creating build directory structure..." -ForegroundColor Green
New-Item -ItemType Directory -Path $BUILD_DIR -Force | Out-Null
New-Item -ItemType Directory -Path "$BUILD_DIR\python" -Force | Out-Null
New-Item -ItemType Directory -Path "$BUILD_DIR\app" -Force | Out-Null
New-Item -ItemType Directory -Path "$BUILD_DIR\data" -Force | Out-Null
New-Item -ItemType Directory -Path "$BUILD_DIR\scripts" -Force | Out-Null
New-Item -ItemType Directory -Path "$BUILD_DIR\docs" -Force | Out-Null

if (-not (Test-Path $BUILD_DIR)) {
    Write-Host "❌ Failed to create build directory!" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "✅ Directory structure created" -ForegroundColor Green
Write-Host ""

# Step 1: Python Embedded
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 1: Python Embedded Download" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Python Embedded 3.11.8 is required." -ForegroundColor Yellow
Write-Host ""
Write-Host "Manual download required:" -ForegroundColor Yellow
Write-Host "  1. Open URL in browser" -ForegroundColor White
Write-Host "  2. $PYTHON_URL" -ForegroundColor White
Write-Host "  3. Extract to $BUILD_DIR\python" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: Use 7-Zip or WinRAR" -ForegroundColor Cyan
Write-Host ""
pause

# Check Python installation
if (-not (Test-Path "$BUILD_DIR\python\python.exe")) {
    Write-Host ""
    Write-Host "❌ Python not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check:" -ForegroundColor Yellow
    Write-Host "  1. Python embedded downloaded" -ForegroundColor White
    Write-Host "  2. Extracted to: $BUILD_DIR\python\" -ForegroundColor White
    Write-Host "  3. python.exe file exists" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host "✅ Python Embedded confirmed" -ForegroundColor Green
$PYTHON_EXE = "$BUILD_DIR\python\python.exe"
& $PYTHON_EXE --version
Write-Host ""

# Step 2: pip installation
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 2: pip Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Download get-pip.py
Write-Host "📥 Downloading get-pip.py..." -ForegroundColor Green
try {
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile "$BUILD_DIR\python\get-pip.py" -ErrorAction Stop
} catch {
    Write-Host "❌ Failed to download get-pip.py!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "  1. Internet connection lost" -ForegroundColor White
    Write-Host "  2. Firewall blocking" -ForegroundColor White
    Write-Host "  3. PowerShell permission issue" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

if (-not (Test-Path "$BUILD_DIR\python\get-pip.py")) {
    Write-Host "❌ get-pip.py download failed!" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "✅ get-pip.py downloaded" -ForegroundColor Green
Write-Host ""

# Install pip
Write-Host "📦 Installing pip..." -ForegroundColor Green
& $PYTHON_EXE "$BUILD_DIR\python\get-pip.py" --no-warn-script-location

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ pip installation failed!" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "✅ pip installed successfully" -ForegroundColor Green
& $PYTHON_EXE -m pip --version
Write-Host ""

# Step 3: Dependencies installation
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 3: Dependencies Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Installing packages:" -ForegroundColor Yellow
Write-Host "  - streamlit (Web dashboard)" -ForegroundColor White
Write-Host "  - telethon (Telegram API)" -ForegroundColor White
Write-Host "  - websockets (Real-time communication)" -ForegroundColor White
Write-Host "  - requests (HTTP client)" -ForegroundColor White
Write-Host "  - python-dotenv (Environment variables)" -ForegroundColor White
Write-Host "  - plotly (Charts)" -ForegroundColor White
Write-Host "  - pandas (Data processing)" -ForegroundColor White
Write-Host "  - watchdog (File monitoring)" -ForegroundColor White
Write-Host ""
Write-Host "⏱️  Estimated time: 5-10 minutes" -ForegroundColor Cyan
Write-Host "📡 Internet connection required" -ForegroundColor Cyan
Write-Host ""

Write-Host "📦 Starting package installation..." -ForegroundColor Green
& $PYTHON_EXE -m pip install --no-warn-script-location streamlit telethon websockets requests python-dotenv plotly pandas watchdog

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Package installation failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "  1. Unstable internet connection" -ForegroundColor White
    Write-Host "  2. Insufficient disk space" -ForegroundColor White
    Write-Host "  3. Package version conflict" -ForegroundColor White
    Write-Host ""
    Write-Host "Solution:" -ForegroundColor Yellow
    Write-Host "  - Upgrade pip: & $PYTHON_EXE -m pip install --upgrade pip" -ForegroundColor White
    Write-Host "  - Retry" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host ""
Write-Host "✅ All packages installed successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Installed packages:" -ForegroundColor Yellow
& $PYTHON_EXE -m pip list | Select-String "streamlit|telethon|websockets|requests|dotenv|plotly|pandas|watchdog"
Write-Host ""

# Step 4: Copy application files
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 4: Copy Application Files" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Copy main source code
Write-Host "📄 Copying main source code..." -ForegroundColor Green
Copy-Item -Path "..\*.py" -Destination "$BUILD_DIR\app\" -Force -ErrorAction SilentlyContinue

# Copy GUI directory
Write-Host "📱 Copying GUI directory..." -ForegroundColor Green
if (Test-Path "..\gui") {
    Copy-Item -Path "..\gui" -Destination "$BUILD_DIR\app\gui\" -Recurse -Force
}

# Copy scripts directory
Write-Host "📜 Copying scripts directory..." -ForegroundColor Green
if (Test-Path "..\scripts") {
    Copy-Item -Path "..\scripts" -Destination "$BUILD_DIR\app\scripts\" -Recurse -Force
}

# Copy .env.example
if (Test-Path "..\.env.example") {
    Write-Host "📋 Copying .env.example..." -ForegroundColor Green
    Copy-Item -Path "..\.env.example" -Destination "$BUILD_DIR\app\.env.example" -Force
}

Write-Host "✅ Application source copied" -ForegroundColor Green
Write-Host ""

# Copy setup GUI
Write-Host "📋 Copying setup GUI..." -ForegroundColor Green
Copy-Item -Path "setup_gui.py" -Destination "$BUILD_DIR\" -Force
if (-not (Test-Path "$BUILD_DIR\setup_gui.py")) {
    Write-Host "❌ Failed to copy setup_gui.py!" -ForegroundColor Red
    pause
    exit 1
}

# Copy launcher
Write-Host "🚀 Copying launcher script..." -ForegroundColor Green
Copy-Item -Path "launcher.py" -Destination "$BUILD_DIR\" -Force

# Copy batch scripts
Write-Host "📝 Copying batch scripts..." -ForegroundColor Green
if (Test-Path "scripts") {
    Copy-Item -Path "scripts\*" -Destination "$BUILD_DIR\scripts\" -Recurse -Force
}
if (-not (Test-Path "$BUILD_DIR\scripts\start.bat")) {
    Write-Host "❌ Failed to copy batch scripts!" -ForegroundColor Red
    pause
    exit 1
}

# Copy template files
Write-Host "📄 Copying template files..." -ForegroundColor Green
if (Test-Path "templates\.env.template") {
    Copy-Item -Path "templates\.env.template" -Destination "$BUILD_DIR\data\.env.template" -Force
}

Write-Host "✅ Settings and scripts copied" -ForegroundColor Green
Write-Host ""

# Step 5: Copy documentation
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 5: Copy Documentation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Copy user guide
Write-Host "📚 Copying user guide..." -ForegroundColor Green
if (Test-Path "docs\USER_GUIDE.md") {
    Copy-Item -Path "docs\USER_GUIDE.md" -Destination "$BUILD_DIR\사용설명서.txt" -Force
}

# Copy README
Write-Host "📖 Copying README..." -ForegroundColor Green
if (Test-Path "..\README.md") {
    Copy-Item -Path "..\README.md" -Destination "$BUILD_DIR\README.txt" -Force
}

# Copy deployment guide
Write-Host "📋 Copying deployment guide..." -ForegroundColor Green
if (Test-Path "docs\DEPLOY.md") {
    Copy-Item -Path "docs\DEPLOY.md" -Destination "$BUILD_DIR\docs\DEPLOY.md" -Force
}

# Copy build verification
Write-Host "📋 Copying build verification..." -ForegroundColor Green
if (Test-Path "BUILD_VERIFICATION.md") {
    Copy-Item -Path "BUILD_VERIFICATION.md" -Destination "$BUILD_DIR\docs\BUILD_VERIFICATION.md" -Force
}

Write-Host "✅ Documentation copied" -ForegroundColor Green
Write-Host ""

# Step 6: Create shortcuts
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 6: Create Shortcuts" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$WshShell = New-Object -ComObject WScript.Shell

# Create "Setup" shortcut
Write-Host "🔗 Creating 'Setup' shortcut..." -ForegroundColor Green
try {
    $Shortcut = $WshShell.CreateShortcut("$PWD\$BUILD_DIR\설정하기.lnk")
    $Shortcut.TargetPath = "$PWD\$BUILD_DIR\scripts\setup.bat"
    $Shortcut.WorkingDirectory = "$PWD\$BUILD_DIR"
    $Shortcut.IconLocation = "$PWD\$BUILD_DIR\python\python.exe,0"
    $Shortcut.Description = "자동매매 시스템 설정"
    $Shortcut.Save()
    Write-Host "✅ 'Setup' shortcut created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  'Setup' shortcut creation failed (can run setup.bat manually)" -ForegroundColor Yellow
}

# Create "Start" shortcut
Write-Host "🔗 Creating 'Start' shortcut..." -ForegroundColor Green
try {
    $Shortcut = $WshShell.CreateShortcut("$PWD\$BUILD_DIR\자동매매 시작.lnk")
    $Shortcut.TargetPath = "$PWD\$BUILD_DIR\scripts\start.bat"
    $Shortcut.WorkingDirectory = "$PWD\$BUILD_DIR"
    $Shortcut.IconLocation = "$PWD\$BUILD_DIR\python\python.exe,0"
    $Shortcut.Description = "자동매매 시스템 시작"
    $Shortcut.Save()
    Write-Host "✅ 'Start' shortcut created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  'Start' shortcut creation failed (can run start.bat manually)" -ForegroundColor Yellow
}

Write-Host ""

# Final validation
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🔍 Build Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ValidationFailed = $false

# Check required files
$RequiredFiles = @(
    "$BUILD_DIR\python\python.exe",
    "$BUILD_DIR\setup_gui.py",
    "$BUILD_DIR\scripts\start.bat",
    "$BUILD_DIR\scripts\stop.bat",
    "$BUILD_DIR\app\auto_trading.py"
)

foreach ($file in $RequiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Missing: $file" -ForegroundColor Red
        $ValidationFailed = $true
    }
}

if ($ValidationFailed) {
    Write-Host ""
    Write-Host "❌ Build validation failed! Required files are missing." -ForegroundColor Red
    pause
    exit 1
}

Write-Host "✅ All required files confirmed" -ForegroundColor Green
Write-Host ""

# Build completion
$EndTime = Get-Date
$Duration = $EndTime - $StartTime

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  🎉 Build Completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📦 Build directory: $BUILD_DIR" -ForegroundColor White
Write-Host "📁 Build size: ~300-400MB" -ForegroundColor White
Write-Host ""
Write-Host "⏱️  Build started: $($StartTime.ToString('HH:mm:ss'))" -ForegroundColor White
Write-Host "⏱️  Build finished: $($EndTime.ToString('HH:mm:ss'))" -ForegroundColor White
Write-Host "⏱️  Duration: $($Duration.ToString('mm\:ss'))" -ForegroundColor White
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Build verification (BUILD_VERIFICATION.md)" -ForegroundColor White
Write-Host "  2. Function test (run 설정하기.lnk)" -ForegroundColor White
Write-Host "  3. ZIP compression (Compress-Archive ...)" -ForegroundColor White
Write-Host "  4. Deploy to users" -ForegroundColor White
Write-Host ""
Write-Host "📚 Reference documentation:" -ForegroundColor Yellow
Write-Host "  - Deployment guide: $BUILD_DIR\docs\DEPLOY.md" -ForegroundColor White
Write-Host "  - Build verification: $BUILD_DIR\docs\BUILD_VERIFICATION.md" -ForegroundColor White
Write-Host "  - User guide: $BUILD_DIR\사용설명서.txt" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Build completed successfully!" -ForegroundColor Green
Write-Host ""
pause
