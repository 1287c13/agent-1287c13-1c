# publish-odata.ps1 - publish the default database from .v8-project.json through
# Apache and print the OData metadata URL.
#
# Thin wrapper around the vendor skill script:
#   .cline/skills/1c-web-publish/scripts/web-publish.ps1
# It only resolves connection parameters from .v8-project.json, so no Cyrillic
# literal (and therefore no BOM requirement) is needed in this file.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\publish-odata.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\publish-odata.ps1 -AppName demoar -Port 8081 -UserName Admin -Password ''

#Requires -Version 5.1
<#
.SYNOPSIS
    Публикация базы из .v8-project.json через Apache + OData (скилл 1c-web-publish).

.DESCRIPTION
    Обёртка над скриптом скилла .cline\skills\1c-web-publish\scripts\web-publish.ps1.
    Сама обёртка содержит только ASCII, поэтому не зависит от BOM и кодовой страницы
    PowerShell 5.1: путь к базе (кириллица) читается из .v8-project.json и передаётся
    в скрипт скилла внутри процесса, минуя командную строку.

.NOTES
    По умолчанию публикует базу из поля "default" конфига проекта под AppName "demoar".
#>

[CmdletBinding()]
param(
    [string]$Root,
    [string]$DatabaseId = '',
    [string]$AppName = 'demoar',
    [int]$Port = 8081,
    [string]$UserName = '',
    [string]$Password = '',
    [switch]$Manual
)

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path -LiteralPath $PSCommandPath).Path }
    # <корень харнесса>\scripts -> <корень харнесса>
    $Root = Split-Path -Parent $scriptDir
}
$projectRoot = $Root

$cfgPath = Join-Path $projectRoot '.v8-project.json'
if (-not (Test-Path -LiteralPath $cfgPath)) {
    Write-Error "Project config not found: $cfgPath"
    exit 1
}

$cfg = Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $DatabaseId) { $DatabaseId = $cfg.default }

$db = @($cfg.databases | Where-Object { $_.id -eq $DatabaseId })[0]
if ($null -eq $db) {
    Write-Error "Database id '$DatabaseId' is not declared in .v8-project.json"
    exit 1
}

$v8path = $db.v8path
if (-not $v8path) { $v8path = $cfg.v8path }

$publisher = Join-Path $projectRoot '.cline\skills\1c-web-publish\scripts\web-publish.ps1'
if (-not (Test-Path -LiteralPath $publisher)) {
    Write-Error "Skill script not found: $publisher"
    exit 1
}

Write-Host "Database  : $($db.name) [$DatabaseId]"
Write-Host "Path      : $($db.path)"
Write-Host "V8Path    : $v8path"
Write-Host "App / Port: $AppName / $Port"

$publishParams = @{
    InfoBasePath = $db.path
    V8Path       = $v8path
    AppName      = $AppName
    Port         = $Port
}
if ($UserName) { $publishParams.UserName = $UserName }
if ($Password) { $publishParams.Password = $Password }
if ($Manual)   { $publishParams.Manual = $true }

& $publisher @publishParams
$rc = $LASTEXITCODE

Write-Host ""
Write-Host "OData URL: http://localhost:$Port/$AppName/odata/standard.odata/"
Write-Host "Metadata : http://localhost:$Port/$AppName/odata/standard.odata/`$metadata"
exit $rc
