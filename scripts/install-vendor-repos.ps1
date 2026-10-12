#Requires -Version 5.1
<#
.SYNOPSIS
  Клонирует/обновляет репозитории сторонних вендоров в skills-vendor.

.DESCRIPTION
  Пин-версии не фиксируются: репозитории вендорские, обновляются по main.
  Для воспроизводимости фиксируйте коммиты в SOURCES.md после установки
  (см. SOURCES.md, скрипт туда пишет хеши).

.NOTES
  Требует git в PATH. Идемпотентен: существующие репозитории обновляются git pull.
#>
[CmdletBinding()]
param(
    [string] $Root
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}

$vendorDir = Join-Path $Root 'skills-vendor'
New-Item -ItemType Directory -Force $vendorDir | Out-Null

$repos = @(
    'https://github.com/Nikolay-Shirokov/cc-1c-skills',
    'https://github.com/Desko77/cursor-1c-skills',
    'https://github.com/Desko77/mcp-bsl-platform-help-context',
    'https://github.com/andrejkaxz/Vanessa_for_AI',
    'https://github.com/shevchenko-dl/va-ai-autotests',
    'https://github.com/gsulamanidzebdoge/product-analyst',
    'https://github.com/ROCTUP/1c-mcp-toolkit'
)

$env:GIT_TERMINAL_PROMPT = '0'

foreach ($url in $repos) {
    $name = ($url -split '/')[-1].Replace('.git', '')
    $dest = Join-Path $vendorDir $name
    if (Test-Path (Join-Path $dest '.git')) {
        Write-Host "[pull]  $name"
        git -C $dest pull --ff-only --depth 1 2>&1 | Out-Null
    }
    else {
        Write-Host "[clone] $name"
        git clone --depth 1 $url $dest 2>&1 | Out-Null
    }
}

Write-Host ''
Write-Host 'Коммиты (зафиксируйте в SOURCES.md для воспроизводимости):'
foreach ($d in Get-ChildItem $vendorDir -Directory) {
    if (Test-Path (Join-Path $d.FullName '.git')) {
        $sha = (git -C $d.FullName rev-parse --short HEAD 2>$null)
        Write-Host ("  {0,-32} {1}" -f $d.Name, $sha)
    }
}
