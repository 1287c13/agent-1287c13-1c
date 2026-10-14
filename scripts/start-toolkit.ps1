#Requires -Version 5.1
<#
.SYNOPSIS
    Поднять встроенный сервер 1C MCP Toolkit в базе из .v8-project.json.

.DESCRIPTION
    Встроенный HTTP-сервер toolkit живёт внутри клиентского сеанса 1С: обработка
    MCP_Toolkit.epf открывается ключом платформы /Execute, а режим сервера включается
    параметром запуска /C "startup;mode=embedded;port=<порт>". Это документированный
    автозапуск обработки (README_FULL.md вендора, раздел "Автоматический запуск
    обработки из командной строки"), поэтому нажимать "Запустить сервер" на форме
    вручную не нужно.

    Скрипт идемпотентен: он НЕ плодит клиентские сеансы. Порядок работы:
      1. разрешает базу по .v8-project.json (id / alias / name, по умолчанию - default);
      2. если /health на порту отвечает - не запускает ничего (сервер уже поднят);
      3. если сеанс 1С с обработкой toolkit уже запущен, но сервер ещё не ответил -
         второй сеанс не поднимается: скрипт ждёт готовности уже запущенного;
      4. только если нет ни сервера, ни сеанса - запускает клиент 1С с обработкой
         и startup-параметрами;
      5. ждёт ответа http://127.0.0.1:<порт>/health и печатает итог.

    Запуск второго сеанса - только явным ключом -Force: он сначала гасит уже
    запущенный сеанс (scripts\stop-toolkit.ps1) и лишь затем поднимает новый.

    Сеанс 1С остаётся открытым - сервер живёт в нём. Закрыть: scripts\stop-toolkit.ps1.
    Сеанс занимает клиентскую лицензию базы, поэтому перед прогоном Vanessa
    (scripts\vanessa-run.ps1 -FreeToolkit) toolkit надо гасить.

.NOTES
    Скрипт обращается к серверу только GET-запросом /health, кириллица в JSON-телах
    toolkit его не касается, поэтому работает и в Windows PowerShell 5.1.

.PARAMETER Root
    Корень харнесса. По умолчанию - каталог уровнем выше scripts\.

.PARAMETER DatabaseId
    id (или alias, или name) базы из .v8-project.json. По умолчанию - поле "default".

.PARAMETER Port
    Порт встроенного сервера. По умолчанию 6003 - на него настроен MCP-сервер
    1c-toolkit в .cline\cline_mcp_settings.json.

.PARAMETER Epf
    Обработка toolkit. По умолчанию .cline\mcp\1c-mcp-toolkit\MCP_Toolkit.epf
    (ставит scripts\install-mcp.ps1).

.PARAMETER Client
    Клиент платформы: Тонкий (1cv8c.exe, по умолчанию) или Толстый (1cv8.exe).
    Встроенный сервер работает в обоих; веб-клиент не годится.

.PARAMETER TimeoutSec
    Сколько секунд ждать ответа /health после запуска (по умолчанию 90).

.PARAMETER Force
    Перезапуск: погасить уже запущенный сеанс toolkit (scripts\stop-toolkit.ps1) и
    поднять новый. Без этого ключа второй сеанс не поднимается: если сервер отвечает -
    скрипт выходит, если сеанс есть, но сервер молчит - скрипт только ждёт.

.PARAMETER NoWait
    Не ждать /health: запустить сеанс (если его ещё нет), напечатать PID и выйти.

.PARAMETER NoRun
    Только разрешить базу и напечатать команду запуска - ничего не запускать.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-toolkit.ps1

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-toolkit.ps1 -DatabaseId demo-ssl -NoWait
#>
[CmdletBinding()]
param(
    [string] $Root,
    [string] $DatabaseId = '',
    [int]    $Port = 6003,
    [string] $Epf = '',
    [ValidateSet('Тонкий', 'Толстый')]
    [string] $Client = 'Тонкий',
    [int]    $TimeoutSec = 90,
    [switch] $Force,
    [switch] $NoWait,
    [switch] $NoRun
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path -LiteralPath $PSCommandPath).Path }
if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent $scriptDir
}

function Test-ToolkitHealth([int] $p) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$p/health" -UseBasicParsing -TimeoutSec 4
        return ($r.StatusCode -eq 200)
    }
    catch { return $false }
}

