<#
.SYNOPSIS
    Скачать MCP-серверы в .\mcp (code-index-mcp, 1c-mcp-toolkit и опциональные).
.EXAMPLE
    .\install-mcp.ps1
    .\install-mcp.ps1 -Optional        # дополнительно mcp-1c и mcp-rsv-data
#>
[CmdletBinding()]
param(
    [switch]$Optional,
    [string]$Root
)
$ErrorActionPreference = 'Stop'
if (-not $Root) { $Root = Split-Path -Parent $PSScriptRoot }
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Get-LatestAssetUrl([string]$repo, [string]$namePattern) {
    $rel = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest" -Headers @{ 'User-Agent' = 'cline-1c-agent' }
    $asset = $rel.assets | Where-Object { $_.name -match $namePattern } | Select-Object -First 1
    if (-not $asset) { throw "В релизе $repo нет актива по маске '$namePattern'" }
    return $asset.browser_download_url
}

function Get-File([string]$url, [string]$out) {
    Write-Host "  -> $url"
    Invoke-WebRequest $url -OutFile $out -UseBasicParsing
    Write-Host "     saved: $out"
}

# --- 1. code-index-mcp (bsl-indexer) : слой кода и метаданных ---
$dst = Join-Path $Root 'mcp\code-index-mcp'
New-Item -ItemType Directory -Force $dst | Out-Null
try {
    $url = Get-LatestAssetUrl 'Regsorm/code-index-mcp' 'bsl-indexer-windows-x64\.zip'
    $zip = Join-Path $env:TEMP 'bsl-indexer.zip'
    Get-File $url $zip
    Expand-Archive $zip -DestinationPath $dst -Force
    Write-Host "code-index-mcp установлен в $dst"
} catch { Write-Warning "code-index-mcp: $($_.Exception.Message)" }

# --- 2. 1c-mcp-toolkit : слой живой базы (встроенный HTTP-сервер в .epf) ---
$dst2 = Join-Path $Root 'mcp\1c-mcp-toolkit'
New-Item -ItemType Directory -Force $dst2 | Out-Null
try {
    $url = Get-LatestAssetUrl 'ROCTUP/1c-mcp-toolkit' '\.epf$'
    Get-File $url (Join-Path $dst2 'MCP_Toolkit.epf')
} catch {
    try {
        Get-File 'https://raw.githubusercontent.com/ROCTUP/1c-mcp-toolkit/main/build/MCP_Toolkit.epf' (Join-Path $dst2 'MCP_Toolkit.epf')
    } catch { Write-Warning "1c-mcp-toolkit: $($_.Exception.Message)" }
}

if ($Optional) {
    # --- 3. mcp-1c : live-метаданные и SELECT-запросы при публикации базы ---
    $dst3 = Join-Path $Root 'mcp\optional\mcp-1c'
    New-Item -ItemType Directory -Force $dst3 | Out-Null
    try {
        $url = Get-LatestAssetUrl 'feenlace/mcp-1c' 'windows.*amd64.*\.zip|mcp-1c.*windows.*\.exe'
        if ($url -match '\.zip$') { Get-File $url (Join-Path $env:TEMP 'mcp1c.zip'); Expand-Archive (Join-Path $env:TEMP 'mcp1c.zip') -DestinationPath $dst3 -Force }
        else { Get-File $url (Join-Path $dst3 'mcp-1c.exe') }
    } catch { Write-Warning "mcp-1c: $($_.Exception.Message)" }

    # --- 4. mcp-rsv-data : read-only данные по COM для аналитика ---
    $dst4 = Join-Path $Root 'mcp\optional\mcp-rsv-data'
    New-Item -ItemType Directory -Force $dst4 | Out-Null
    try {
        Get-File 'https://github.com/prepod2003/mcp-rsv-data/releases/latest/download/MCP-RSV-Data.zip' (Join-Path $env:TEMP 'rsv.zip')
        Expand-Archive (Join-Path $env:TEMP 'rsv.zip') -DestinationPath $dst4 -Force
    } catch { Write-Warning "mcp-rsv-data: $($_.Exception.Message)" }
}

Write-Host ''
Write-Host 'Проверьте содержимое:' $dst ' ' $dst2
