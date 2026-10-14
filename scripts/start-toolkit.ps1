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

    Порядок работы:
      1. разрешает базу по .v8-project.json (id / alias / name, по умолчанию - default);
      2. если /health на порту уже отвечает - ничего не запускает;
      3. запускает клиент 1С с обработкой и startup-параметрами;
      4. ждёт ответа http://127.0.0.1:<порт>/health и печатает итог.

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
    Запустить сеанс, даже если порт уже отвечает.

.PARAMETER NoWait
    Не ждать /health: запустить сеанс, напечатать PID и выйти.

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

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path -LiteralPath $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}

function Test-ToolkitHealth([int] $p) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$p/health" -UseBasicParsing -TimeoutSec 4
        return ($r.StatusCode -eq 200)
    }
    catch { return $false }
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
if (-not $Force -and (Test-ToolkitHealth $Port)) {
    Write-Host "[=] Сервер уже отвечает: http://127.0.0.1:$Port/health (перезапуск - с ключом -Force)"
    exit 0
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
