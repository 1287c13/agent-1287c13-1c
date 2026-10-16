@echo off
rem Сервер HTTP-интерфейса очереди (локальная проверка). Хостинг - transport\wsgi.py.
chcp 65001 >nul
setlocal
for %%i in ("%~dp0..") do set "ROOT=%%~fi"
set "CFG=%ROOT%\deploy\config.json"
set "HOST=127.0.0.1"
set "PORT=8760"
if exist "%CFG%" for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "$c = Get-Content '%CFG%' -Raw -Encoding UTF8 | ConvertFrom-Json; if ($c.server.host) { $c.server.host } else { '127.0.0.1' }"`) do set "HOST=%%v"
if exist "%CFG%" for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "$c = Get-Content '%CFG%' -Raw -Encoding UTF8 | ConvertFrom-Json; if ($c.server.port) { $c.server.port } else { '8760' }"`) do set "PORT=%%v"
if exist "%CFG%" for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "$c = Get-Content '%CFG%' -Raw -Encoding UTF8 | ConvertFrom-Json; $c.server.token"`) do set "INTEGRATION_TOKEN=%%v"
py -3 "%ROOT%\integration\transport\http_server.py" --root "%ROOT%" --host %HOST% --port %PORT%
pause
endlocal
