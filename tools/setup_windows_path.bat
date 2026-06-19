@echo off
setlocal EnableExtensions

REM PQViewer Remote Open Windows setup.
REM This script:
REM   1. Detects the repository root and tools directory.
REM   2. Generates a fixed token if tools\pqv_token.txt does not exist.
REM   3. Adds tools to the user PATH.
REM   4. Sets PQVIEWER_ROOT, PQVIEWER_TOOLS, and PQV_TOKEN as user environment variables.

set "TOOLS_DIR=%~dp0"
for %%I in ("%TOOLS_DIR%.") do set "TOOLS_DIR=%%~fI"
for %%I in ("%TOOLS_DIR%..") do set "REPO_ROOT=%%~fI"
set "TOKEN_FILE=%TOOLS_DIR%\pqv_token.txt"

if not exist "%REPO_ROOT%\index.html" (
    echo [ERROR] index.html was not found:
    echo   %REPO_ROOT%\index.html
    echo.
    echo Please run this script from the tools directory inside the PQViewer repository.
    pause
    exit /b 1
)

if not exist "%TOOLS_DIR%\pqv_agent.py" (
    echo [ERROR] pqv_agent.py was not found:
    echo   %TOOLS_DIR%\pqv_agent.py
    pause
    exit /b 1
)

if not exist "%TOOLS_DIR%\pqv_agent.bat" (
    echo [ERROR] pqv_agent.bat was not found:
    echo   %TOOLS_DIR%\pqv_agent.bat
    pause
    exit /b 1
)

if not exist "%TOKEN_FILE%" (
    echo Generating a fixed PQViewer token...
    py -3 -c "import secrets, pathlib; pathlib.Path(r'%TOKEN_FILE%').write_text(secrets.token_urlsafe(32), encoding='utf-8')"
    if errorlevel 1 (
        echo [ERROR] Failed to generate token with Python launcher py -3.
        echo Try installing Python or generate tools\pqv_token.txt manually.
        pause
        exit /b 1
    )
)

set /p PQV_TOKEN=<"%TOKEN_FILE%"

if "%PQV_TOKEN%"=="" (
    echo [ERROR] Token file is empty:
    echo   %TOKEN_FILE%
    pause
    exit /b 1
)

echo PQViewer repository root:
echo   %REPO_ROOT%
echo.
echo PQViewer tools directory:
echo   %TOOLS_DIR%
echo.
echo Fixed token file:
echo   %TOKEN_FILE%
echo.
echo Token:
echo   %PQV_TOKEN%
echo.

REM Set user environment variables.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "[Environment]::SetEnvironmentVariable('PQVIEWER_ROOT', '%REPO_ROOT%', 'User');" ^
  "[Environment]::SetEnvironmentVariable('PQVIEWER_TOOLS', '%TOOLS_DIR%', 'User');" ^
  "[Environment]::SetEnvironmentVariable('PQV_TOKEN', '%PQV_TOKEN%', 'User')"

REM Add tools directory to the user PATH if it is not already present.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$tools = [IO.Path]::GetFullPath('%TOOLS_DIR%').TrimEnd('\');" ^
  "$path = [Environment]::GetEnvironmentVariable('Path', 'User');" ^
  "if ([string]::IsNullOrWhiteSpace($path)) { $items = @() } else { $items = $path -split ';' }" ^
  "$exists = $false;" ^
  "foreach ($item in $items) { if ($item -and ([IO.Path]::GetFullPath($item).TrimEnd('") -ieq $tools)) { $exists = $true } }" ^
  "if (-not $exists) { $newPath = (($items + $tools) | Where-Object { $_ -ne '' }) -join ';'; [Environment]::SetEnvironmentVariable('Path', $newPath, 'User'); Write-Host 'Added tools directory to the user PATH.' } else { Write-Host 'Tools directory is already in the user PATH.' }"

if errorlevel 1 (
    echo [WARNING] PATH setup may have failed. You can still run tools\pqv_agent.bat directly.
)

echo.
echo Setup finished.
echo.
echo IMPORTANT:
echo   Open a new Command Prompt, PowerShell, or Windows Terminal to load the updated PATH.
echo.
echo Local usage after reopening the terminal:
echo   pqv_agent.bat
echo.
echo Remote setup command using this fixed token:
echo   bash tools/setup_remote_path.sh --token %PQV_TOKEN%
echo.
echo If you do not want to pass the token on the command line, copy this token
echo into remote tools/pqv_token.txt, then run:
echo   bash tools/setup_remote_path.sh

echo.
pause
