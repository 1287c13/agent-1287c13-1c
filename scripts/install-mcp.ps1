#Requires -Version 5.1
<#
.SYNOPSIS
  Ставит MCP-серверы харнесса внутрь каталога проекта (.cline\mcp).

.DESCRIPTION
  Ставятся три сервера, каждый - в свой подкаталог .cline\mcp\:
    1c-code-index     bsl-indexer.exe            (структурный поиск по коду, сборка с поддержкой 1С)
    1c-toolkit        MCP_Toolkit.epf            (живая база 1С: данные, код, метаданные, OData)
    1c-platform-help  mcp-bsl-context (venv)     (справка API платформы 1С, стандарты BSL)

  Бинарники в git не хранятся (крупные). В git лежат конфиг, скрипты и скиллы;
  этот скрипт восстанавливает бинарную часть на любой машине.

.NOTES
  Требует: git, python-лаунчер (py), интернет. Идемпотентен; -Force переустанавливает.
#>
[CmdletBinding()]
param(
    [string] $Root,
    # Версия релиза code-index-mcp ("latest" или, например, "v1.8.6").
    [string] $CodeIndexRelease = 'latest',
    # Лаунчер Python для venv сервера справки.
    [string] $PythonLauncher = 'py -3',
    [switch] $Force
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}

$mcpDir   = Join-Path $Root '.cline\mcp'
$vendor   = Join-Path $Root 'skills-vendor'
New-Item -ItemType Directory -Force $mcpDir | Out-Null

$userAgent = @{ 'User-Agent' = '1c-ai-agent-harness' }

# ============================================================================
# 1. code-index-mcp (bsl-indexer.exe)
# ============================================================================
$ciDir = Join-Path $mcpDir 'code-index-mcp'
$ciExe = Join-Path $ciDir 'bsl-indexer.exe'
New-Item -ItemType Directory -Force $ciDir | Out-Null

if ((Test-Path $ciExe) -and -not $Force) {
    Write-Host "[=] 1c-code-index: bsl-indexer.exe уже установлен"
}
else {
    $metaUrl = if ($CodeIndexRelease -eq 'latest') {
        'https://api.github.com/repos/Regsorm/code-index-mcp/releases/latest'
    } else {
        "https://api.github.com/repos/Regsorm/code-index-mcp/releases/tags/$CodeIndexRelease"
    }
    Write-Host "[*] 1c-code-index: $metaUrl"
    $rel = Invoke-RestMethod $metaUrl -Headers $userAgent -TimeoutSec 60
    $asset = $rel.assets | Where-Object { $_.name -eq 'bsl-indexer-windows-x64.zip' } | Select-Object -First 1
    if (-not $asset) { throw 'В релизе нет актива bsl-indexer-windows-x64.zip' }
    $zip = Join-Path $env:TEMP 'bsl-indexer-windows-x64.zip'
    Invoke-WebRequest $asset.browser_download_url -OutFile $zip -UseBasicParsing -Headers $userAgent
    ($rel.tag_name) | Set-Content (Join-Path $ciDir 'VERSION.txt') -Encoding UTF8
    Remove-Item $ciExe -Force -ErrorAction SilentlyContinue
    Expand-Archive -Path $zip -DestinationPath $ciDir -Force
    Write-Host "[+] 1c-code-index: $($rel.tag_name) -> $ciExe"
}

# ============================================================================
# 2. 1c-mcp-toolkit (MCP_Toolkit.epf) — берём из вендорского репозитория
# ============================================================================
$tkDir = Join-Path $mcpDir '1c-mcp-toolkit'
New-Item -ItemType Directory -Force $tkDir | Out-Null
$tkSrc = Join-Path $vendor '1c-mcp-toolkit\build\MCP_Toolkit.epf'

if ((Test-Path (Join-Path $tkDir 'MCP_Toolkit.epf')) -and -not $Force) {
    Write-Host '[=] 1c-toolkit: MCP_Toolkit.epf уже установлен'
}
elseif (Test-Path $tkSrc) {
    Copy-Item $tkSrc $tkDir -Force
    Copy-Item (Join-Path $vendor '1c-mcp-toolkit\build\MCP_Toolkit_x86.epf') $tkDir -Force -ErrorAction SilentlyContinue
    Write-Host "[+] 1c-toolkit: MCP_Toolkit.epf скопирован из skills-vendor"
}
else {
    throw "Нет $tkSrc. Сначала выполните scripts\install-vendor-repos.ps1"
}

# ============================================================================
# 3. bsl-platform-help-context (venv)
# ============================================================================
$phDir = Join-Path $mcpDir 'bsl-platform-help-context'
$phSrc = Join-Path $vendor 'mcp-bsl-platform-help-context'
$phPy  = Join-Path $phDir '.venv\Scripts\python.exe'
New-Item -ItemType Directory -Force $phDir | Out-Null

if (-not (Test-Path $phSrc)) {
    Write-Warning "Нет исходников $phSrc - запускаю install-vendor-repos.ps1"
    & (Join-Path $PSScriptRoot 'install-vendor-repos.ps1') -Root $Root
}

$installed = (Test-Path (Join-Path $phDir '.venv\Scripts\mcp-bsl-context.exe'))
if ($installed -and -not $Force) {
    Write-Host '[=] 1c-platform-help: venv уже собран'
}
else {
    Write-Host "[*] 1c-platform-help: создаю venv ($PythonLauncher) - это несколько минут"
    if (Test-Path (Join-Path $phDir '.venv')) { Remove-Item (Join-Path $phDir '.venv') -Recurse -Force }
    $pyParts = $PythonLauncher -split '\s+'
    & $pyParts[0] @($pyParts[1..($pyParts.Count - 1)] + @('-m', 'venv', (Join-Path $phDir '.venv')))
    & $phPy -m pip install --upgrade pip --disable-pip-version-check --quiet
    & $phPy -m pip install --disable-pip-version-check $phSrc
    Write-Host '[+] 1c-platform-help: venv собран'
}

Write-Host ''
Write-Host 'Готово. Дальше: scripts\enable-mcp.ps1 (подключить серверы к Cline).'
