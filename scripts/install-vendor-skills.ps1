#Requires -Version 5.1
<#
.SYNOPSIS
  Собирает вендорские Agent Skills в каталог .cline\skills проекта.

.DESCRIPTION
  Cline (VS Code extension saoudrizwan.claude-dev) читает project-скиллы из
  <project>\.cline\skills\<skill-name>\SKILL.md — подробнее docs\05-skills.md.

  Скрипт копирует каталоги скиллов из skills-vendor\* в .cline\skills\.
  Порядок источников = приоритет: последний источник перекрывает предыдущий
  при совпадении имени каталога скилла (см. docs\05-skills.md, «Источники»).

.NOTES
  Идемпотентен: повторный запуск перезаписывает .cline\skills заново.
  Ничего вне каталога проекта не меняет.
#>
[CmdletBinding()]
param(
    # Корень проекта. По умолчанию — каталог выше этого скрипта (корень харнесса).
    [string] $Root
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}

$vendorDir  = Join-Path $Root 'skills-vendor'
$targetDir  = Join-Path $Root '.cline\skills'

# Порядок = приоритет (поздний источник выигрывает конфликт имён каталога).
# Источник: <подкаталог в skills-vendor> / <путь к каталогу со скиллами внутри него>
$sources = @(
    @{ Repo = 'cc-1c-skills';                 Path = '.claude\skills' },   # 81 скилл, имена без префикса (cf-edit, db-create)
    @{ Repo = 'Vanessa_for_AI';               Path = '.claude\skills' },   # Vanessa Automation для AI-агента
    @{ Repo = 'va-ai-autotests';              Path = 'skill' },            # генератор Gherkin-сценариев
    @{ Repo = '1c-mcp-toolkit';               Path = 'skills' },           # навыки работы с 1C MCP Toolkit
    @{ Repo = 'product-analyst';              Path = '.' },                # SKILL.md в корне репозитория
    @{ Repo = 'cursor-1c-skills';             Path = 'skills' }            # 121 скилл, имена с префиксом 1c-*; ВЫИГРЫВАЕТ конфликты
)

if (-not (Test-Path $vendorDir)) {
    throw "Не найден каталог вендорских скиллов: $vendorDir. Сначала выполните install-vendor-repos.ps1."
}

if (Test-Path $targetDir) { Remove-Item $targetDir -Recurse -Force }
New-Item -ItemType Directory -Force $targetDir | Out-Null

$copied   = 0
$skipped  = 0
$overwrote = @()

foreach ($src in $sources) {
    $srcPath = Join-Path $vendorDir (Join-Path $src.Repo $src.Path)
    if (-not (Test-Path $srcPath)) {
        Write-Warning "Пропуск источника (нет каталога): $srcPath"
        continue
    }

    # Скилл = каталог, содержащий SKILL.md. Для product-analyst источник сам является скиллом.
    $skillDirs = @()
    if (Test-Path (Join-Path $srcPath 'SKILL.md')) {
        $skillDirs += Get-Item $srcPath
    }
    $skillDirs += Get-ChildItem $srcPath -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }

    foreach ($sd in $skillDirs) {
        $name = Split-Path -Leaf $sd.FullName
        $dest = Join-Path $targetDir $name

        if (Test-Path $dest) {
            $overwrote += $name
            Remove-Item $dest -Recurse -Force
        }

        Copy-Item $sd.FullName $dest -Recurse -Force
        $copied++
    }

    Write-Host ("[{0}] +{1} скиллов из {2}" -f $src.Repo, $skillDirs.Count, $src.Path)
}

# --- Валидация: у каждого скилла name в frontmatter должен совпадать с именем каталога ---
$problems = @()
foreach ($d in Get-ChildItem $targetDir -Directory) {
    $skillMd = Join-Path $d.FullName 'SKILL.md'
    if (-not (Test-Path $skillMd)) { $problems += "$($d.Name): нет SKILL.md"; continue }

    $head = Get-Content $skillMd -TotalCount 40 -Encoding UTF8
    $nameLine = $head | Where-Object { $_ -match '^\s*name\s*:\s*(.+?)\s*$' } | Select-Object -First 1
    if (-not $nameLine) { $problems += "$($d.Name): нет поля name"; continue }

    $declared = ($nameLine -replace '^\s*name\s*:\s*', '').Trim().Trim('"').Trim("'")
    if ($declared -ne $d.Name) { $problems += "$($d.Name): name='$declared' != каталог" }
}

Write-Host ''
Write-Host ("ИТОГО: скопировано {0} скиллов в {1}" -f $copied, $targetDir)
if ($overwrote.Count -gt 0) {
    Write-Host ("Перекрыто при конфликте имён ({0}): {1}" -f $overwrote.Count, (($overwrote | Sort-Object -Unique) -join ', '))
}
if ($problems.Count -gt 0) {
    Write-Warning "Проблемы с frontmatter у $($problems.Count) скиллов:"
    $problems | ForEach-Object { Write-Warning "  $_" }
    exit 2
}

Write-Host 'Валидация frontmatter: OK'
