param(
    [Parameter(Mandatory = $true)]
    [string]$Version,
    [string]$Token = $env:GITHUB_TOKEN,
    [string]$Repo = $(if ($env:GITHUB_REPO) { $env:GITHUB_REPO } else { "Trung-edmicro/matrixquesgen" }),
    [string]$Changelog = ""
)

if (-not $Token) {
    Write-Error "GitHub token not found. Set GITHUB_TOKEN env var or pass -Token."
    exit 1
}
if (-not $Repo) {
    Write-Error "GitHub repo not found. Set GITHUB_REPO env var (e.g. Trung-edmicro/matrixquesgen.git) or pass -Repo."
    exit 1
}

$installerName = "MatrixQuesGen_Setup_$Version.exe"
$installerPath = "installer\$installerName"
if (-not (Test-Path $installerPath)) {
    Write-Error "Installer not found at $installerPath. Run build_release.ps1 first."
    exit 1
}

if (-not $Changelog) {
    $Changelog = "MatrixQuesGen v$Version"
}

$headers = @{
    "Authorization"        = "Bearer $Token"
    "Accept"               = "application/vnd.github+json"
    "Content-Type"         = "application/json"
    "X-GitHub-Api-Version" = "2022-11-28"
}

Write-Host "Creating GitHub release v$Version..." -ForegroundColor Cyan

# Delete existing release + tag if they already exist (allows re-running for same version)
try {
    $existing = Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$Repo/releases/tags/v$Version" `
        -Method Get `
        -Headers $headers `
        -ErrorAction Stop
    Write-Host "  Found existing release (id=$($existing.id)), deleting..." -ForegroundColor Yellow
    Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$Repo/releases/$($existing.id)" `
        -Method Delete `
        -Headers $headers | Out-Null
    Write-Host "  Deleted existing release." -ForegroundColor Yellow
} catch { <# not found — nothing to delete #> }

try {
    Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$Repo/git/refs/tags/v$Version" `
        -Method Delete `
        -Headers $headers `
        -ErrorAction Stop | Out-Null
    Write-Host "  Deleted existing tag v$Version." -ForegroundColor Yellow
} catch { <# tag didn't exist #> }

$releaseBody = @{
    tag_name   = "v$Version"
    name       = "MatrixQuesGen v$Version"
    body       = $Changelog
    draft      = $false
    prerelease = $false
} | ConvertTo-Json -Compress

try {
    $release = Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$Repo/releases" `
        -Method Post `
        -Headers $headers `
        -Body $releaseBody

    Write-Host "OK Release created: $($release.html_url)" -ForegroundColor Green

    # Upload binary asset
    Write-Host "Uploading $installerName..." -ForegroundColor Cyan
    $uploadUrl = "https://uploads.github.com/repos/$Repo/releases/$($release.id)/assets?name=$installerName"

    $uploadHeaders = @{
        "Authorization"        = "Bearer $Token"
        "Accept"               = "application/vnd.github+json"
        "Content-Type"         = "application/octet-stream"
        "X-GitHub-Api-Version" = "2022-11-28"
    }

    $fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $installerPath))

    $asset = Invoke-RestMethod `
        -Uri $uploadUrl `
        -Method Post `
        -Headers $uploadHeaders `
        -Body $fileBytes

    Write-Host "OK Asset uploaded: $($asset.browser_download_url)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Release v$Version published successfully!" -ForegroundColor Green
    Write-Host "URL: $($release.html_url)" -ForegroundColor Cyan

}
catch {
    Write-Host "Failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message -ForegroundColor Red
    }
    exit 1
}
