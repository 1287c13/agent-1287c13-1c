<#
.SYNOPSIS
    Погасить watcher очереди, поднятый scripts\start-watcher.ps1.

.DESCRIPTION
    Останавливает процессы с integration\watcher.py в командной строке (pid-файл
    queue\watcher.pid - только подсказка: watcher мог быть запущен и вручную),
    снимает pid-файл и замок queue\.watcher.lock. Замок живого процесса watcher
    обновляет сам, а после остановки он остаётся и через две минуты уже не мешает;
    снимаем сразу, чтобы следующий запуск не ждал.

    Очередь не чистится: задачи в queue\inbox и итоги в queue\outbox остаются на месте.
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
$configPath = Join-Path $Root 'deploy\config.json'
if (Test-Path $configPath) {
    try {
        $config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($config.root -and (Test-Path ([string]$config.root))) { $Root = [string]$config.root }
    } catch { }
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

$pidFile = Join-Path $Root 'queue\watcher.pid'
if (Test-Path $pidFile) { Remove-Item $pidFile -Force -ErrorAction SilentlyContinue }
$lockFile = Join-Path $Root 'queue\.watcher.lock'
if (Test-Path $lockFile) { Remove-Item $lockFile -Force -ErrorAction SilentlyContinue }

if ($stopped.Count -gt 0) {
    Write-Host "[ok] watcher остановлен: pid $($stopped -join ', ')"
    Write-Host '     задачи в очереди не тронуты; поднять снова - scripts\start-watcher.ps1'
} else {
    Write-Host '[ok] watcher не запущен: останавливать нечего'
    Write-Host '     поднять - scripts\start-watcher.ps1'
}
exit 0
