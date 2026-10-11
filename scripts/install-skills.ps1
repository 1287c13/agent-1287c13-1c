<#
.SYNOPSIS
    Разложить вендорные скиллы (skills-vendor\*) в каталог, откуда их читает Cline.
.DESCRIPTION
    Источник — только скиллы, скачанные с GitHub скриптом install-vendor-skills.ps1.
    Своих («придуманных») скиллов здесь нет и не должно быть.

    Каталоги, которые читает Cline (см. документацию Cline -> Config):
      * глобально:  ~/.cline/skills
      * в проекте:  <проект>/.cline/skills
      * совместимость: <проект>/.clinerules/skills, <проект>/.agents/skills, ~/.agents/skills

    Скиллом считается каталог, внутри которого лежит SKILL.md.
.EXAMPLE
    .\install-skills.ps1                                   # глобально: ~/.cline/skills
    .\install-skills.ps1 -Scope Project -ProjectDir 'C:\w\1c\агент'
    .\install-skills.ps1 -Target 'D:\cline-skills' -Force
#>
[CmdletBinding()]
param(
    [ValidateSet('Global', 'Project', 'Custom')][string]$Scope = 'Global',
    [string]$ProjectDir,
    [string]$Target,
    [string]$Vendor,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
$agentRoot = Split-Path -Parent $PSScriptRoot
if (-not $Vendor) { $Vendor = Join-Path $agentRoot 'skills-vendor' }

if ($Scope -eq 'Global' -and -not $Target) { $Target = Join-Path $HOME '.cline\skills' }
if ($Scope -eq 'Project') {
    if (-not $ProjectDir) { $ProjectDir = $agentRoot }
    if (-not $Target)     { $Target = Join-Path $ProjectDir '.cline\skills' }
}
if (-not $Target) { throw 'Не задан целевой каталог (укажите -Target)' }
if (-not (Test-Path $Vendor)) { throw "Нет каталога вендорных скиллов: $Vendor. Сначала .\install-vendor-skills.ps1" }

# скилл = каталог с SKILL.md
$skills = Get-ChildItem $Vendor -Recurse -File -Filter 'SKILL.md' |
    ForEach-Object { $_.Directory } |
    Sort-Object FullName -Unique

Write-Host "Источник: $Vendor"
Write-Host "Найдено вендорных скиллов: $($skills.Count)"
New-Item -ItemType Directory -Force $Target | Out-Null

foreach ($s in $skills) {
    $dst = Join-Path $Target $s.Name
    if (Test-Path $dst) {
        if (-not $Force) { Write-Host "  skip (уже есть): $($s.Name)"; continue }
        Remove-Item $dst -Recurse -Force
    }
    Copy-Item $s.FullName $dst -Recurse -Force
    Write-Host "  ok: $($s.Name)"
}

Write-Host ''
Write-Host "Готово. Cline читает скиллы из: $Target"
Write-Host 'Проверьте в Cline: иконка Skills -> вкладка Skills (включить нужные).'