# Сеансы 1С, в командной строке которых есть обработка toolkit. Результат идёт через
# конвейер: одиночный процесс разворачивается в скаляр, а у скаляра нет .Count,
# поэтому вызывающий оборачивает вызов в @(...).
function Get-ToolkitSessions {
    @(Get-CimInstance Win32_Process -Filter "Name='1cv8.exe' or Name='1cv8c.exe' or Name='1cv8s.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and ($_.CommandLine -like '*MCP_Toolkit*') })
}

# --- 1. База и платформа из .v8-project.json ---------------------------------
$cfgPath = Join-Path $Root '.v8-project.json'
if (-not (Test-Path -LiteralPath $cfgPath)) { throw "Нет конфига проекта: $cfgPath" }
$cfg = Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $DatabaseId) { $DatabaseId = $cfg.default }

$db = @($cfg.databases | Where-Object {
    $_.id -eq $DatabaseId -or $_.name -eq $DatabaseId -or (@($_.aliases) -contains $DatabaseId)
})[0]
if ($null -eq $db) { throw "База '$DatabaseId' не объявлена в .v8-project.json" }

if ($db.type -eq 'file') {
    if (-not (Test-Path -LiteralPath $db.path)) { throw "Каталог базы не найден: $($db.path)" }
    $ibParam = '/F"' + $db.path + '"'
}
elseif ($db.server -and $db.ref) {
    $ibParam = '/S"' + $db.server + '\' + $db.ref + '"'
}
else { throw "В записи '$DatabaseId' нет ни пути файловой базы, ни пары server/ref" }

$v8path = if ($db.v8path) { $db.v8path } else { $cfg.v8path }
$exeName = if ($Client -eq 'Толстый') { '1cv8.exe' } else { '1cv8c.exe' }
$v8exe = Join-Path $v8path $exeName
if (-not (Test-Path -LiteralPath $v8exe)) { throw "Нет файла платформы: $v8exe" }

# Учётные данные: поля user/password записи базы. Без них платформа ответит
# "Пользователь ИБ не идентифицирован" и сеанс останется на форме входа.
$dbUser = if ($db.user) { [string] $db.user } else { '' }
$dbPassword = if ($db.password) { [string] $db.password } else { '' }
$authParams = ''
if ($dbUser) { $authParams = '/N"' + $dbUser + '" /P"' + $dbPassword + '"' }

if ([string]::IsNullOrWhiteSpace($Epf)) { $Epf = Join-Path $Root '.cline\mcp\1c-mcp-toolkit\MCP_Toolkit.epf' }
if (-not (Test-Path -LiteralPath $Epf)) {
    throw "Нет обработки toolkit: $Epf`nОна ставится скриптом scripts\install-mcp.ps1"
}

# --- 2. Может, сервер уже поднят? --------------------------------------------
# Главное правило: клиентский сеанс 1С не плодится. Порядок проверок -
# сначала живой сервер, затем уже запущенный сеанс, и только потом запуск.
$sessions = @(Get-ToolkitSessions)
$serveNow = Test-ToolkitHealth $Port

if ($Force -and ($serveNow -or $sessions.Count -gt 0)) {
    Write-Host '[*] -Force: гашу уже запущенный сеанс toolkit перед новым запуском...' -ForegroundColor Yellow
    $stopScript = Join-Path $scriptDir 'stop-toolkit.ps1'
    if (-not (Test-Path -LiteralPath $stopScript)) { throw "Нет скрипта остановки: $stopScript" }
    & $stopScript -Port $Port -TimeoutSec 60 | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'Сеанс toolkit закрыть не удалось - подъём нового отменён' }
    $sessions = @(Get-ToolkitSessions)
    $serveNow = $false
}

if (-not $Force -and $serveNow) {
    if ($sessions.Count -gt 0) {
        $pids = ($sessions | ForEach-Object { [string] $_.ProcessId }) -join ', '
        Write-Host "[=] Сервер уже поднят: http://127.0.0.1:$Port/health (сеанс 1С PID $pids)" -ForegroundColor Green
    }
    else { Write-Host "[=] Сервер уже поднят: http://127.0.0.1:$Port/health" -ForegroundColor Green }
    Write-Host '    Новый сеанс не запускаю. Перезапуск - с ключом -Force.'
    exit 0
}

