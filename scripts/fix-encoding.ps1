<#
.SYNOPSIS
    Пересохранить .ps1 файлы агента в UTF-8 с BOM.
.DESCRIPTION
    Windows PowerShell 5.1 читает .ps1 без BOM как ANSI — русский текст в
    скриптах превращается в мусор и может ломать парсинг. Запускайте этот
    скрипт после правки любого .ps1 вручную или из редактора.
.EXAMPLE
    .\fix-encoding.ps1
#>
[CmdletBinding()]
param([string]$Path)
# По умолчанию правим .ps1 самого харнесса (каталог scripts). Значением по умолчанию НЕ должен
# быть корень проекта: рекурсивный обход dump\, skills-vendor\ и .code-index\ - это минуты
# (именно это дало таймаут). Широкий обход задаётся явно: -Path <каталог>.
if (-not $Path) {
    $Path = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path $PSCommandPath).Path }
}

$enc = New-Object System.Text.UTF8Encoding($true)
$files = Get-ChildItem -Path $Path -Filter *.ps1 -Recurse -ErrorAction SilentlyContinue
foreach ($f in $files) {
    $text = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText($f.FullName, $text, $enc)
    Write-Host ("fixed: " + $f.FullName)
}
Write-Host ("Всего файлов: " + $files.Count)
