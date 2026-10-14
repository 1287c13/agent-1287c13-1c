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

    Обработку Vanessa скрипт разворачивает сам: если .vanessa\vanessa-automation-single.epf
    нет, он достаёт epf из свежего релизного архива vanessa-automation-single*.zip
    (каталог Загрузки или -VanessaZip). Отдельный шаг установки не нужен.

    Прогон делается ПО ТРЕБОВАНИЮ ЗАДАЧИ и обязательной проверкой харнесса не
    является: он нужен там, где в цели задачи есть прогон сценария в базе.

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
    Каталог фич или путь к одному .feature файлу. По умолчанию <корень>\temp\features:
    сценарий, собранный под задачу, - временный артефакт, а temp\ - единственное место
    временных файлов задачи (.clinerules\00-contract.md, п.4). Каталог features\ в корне
    репозитория не создаётся и не хранится.

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

.PARAMETER FreeToolkit
    Перед прогоном погасить сеанс 1C MCP Toolkit (scripts\stop-toolkit.ps1), а после
    прогона поднять его обратно (scripts\start-toolkit.ps1). Нужно потому, что прогону
    требуются два клиента той же базы, а занятый сеанс toolkit упирается в лицензию.
    При -NoWait обратный подъём не выполняется - его делает start-toolkit.ps1.

.PARAMETER ToolkitPort
    Порт сеанса toolkit для -FreeToolkit (по умолчанию 6003).

.PARAMETER VanessaZip
    Релизный архив vanessa-automation-single*.zip для автоматического развёртывания
    обработки. По умолчанию берётся самый свежий такой архив из каталога Загрузки.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\vanessa-run.ps1

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\vanessa-run.ps1 `
        -DatabaseId demo-ar -Features .\temp\features\Печать_ТОРГ12_ИзРеализацииТоваровУслуг.feature -NoWait
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
    [switch] $NoRun,
    [switch] $FreeToolkit,
    [int] $ToolkitPort = 6003,
    [string] $VanessaZip = ''
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

# Каталог скриптов нужен и ниже - им находятся соседние скрипты toolkit.
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path -LiteralPath $PSCommandPath).Path }
if ([string]::IsNullOrWhiteSpace($Root)) { $Root = Split-Path -Parent $scriptDir }
$projectRoot = $Root

# Автоматическое развёртывание обработки Vanessa Automation. Vanessa ставится не в
# конфигурацию базы, а запускается внешней обработкой - нужен только файл epf,
# поэтому его достаточно достать из релизного архива.
function Install-VanessaEpf([string] $Target, [string] $Zip) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    if ([string]::IsNullOrWhiteSpace($Zip)) {
        $downloads = Join-Path $env:USERPROFILE 'Downloads'
        $Zip = @(Get-ChildItem -LiteralPath $downloads -Filter 'vanessa-automation-single*.zip' -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName)[0]
    }
    if (-not $Zip -or -not (Test-Path -LiteralPath $Zip)) { return $null }
    $archive = [System.IO.Compression.ZipFile]::OpenRead($Zip)
    try {
        $entry = @($archive.Entries | Where-Object { $_.Name -like '*.epf' } | Sort-Object Length -Descending)[0]
        if (-not $entry) { return $null }
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $Target, $true)
        return ($entry.Name + ' из ' + $Zip)
    }
    finally { $archive.Dispose() }
}

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
    Write-Host "Обработка Vanessa не развёрнута - разворачиваю: $Epf" -ForegroundColor Yellow
    $deployedFrom = Install-VanessaEpf -Target $Epf -Zip $VanessaZip
    if (-not $deployedFrom) {
        throw ("Нет обработки Vanessa Automation: $Epf`n" +
               "Не найден релизный архив vanessa-automation-single*.zip (каталог Загрузки).`n" +
               "Скачайте его: https://github.com/Pr-Mex/vanessa-automation/releases `n" +
               "и повторите либо укажите архив явно: -VanessaZip <путь к zip>")
    }
    Write-Host "  развёрнуто: $deployedFrom" -ForegroundColor Green
}
if ([string]::IsNullOrWhiteSpace($Features)) { $Features = Join-Path $projectRoot 'temp\features' }
$Features = [System.IO.Path]::GetFullPath($Features)
if (-not (Test-Path -LiteralPath $Features)) { throw "Не найден каталог фич или файл: $Features. Сценарий под задачу кладётся в temp\features\ (единственное место временных файлов задачи)" }

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

# --- 3a. Освобождение базы под прогон (по требованию: -FreeToolkit) ---------
# Прогону нужны ДВА клиента одной базы: менеджер тестирования и клиент тестирования.
# Сеанс toolkit - тоже клиент базы, поэтому его гасят до прогона и поднимают обратно
# после, но только если он был поднят и только когда скрипт ждёт конца прогона.
$toolkitScripts = @{
    Stop  = Join-Path $scriptDir 'stop-toolkit.ps1'
    Start = Join-Path $scriptDir 'start-toolkit.ps1'
}
$toolkitWasUp = $false
if ($FreeToolkit) {
    foreach ($s in $toolkitScripts.Values) { if (-not (Test-Path -LiteralPath $s)) { throw "Нет скрипта: $s" } }
    try {
        Invoke-WebRequest "http://127.0.0.1:$ToolkitPort/health" -UseBasicParsing -TimeoutSec 4 | Out-Null
        $toolkitWasUp = $true
    }
    catch { }
    if ($toolkitWasUp) {
        Write-Host "Освобождаю базу: гашу сеанс toolkit на порту $ToolkitPort" -ForegroundColor Yellow
        & $toolkitScripts.Stop -Port $ToolkitPort -TimeoutSec 60
        if ($LASTEXITCODE -ne 0) { throw 'Сеанс toolkit закрыть не удалось - база занята, прогон отменён' }
    }
    else { Write-Host '[=] Сеанса toolkit нет - база свободна' }
}

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
    if ($toolkitWasUp) { Write-Host "Сеанс toolkit погашен - поднять обратно: scripts\start-toolkit.ps1 -Port $ToolkitPort" -ForegroundColor Yellow }
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

# --- 6. Возврат сеанса toolkit ------------------------------------------------
if ($toolkitWasUp) {
    Write-Host ''
    Write-Host 'Поднимаю сеанс toolkit обратно...' -ForegroundColor Cyan
    & $toolkitScripts.Start -Root $projectRoot -Port $ToolkitPort -NoWait
}
