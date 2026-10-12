#Requires -Version 5.1
<#
.SYNOPSIS
    Развернуть внешнюю обработку Vanessa Automation из релизного zip-архива.

.DESCRIPTION
    Vanessa Automation не нужно устанавливать в конфигурацию базы: она
    запускается ВНЕШНЕЙ обработкой (ключ платформы /Execute). Нужен только сам
    файл обработки. В релизном архиве он называется vanessa-automation-single.epf
    (сборка Single - один epf, внутри которого уже лежит библиотека шагов).

    Архив берётся из релизов проекта:
      https://github.com/Pr-Mex/vanessa-automation/releases
      файл vanessa-automation-single.<версия>.zip

    Скрипт достаёт epf из архива в <корень>\.vanessa\. Каталог .vanessa в git не
    хранится (.gitignore: *.epf и .vanessa/), как и прочие тяжёлые артефакты.

.PARAMETER Zip
    Путь к релизному архиву vanessa-automation-single.*.zip.
    Если не указан - берётся самый свежий такой архив из каталога Загрузки.

.PARAMETER Force
    Перезаписать уже развёрнутый epf.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\install-vanessa.ps1

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\install-vanessa.ps1 `
        -Zip "$env:USERPROFILE\Downloads\vanessa-automation-single.1.2.043.1.zip" -Force
#>
[CmdletBinding()]
param(
    [string] $Zip,
    [switch] $Force
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path -LiteralPath $PSCommandPath).Path }
$Root = Split-Path -Parent $scriptDir

Add-Type -AssemblyName System.IO.Compression.FileSystem

if ([string]::IsNullOrWhiteSpace($Zip)) {
    $downloads = Join-Path $env:USERPROFILE 'Downloads'
    $Zip = Get-ChildItem -LiteralPath $downloads -Filter 'vanessa-automation-single*.zip' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
    if (-not $Zip) {
        Write-Host "Не найден архив vanessa-automation-single*.zip в $downloads." -ForegroundColor Red
        Write-Host 'Скачайте его со страницы релизов: https://github.com/Pr-Mex/vanessa-automation/releases'
        exit 1
    }
}

if (-not (Test-Path -LiteralPath $Zip)) {
    Write-Host "Нет файла: $Zip" -ForegroundColor Red
    exit 1
}

$targetDir = Join-Path $Root '.vanessa'
if (-not (Test-Path -LiteralPath $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
$target = Join-Path $targetDir 'vanessa-automation-single.epf'

if ((Test-Path -LiteralPath $target) -and -not $Force) {
    Write-Host "Уже развёрнуто: $target (повторить - с ключом -Force)"
    exit 0
}

$archive = [System.IO.Compression.ZipFile]::OpenRead($Zip)
try {
    $entry = $archive.Entries | Where-Object { $_.Name -like '*.epf' } |
        Sort-Object Length -Descending | Select-Object -First 1
    if (-not $entry) {
        Write-Host "В архиве $Zip нет epf-файла." -ForegroundColor Red
        Write-Host 'Похоже, это архив с исходниками. Возьмите vanessa-automation-single.*.zip из релизов.'
        exit 1
    }
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target, $true)
    $name = $entry.Name
}
finally {
    $archive.Dispose()
}

$size = [Math]::Round((Get-Item -LiteralPath $target).Length / 1MB, 1)
Write-Host "Развёрнуто: $target ($size МБ, из $name)"
Write-Host 'Дальше: scripts\vanessa-run.ps1 -DatabaseId <id> -Features <каталог или .feature>'
