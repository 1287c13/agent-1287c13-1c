@echo off
rem Окно постановки задач во внешнюю очередь. Обёртка: вся логика в gui\AgentGUI.py.
chcp 65001 >nul
setlocal
for %%i in ("%~dp0..") do set "ROOT=%%~fi"
py -3 "%ROOT%\gui\AgentGUI.py" --root "%ROOT%" %*
if errorlevel 1 pause
endlocal
