<#
.SYNOPSIS
    Поднять watcher очереди фоном: забирает задачи с сервера и передаёт их в Cline.

.DESCRIPTION
    Watcher - единственный процесс на машине агента, который берёт задачи с сервера.
    Пока он не работает, задача остаётся в очереди на сервере и до Cline не доходит.
    Поэтому watcher поднимают до постановки задач и держат запущенным: процесс живёт,
    пока его не погасят явно (scripts\stop-watcher.ps1). Сбой отдельного прохода его
    не завершает - ошибка печатается в окне watcher-а.

    Скрипт идемпотентен: если watcher уже работает, второй не поднимается (повторный
    запуск - только ключом -Force, который сначала гасит старый). Проверка идёт по
    живым процессам с integration\watcher.py в командной строке, а pid последнего
    запуска лежит в temp\queue\watcher.pid.

    Адрес сервера, ключ агента, режим доставки и паузы берутся из deploy\config.json
    (секция agent), ключи командной строки их перекрывают.

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
    [string] $Server,
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
$Root = (Resolve-Path $Root).Path
Write-Host "корень харнесса: $Root"

if (-not $Deliver) {
    if ($config -and $config.agent -and $config.agent.deliver) { $Deliver = [string]$config.agent.deliver }
    else { $Deliver = 'uri' }
}
if ($Interval -le 0) {
    if ($config -and $config.agent -and $config.agent.interval) { $Interval = [double]$config.agent.interval }
    else { $Interval = 2.0 }
}
if (-not $Server -and $config -and $config.agent -and $config.agent.server_url) {
    $Server = [string]$config.agent.server_url
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

$workDir = Join-Path $Root 'temp\queue'
$pidFile = Join-Path $workDir 'watcher.pid'
$lockFile = Join-Path $workDir '.watcher.lock'

$alive = Get-WatcherProcesses
if ($alive.Count -gt 0 -and -not $Force) {
    Write-Host "[ok] watcher уже запущен: pid $(($alive | ForEach-Object { $_.ProcessId }) -join ', ')"
    Write-Host "     режим: $Deliver, пауза: $intervalText с"
    Write-Host '     перезапуск: -Force; остановка: scripts\stop-watcher.ps1'
    exit 0
}
if ($alive.Count -gt 0) {
    Write-Host "перезапуск: гашу текущий watcher (pid $(($alive | ForEach-Object { $_.ProcessId }) -join ', '))"
    $stopper = Join-Path $scriptDir 'stop-watcher.ps1'
    if (Test-Path $stopper) { & $stopper -Root $Root | Out-Null }
    else { foreach ($p in $alive) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue } }
}

New-Item -ItemType Directory -Force -Path $workDir | Out-Null
# Замок мёртвого watcher-а снимаем сами: он обновляется каждым проходом, а живого
# процесса рядом уже нет - иначе новый watcher не подхватит очередь.
if (Test-Path $lockFile) { Remove-Item $lockFile -Force -ErrorAction SilentlyContinue }

$argLine = (@($pythonArgs) + @('"' + $watcher + '"', '--root', '"' + $Root + '"', '--run',
    '--deliver', $Deliver, '--interval', $intervalText)) -join ' '
if ($Server) { $argLine += ' --server "' + $Server + '"' }

Write-Host "запускаю: $pythonExe $argLine"
$proc = Start-Process -FilePath $pythonExe -ArgumentList $argLine -WorkingDirectory $Root -PassThru

$payload = [ordered]@{
    pid        = $proc.Id
    started_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
    deliver    = $Deliver
    interval_s = $Interval
    server     = $Server
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
    Write-Host "[ok] watcher работает: pid $($proc.Id), режим $Deliver, пауза $intervalText с"
    Write-Host "     сервер: $Server"
    Write-Host "     pid-файл: $pidFile"
    Write-Host '     остановка: scripts\stop-watcher.ps1'
    exit 0
}
Write-Host '[FAIL] watcher не взял замок очереди: причина - в окне watcher-а'
exit 1
