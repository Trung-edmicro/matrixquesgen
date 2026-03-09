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
$content | Set-Content "inno_setup.iss" -Encoding UTF8

if (-not $SkipBuild) {
    Write-Host "Building executable with PyInstaller..."
    $pythonExe = ".venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) { $pythonExe = "python" }
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
    } else {
        Write-Warning "Inno Setup not found. Please install Inno Setup 6 and run again."
        Write-Host "Download from: https://jrsoftware.org/isdl.php"
    }
}

Write-Host ""
Write-Host "Build completed!" -ForegroundColor Green
Write-Host "Files created:"
if (-not $SkipBuild) {
    Write-Host "  - dist/MatrixQuesGen.exe"
}
if (-not $SkipInstaller) {
    Write-Host "  - installer/MatrixQuesGen_Installer.exe"
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Test the executable: .\dist\MatrixQuesGen.exe"
Write-Host "2. Create a GitHub release with tag v$Version"
Write-Host "3. Upload MatrixQuesGen_Installer.exe as release asset"
Write-Host "4. Update GITHUB_REPO in update.py with your repository"