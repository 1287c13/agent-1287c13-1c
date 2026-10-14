#Requires -Version 5.1
<#
.SYNOPSIS
  Заводит файл результата анализа в каталоге analysis\ с меткой времени в имени.

.DESCRIPTION
  Имя файла: <ГГГГ-ММ-ДД>_<ЧЧММ>_<краткое-имя>.md - метка времени даёт уникальность,
  краткое имя - человекочитаемость. Каталог analysis\ закрыт .gitignore: разбор кейса
  и расследование - рабочий артефакт агента, в репозиторий он не идёт.

  Скрипт создаёт каталог (если его нет), файл с шапкой (дата, задача) и печатает путь.
  Если файл на эту минуту уже есть, метка дополняется секундами - имя остаётся
  уникальным. Существующий файл без -Force не перезаписывается.

.PARAMETER Name
  Краткое имя анализа латиницей: upd-gruzopoluchatel-edo, ostatki-po-skladam.
  Прочие символы заменяются дефисом, регистр приводится к нижнему.

.PARAMETER Title
  Заголовок файла (первая строка). По умолчанию - Name с заменой дефисов пробелами.

.PARAMETER Task
  Формулировка задачи, по которой сделан анализ: идёт в шапку файла.

.PARAMETER Root
  Корень харнесса. По умолчанию - родитель каталога scripts.

.PARAMETER Force
  Перезаписать файл, если он существует.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\new-analysis.ps1 `
      -Name upd-gruzopoluchatel-edo -Task "как аналитик разбери расхождение печатной формы и ЭД"

.NOTES
  Код возврата 0 - файл создан (путь печатается последней строкой), 1 - ошибка.
  Каталог analysis\ прописан в .gitignore.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $Name,

    [string] $Title,
    [string] $Task,
    [string] $Root,

    [switch] $Force
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}

# Краткое имя -> имя файла: только латиница, цифры, дефис и подчёркивание.
$slug = $Name.Trim().ToLower()
$slug = $slug -replace '[^0-9a-z\-_]+', '-'
$slug = $slug.Trim('-', '_')
$slug = $slug -replace '-{2,}', '-'
if ([string]::IsNullOrWhiteSpace($slug)) {
    Write-Host 'Не удалось построить краткое имя: нужны латинские буквы или цифры.' -ForegroundColor Red
    exit 1
}

$analysisDir = Join-Path $Root 'analysis'
if (-not (Test-Path $analysisDir)) {
    New-Item -ItemType Directory -Path $analysisDir | Out-Null
}

# Метка времени: минуты для читаемости, секунды - если на эту минуту файл уже есть.
$stamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$file = Join-Path $analysisDir ("{0}_{1}.md" -f $stamp, $slug)
if ((Test-Path $file) -and -not $Force) {
    $stamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
    $file = Join-Path $analysisDir ("{0}_{1}.md" -f $stamp, $slug)
}
if ((Test-Path $file) -and -not $Force) {
    Write-Host "Файл уже существует: $file (перезапись - ключом -Force)" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrWhiteSpace($Title)) { $Title = ($slug -replace '[-_]', ' ') }
if ([string]::IsNullOrWhiteSpace($Task)) { $Task = '(не указана)' }

$body = @(
    "# $Title"
    ''
    "- Дата: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    "- Задача: $Task"
    "- Создал: scripts\new-analysis.ps1"
    ''
    '<!-- Результат анализа. Каталог analysis\ в .gitignore: файл не коммитится. -->'
    ''
) -join [Environment]::NewLine

# UTF-8 без BOM: файл читает и агент, и человек; BOM в markdown не нужен.
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($file, $body, $utf8NoBom)

Write-Host "  [ok]   анализ: $(Split-Path -Leaf $file)" -ForegroundColor Green
Write-Host "         каталог: $analysisDir" -ForegroundColor DarkGray
Write-Host $file
exit 0
