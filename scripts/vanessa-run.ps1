#Requires -Version 5.1
<#
.SYNOPSIS
    Прогон Gherkin/Vanessa-сценариев на базе из .v8-project.json.

.DESCRIPTION
    Vanessa Automation запускается внешней обработкой - установка в конфигурацию
    базы не требуется. Скрипт:

      1. читает путь к базе и каталог платформы из .v8-project.json;
      2. собирает .vanessa\VAParams.json (каталог фич, клиент тестирования,
         статус/лог/jUnit-отчёт);
      3. запускает сеанс менеджера тестирования:
         1cv8c ENTERPRISE /F<база> /Execute <epf> /C"StartFeaturePlayer;VAParams=..." /TESTMANAGER
      4. по умолчанию ждёт завершения сеанса и печатает статус, упавшие шаги и хвост лога.

    Строка запуска и имена ключей VAParams взяты из самого проекта Vanessa
    Automation: tools\onescript\run-behavior-check-session.os (функция
    ПолучитьСтрокуЗапускаСборки) и tools\JSON\VBParams*.json.

    Прогону нужен интерактивный рабочий стол: клиент тестирования - обычное окно
    1С, шаги выполняются в нём.

.NOTES
    Лицензия разработчика ограничивает число одновременных КЛИЕНТОВ ИБ. Прогону
    нужно два клиентских сеанса: менеджер тестирования и клиент тестирования,
    который Vanessa запускает сама. Если база уже открыта другим сеансом (например,
    встроенным сервером 1C MCP Toolkit), платформа отвечает "Превышено ограничение
    лицензии для разработчиков на количество клиентов информационной базы... запрещен".

    Проверено на этой машине: отказ одинаков для тонкого и для толстого клиента,
    то есть ключ -ManagerClient Толстый от лицензии не спасает. Лечение одно:
    освободить базу от чужих клиентских сеансов (включая сеанс toolkit), прогнать
    сценарии и поднять сеанс обратно.

.PARAMETER DatabaseId
    id базы из .v8-project.json. По умолчанию - поле "default".

.PARAMETER Features
    Каталог фич или путь к одному .feature файлу. По умолчанию <корень>\features.

.PARAMETER Epf
    Внешняя обработка Vanessa Automation.
    По умолчанию .vanessa\vanessa-automation-single.epf (см. install-vanessa.ps1).

.PARAMETER ManagerClient
    Клиент, в котором поднимается сеанс менеджера тестирования:
    Тонкий (1cv8c.exe, по умолчанию) или Толстый (1cv8.exe).
    На лицензию выбор клиента не влияет (см. .NOTES): при занятой базе платформа
    отвергает и тонкий, и толстый.

.PARAMETER TestClient
    Клиент тестирования, который Vanessa запускает сама:
    Тонкий (по умолчанию) или Толстый. Передаётся в VAParams (ТипКлиента).

.PARAMETER ExtraParams
    Дополнительные параметры, дописываемые в /C через ';'
    (например 'ОстановкаПриВозникновенииОшибки', 'ClearCacheSteps').

.PARAMETER TimeoutSec
    Сколько секунд ждать завершения сеанса (по умолчанию 1800).

.PARAMETER NoWait
    Не ждать завершения: запустить сеанс и выйти. Статус смотреть в
    .vanessa\status.txt, лог - в .vanessa\va-log.txt.

