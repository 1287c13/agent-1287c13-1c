@echo off
rem Watcher очереди: разбирает журнал и передаёт задачи в Cline. Оставьте окно открытым.
chcp 65001 >nul
setlocal
for %%i in ("%~dp0..") do set "ROOT=%%~fi"
set "CFG=%ROOT%\deploy\config.json"
set "DELIVER=auto"
set "INTERVAL=2.0"
set "WEBHOOK="
if exist "%CFG%" for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "$c = Get-Content '%CFG%' -Raw -Encoding UTF8 | ConvertFrom-Json; if ($c.watcher.deliver) { $c.watcher.deliver } else { 'auto' }"`) do set "DELIVER=%%v"
if exist "%CFG%" for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "$c = Get-Content '%CFG%' -Raw -Encoding UTF8 | ConvertFrom-Json; if ($c.watcher.interval) { $c.watcher.interval.ToString([System.Globalization.CultureInfo]::InvariantCulture) } else { '2.0' }"`) do set "INTERVAL=%%v"
if exist "%CFG%" for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "$c = Get-Content '%CFG%' -Raw -Encoding UTF8 | ConvertFrom-Json; if ($c.watcher.webhook_url) { $c.watcher.webhook_url }"`) do set "WEBHOOK=%%v"
set "EXTRA="
if not "%WEBHOOK%"=="" set "EXTRA=--webhook-url %WEBHOOK%"
py -3 "%ROOT%\integration\watcher.py" --root "%ROOT%" --run --process --deliver %DELIVER% --interval %INTERVAL% %EXTRA%
pause
endlocal
