param(
    [string]$Version = "1.0.0",
    [switch]$SkipBuild,
    [switch]$SkipInstaller
)

Write-Host "Building MatrixQuesGen Release v$Version" -ForegroundColor Green
Write-Host "=" * 50

# Update version in version.py
Write-Host "Updating version to $Version..."
$content = Get-Content "version.py" -Raw
$content = $content -replace '__version__ = "[\d\.]+"', "__version__ = `"$Version`""
$content | Set-Content "version.py" -Encoding UTF8

# Update version in inno_setup.iss
$content = Get-Content "inno_setup.iss" -Raw
$content = $content -replace 'AppVersion=[\d\.]+', "AppVersion=$Version"
$content = $content -replace 'OutputBaseFilename=MatrixQuesGen_Setup_[\d\.]+', "OutputBaseFilename=MatrixQuesGen_Setup_$Version"
$content | Set-Content "inno_setup.iss" -Encoding UTF8

# Commit and push version bump immediately so git stays clean
Write-Host "Committing version bump..."
git add version.py inno_setup.iss
git commit -m "chore: bump version to $Version"
git push github main
if ($LASTEXITCODE -ne 0) {
    Write-Warning "git push failed - continuing build anyway"
}

if (-not $SkipBuild) {
    $pythonExe = ".venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) { $pythonExe = "python" }

    Write-Host "Installing/verifying build dependencies..."
    & $pythonExe -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install build dependencies from requirements-build.txt"
        exit 1
    }

    Write-Host "Checking required Python imports..."
    & $pythonExe -c "import fitz; print('PyMuPDF/fitz import OK:', fitz.__file__)"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyMuPDF is missing or broken. Run: $pythonExe -m pip install PyMuPDF"
        exit 1
    }

    # Build React client first so client/dist is up to date
    Write-Host "Building React client..."
    Push-Location "client"
    
    # Install npm dependencies first
    Write-Host "Installing Node.js dependencies..."
    npm install
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Error "npm install failed!"
        exit 1
    }
    
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        Write-Error "npm run build failed!"
        exit 1
    }
    Pop-Location
    Write-Host "React client built successfully" -ForegroundColor Green

    # Prepare English resources for bundling
    Write-Host "Preparing English resource files for bundling..."
    $distDataDir = "dist\data"
    if (-not (Test-Path $distDataDir)) {
        New-Item -ItemType Directory -Path $distDataDir -Force | Out-Null
    }
    
    # Copy English resources to dist/data
    if (Test-Path "data\prompts\prompts_english") {
        Write-Host "  → Copying English prompts..."
        Copy-Item -Path "data\prompts\prompts_english" -Destination "$distDataDir\prompts" -Recurse -Force
    }
    if (Test-Path "data\vocabulary_english") {
        Write-Host "  → Copying English vocabulary..."
        Copy-Item -Path "data\vocabulary_english" -Destination $distDataDir -Recurse -Force
    }

    Write-Host "Building executable with PyInstaller..."
    
    # Clean up temporary/lock files that can cause PyInstaller permission errors
    Write-Host "Cleaning up temporary files..."
    Get-ChildItem -Path "data" -Recurse -Filter "~$*" -Force | Remove-Item -Force
    Get-ChildItem -Path "data" -Recurse -Filter ".~*" -Force | Remove-Item -Force
    
    & $pythonExe -m PyInstaller --clean --noconfirm matrixquesgen.spec

    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller build failed!"
        exit 1
    }

    Write-Host "Executable built successfully" -ForegroundColor Green
}

if (-not $SkipInstaller) {
    Write-Host "Building installer with Inno Setup..."

    # Check if Inno Setup is installed
    $isccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (-not (Test-Path $isccPath)) {
        $isccPath = "C:\Program Files\Inno Setup 6\ISCC.exe"
    }

    if (Test-Path $isccPath) {
        & $isccPath inno_setup.iss

        if ($LASTEXITCODE -ne 0) {
            Write-Error "Inno Setup build failed!"
            exit 1
        }

        Write-Host "Installer built successfully" -ForegroundColor Green
    }
    else {
        Write-Warning "Inno Setup not found. Please install Inno Setup 6 and run again."
        Write-Host "Download from: https://jrsoftware.org/isdl.php"
    }
}

Write-Host ""
Write-Host "Build completed!" -ForegroundColor Green
Write-Host "Features included:"
Write-Host "  ✓ TOAN subject processing"
Write-Host "  ✓ English subject support"
Write-Host "  ✓ English resource files bundled"
Write-Host ""
Write-Host "📦 Resource files bundled:"
Write-Host "  • data/prompts/prompts_english/"
Write-Host "  • data/vocabulary_english/"
Write-Host ""
Write-Host "Note: TOAN prompts are managed separately (not bundled in installer)"
Write-Host ""
Write-Host "Files created:"
if (-not $SkipBuild) {
    Write-Host "  - dist/MatrixQuesGen.exe"
}
if (-not $SkipInstaller) {
    Write-Host "  - installer/MatrixQuesGen_Setup_$Version.exe"
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Test: .\dist\MatrixQuesGen.exe"
Write-Host "2. Create GitHub release v$Version"
Write-Host "3. Upload MatrixQuesGen_Setup_$Version.exe"
