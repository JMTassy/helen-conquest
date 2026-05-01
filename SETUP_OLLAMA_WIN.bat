@echo off
REM ============================================================================
REM SETUP_OLLAMA_WIN.bat — Make Windows Ollama reachable from WSL2
REM
REM Right-click this file -> "Run as administrator"
REM (or run it from a PowerShell Admin window: .\SETUP_OLLAMA_WIN.bat)
REM
REM Does:
REM   1. Self-elevates to Administrator
REM   2. Sets OLLAMA_HOST=0.0.0.0:11434 (User scope, persists across reboots)
REM   3. Adds Windows Firewall inbound rule for TCP 11434
REM   4. Stops any running ollama.exe and relaunches it with the new env
REM   5. Verifies Ollama is listening on 0.0.0.0:11434
REM ============================================================================

REM ---- Self-elevate ----
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator elevation...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo ================================================================
echo   SETUP_OLLAMA_WIN — Making Ollama reachable from WSL2
echo ================================================================
echo.

echo [1/4] Setting OLLAMA_HOST=0.0.0.0:11434 (User scope, persistent)...
setx OLLAMA_HOST "0.0.0.0:11434" >nul
echo   OK
echo.

echo [2/4] Adding Windows Firewall inbound rule for TCP 11434...
powershell -NoProfile -Command "if (-not (Get-NetFirewallRule -DisplayName 'Ollama WSL2' -ErrorAction SilentlyContinue)) { New-NetFirewallRule -DisplayName 'Ollama WSL2' -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow | Out-Null; Write-Host '  Rule created' } else { Write-Host '  Rule already exists' }"
echo.

echo [3/4] Restarting Ollama with new environment...
powershell -NoProfile -Command "Get-Process ollama* -ErrorAction SilentlyContinue | Stop-Process -Force"
timeout /t 2 /nobreak >nul
REM Set process-level env so the relaunched ollama inherits it
set OLLAMA_HOST=0.0.0.0:11434
start "" ollama serve
timeout /t 4 /nobreak >nul
echo   OK
echo.

echo [4/4] Verifying Ollama is listening on 0.0.0.0:11434...
powershell -NoProfile -Command "$r = try { Invoke-WebRequest -Uri 'http://127.0.0.1:11434/api/tags' -UseBasicParsing -TimeoutSec 3 } catch { $null }; if ($r -and $r.StatusCode -eq 200) { Write-Host '  OK - Ollama responding' -ForegroundColor Green } else { Write-Host '  WARNING - Ollama not responding on localhost. Check the Ollama tray icon.' -ForegroundColor Yellow }"
echo.

echo ================================================================
echo   DONE on Windows side.
echo ================================================================
echo.
echo Next: open Ubuntu (Start menu -^> Ubuntu, or 'wsl' in PowerShell)
echo and run the one-line bootstrap shown in your chat.
echo.
pause