.PARAMETER NoRun
    Только собрать VAParams.json и напечатать строку запуска.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\vanessa-run.ps1

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\vanessa-run.ps1 `
        -DatabaseId demo-ar -Features .\features\Печать_ТОРГ12_ИзРеализацииТоваровУслуг.feature -NoWait
#>
[CmdletBinding()]
param(
    [string] $Root,
    [string] $DatabaseId = '',
    [string] $Features = '',
    [string] $Epf = '',
    [ValidateSet('Тонкий', 'Толстый')]
    [string] $ManagerClient = 'Тонкий',
    [ValidateSet('Тонкий', 'Толстый')]
    [string] $TestClient = 'Тонкий',
    [string[]] $ExtraParams = @(),
    [int] $TimeoutSec = 1800,
    [switch] $NoWait,
    [switch] $NoRun
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path -LiteralPath $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}
$projectRoot = $Root

# --- 1. База и платформа из .v8-project.json ---------------------------------
$cfgPath = Join-Path $projectRoot '.v8-project.json'
if (-not (Test-Path -LiteralPath $cfgPath)) { throw "Нет конфига проекта: $cfgPath" }
$cfg = Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $DatabaseId) { $DatabaseId = $cfg.default }
$db = @($cfg.databases | Where-Object { $_.id -eq $DatabaseId })[0]
if ($null -eq $db) { throw "База '$DatabaseId' не объявлена в .v8-project.json" }
if ($db.type -ne 'file') { throw "Поддерживаются только файловые базы; '$DatabaseId' имеет type=$($db.type)" }

$basePath = $db.path
if (-not (Test-Path -LiteralPath $basePath)) { throw "Каталог базы не найден: $basePath" }
$v8path = if ($db.v8path) { $db.v8path } else { $cfg.v8path }
$v8exe = Join-Path $v8path $(if ($ManagerClient -eq 'Толстый') { '1cv8.exe' } else { '1cv8c.exe' })
if (-not (Test-Path -LiteralPath $v8exe)) { throw "Нет файла платформы: $v8exe" }

# Учётные данные базы: поля user/password записи в .v8-project.json.
# Нужны, если в базе есть пользователи ИБ (иначе "Пользователь ИБ не идентифицирован").
$dbUser = if ($db.user) { [string] $db.user } else { '' }
$dbPassword = if ($db.password) { [string] $db.password } else { '' }
$authParams = ''
if ($dbUser) { $authParams = '/N"' + $dbUser + '" /P"' + $dbPassword + '"' }

# --- 2. Артефакты прогона ----------------------------------------------------
$runDir = Join-Path $projectRoot '.vanessa'
if (-not (Test-Path -LiteralPath $runDir)) { New-Item -ItemType Directory -Path $runDir -Force | Out-Null }
$vaParams = Join-Path $runDir 'VAParams.json'
$statusFile = Join-Path $runDir 'status.txt'
$logFile = Join-Path $runDir 'va-log.txt'
$junitDir = Join-Path $runDir 'junit'

if ([string]::IsNullOrWhiteSpace($Epf)) { $Epf = Join-Path $runDir 'vanessa-automation-single.epf' }
if (-not (Test-Path -LiteralPath $Epf)) {
    throw "Нет обработки Vanessa Automation: $Epf`nРазверните её: scripts\install-vanessa.ps1"
}
if ([string]::IsNullOrWhiteSpace($Features)) { $Features = Join-Path $projectRoot 'features' }
$Features = [System.IO.Path]::GetFullPath($Features)
if (-not (Test-Path -LiteralPath $Features)) { throw "Не найден каталог фич или файл: $Features" }

foreach ($f in @($statusFile, $logFile)) { if (Test-Path -LiteralPath $f) { Remove-Item -LiteralPath $f -Force } }
if (-not (Test-Path -LiteralPath $junitDir)) { New-Item -ItemType Directory -Path $junitDir -Force | Out-Null }

# --- 3. VAParams.json --------------------------------------------------------
function JsonEscape([string] $s) { return ($s -replace '\\', '\\' -replace '"', '\"') }

