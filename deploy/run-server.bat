@echo off
rem Локальный сервер очереди (проверка без Passenger). Настройки - deploy\config.json.
chcp 65001 >nul
setlocal
for %%i in ("%~dp0..") do set "ROOT=%%~fi"
py -3 "%ROOT%\integration\transport\http_server.py" --root "%ROOT%" --config "%ROOT%\deploy\config.json"
pause
endlocal
