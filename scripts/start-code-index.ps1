<#
.SYNOPSIS
    Поднять code-index-mcp без окон: демон индексации + MCP-сервер.
.DESCRIPTION
    Для автозапуска положите ярлык на этот скрипт в папку shell:startup.
    Скрипт намеренно запускает процессы скрытыми и сразу выходит.
.EXAMPLE
    .\start-code-index.ps1
#>
[CmdletBinding()]
param(
    [string]$IndexHome,
    [int]$ServePort = 8011
)
$ErrorActionPreference = 'Stop'
if (-not $IndexHome) { $IndexHome = Join-Path (Split-Path -Parent $PSScriptRoot) 'mcp\code-index-mcp' }

$env:CODE_INDEX_HOME = $IndexHome
[Environment]::SetEnvironmentVariable('CODE_INDEX_HOME', $IndexHome, 'User')

$exe = Join-Path $IndexHome 'bsl-indexer.exe'
if (-not (Test-Path $exe)) { throw "Не найден $exe. Сначала install-mcp.ps1" }
$cfg = Join-Path $IndexHome 'daemon.toml'

Start-Process -FilePath $exe -ArgumentList @('daemon','run') -WorkingDirectory $IndexHome -WindowStyle Hidden
Start-Sleep -Seconds 3
Start-Process -FilePath $exe -ArgumentList @('serve','--transport','http','--port',"$ServePort",'--config',"`"$cfg`"") -WorkingDirectory $IndexHome -WindowStyle Hidden
Write-Host "Запущено. MCP endpoint: http://127.0.0.1:$ServePort/mcp"
