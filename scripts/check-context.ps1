<#
.SYNOPSIS
    Промпт-бюджет: что уходит в каждый запрос к модели и сколько это стоит.
.DESCRIPTION
    Считает всегда-инжектируемый префикс: файлы .clinerules\*.md, AGENTS.md,
    метаданные скиллов (в контекст идут только id). Сверяет с бюджетами и
    возвращает 1 при перерасходе. START.md, README.md, SOURCES.md, docs\,
    analysis\ не инжектируются: они перечисляются отдельно, чтобы их объём не
    путали с префиксом.

    Оценка токенов приблизительная: кириллица в токенизаторах плотнее латиницы.
    Точный замер - только по метрике tokensIn живой сессии Cline.
.PARAMETER Root
    Корень проекта. По умолчанию - каталог уровнем выше scripts\.
.PARAMETER Quiet
    Печатать только итоговую строку (режим для check-harness.ps1).
.PARAMETER Mcp
    Дополнительно измерить объём схем MCP-сервера по адресу порта 6003.
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-context.ps1
#>
[CmdletBinding()]
param(
    [string] $Root = '',
    [switch] $Quiet,
    [switch] $Mcp
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
if (-not $Root) {
    # В блоке param() в PowerShell 5.1 $PSScriptRoot ещё не заполнен: корень считаем здесь.
    $Root = Split-Path -Parent $PSScriptRoot
}

# Бюджеты всегда-инжектируемого текста, символы.
$budgetRules    = 45000
$budgetLessons  = 15500
$budgetAgents   = 3000
$budgetSkillIds = 6000

$problems = New-Object System.Collections.Generic.List[string]

function Get-TextInfo {
    param([string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $text  = [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
    $chars = $text.Length
    $cyr   = ([regex]::Matches($text, '[\u0400-\u04FF]')).Count
    # Оценка токенов: кириллица ~2.2 символа на токен, прочее ~4.
    $tokens = [int](($cyr / 2.2) + (($chars - $cyr) / 4.0))
    return [pscustomobject]@{ Chars = $chars; Cyr = $cyr; Tokens = $tokens }
}

function Write-Row {
    param([string] $Name, [int] $Chars, [int] $Tokens, [int] $Budget)
    $mark = '  '
    if ($Budget -gt 0) {
        if ($Chars -gt $Budget) { $mark = '!!' } elseif ($Chars -gt ($Budget * 0.9)) { $mark = ' ^' }
    }
    $tail = ''
    if ($Budget -gt 0) { $tail = (' бюджет {0,6}' -f $Budget) }
    '{0} {1,-44} {2,7} {3,7}{4}' -f $mark, $Name, $Chars, $Tokens, $tail
}
$rulesDir = Join-Path $Root '.clinerules'
$rulesFiles = @()
if (Test-Path $rulesDir) { $rulesFiles = Get-ChildItem $rulesDir -Filter '*.md' -File | Sort-Object Name }

$rulesRows   = @()
$rulesChars  = 0
$rulesTokens = 0
foreach ($f in $rulesFiles) {
    $info = Get-TextInfo $f.FullName
    $rulesChars  += $info.Chars
    $rulesTokens += $info.Tokens
    $rulesRows   += [pscustomobject]@{ Name = $f.Name; Chars = $info.Chars; Tokens = $info.Tokens }
}
if ($rulesChars -gt $budgetRules) {
    $problems.Add(('правила .clinerules: {0} символов при бюджете {1}' -f $rulesChars, $budgetRules))
}
$lessonsChars = 0
foreach ($r in $rulesRows) { if ($r.Name -eq '40-lessons.md') { $lessonsChars = $r.Chars } }
if ($lessonsChars -gt $budgetLessons) {
    $problems.Add(('40-lessons.md: {0} символов при бюджете {1}: в правилах остается инвариант, разбор уходит в analysis\' -f $lessonsChars, $budgetLessons))
}

$agentsInfo  = Get-TextInfo (Join-Path $Root 'AGENTS.md')
$agentsChars = 0
$agentsTokens = 0
if ($agentsInfo) {
    $agentsChars  = $agentsInfo.Chars
    $agentsTokens = $agentsInfo.Tokens
    if ($agentsChars -gt $budgetAgents) {
        $problems.Add(('AGENTS.md: {0} символов при бюджете {1}: это указатель на правила, а не их пересказ' -f $agentsChars, $budgetAgents))
    }
}

# Скиллы: в контекст уходят только метаданные (id), тела SKILL.md подгружаются по релевантности.
$skillsDir  = Join-Path $Root '.cline\skills'
$skillDirs  = @()
if (Test-Path $skillsDir) { $skillDirs = Get-ChildItem $skillsDir -Directory }
$skillIdChars = 0
foreach ($d in $skillDirs) { $skillIdChars += ($d.Name.Length + 2) }
if ($skillIdChars -gt $budgetSkillIds) {
    $problems.Add(('метаданные скиллов: {0} символов при бюджете {1}' -f $skillIdChars, $budgetSkillIds))
}

$skillTokens    = [int]($skillIdChars / 4.0)
$injectedChars  = $rulesChars + $agentsChars + $skillIdChars
$injectedTokens = $rulesTokens + $agentsTokens + $skillTokens
if (-not $Quiet) {
    Write-Host 'Промпт-бюджет: всегда-инжектируемый префикс'
    Write-Host ''
    Write-Host '  Правила (.clinerules):'
    foreach ($r in $rulesRows) { Write-Row ('    ' + $r.Name) $r.Chars $r.Tokens 0 }
    Write-Row '    AGENTS.md' $agentsChars $agentsTokens $budgetAgents
    Write-Host ''
    Write-Host '  В префиксе целиком:'
    Write-Row '    .clinerules\*.md' $rulesChars $rulesTokens $budgetRules
    Write-Row '    .clinerules\40-lessons.md (внутри правил)' $lessonsChars 0 $budgetLessons
    Write-Row '    AGENTS.md' $agentsChars $agentsTokens $budgetAgents
    Write-Row ('    метаданные скиллов ({0})' -f $skillDirs.Count) $skillIdChars $skillTokens $budgetSkillIds
    Write-Host ''
    Write-Host ('    ВСЕГО: {0} символов, ~{1} токенов (оценка)' -f $injectedChars, $injectedTokens)
    Write-Host ''
    Write-Host '  Не инжектируется (объём контролируется отдельно):'
    foreach ($name in @('START.md', 'README.md', 'SOURCES.md')) {
        $info = Get-TextInfo (Join-Path $Root $name)
        if ($info) { Write-Row ('    ' + $name) $info.Chars $info.Tokens 0 }
    }
    $docsChars = 0
    $docsDir = Join-Path $Root 'docs'
    if (Test-Path $docsDir) {
        foreach ($f in (Get-ChildItem $docsDir -Filter '*.md' -File)) { $docsChars += (Get-TextInfo $f.FullName).Chars }
    }
    Write-Row '    docs\*.md' $docsChars 0 0
    $skillBodyChars = 0
    foreach ($d in $skillDirs) {
        $sk = Join-Path $d.FullName 'SKILL.md'
        if (Test-Path $sk) { $skillBodyChars += ([System.IO.File]::ReadAllText($sk, [System.Text.Encoding]::UTF8)).Length }
    }
    Write-Row ('    тела SKILL.md ({0}) - читаются по требованию' -f $skillDirs.Count) $skillBodyChars 0 0
    Write-Host ''
}

if ($Mcp) {
    $url = 'http://127.0.0.1:6003/mcp'
    try {
        $hdr = @{ Accept = 'application/json, text/event-stream' }
        $init = @{ jsonrpc = '2.0'; id = 1; method = 'initialize'; params = @{ protocolVersion = '2024-11-05'; capabilities = @{}; clientInfo = @{ name = 'check-context'; version = '1.0' } } } | ConvertTo-Json -Depth 10 -Compress
        $r1 = Invoke-WebRequest -Uri $url -Method Post -Body ([System.Text.Encoding]::UTF8.GetBytes($init)) -ContentType 'application/json; charset=utf-8' -Headers $hdr -UseBasicParsing -TimeoutSec 20
        $sid = $r1.Headers['mcp-session-id']
        if ($sid) { $hdr['mcp-session-id'] = $sid }
        $null = Invoke-WebRequest -Uri $url -Method Post -Body ([System.Text.Encoding]::UTF8.GetBytes((@{ jsonrpc = '2.0'; method = 'notifications/initialized' } | ConvertTo-Json -Compress))) -ContentType 'application/json; charset=utf-8' -Headers $hdr -UseBasicParsing -TimeoutSec 20
        $lst = @{ jsonrpc = '2.0'; id = 2; method = 'tools/list'; params = @{} } | ConvertTo-Json -Depth 5 -Compress
        $r2 = Invoke-WebRequest -Uri $url -Method Post -Body ([System.Text.Encoding]::UTF8.GetBytes($lst)) -ContentType 'application/json; charset=utf-8' -Headers $hdr -UseBasicParsing -TimeoutSec 20
        $text = [System.Text.Encoding]::UTF8.GetString($r2.RawContentStream.ToArray())
        # SSE: однособытийный ответ приходит строками data:, их надо склеить в один JSON.
        $payload = ''
        foreach ($line in ($text -split "`r?`n")) {
            if ($line.StartsWith('data:')) { $payload += $line.Substring(5).TrimStart() }
        }
        if (-not $payload) { $payload = $text }
        $obj   = $payload | ConvertFrom-Json
        $sum   = 0
        foreach ($t in $obj.result.tools) { $sum += ($t | ConvertTo-Json -Depth 30 -Compress).Length }
        Write-Host ('  MCP 1c-toolkit (6003): инструментов {0}, схемы {1} символов (compact)' -f $obj.result.tools.Count, $sum)
        Write-Host ('  Средний инструмент: {0} символов. Разбор по инструментам - temp\probe-tools.ps1' -f [int]($sum / $obj.result.tools.Count))
    }
    catch {
        Write-Host ('  MCP 1c-toolkit (6003): замер пропущен - ' + $_.Exception.Message)
    }
}

if ($problems.Count -gt 0) {
    Write-Host ''
    foreach ($p in $problems) { Write-Host ('[FAIL] ' + $p) }
    if ($Quiet) { Write-Host ('Промпт-бюджет: перерасход, замечаний {0}' -f $problems.Count) }
    exit 1
}
if ($Quiet) {
    Write-Host ('Промпт-бюджет: {0} символов, ~{1} токенов (правила {2}, AGENTS {3}, скиллы {4})' -f $injectedChars, $injectedTokens, $rulesChars, $agentsChars, $skillIdChars)
}
else {
    Write-Host 'Промпт-бюджет: в пределах нормы.'
}
exit 0
