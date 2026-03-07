# Build script for MatrixQuesGen
# This script will:
# 1. Build React client
# 2. Package server with PyInstaller
# 3. Create distributable exe

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host " MatrixQuesGen - Build Script" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Step 1: Build React Client
Write-Host "`n-> Buoc 1: Build React Client..." -ForegroundColor Yellow
Write-Host ""

Set-Location client

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "  Installing npm dependencies..." -ForegroundColor Cyan
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "X Loi khi cai dat npm dependencies!" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
}

Write-Host "  Building React app..." -ForegroundColor Cyan
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Loi khi build React app!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Verify dist folder was created
if (-not (Test-Path "dist")) {
    Write-Host "X Loi: Thu muc dist khong duoc tao!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "OK Build React thanh cong!" -ForegroundColor Green
Write-Host ""

Set-Location ..

# Step 2: Check Python dependencies
Write-Host "`n-> Buoc 2: Kiem tra Python dependencies..." -ForegroundColor Yellow
Write-Host ""

$pythonExe = ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "X Khong tim thay Python virtual environment!" -ForegroundColor Red
    Write-Host "  Vui long tao .venv truoc khi build" -ForegroundColor Red
    exit 1
}

# Check if PyInstaller is installed
& $pythonExe -c "import pyinstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installing PyInstaller..." -ForegroundColor Cyan
    & $pythonExe -m pip install pyinstaller
}

# Check if Playwright browsers are installed (needed for chart rendering in DOCX)
Write-Host "  Kiem tra Playwright Chromium cho chart rendering..." -ForegroundColor Cyan
$pwBrowsersPath = Join-Path $env:LOCALAPPDATA "ms-playwright"
if (-not (Test-Path $pwBrowsersPath)) {
    Write-Host "  Playwright Chromium chua duoc cai dat. Dang cai dat..." -ForegroundColor Yellow
    & $pythonExe -m playwright install chromium
    if ($LASTEXITCODE -ne 0) {
        Write-Host "! Canh bao: Khong the cai dat Playwright Chromium." -ForegroundColor Yellow
        Write-Host "  Chart rendering trong DOCX se bi vo hieu hoa trong ban build nay." -ForegroundColor Yellow
    }
    else {
        Write-Host "  OK Playwright Chromium da duoc cai dat." -ForegroundColor Green
    }
}
else {
    Write-Host "  OK Playwright Chromium da co san tai: $pwBrowsersPath" -ForegroundColor Green
}

Write-Host "OK Dependencies OK!" -ForegroundColor Green
Write-Host ""

# Step 2b: Copy MML2OMML.XSL from Office (for math equation support in DOCX export)
Write-Host "`n-> Buoc 2b: Tim MML2OMML.XSL cho math OMML..." -ForegroundColor Yellow
$officePaths = @(
    "C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL",
    "C:\Program Files\Microsoft Office\root\Office15\MML2OMML.XSL",
    "C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL",
    "C:\Program Files\Microsoft Office\Office16\MML2OMML.XSL"
)
$xslCopied = $false
foreach ($src in $officePaths) {
    if (Test-Path $src) {
        New-Item -ItemType Directory -Force -Path "assets" | Out-Null
        Copy-Item $src "assets\MML2OMML.XSL" -Force
        Write-Host "  OK Da copy MML2OMML.XSL tu: $src" -ForegroundColor Green
        $xslCopied = $true
        break
    }
}
if (-not $xslCopied) {
    Write-Host "  ! Office khong tim thay - math OMML bi tat trong ban build nay" -ForegroundColor Yellow
}

# Step 3: Clean previous build
Write-Host "`n-> Buoc 3: Don dep build cu..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "  Da xoa thu muc dist/" -ForegroundColor Cyan
}

if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "  Da xoa thu muc build/" -ForegroundColor Cyan
}

Write-Host "OK Don dep hoan tat!" -ForegroundColor Green
Write-Host ""

# Step 4: Build with PyInstaller
Write-Host "`n-> Buoc 4: Dong goi voi PyInstaller..." -ForegroundColor Yellow
Write-Host ""

# Verify client/dist exists before building
if (-not (Test-Path "client/dist")) {
    Write-Host "X Loi: client/dist khong ton tai!" -ForegroundColor Red
    Write-Host "  Vui long build React client truoc" -ForegroundColor Red
    exit 1
}

& $pythonExe -m PyInstaller matrixquesgen.spec --clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Loi khi dong goi voi PyInstaller!" -ForegroundColor Red
    exit 1
}

Write-Host "OK Dong goi thanh cong!" -ForegroundColor Green
Write-Host ""

# Step 5: Copy additional files
Write-Host "`n-> Buoc 5: Copy cac file bo sung..." -ForegroundColor Yellow
Write-Host ""

$distDir = "dist\MatrixQuesGen"

# Tao thu muc MatrixQuesGen neu chua co
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir -Force | Out-Null
    Write-Host "  Da tao thu muc $distDir" -ForegroundColor Cyan
}

# Di chuyen EXE vao thu muc
if (Test-Path "dist\MatrixQuesGen.exe") {
    Move-Item "dist\MatrixQuesGen.exe" "$distDir\MatrixQuesGen.exe" -Force
    Write-Host "  Da di chuyen MatrixQuesGen.exe" -ForegroundColor Cyan
}

