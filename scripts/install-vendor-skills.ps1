<#
.SYNOPSIS
    Скачать вендорские скиллы и документацию (только чужие репозитории, файлы не правятся).
.DESCRIPTION
    Скиллы кладутся в skills-vendor\<репозиторий>\, документация по инструментам MCP —
    в mcp\<сервер>\vendor-docs\. Источники и лицензии — skills-vendor\SOURCES.md.
.EXAMPLE
    .\install-vendor-skills.ps1
#>
[CmdletBinding()]
param([string]$AgentRoot)
$ErrorActionPreference = 'Stop'
if (-not $AgentRoot) { $AgentRoot = Split-Path -Parent $PSScriptRoot }
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-File([string]$url, [string]$out) {
    $dir = Split-Path -Parent $out
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
    Write-Host "  -> $url"
    Invoke-WebRequest $url -OutFile $out -UseBasicParsing
}

function Get-RepoPack {
    <#
        Скачивает zip указанной ветки репозитория и копирует только перечисленные элементы.
        Если в корне репозитория лежит SKILL.md — репозиторий считается одним скиллом.
    #>
    param([string]$Repo, [string]$Branch, [string]$Dest, [string[]]$Keep)
    $slug = $Repo -replace '/', '-'
    $zip  = Join-Path $env:TEMP "pack-$slug.zip"
    $tmp  = Join-Path $env:TEMP "unpack-$slug"
    Get-File "https://codeload.github.com/$Repo/zip/refs/heads/$Branch" $zip
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $tmp)
    $top = Get-ChildItem $tmp -Directory | Select-Object -First 1

    Remove-Item $Dest -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force $Dest | Out-Null

    $items = if (Test-Path (Join-Path $top.FullName 'SKILL.md')) { @('SKILL.md') + $Keep } else { $Keep }
    foreach ($n in $items) {
        $src = Join-Path $top.FullName $n
        if (Test-Path $src) {
            Copy-Item $src -Destination $Dest -Recurse -Force
            Write-Host "  ok: $Repo / $n"
        }
    }
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}

$sv = Join-Path $AgentRoot 'skills-vendor'

Write-Host '== 1. ROCTUP/1c-mcp-toolkit — скиллы авторов выбранного MCP (живая база) =='
$t = 'https://raw.githubusercontent.com/ROCTUP/1c-mcp-toolkit/main/skills'
$files = @(
    "$t/calling-1c-rest-api-via-curl/SKILL.md",
    "$t/calling-1c-rest-api-via-curl/references/object-description-format.md",
    "$t/calling-1c-rest-api-via-curl/references/tools-full-reference.md",
    "$t/calling-1c-rest-api-via-curl/references/workflow-examples.md",
    "$t/composing-1c-queries/SKILL.md",
    "$t/composing-1c-queries/references/functions-and-expressions.md",
    "$t/composing-1c-queries/references/optimization-and-pitfalls.md",
    "$t/composing-1c-queries/references/query-syntax-reference.md"
)
foreach ($u in $files) {
    $rel = $u.Substring($t.Length + 1) -replace '/', '\'
    Get-File $u (Join-Path $sv "1c-mcp-toolkit\$rel")
}

Write-Host '== 2. Nikolay-Shirokov/cc-1c-skills — разработка 1С (MIT) =='
Get-RepoPack -Repo 'Nikolay-Shirokov/cc-1c-skills' -Branch 'main' -Dest (Join-Path $sv 'cc-1c-skills') `
    -Keep @('.claude', 'docs', 'scripts', 'README.md', 'LICENSE', 'requirements.txt')

Write-Host '== 3. andrejkaxz/Vanessa_for_AI — скиллы Vanessa Automation (CC BY 4.0) =='
Get-RepoPack -Repo 'andrejkaxz/Vanessa_for_AI' -Branch 'main' -Dest (Join-Path $sv 'Vanessa_for_AI') `
    -Keep @('.claude', 'knowledge', 'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md')

Write-Host '== 4. shevchenko-dl/va-ai-autotests — Gherkin-сценарии для Vanessa (MIT) =='
Get-RepoPack -Repo 'shevchenko-dl/va-ai-autotests' -Branch 'main' -Dest (Join-Path $sv 'va-ai-autotests') `
    -Keep @('skill', 'docs', 'prompts', 'README.md', 'LICENSE')

Write-Host '== 5. gsulamanidzebdoge/product-analyst — ТЗ/ЧТЗ, ГОСТ 34.602, 1С-ERP (MIT) =='
Get-RepoPack -Repo 'gsulamanidzebdoge/product-analyst' -Branch 'main' -Dest (Join-Path $sv 'product-analyst') `
    -Keep @('references', 'assets', 'README.md', 'LICENSE')

Write-Host '== 6. Regsorm/code-index-mcp — документация по инструментам (своих скиллов нет) =='
$c = 'https://raw.githubusercontent.com/Regsorm/code-index-mcp/main'
foreach ($u in @("$c/README_RU.md", "$c/docs/PROGRAM_OVERVIEW.md", "$c/docs/operations.md", "$c/docs/manual-install.md", "$c/docs/bsl-indexer.md")) {
    Get-File $u (Join-Path $AgentRoot ("mcp\code-index-mcp\vendor-docs\" + (Split-Path -Leaf $u)))
}

Write-Host ''
Write-Host 'Готово. Дальше: .\install-skills.ps1 (разложить скиллы для Cline).'
