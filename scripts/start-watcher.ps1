<#
.SYNOPSIS
    Поднять watcher очереди фоном: разбор журнала и передача задач в Cline.

.DESCRIPTION
    Watcher - единственный разборщик очереди (queue\tasks.jsonl): он раскладывает строки
    журнала по inbox/failed и передаёт задачи в Cline. Пока он не работает, задача,
    отправленная из окна или по HTTP, остаётся строкой в журнале и до агента не доходит.
    Поэтому watcher поднимают до постановки задач и держат запущенным: процесс живёт,
    пока его не погасят явно (scripts\stop-watcher.ps1). Сбой отдельного прохода его
    не завершает - ошибка уходит в logs\watcher.log и в queue\bridge.jsonl.

    Скрипт идемпотентен: если watcher уже работает, второй не поднимается (повторный
    запуск - только ключом -Force, который сначала гасит старый). Проверка идёт по
    живым процессам с integration\watcher.py в командной строке, а pid последнего
    запуска лежит в queue\watcher.pid.

    Режим доставки, интервал и вебхук берутся из deploy\config.json (секция watcher),
    ключи командной строки их перекрывают.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-watcher.ps1
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-watcher.ps1 -Deliver echo
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-watcher.ps1 -Force
#>
[CmdletBinding()]
param(
    [string] $Root,
    [string] $Deliver,
    [double] $Interval = 0,
    [string] $WebhookUrl,
    [switch] $Force
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

function Read-Json ([string]$Path) {
    if (-not (Test-Path $Path)) { return $null }
    try { return (Get-Content $Path -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { return $null }
}

function Get-WatcherProcesses {
    # Ищем живые процессы watcher-а по командной строке: pid-файл может отсутствовать,
    # если watcher запущен вручную или через deploy\run-watcher.bat.
    $found = @()
    foreach ($p in (Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
        if (-not $p.CommandLine) { continue }
        if ($p.ProcessId -eq $PID) { continue }
        if ($p.CommandLine -notlike '*watcher.py*') { continue }
        if ($p.CommandLine -like '*stop-watcher*') { continue }
        $found += $p
    }
    return @($found)
}

if (-not $Root) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}
$config = Read-Json (Join-Path $Root 'deploy\config.json')
if ($config -and $config.root -and (Test-Path ([string]$config.root))) { $Root = [string]$config.root }
$Root = (Resolve-Path $Root).Path
Write-Host "корень харнесса: $Root"

if (-not $Deliver) {
    if ($config -and $config.watcher -and $config.watcher.deliver) { $Deliver = [string]$config.watcher.deliver }
    else { $Deliver = 'uri' }
}
if ($Interval -le 0) {
    if ($config -and $config.watcher -and $config.watcher.interval) { $Interval = [double]$config.watcher.interval }
    else { $Interval = 2.0 }
}
if (-not $WebhookUrl -and $config -and $config.watcher -and $config.watcher.webhook_url) {
    $WebhookUrl = [string]$config.watcher.webhook_url
}
$intervalText = $Interval.ToString([System.Globalization.CultureInfo]::InvariantCulture)

$pythonExe = 'py'
$pythonArgs = @('-3')
if ($config -and $config.python) {
    $parts = @(([string]$config.python).Split(' ') | Where-Object { $_ })
    if ($parts.Count -gt 0) {
        $pythonExe = $parts[0]
        $pythonArgs = @()
        if ($parts.Count -gt 1) { $pythonArgs = @($parts[1..($parts.Count - 1)]) }
    }
}
$watcher = Join-Path $Root 'integration\watcher.py'
if (-not (Test-Path $watcher)) { throw "нет файла watcher-а: $watcher" }

$queueDir = Join-Path $Root 'queue'
$pidFile = Join-Path $queueDir 'watcher.pid'
$lockFile = Join-Path $queueDir '.watcher.lock'
$logDir = Join-Path $Root 'logs'
$logFile = Join-Path $logDir 'watcher.log'
$errFile = Join-Path $logDir 'watcher.err.log'
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path $PSCommandPath).Path }

$alive = Get-WatcherProcesses
if ($alive.Count -gt 0 -and -not $Force) {
    Write-Host "[ok] watcher уже запущен: pid $(($alive | ForEach-Object { $_.ProcessId }) -join ', ')"
    Write-Host "     режим: $Deliver, интервал: $intervalText с, лог: $logFile"
    Write-Host '     перезапуск: -Force; остановка: scripts\stop-watcher.ps1'
    exit 0
}
if ($alive.Count -gt 0) {
    Write-Host "перезапуск: гашу текущий watcher (pid $(($alive | ForEach-Object { $_.ProcessId }) -join ', '))"
    $stopper = Join-Path $scriptDir 'stop-watcher.ps1'
    if (Test-Path $stopper) { & $stopper -Root $Root | Out-Null }
    else { foreach ($p in $alive) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue } }
}

New-Item -ItemType Directory -Force -Path $queueDir, $logDir | Out-Null
# Замок мёртвого watcher-а (queue\.watcher.lock) снимаем сами: он обновляется каждым
# проходом, а живого процесса рядом уже нет - иначе новый watcher не подхватит очередь.
if (Test-Path $lockFile) { Remove-Item $lockFile -Force -ErrorAction SilentlyContinue }

$argLine = (@($pythonArgs) + @('"' + $watcher + '"', '--root', '"' + $Root + '"', '--run', '--process',
    '--deliver', $Deliver, '--interval', $intervalText)) -join ' '
if ($WebhookUrl) { $argLine += ' --webhook-url ' + $WebhookUrl }

Write-Host "запускаю: $pythonExe $argLine"
$proc = Start-Process -FilePath $pythonExe -ArgumentList $argLine -WorkingDirectory $Root `
    -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errFile -PassThru

$payload = [ordered]@{
    pid        = $proc.Id
    started_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
    deliver    = $Deliver
    interval_s = $Interval
    log        = $logFile
    root       = $Root
} | ConvertTo-Json
[System.IO.File]::WriteAllText($pidFile, $payload, (New-Object System.Text.UTF8Encoding($false)))

$held = $false
for ($i = 0; $i -lt 24; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-Path $lockFile) { $held = $true; break }
    if (-not (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)) { break }
}
if ($held) {
    Write-Host "[ok] watcher работает: pid $($proc.Id), режим $Deliver, интервал $intervalText с"
    Write-Host "     лог: $logFile (ошибки: $errFile)"
    Write-Host "     pid-файл: $pidFile"
    Write-Host '     остановка: scripts\stop-watcher.ps1'
    exit 0
}
Write-Host '[FAIL] watcher не взял замок очереди: смотрите лог'
foreach ($f in @($errFile, $logFile)) {
    if (Test-Path $f) { Write-Host "--- $f"; Get-Content $f -Tail 20 -Encoding UTF8 }
}
exit 1

