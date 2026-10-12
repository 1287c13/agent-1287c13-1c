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
  Каталог, который существует, но не является git-репозиторием (набор принесён
  копированием), сам не переклонируется: скрипт остановится с подсказкой, а
  повторный запуск с -Force переклонирует каталог.
#>
[CmdletBinding()]
param(
    [string] $Root,
    # Переклонировать каталог, который существует, но не является git-репозиторием
    # (содержимое каталога будет удалено).
    [switch] $Force
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

# git пишет прогресс и предупреждения в stderr: при ErrorActionPreference=Stop
# это превращается в исключение, поэтому на время git-операций режим ослабляем
# и проверяем код возврата сами.
$ErrorActionPreference = 'Continue'
$failed = New-Object 'System.Collections.Generic.List[string]'

foreach ($url in $repos) {
    $name = ($url -split '/')[-1].Replace('.git', '')
    $dest = Join-Path $vendorDir $name

    if (Test-Path (Join-Path $dest '.git')) {
        Write-Host "[pull]  $name"
        $out = git -C $dest pull --ff-only --depth 1 2>&1
        if ($LASTEXITCODE -ne 0) {
            $failed.Add($name)
            Write-Host '       git pull не удался:' -ForegroundColor Red
            $out | ForEach-Object { Write-Host "       $_" }
        }
        continue
    }

    if (Test-Path $dest) {
        if (-not $Force) {
            $ErrorActionPreference = 'Stop'
            throw "$dest уже существует, но это не git-репозиторий. Запустите скрипт с -Force, чтобы переклонировать каталог (содержимое каталога будет удалено)."
        }
        Write-Host "[force] $name - каталог без .git, переклонирую"
        Remove-Item $dest -Recurse -Force
    }
    else {
        Write-Host "[clone] $name"
    }

    $out = git clone --depth 1 $url $dest 2>&1
    if ($LASTEXITCODE -ne 0) {
        $failed.Add($name)
        Write-Host '       git clone не удался:' -ForegroundColor Red
        $out | ForEach-Object { Write-Host "       $_" }
    }
}
$ErrorActionPreference = 'Stop'

Write-Host ''
Write-Host 'Коммиты (зафиксируйте в SOURCES.md для воспроизводимости):'
foreach ($d in Get-ChildItem $vendorDir -Directory) {
    if (Test-Path (Join-Path $d.FullName '.git')) {
        $sha = (git -C $d.FullName rev-parse --short HEAD 2>$null)
        Write-Host ("  {0,-32} {1}" -f $d.Name, $sha)
    }
}

if ($failed.Count -gt 0) {
    Write-Host ''
    Write-Host ("Не развернуты: {0}" -f ($failed -join ', ')) -ForegroundColor Red
    exit 1
}
