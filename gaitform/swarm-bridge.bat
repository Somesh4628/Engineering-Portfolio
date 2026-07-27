@echo off
:: SWARM BRIDGE PROTOCOL v3.4 - FreeLLMAPI Multi-Provider Architecture
:: Writes live output to swarm.log so you can watch it in the IDE terminal.

if "%~1"=="" (
    echo [ ERROR ] No prompt provided!
    echo Usage: swarm-bridge.bat "Your instruction here"
    exit /b 1
)

set LOGFILE=%~dp0swarm.log

echo. > "%LOGFILE%"
echo ============================================= >> "%LOGFILE%"
echo  SWARM BRIDGE: ACTIVE >> "%LOGFILE%"
echo  %DATE% %TIME% >> "%LOGFILE%"
echo ============================================= >> "%LOGFILE%"
echo Checking FreeLLMAPI local router... >> "%LOGFILE%"

:: Load .env keys if available
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do set "%%a=%%b"
)

:: Check if FreeLLMAPI is online
curl -s -o NUL -w "%%{http_code}" http://localhost:3001/api/health > "%TEMP%\fllm_status.txt" 2>NUL
set /p FLLM_STATUS=<"%TEMP%\fllm_status.txt"

set FLLM_ONLINE=0
if "%FLLM_STATUS%"=="200" set FLLM_ONLINE=1
if "%FLLM_STATUS%"=="401" set FLLM_ONLINE=1

if "%FLLM_ONLINE%"=="1" (
    echo [ INFO ] FreeLLMAPI ONLINE - 161 models, auto-failover active >> "%LOGFILE%"
    set ANTHROPIC_BASE_URL=http://localhost:3001
    set ANTHROPIC_AUTH_TOKEN=freellmapi-local
) else (
    echo [ WARN ] FreeLLMAPI offline - Status: %FLLM_STATUS% - Using OpenRouter directly >> "%LOGFILE%"
    set ANTHROPIC_BASE_URL=https://openrouter.ai/api
    set ANTHROPIC_AUTH_TOKEN=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
)

echo [ INFO ] Executing: %~1 >> "%LOGFILE%"
echo. >> "%LOGFILE%"

:: Run claude and pipe all output to the log file live
claude -p "%~1" --dangerously-skip-permissions --print < NUL >> "%LOGFILE%" 2>&1

echo. >> "%LOGFILE%"
echo [ SWARM BRIDGE: TASK COMPLETED ] >> "%LOGFILE%"
echo ============================================= >> "%LOGFILE%"
