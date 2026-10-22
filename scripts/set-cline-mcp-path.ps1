#Requires -Version 5.1
<#
.SYNOPSIS
  Команда "измени переменную": навести CLINE_MCP_SETTINGS_PATH на конфиг MCP текущего каталога.

.DESCRIPTION
  Cline читает список MCP-серверов из одного файла, путь к которому задает переменная
  окружения CLINE_MCP_SETTINGS_PATH. Переменная одна на пользователя, поэтому активен
  тот каталог, на который она указывает: харнесс, склонированный в новый каталог,
  без этой команды остается без MCP - Cline видит серверы прежнего проекта.

  Скрипт делает ровно одно действие:
    1) разрешает целевой путь <Root>\.cline\cline_mcp_settings.json;
    2) проверяет, что файл существует (иначе это не корень харнесса - переменную не трогаем);
    3) пишет переменную уровня пользователя, если она отличается;
    4) печатает прежнее и новое значение.

  Чего скрипт не делает: не опрашивает /health, не поднимает серверы, не запускает
  индексатор, не проверяет базы. Это отдельные действия, и выполняются они только
  тогда, когда нужны задаче.

.PARAMETER Root
  Корень харнесса. По умолчанию - каталог уровнем выше scripts\.

.PARAMETER Show
  Только показать текущее и требуемое значение: переменную не менять.

.NOTES
  Единственное изменение вне каталога проекта - пользовательская переменная окружения,
  без нее in-project конфиг MCP недостижим. Переменная читается при старте VS Code,
  поэтому после команды окно перезапускают. Идемпотентен: повторный запуск ничего
  не меняет и сообщает об этом.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\set-cline-mcp-path.ps1
#>
[CmdletBinding()]
param(
    [string] $Root,
    [switch] $Show
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path -LiteralPath $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}

$variable = 'CLINE_MCP_SETTINGS_PATH'
$target = Join-Path $Root '.cline\cline_mcp_settings.json'
$current = [Environment]::GetEnvironmentVariable($variable, 'User')

Write-Host "=== $variable ==="
if ([string]::IsNullOrWhiteSpace($current)) { Write-Host 'было:   (не задана)' }
else { Write-Host "было:   $current" }
Write-Host "нужно:  $target"

if (-not (Test-Path -LiteralPath $target)) {
    Write-Host '[!] в каталоге нет .cline\cline_mcp_settings.json - это не корень харнесса' -ForegroundColor Red
    Write-Host '    переменная не изменена' -ForegroundColor Red
    exit 1
}

if ($current -eq $target) {
    Write-Host '[=] переменная уже указывает на текущий каталог - менять нечего' -ForegroundColor Green
    exit 0
}

if ($Show) {
    Write-Host '[i] ключ -Show: переменная не изменена' -ForegroundColor Yellow
    exit 0
}

[Environment]::SetEnvironmentVariable($variable, $target, 'User')
Write-Host '[+] переменная уровня пользователя обновлена' -ForegroundColor Green
Write-Host 'Дальше: полностью закрыть и заново открыть VS Code - переменная читается при старте.'
exit 0
