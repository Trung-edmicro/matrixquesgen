<#
.SYNOPSIS
    Bump version number across all project files.

.PARAMETER Version
    New version string e.g. "1.2.3"

.EXAMPLE
    .\bump_version.ps1 -Version 1.2.3
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

# Validate semver format
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Error "Version must be in semver format: MAJOR.MINOR.PATCH (e.g. 1.2.3)"
    exit 1
}

Write-Host "Bumping version to $Version..." -ForegroundColor Cyan

# Helper: write UTF-8 WITHOUT BOM (PowerShell 5.x Set-Content -Encoding UTF8 adds BOM)
function Write-UTF8NoBOM([string]$Path, [string]$Content) {
    [System.IO.File]::WriteAllText(
        (Resolve-Path $Path -ErrorAction SilentlyContinue ?? $Path),
        $Content,
        [System.Text.UTF8Encoding]::new($false)
    )
}

# 1. version.py
$versionPy = "version.py"
$content = (Get-Content $versionPy -Raw) -replace '__version__ = ".*"', "__version__ = `"$Version`""
Write-UTF8NoBOM $versionPy $content
Write-Host "  OK version.py" -ForegroundColor Green

# 2. inno_setup.iss
$issFile = "inno_setup.iss"
$content = (Get-Content $issFile -Raw) `
    -replace 'AppVersion=.*', "AppVersion=$Version" `
    -replace 'OutputBaseFilename=.*', "OutputBaseFilename=MatrixQuesGen_Setup_$Version"
Write-UTF8NoBOM $issFile $content
Write-Host "  OK inno_setup.iss" -ForegroundColor Green

# 3. client/package.json
$packageJson = "client\package.json"
if (Test-Path $packageJson) {
    $pkg = Get-Content $packageJson -Raw | ConvertFrom-Json
    $pkg.version = $Version
    $newContent = $pkg | ConvertTo-Json -Depth 10
    Write-UTF8NoBOM $packageJson $newContent
    Write-Host "  OK client/package.json" -ForegroundColor Green
}

Write-Host ""
Write-Host "Version bumped to $Version" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review changes: git diff"
Write-Host "  2. Commit: git add -A ; git commit -m `"chore: bump version to $Version`""
Write-Host "  3. Tag:    git tag v$Version"
Write-Host "  4. Push:   git push origin main --tags"
Write-Host "     -> GitHub Actions will automatically build & publish the release."
Write-Host ""
Write-Host "Or to release manually after building:" -ForegroundColor Yellow
Write-Host "  .\build_release.ps1"
Write-Host "  .\create_release.ps1 -Version $Version"
