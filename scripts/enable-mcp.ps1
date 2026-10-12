#Requires -Version 5.1
<#
.SYNOPSIS
  Подключает MCP-серверы харнесса, размещённые внутри каталога проекта.

.DESCRIPTION
  Cline (VS Code extension saoudrizwan.claude-dev) читает список MCP-серверов
  только из глобального файла настроек. Единственная точка, где этот путь можно
  переопределить, - переменная окружения CLINE_MCP_SETTINGS_PATH. Здесь она
  указывает на .cline\cline_mcp_settings.json ВНУТРИ проекта.

  Скрипт делает:
    1) рабочий каталог индексатора кода и daemon.toml (алиас репозитория "main");
    2) запуск фонового индексатора bsl-indexer daemon run;
    3) установку переменной CLINE_MCP_SETTINGS_PATH на in-project конфиг;
    4) печать списка шагов, которые нужно сделать руками.

.NOTES
  Единственное изменение вне каталога проекта - пользовательская переменная
  окружения CLINE_MCP_SETTINGS_PATH. Без неё in-project конфиг MCP недостижим.
  Идемпотентен.
#>
[CmdletBinding()]
param(
    [string] $Root,
    # Не выставлять переменную окружения (для проверки без side-effects).
    [switch] $SkipEnvVar,
    # Не запускать индексатор.
    [switch] $SkipIndexer
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}

$settingsPath = Join-Path $Root '.cline\cline_mcp_settings.json'
$indexHome    = Join-Path $Root '.cline\mcp\code-index-mcp\home'
$indexerExe   = Join-Path $Root '.cline\mcp\code-index-mcp\bsl-indexer.exe'

Write-Host '=== 1C-agent harness / enable-mcp ==='
Write-Host "Проект: $Root"

# --- 0. Проверка артефактов -------------------------------------------------
if (-not (Test-Path $settingsPath)) { throw "Нет файла настроек MCP: $settingsPath" }
if (-not (Test-Path $indexerExe))   { Write-Warning "Нет индексатора: $indexerExe. Выполните scripts\install-mcp.ps1" }

# --- 1. Каталог индексатора и daemon.toml -----------------------------------
New-Item -ItemType Directory -Force $indexHome | Out-Null
$daemonToml = Join-Path $indexHome 'daemon.toml'

if (-not (Test-Path $daemonToml)) {
    $tomlPath = $Root.Replace('\', '/')
    $toml = @"
[daemon]
http_host = "127.0.0.1"
http_port = 8015
log_level = "info"

[[paths]]
path = "$tomlPath"
alias = "main"
"@
    # Пишем с BOM: rust-парсер toml и так читает UTF-8, BOM ему не мешает,
    # а русские пути дальше читаются предсказуемо.
    [System.IO.File]::WriteAllText($daemonToml, $toml, (New-Object System.Text.UTF8Encoding($true)))
    Write-Host "[+] создан $daemonToml"
}
else {
    Write-Host "[=] daemon.toml уже есть, не трогаем"
}

# --- 2. Запуск фонового индексатора -----------------------------------------
if (-not $SkipIndexer -and (Test-Path $indexerExe)) {
    $env:CODE_INDEX_HOME = $indexHome
    $running = @(Get-Process -Name 'bsl-indexer' -ErrorAction SilentlyContinue).Count -gt 0
    if ($running) {
        Write-Host '[=] индексатор уже запущен'
    }
    else {
        Start-Process -FilePath $indexerExe -ArgumentList @('daemon', 'run') `
            -WorkingDirectory $indexHome -WindowStyle Hidden | Out-Null
        Start-Sleep -Seconds 3
        Write-Host '[+] индексатор запущен (первичная индексация идёт в фоне)'
    }
}

# --- 3. Переменная окружения для Cline --------------------------------------
if (-not $SkipEnvVar) {
    $current = [Environment]::GetEnvironmentVariable('CLINE_MCP_SETTINGS_PATH', 'User')
    if ($current -eq $settingsPath) {
        Write-Host '[=] CLINE_MCP_SETTINGS_PATH уже указывает на проект'
    }
    else {
        [Environment]::SetEnvironmentVariable('CLINE_MCP_SETTINGS_PATH', $settingsPath, 'User')
        Write-Host "[+] CLINE_MCP_SETTINGS_PATH = $settingsPath (уровень пользователя)"
    }
}

# --- 4. Итог ----------------------------------------------------------------
Write-Host ''
Write-Host 'Дальше руками:'
Write-Host '  1. Полностью закрыть и заново открыть VS Code (переменная окружения читается при старте).'
Write-Host '  2. Проверить подключение: scripts\check-harness.ps1'
Write-Host '  3. Поднять MCP-сервер базы: открыть в 1С файл'
Write-Host "     $Root\.cline\mcp\1c-mcp-toolkit\MCP_Toolkit.epf"
Write-Host '     выбрать режим "Встроенный сервер" и нажать "Запустить сервер" (порт 6003).'