# Сеанс уже запущен, но сервер ещё не ответил: второй сеанс не поднимается - ждём этот.
if (-not $Force -and $sessions.Count -gt 0) {
    $pids = ($sessions | ForEach-Object { [string] $_.ProcessId }) -join ', '
    Write-Host "[=] Сеанс toolkit уже запущен (PID $pids), но http://127.0.0.1:$Port/health пока не отвечает." -ForegroundColor Yellow
    Write-Host '    Второй сеанс не поднимаю - жду готовности уже запущенного.' -ForegroundColor Yellow
    if ($NoWait) { exit 0 }
    $elapsed = 0
    while ($elapsed -lt $TimeoutSec) {
        Start-Sleep -Seconds 3
        $elapsed += 3
        if (Test-ToolkitHealth $Port) {
            Write-Host "[ok] Сервер поднялся в уже запущенном сеансе: http://127.0.0.1:$Port/health (PID $pids)" -ForegroundColor Green
            exit 0
        }
        Write-Host "  ... $elapsed с, сервер ещё не ответил" -ForegroundColor DarkGray
    }
    Write-Host "[FAIL] Сеанс toolkit есть (PID $pids), но сервер не ответил за $TimeoutSec с." -ForegroundColor Red
    Write-Host '       Что смотреть: 1) окно 1С с обработкой - нет ли в нём диалога (например, вход);' -ForegroundColor Yellow
    Write-Host '                     2) не занята ли клиентская лицензия базы чужими сеансами 1С.' -ForegroundColor Yellow
    Write-Host '       Перезапуск сеанса: этот же скрипт с ключом -Force.' -ForegroundColor Yellow
    exit 1
}

# --- 3. Параметры автозапуска ------------------------------------------------
# startup-параметры обработки: mode=embedded;port=<порт>.
# auth=password;pwd=... нужен только для последующего restart_1c_session,
# поэтому передаётся лишь при непустом пароле без символов ';' и '='.
$startup = "startup;mode=embedded;port=$Port"
if ($dbPassword -and $dbPassword -notmatch '[;=]') { $startup += ";auth=password;pwd=$dbPassword" }

$cmdLine = 'ENTERPRISE ' + $ibParam + ' ' + $authParams + ' /Execute "' + $Epf + '" /C"' + $startup +
    '" /DisableStartupDialogs /DisableStartupMessages'

Write-Host "База:      $DatabaseId ($ibParam)"
Write-Host "Платформа: $v8exe"
Write-Host "Обработка: $Epf"
Write-Host "Команда:   $v8exe $cmdLine"

if ($NoRun) { exit 0 }

# --- 4. Запуск сеанса 1С ------------------------------------------------------
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $v8exe
$psi.Arguments = $cmdLine
$psi.UseShellExecute = $false
$psi.WorkingDirectory = $Root
$proc = [System.Diagnostics.Process]::Start($psi)
Write-Host "Сеанс 1С запущен, PID $($proc.Id)" -ForegroundColor Green

if ($NoWait) {
    Write-Host "Ждём ответа: http://127.0.0.1:$Port/health (состояние - scripts\check-harness.ps1)"
    exit 0
}

# --- 5. Ожидание готовности ---------------------------------------------------
$elapsed = 0
while ($elapsed -lt $TimeoutSec) {
    Start-Sleep -Seconds 3
    $elapsed += 3
    if (Test-ToolkitHealth $Port) {
        Write-Host "[ok] Сервер поднят: http://127.0.0.1:$Port/health (PID $($proc.Id))" -ForegroundColor Green
        exit 0
    }
    Write-Host "  ... $elapsed с, сервер ещё не ответил" -ForegroundColor DarkGray
}

Write-Host "[FAIL] Сервер не ответил на http://127.0.0.1:$Port/health за $TimeoutSec с." -ForegroundColor Red
Write-Host '       Что смотреть: 1) открылось ли окно 1С (PID выше) и нет ли в нём диалога;' -ForegroundColor Yellow
Write-Host '                     2) не занята ли клиентская лицензия базы чужими сеансами 1С;' -ForegroundColor Yellow
Write-Host '                     3) не держит ли порт другая обработка toolkit (другой сеанс).' -ForegroundColor Yellow
Write-Host '       Ручной путь: открыть .cline\mcp\1c-mcp-toolkit\MCP_Toolkit.epf и нажать "Запустить сервер".' -ForegroundColor Yellow
exit 1