# Tao cac thu muc data (prompts se duoc tu dong tai ve tu Drive)
New-Item -ItemType Directory -Path "$distDir\data" -Force | Out-Null
@('input', 'output', 'sessions', 'questions', 'exports', 'prompts', '.drive_metadata', 'matrix', 'content', 'images', 'logs') | ForEach-Object {
    $dir = "$distDir\data\$_"
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "  Da tao cac thu muc data" -ForegroundColor Cyan

# Copy matrix files mau
if (Test-Path "data\matrix") {
    Copy-Item "data\matrix\*.json" "$distDir\data\matrix\" -Force
    Write-Host "  Da copy cac file ma tran mau" -ForegroundColor Cyan
}

# Copy prompts TIENGANH vao dist
if (Test-Path "data\prompts\TIENGANH") {
    $taPromptDest = "$distDir\data\prompts\TIENGANH"
    if (-not (Test-Path $taPromptDest)) {
        New-Item -ItemType Directory -Path $taPromptDest -Force | Out-Null
    }
    Copy-Item "data\prompts\TIENGANH\*" "$taPromptDest\" -Force
    Write-Host "  Da copy prompts TIENGANH" -ForegroundColor Cyan
}

# Copy .env if exists
if (Test-Path ".env") {
    Copy-Item ".env" "$distDir\.env"
    Write-Host "  Da copy .env" -ForegroundColor Cyan
}

# Copy install_playwright.bat so end-users can enable chart rendering
if (Test-Path "install_playwright.bat") {
    Copy-Item "install_playwright.bat" "$distDir\install_playwright.bat" -Force
    Write-Host "  Da copy install_playwright.bat" -ForegroundColor Cyan
}

# Create README for distribution
$readmeContent = @"
MatrixQuesGen - He thong sinh cau hoi tu dong
============================================

Huong dan su dung:
1. Chay file MatrixQuesGen.exe
2. Ung dung se tu dong mo trong trinh duyet
3. Cua so console hien thi log cua server

Yeu cau:
- Windows 10 tro len
- Ket noi internet (de su dung Google AI va tai prompts tu Drive)

Cau hinh:
- Chinh sua file .env de cau hinh API keys va cac tham so khac

Thu muc quan trong:
- data/prompts: Cac prompt template (TU DONG TAI VE tu Google Drive)
- data/input: Dat file input cua ban vao day
- data/output: Ket qua se duoc luu tai day
- data/sessions: Luu tru cac phien lam viec
- data/questions: Luu cac bo cau hoi da tao
- data/exports: File DOCX xuat ra
- data/images: Luu anh sinh tu AI (neu dung tinh nang Image Generation)
- data/.drive_metadata: Metadata de kiem tra phien ban prompts
- data/logs: Log files

Tinh nang moi (v1.1.0):
+ Sinh lai cau hoi (regenerate mot hoac nhieu cau)
+ Sinh anh minh hoa bang AI (Imagen)
+ Batch operations (update/delete/duplicate nhieu cau)
+ Validation cau hoi tu dong
+ Thong ke & analytics chi tiet

Xuat bieu do (BD) vao DOCX:
- Chay install_playwright.bat mot lan de cai dat Chromium
- Sau khi cai dat, chuc nang xuat anh bieu do se hoat dong
- Khong can internet sau khi da cai dat

Luu y:
- Prompts se tu dong kiem tra va cap nhat tu Google Drive
- Image generation can Google Cloud credentials hop le
- Ket noi internet la can thiet

API Docs:
- Swagger UI: http://localhost:8000/docs
- Chi tiet: xem FEATURES_UPDATE.md

Version: 1.1.0
Build date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
"@

Set-Content -Path "$distDir\README.txt" -Value $readmeContent -Encoding UTF8
Write-Host "  Da tao README.txt" -ForegroundColor Cyan

Write-Host "OK Hoan tat!" -ForegroundColor Green
Write-Host ""

# Final message
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host " Build hoan tat!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""
Write-Host "Ung dung da duoc dong goi tai:" -ForegroundColor White
Write-Host "  -> $((Get-Location).Path)\dist\MatrixQuesGen\" -ForegroundColor Cyan
Write-Host ""

# Step 6: Build Inno Setup installer (optional)
Write-Host "`n-> Buoc 6: Tao Installer voi Inno Setup..." -ForegroundColor Yellow
Write-Host ""

$iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) {
    Write-Host "  Khong tim thay Inno Setup 6. Bo qua buoc tao installer." -ForegroundColor Yellow
    Write-Host "  Cai dat tu: https://jrsoftware.org/isdl.php" -ForegroundColor Cyan
}
else {
    if (-not (Test-Path "installer")) {
        New-Item -ItemType Directory -Path "installer" -Force | Out-Null
    }
    & $iscc inno_setup.iss
    if ($LASTEXITCODE -eq 0) {
        $setupFile = Get-ChildItem "installer\MatrixQuesGen_Setup_*.exe" | Select-Object -Last 1
        Write-Host "OK Tao installer thanh cong!" -ForegroundColor Green
        if ($setupFile) {
            Write-Host "  -> $($setupFile.FullName)" -ForegroundColor Cyan
        }
    }
    else {
        Write-Host "X Loi khi tao installer!" -ForegroundColor Red
    }
}
Write-Host ""
