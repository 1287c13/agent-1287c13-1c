@echo off
rem Один проход агента очереди: взять задачу из inbox и передать её в Cline.
chcp 65001 >nul
setlocal
for %%i in ("%~dp0..") do set "ROOT=%%~fi"
py -3 "%ROOT%\integration\agent.py" --root "%ROOT%" --process --deliver auto --json %*
if errorlevel 1 pause
endlocal
