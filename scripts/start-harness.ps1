#Requires -Version 5.1
<#
.SYNOPSIS
  Ежедневный запуск харнесса (после перезагрузки машины).

.DESCRIPTION
  Поднимает то, что должно работать в фоне:
    - индексатор кода bsl-indexer daemon run;
    - встроенный сервер 1C MCP Toolkit (порт 6003): если он не отвечает, вызывается
      scripts\start-toolkit.ps1 - обработка поднимается автозапуском из базы проекта;
    - печатает короткий статус.

.PARAMETER ToolkitDatabase
  id (или alias, name) базы из .v8-project.json, в которой поднимать встроенный сервер
  toolkit. По умолчанию - поле "default" конфига.

.NOTES
  Скрипт нужен потому, что фон индексатора живёт до перезагрузки. Если нужно,
  чтобы он поднимался сам - добавьте ярлык на него в автозагрузку (shell:startup).
#>
[CmdletBinding()]
param(
    [string] $Root,
    [string] $ToolkitDatabase = ''
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}

$indexer   = Join-Path $Root '.cline\mcp\code-index-mcp\bsl-indexer.exe'
$indexHome = Join-Path $Root '.cline\mcp\code-index-mcp\home'

if (-not (Test-Path $indexer)) {
    Write-Host 'Индексатор не установлен. Выполните: scripts\install-mcp.ps1' -ForegroundColor Red
    exit 1
}

$env:CODE_INDEX_HOME = $indexHome
$running = @(Get-Process -Name 'bsl-indexer' -ErrorAction SilentlyContinue).Count -gt 0

if ($running) {
    Write-Host '[=] индексатор уже работает' -ForegroundColor Green
}
else {
    Write-Host '[*] запускаю индексатор...'
    Start-Process -FilePath $indexer -ArgumentList @('daemon', 'run') -WorkingDirectory $indexHome -WindowStyle Hidden | Out-Null
    Start-Sleep -Seconds 3
    Write-Host '[+] индексатор запущен' -ForegroundColor Green
}

$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'SilentlyContinue'
& $indexer daemon status 2>&1 | Out-String | Write-Host
$ErrorActionPreference = $prevEap

# --- Живая база ------------------------------------------------------------
try {
    Invoke-WebRequest 'http://127.0.0.1:6003/health' -UseBasicParsing -TimeoutSec 4 | Out-Null
    Write-Host '[=] 1c-toolkit (порт 6003) отвечает' -ForegroundColor Green
}
catch {
    Write-Host '[*] 1c-toolkit не отвечает - поднимаю встроенный сервер автоматически...'
    $startToolkit = Join-Path $Root 'scripts\start-toolkit.ps1'
    if (Test-Path $startToolkit) {
        if ([string]::IsNullOrWhiteSpace($ToolkitDatabase)) { & $startToolkit -Root $Root -TimeoutSec 60 }
        else { & $startToolkit -Root $Root -DatabaseId $ToolkitDatabase -TimeoutSec 60 }
        if ($LASTEXITCODE -eq 0) { Write-Host '[+] 1c-toolkit поднят (порт 6003)' -ForegroundColor Green }
        else { Write-Host '[!] сервер не поднялся - разбор причин напечатан выше' -ForegroundColor Yellow }
    }
    else {
        Write-Host "[!] Нет $startToolkit - откройте в базе 1С .cline\mcp\1c-mcp-toolkit\MCP_Toolkit.epf" -ForegroundColor Yellow
        Write-Host '    и нажмите "Запустить сервер" (порт 6003)' -ForegroundColor Yellow
    }
}

Write-Host ''
Write-Host 'Полная диагностика: scripts\check-harness.ps1'
