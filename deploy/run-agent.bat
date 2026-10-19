@echo off
chcp 65001 >nul
setlocal
for %%i in ("%~dp0..") do set "ROOT=%%~fi"
py -3 "%ROOT%\integration\agent.py" --root "%ROOT%" --config "%ROOT%\deploy\config.json" --health
pause
endlocal
