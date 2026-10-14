#Requires -Version 5.1
<#
.SYNOPSIS
    Погасить встроенный сервер 1C MCP Toolkit и освободить занятый клиентский сеанс 1С.

.DESCRIPTION
    Зачем: сеанс toolkit - это клиент базы, а прогону Vanessa Automation нужны ДВА
    клиента той же базы. Пока сеанс toolkit жив, платформа отвечает "Превышено
    ограничение лицензии для разработчиков на количество клиентов информационной базы".
    Скрипт освобождает базу от этого сеанса.

    Порядок работы:
      1. если /health не отвечает и процессов 1С с обработкой toolkit нет - гасить нечего;
         сеанс, который есть, но не отвечает (завис), виден по процессам и всё равно гасится;
      2. штатный путь: POST /api/close_1c_session - обработка закрывает свой сеанс 1С
         сама (документированный эндпоинт toolkit, он же инструмент close_1c_session);
      3. резервный путь (он же режим -Force): остановка процессов 1С, в командной
         строке которых есть MCP_Toolkit.epf;
      4. результат - только когда /health перестал отвечать и процессов не осталось.

.PARAMETER Port
    Порт встроенного сервера (по умолчанию 6003).

.PARAMETER TimeoutSec
    Сколько секунд ждать закрытия сеанса на каждом шаге (по умолчанию 60).

.PARAMETER Force
    Пропустить штатный путь и сразу остановить процесс 1С - для случая, когда
    сервер висит или не отвечает на /api/*.

.PARAMETER NoRun
    Только показать, что будет сделано.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-toolkit.ps1

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-toolkit.ps1 -Force -TimeoutSec 15
#>
[CmdletBinding()]
param(
    [int]    $Port = 6003,
    [int]    $TimeoutSec = 60,
    [switch] $Force,
    [switch] $NoRun
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

function Test-ToolkitHealth([int] $p) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$p/health" -UseBasicParsing -TimeoutSec 4
        return ($r.StatusCode -eq 200)
    }
    catch { return $false }
}

# Результат функции идёт через конвейер: одиночный процесс разворачивается в скаляр,
# а у скалярного CimInstance нет свойства Count. Поэтому вызывающий оборачивает
# результат в @(...), а не полагается на внутреннее @(...) функции.
function Get-ToolkitSessions {
    @(Get-CimInstance Win32_Process -Filter "Name='1cv8.exe' or Name='1cv8c.exe' or Name='1cv8s.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and ($_.CommandLine -like '*MCP_Toolkit*') })
}

function Wait-PortClosed([int] $p, [int] $seconds) {
    $elapsed = 0
    while ($elapsed -lt $seconds) {
        Start-Sleep -Seconds 2
        $elapsed += 2
        if (-not (Test-ToolkitHealth $p)) { return $true }
    }
    return $false
}

$sessions = @(Get-ToolkitSessions)
$serveNow = Test-ToolkitHealth $Port

# Гасить нечего только если и сервер молчит, и процессов с обработкой нет.
# Сеанс, который есть, но на /health не отвечает (завис), надо уметь закрыть -
# иначе следующий scripts\start-toolkit.ps1 упрётся в занятый порт/лицензию.
if (-not $serveNow -and $sessions.Count -eq 0) {
    Write-Host "[=] Порт $Port не отвечает и процессов 1С с обработкой toolkit нет - гасить нечего"
    exit 0
}

if ($serveNow) { Write-Host "Сеанс toolkit отвечает на http://127.0.0.1:$Port/health" }
else { Write-Host "Сеанс toolkit на /health не отвечает, но процессы 1С с обработкой есть - идёт резервный путь" -ForegroundColor Yellow }
Write-Host ("Процессов 1С с обработкой toolkit: " + $sessions.Count)

if ($NoRun) {
    Write-Host 'Будет сделано:'
    if (-not $Force) { Write-Host '  1) POST /api/close_1c_session (штатный путь)' }
    Write-Host '  2) остановка процессов 1С с обработкой MCP_Toolkit.epf (резервный путь)'
    foreach ($s in $sessions) { Write-Host ("       PID " + $s.ProcessId) }
    exit 0
}

# --- 1. Штатный путь: обработка закрывает свой сеанс сама --------------------
if (-not $Force -and $serveNow) {
    Write-Host 'Штатный путь: POST /api/close_1c_session' -ForegroundColor Cyan
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/close_1c_session" -Method Post `
            -ContentType 'application/json' -Body '{}' -UseBasicParsing -TimeoutSec 60
        Write-Host ("  ответ: " + $r.StatusCode)
    }
    catch { Write-Host ("  штатный путь не сработал: " + $_.Exception.Message) -ForegroundColor Yellow }

    if (Wait-PortClosed $Port $TimeoutSec) {
        Write-Host "[ok] Сеанс toolkit закрыт, порт $Port свободен" -ForegroundColor Green
        exit 0
    }
}

# --- 2. Резервный путь: остановка процесса 1С с обработкой toolkit -----------
Write-Host 'Резервный путь: остановка процессов 1С с обработкой MCP_Toolkit.epf' -ForegroundColor Cyan
$killSessions = @(Get-ToolkitSessions)
if ($killSessions.Count -eq 0) { Write-Host '  процессов 1С с обработкой toolkit не найдено - останавливать нечего' -ForegroundColor Yellow }
foreach ($s in $killSessions) {
    Stop-Process -Id $s.ProcessId -Force -ErrorAction SilentlyContinue
    Write-Host ("  остановлен PID " + $s.ProcessId)
}

$portClosed = Wait-PortClosed $Port $TimeoutSec
$leftSessions = @(Get-ToolkitSessions)
if ($portClosed -and $leftSessions.Count -eq 0) {
    Write-Host "[ok] Сеанс toolkit закрыт, порт $Port свободен" -ForegroundColor Green
    exit 0
}

Write-Host "[FAIL] Сеанс toolkit закрыть не удалось." -ForegroundColor Red
if (-not $portClosed) { Write-Host "       Порт $Port всё ещё отвечает." -ForegroundColor Yellow }
foreach ($s in $leftSessions) { Write-Host ("       Остался процесс 1С PID " + $s.ProcessId) -ForegroundColor Yellow }
Write-Host '       Что смотреть: нет ли второй обработки toolkit на том же порту;' -ForegroundColor Yellow
Write-Host '                     закройте её окно 1С вручную.' -ForegroundColor Yellow
exit 1