$json = @"
{
   "КаталогФич": "$(JsonEscape $Features)",
   "КлиентыТестирования":[
      {
         "Имя": "ТестКлиент",
         "ПутьКИнфобазе": "/F\"$(JsonEscape $basePath)\"",
         "ДопПараметры": "$(JsonEscape $authParams)",
         "ТипКлиента": "$TestClient",
         "ИмяКомпьютера": "localhost",
         "ПортЗапускаТестКлиента": "48110",
         "АктивизироватьСтроку": "Истина"
      }
   ],
   "ВыполнитьСценарии": true,
   "ЗавершитьРаботуСистемы": "Истина",
   "ЗакрытьTestClientПослеЗапускаСценариев": "Истина",
   "ЗапускатьКлиентТестированияСМаксимизированнымОкном": "Истина",
   "ДелатьЛогВыполненияСценариевВТекстовыйФайл": "Истина",
   "ИмяФайлаЛогВыполненияСценариев": "$(JsonEscape $logFile)",
   "ДелатьОтчетВФорматеjUnit": "Истина",
   "КаталогOutputjUnit": "$(JsonEscape $junitDir)",
   "ВыгружатьСтатусВыполненияСценариевВФайл": "Истина",
   "ПутьКФайлуДляВыгрузкиСтатусаВыполненияСценариев": "$(JsonEscape $statusFile)",
   "ТаймаутЗапуска1С": "300",
   "ОстановкаПриВозникновенииОшибки": "Истина",
   "ОбновлятьСтатистикуВДереве": "Ложь"
}
"@
$utf8Bom = New-Object System.Text.UTF8Encoding($true)
[System.IO.File]::WriteAllText($vaParams, $json, $utf8Bom)

# --- 4. Строка запуска -------------------------------------------------------
$cParams = @('StartFeaturePlayer', "VAParams=$vaParams") + $ExtraParams
$cmdLine = 'ENTERPRISE /F"' + $basePath + '" ' + $authParams + ' /Execute "' + $Epf + '" /C"' +
    ($cParams -join ';') + '" /TESTMANAGER /DisableStartupDialogs /DisableStartupMessages'

Write-Host "База:      $DatabaseId ($basePath)"
Write-Host "Платформа: $v8exe"
Write-Host "Фичи:      $Features"
Write-Host "VAParams:  $vaParams"
Write-Host "Команда:   $v8exe $cmdLine"

if ($NoRun) { exit 0 }

# --- 5. Запуск ---------------------------------------------------------------
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $v8exe
$psi.Arguments = $cmdLine
$psi.UseShellExecute = $false
$psi.WorkingDirectory = $runDir
$proc = [System.Diagnostics.Process]::Start($psi)
Write-Host "Сеанс запущен, PID $($proc.Id)"

if ($NoWait) {
    Write-Host "Ждём завершения: .vanessa\status.txt (0 - успех, 1 - есть упавшие сценарии). Лог: .vanessa\va-log.txt, отчёт: .vanessa\junit\junit.xml"
    exit 0
}

if (-not $proc.WaitForExit($TimeoutSec * 1000)) {
    Write-Host "Сеанс не завершился за $TimeoutSec с. Смотрите .vanessa\va-log.txt" -ForegroundColor Yellow
}

Write-Host ''
if (Test-Path -LiteralPath $statusFile) {
    Write-Host ("Статус: " + (Get-Content -LiteralPath $statusFile -Raw -Encoding UTF8).Trim())
}
else {
    Write-Host 'Файл статуса не создан - прогон не доехал до выгрузки статуса.' -ForegroundColor Yellow
}

$steps = Get-ChildItem -LiteralPath $junitDir -Filter '*.xml' -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
if ($steps) {
    Write-Host ''
    Write-Host ("Упавшие шаги (jUnit: " + (Split-Path -Leaf $steps) + "):")
    Select-String -LiteralPath $steps -Pattern '<failure|<error' -Encoding UTF8 |
        Select-Object -First 20 | ForEach-Object { Write-Host ('  ' + $_.Line.Trim()) }
}

if (Test-Path -LiteralPath $logFile) {
    Write-Host ''
    Write-Host 'Хвост лога выполнения сценариев:'
    Get-Content -LiteralPath $logFile -Encoding UTF8 -Tail 40 | ForEach-Object { Write-Host ('  ' + $_) }
}
else {
    Write-Host 'Текстовый лог выполнения не создан.' -ForegroundColor Yellow
}
