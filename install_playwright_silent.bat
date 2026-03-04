@echo off
:: Silent Playwright Chromium installer
:: Called automatically by MatrixQuesGen Setup
setlocal
set LOG=%TEMP%\matrixquesgen_playwright_install.log
echo [%DATE% %TIME%] Starting Playwright Chromium install >> "%LOG%"

:: Try to find Python (3.8+)
set PYTHON=
for %%P in (python python3 py) do (
    %%P --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON=%%P
        goto :found_python
    )
)
echo [%DATE% %TIME%] Python not found, skipping Playwright install >> "%LOG%"
exit /b 0

:found_python
echo [%DATE% %TIME%] Found Python: %PYTHON% >> "%LOG%"

:: Install playwright package if not present
%PYTHON% -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] Installing playwright package... >> "%LOG%"
    %PYTHON% -m pip install playwright --quiet >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo [%DATE% %TIME%] Failed to install playwright package >> "%LOG%"
        exit /b 0
    )
)

:: Install Chromium browser
echo [%DATE% %TIME%] Installing Chromium browser... >> "%LOG%"
%PYTHON% -m playwright install chromium >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%DATE% %TIME%] Chromium install failed (non-critical) >> "%LOG%"
) else (
    echo [%DATE% %TIME%] Chromium installed successfully >> "%LOG%"
)

exit /b 0
