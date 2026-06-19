@echo off
setlocal EnableExtensions

REM PQViewer Remote Open v1.2 launcher for Windows.
REM This script resolves paths relative to the tools directory.

set "TOOLS_DIR=%~dp0"
for %%I in ("%TOOLS_DIR%.") do set "TOOLS_DIR=%%~fI"
for %%I in ("%TOOLS_DIR%..") do set "REPO_ROOT=%%~fI"

set "VIEWER_DIR=%REPO_ROOT%"
set "AGENT=%TOOLS_DIR%\pqv_agent.py"
set "TOKEN_FILE=%TOOLS_DIR%\pqv_token.txt"
set "PORT=18765"

REM Prefer an existing environment variable. Otherwise read tools\pqv_token.txt.
if "%PQV_TOKEN%"=="" (
    if exist "%TOKEN_FILE%" (
        set /p PQV_TOKEN=<"%TOKEN_FILE%"
    )
)

if "%PQV_TOKEN%"=="" (
    echo [ERROR] PQV_TOKEN is not set and token file was not found:
    echo   %TOKEN_FILE%
    echo.
    echo Run tools\setup_windows_path.bat first.
    pause
    exit /b 1
)

if not exist "%VIEWER_DIR%\index.html" (
    echo [ERROR] index.html was not found:
    echo   %VIEWER_DIR%\index.html
    pause
    exit /b 1
)

if not exist "%AGENT%" (
    echo [ERROR] pqv_agent.py was not found:
    echo   %AGENT%
    pause
    exit /b 1
)

cd /d "%VIEWER_DIR%"

echo Starting PQViewer Remote Open agent...
echo Viewer directory: %VIEWER_DIR%
echo Agent: %AGENT%
echo Port: %PORT%
echo Token file: %TOKEN_FILE%
echo.
echo Keep this window open while using pqv-open from the remote machine.
echo The fixed token is already set for this agent process.
echo.

py -3 "%AGENT%" --viewer-root "." --host 127.0.0.1 --host-for-url 127.0.0.1 --port %PORT% --token "%PQV_TOKEN%"

echo.
echo PQViewer agent has stopped.
pause
