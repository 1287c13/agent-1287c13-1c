<#
.SYNOPSIS
    Погасить watcher очереди, поднятый scripts\start-watcher.ps1.

.DESCRIPTION
    Останавливает процессы с integration\watcher.py в командной строке (pid-файл
    temp\queue\watcher.pid - только подсказка: watcher мог быть запущен и вручную),
    снимает pid-файл и замок temp\queue\.watcher.lock. Замок живого процесса watcher
    обновляет сам, а после остановки он остаётся и через две минуты уже не мешает;
    снимаем сразу, чтобы следующий запуск не ждал.

    Очередь не чистится: она живёт на сервере, а здесь лежит только рабочий каталог
    задачи (temp\queue\<id>) - незавершённые каталоги не удаляются, по ним видно,
    на чём остановились.

    Если watcher не запущен, скрипт просто сообщает об этом (код возврата 0).

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop-watcher.ps1
#>
[CmdletBinding()]
param(
    [string] $Root
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

if (-not $Root) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}
$Root = (Resolve-Path $Root).Path

$stopped = @()
foreach ($p in (Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
    if (-not $p.CommandLine) { continue }
    if ($p.ProcessId -eq $PID) { continue }
    if ($p.CommandLine -notlike '*watcher.py*') { continue }
    if ($p.CommandLine -like '*stop-watcher*') { continue }
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    $stopped += $p.ProcessId
}

$workDir = Join-Path $Root 'temp\queue'
$pidFile = Join-Path $workDir 'watcher.pid'
if (Test-Path $pidFile) { Remove-Item $pidFile -Force -ErrorAction SilentlyContinue }
$lockFile = Join-Path $workDir '.watcher.lock'
if (Test-Path $lockFile) { Remove-Item $lockFile -Force -ErrorAction SilentlyContinue }

if ($stopped.Count -gt 0) {
    Write-Host "[ok] watcher остановлен: pid $($stopped -join ', ')"
    Write-Host '     очередь на сервере не тронута; поднять снова - scripts\start-watcher.ps1'
} else {
    Write-Host '[ok] watcher не запущен: останавливать нечего'
    Write-Host '     поднять - scripts\start-watcher.ps1'
}
exit 0
