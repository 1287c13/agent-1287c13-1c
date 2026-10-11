<#
.SYNOPSIS
    Настроить и запустить code-index-mcp (bsl-indexer): демон индексации + MCP-сервер.
.EXAMPLE
    .\setup-code-index.ps1
    .\setup-code-index.ps1 -IndexHome 'C:\w\1c\агент\mcp\code-index-mcp' -Paths 'C:\w\1c\агент\dump'
#>
[CmdletBinding()]
param(
    [string]$IndexHome,
    [string[]]$Paths,
    [string]$Alias = 'ar208',
    [int]$DaemonPort = 8015,
    [int]$ServePort  = 8011,
    [switch]$NoServe
)
$ErrorActionPreference = 'Stop'
$agentRoot = Split-Path -Parent $PSScriptRoot
if (-not $IndexHome) { $IndexHome = Join-Path $agentRoot 'mcp\code-index-mcp' }
if (-not $Paths)     { $Paths     = @((Join-Path $agentRoot 'dump')) }
$exe = Join-Path $IndexHome 'bsl-indexer.exe'
if (-not (Test-Path $exe)) { throw "Не найден $exe. Сначала: .\install-mcp.ps1" }

# 1. CODE_INDEX_HOME — обязательна для обоих процессов
[Environment]::SetEnvironmentVariable('CODE_INDEX_HOME', $IndexHome, 'User')
$env:CODE_INDEX_HOME = $IndexHome

# 2. daemon.toml
$toml = @("[daemon]", "http_host = ""127.0.0.1""", "http_port = $DaemonPort", "log_level = ""info""", "")
foreach ($p in $Paths) {
    $fwd = $p -replace '\\', '/'
    $toml += "[[paths]]"; $toml += "path = ""$fwd"""; $toml += "alias = ""$Alias"""; $toml += ""
}
$cfg = Join-Path $IndexHome 'daemon.toml'
$toml | Set-Content -Encoding UTF8 $cfg
Write-Host "Конфиг: $cfg"

# 3. демон индексации (писатель индекса)
Start-Process -FilePath $exe -ArgumentList @('daemon', 'run') -WorkingDirectory $IndexHome -WindowStyle Hidden
Start-Sleep -Seconds 4
& $exe daemon status

# 4. MCP-сервер (read-only выдача)
if (-not $NoServe) {
    Start-Process -FilePath $exe -ArgumentList @('serve','--transport','http','--port',"$ServePort",'--config',"`"$cfg`"") -WorkingDirectory $IndexHome -WindowStyle Hidden
    Start-Sleep -Seconds 2
    Write-Host "MCP endpoint: http://127.0.0.1:$ServePort/mcp"
}
Write-Host 'Готово. Индексация крупной конфигурации занимает минуты — смотрите daemon.log'
