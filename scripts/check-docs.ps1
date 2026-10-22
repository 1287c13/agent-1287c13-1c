#Requires -Version 5.1
<#
.SYNOPSIS
  Аудит расхождений: что доки и правила харнесса говорят против того, что лежит на диске.

.DESCRIPTION
  Проверяет офлайн, без сети и без запуска платформы:
    - число собранных скиллов (.cline\skills) против карты источников install-vendor-skills.ps1;
    - числа скиллов, названные в README.md, docs\*, AGENTS.md, START.md, SOURCES.md, .clinerules\*;
    - число скиллов по каждому вендору против таблицы docs\05-skills.md и комментариев в скрипте сборки;
    - состав файлов правил .clinerules\*.md: число и упоминание каждого файла в AGENTS.md и docs\01-architecture.md;
    - пути и имена файлов, названные в доках в обратных кавычках, - существуют ли они;
    - имена MCP-инструментов из .clinerules\10-mcp-and-skills.md - есть ли они в офлайн-описаниях серверов;
    - ревизии вендоров в skills-vendor против таблицы SOURCES.md (только предупреждение);
    - обязательные строки .gitignore;
    - сохранение анализа: скрипт scripts\new-analysis.ps1, требования правил (артефакт
      анализа в каталоге analysis, запрет коммита в задачах по базе, отправка правок
      в origin у задач по харнессу);
    - команду "измени переменную" (scripts\set-cline-mcp-path.ps1) и флаги чекеров:
      пробы живости у check-harness.ps1 только с ключом -Health, у start-harness.ps1 -
      выбор слоя ключом -Layer.

.NOTES
  Ничего не меняет. Код возврата 0 - расхождений нет, 1 - есть.
  Сверяется локальный факт с локальным утверждением; появление новых версий у вендоров
  не проверяется (это решение человека, а не расхождение).
  Ссылки в доках проверяются в два шага: точный путь от корня, затем имя файла в индексе
  файлов проекта. Поэтому переименование файла ловится, а перенос между каталогами - нет.
  Скиллы считаются по карте источников (как в scripts\install-vendor-skills.ps1, $sources),
  а не рекурсивным обходом SKILL.md: у части вендоров каталоги дублированы (.agents\skills
  и .claude\skills), рекурсивный счёт даёт завышенное число.
  Исключение из проверки чисел - .clinerules\40-lessons.md: это журнал прошлого состояния,
  он намеренно называет устаревшие числа. Отдельную строку в любом доке можно пометить
  пометкой check-docs:ignore - такая строка исключается из проверок чисел и ссылок.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-docs.ps1
#>
[CmdletBinding()]
param(
    [string] $Root
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent (Resolve-Path $PSCommandPath).Path }
    $Root = Split-Path -Parent $scriptDir
}

$script:problems = 0

function Ok   ($m) { Write-Host "  [ok]   $m" -ForegroundColor Green }
function Bad  ($m) { Write-Host "  [FAIL] $m" -ForegroundColor Red; $script:problems++ }
function Warn ($m) { Write-Host "  [warn] $m" -ForegroundColor Yellow }
function Info ($m) { Write-Host "  [info] $m" -ForegroundColor DarkGray }
function Head ($m) { Write-Host ''; Write-Host "== $m" -ForegroundColor Cyan }

function Rel ([string]$p) { return $p.Replace($Root + '\', '') }

Write-Host "Проверка доков: $Root"

# --- Карта источников (копия $sources из scripts\install-vendor-skills.ps1) -----
# Doc - сколько скиллов этого набора названо в docs\05-skills.md (независимая точка сверки).
$vendorSources = @(
    @{ Repo = 'cc-1c-skills';     Path = '.claude\skills'; Doc = 81 },
    @{ Repo = 'Vanessa_for_AI';   Path = '.claude\skills'; Doc = 2 },
    @{ Repo = 'va-ai-autotests';  Path = 'skill';          Doc = 1 },
    @{ Repo = '1c-mcp-toolkit';   Path = 'skills';         Doc = 2 },
    @{ Repo = 'product-analyst';  Path = '.';              Doc = 1 },
    @{ Repo = 'cursor-1c-skills'; Path = 'skills';         Doc = 120 }
)
$vendorDir = Join-Path $Root 'skills-vendor'

# Имена скиллов набора: сам путь, если в нём SKILL.md, плюс вложенные каталоги с SKILL.md.
function Get-SkillNames ([string]$base, [string]$rel) {
    $names = @()
    $p = Join-Path $base $rel
    if (-not (Test-Path $p)) { return $names }
    if (Test-Path (Join-Path $p 'SKILL.md')) { $names += (Split-Path -Leaf $p) }
    foreach ($d in (Get-ChildItem $p -Directory -ErrorAction SilentlyContinue)) {
        if (Test-Path (Join-Path $d.FullName 'SKILL.md')) { $names += $d.Name }
    }
    return $names
}

function Get-SkillCount ([hashtable]$src) {
    return @(Get-SkillNames $vendorDir (Join-Path $src.Repo $src.Path)).Count
}

# --- Что считается доками харнесса -------------------------------------------
$docFiles = @()
foreach ($n in @('README.md', 'AGENTS.md', 'START.md', 'SOURCES.md')) {
    $p = Join-Path $Root $n
    if (Test-Path $p) { $docFiles += $p }
}
$docsDir  = Join-Path $Root 'docs'
$rulesDir = Join-Path $Root '.clinerules'
$scriptsDir = Join-Path $Root 'scripts'
if (Test-Path $docsDir)  { $docFiles += @(Get-ChildItem $docsDir -Filter *.md -File | Select-Object -ExpandProperty FullName) }
if (Test-Path $rulesDir) { $docFiles += @(Get-ChildItem $rulesDir -Filter *.md -File | Select-Object -ExpandProperty FullName) }

# Числа о скиллах сверяются не только в доках, но и в комментариях скриптов.
$numberFiles = @($docFiles)
if (Test-Path $scriptsDir) { $numberFiles += @(Get-ChildItem $scriptsDir -Filter *.ps1 -File | Select-Object -ExpandProperty FullName) }

# --- 1. Число скиллов ---------------------------------------------------------
Head 'Число скиллов'
$allNames = @()
foreach ($src in $vendorSources) { $allNames += @(Get-SkillNames $vendorDir (Join-Path $src.Repo $src.Path)) }
$computed = @($allNames | Sort-Object -Unique).Count

$skillsDir = Join-Path $Root '.cline\skills'
$assembled = 0
if (Test-Path $skillsDir) {
    $assembled = @(Get-ChildItem $skillsDir -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
}
if ($assembled -eq 0) { Bad 'нет собранных скиллов: .cline\skills пуст - выполните scripts\install-vendor-skills.ps1' }
elseif ($assembled -eq $computed) { Ok "собрано $assembled скиллов - совпадает с картой источников" }
else { Bad "в .cline\skills $assembled скиллов, карта источников даёт $computed - пересоберите scripts\install-vendor-skills.ps1" }

# Разрешённые числа рядом со словом «скилл»: общее число и числа по вендорам.
$allowedNumbers = @($assembled)
foreach ($src in $vendorSources) { $allowedNumbers += (Get-SkillCount $src) }
$allowedNumbers = @($allowedNumbers | Sort-Object -Unique)

$numberRe = [regex]'(?<![0-9])(\d{3})(?![0-9])'
$checkedLines = 0
foreach ($f in $numberFiles) {
    if ((Split-Path -Leaf $f) -eq '40-lessons.md') { continue }
    $ln = 0
    foreach ($line in (Get-Content $f -Encoding UTF8)) {
        $ln++
        if ($line -notmatch '(?i)скилл' -and $line -notmatch '\.cline[\\/]skills') { continue }
        if ($line -match 'check-docs:ignore') { continue }
        $checkedLines++
        # Хеши коммитов (40 шестнадцатеричных знаков) содержат тройки цифр - это не числа.
        $scanLine = $line -replace '[0-9a-f]{40}', ''
        foreach ($m in $numberRe.Matches($scanLine)) {
            $num = [int]$m.Groups[1].Value
            if ($allowedNumbers -contains $num) { continue }
            Bad "$(Rel $f):$ln - сказано '$($m.Value)' рядом со словом 'скилл'; допустимые числа: $($allowedNumbers -join ', ')"
        }
    }
}
Info "строк со словом 'скилл' проверено: $checkedLines (40-lessons.md исключён как журнал прошлого)"

# --- 2. Числа по вендорам -----------------------------------------------------
Head 'Числа скиллов по вендорам (docs\05-skills.md)'
$skillsDoc = Join-Path $Root 'docs\05-skills.md'
if (-not (Test-Path $skillsDoc)) { Bad 'нет docs\05-skills.md - таблица источников не проверена' }
else {
    $ln = 0
    $seenRepos = @{}
    foreach ($line in (Get-Content $skillsDoc -Encoding UTF8)) {
        $ln++
        if ($line -notmatch '^\|\s*`([A-Za-z0-9_\-]+)`') { continue }
        $repo = $Matches[1]
        $src = $vendorSources | Where-Object { $_.Repo -eq $repo } | Select-Object -First 1
        if (-not $src) { continue }  # строка другой таблицы: это имя скилла, а не набор из карты
        $seenRepos[$repo] = $true
        $cells = @($line.Trim().Trim('|') -split '\|' | ForEach-Object { $_.Trim() })
        $fact = Get-SkillCount $src
        if ($cells.Count -lt 2 -or $cells[1] -notmatch '^\d+$') { Bad "docs\05-skills.md:$ln - у '$repo' не число в графе 'Скиллов'" ; continue }
        $num = [int]$cells[1]
        if ($num -eq $fact) { Ok "docs\05-skills.md:$ln - $repo = $num (совпадает)" }
        else { Bad "docs\05-skills.md:$ln - $repo названо $num, на диске $fact" }
    }
    foreach ($src in $vendorSources) {
        if (-not $seenRepos.ContainsKey($src.Repo)) { Bad "docs\05-skills.md - набора '$($src.Repo)' нет в таблице источников" }
    }
}

# --- 3. Файлы правил ----------------------------------------------------------
Head 'Файлы правил (.clinerules\*.md)'
$ruleFiles = @()
if (Test-Path $rulesDir) { $ruleFiles = @(Get-ChildItem $rulesDir -Filter *.md -File) }
if ($ruleFiles.Count -eq 0) { Bad 'каталог .clinerules пуст или отсутствует' }
else {
    Ok "файлов правил: $($ruleFiles.Count)"
    # Название каждого файла правил должно быть видно там, где перечисляются правила.
    $ruleHomes = @('AGENTS.md', 'docs\01-architecture.md')
    foreach ($rf in ($ruleFiles | Sort-Object Name)) {
        $missing = @()
        foreach ($h in $ruleHomes) {
            $hp = Join-Path $Root $h
            if (-not (Test-Path $hp)) { $missing += $h; continue }
            $text = Get-Content $hp -Raw -Encoding UTF8
            if ($text -notmatch [regex]::Escape($rf.Name)) { $missing += $h }
        }
        if ($missing.Count -eq 0) { Ok "$($rf.Name) назван в: $($ruleHomes -join ', ')" }
        else { Bad "$($rf.Name) не назван в: $($missing -join ', ')" }
    }
    # Словесное число рядом со словом «файл»/«правил»: «шесть коротких операционных файлов».
    $numberWords = @{ 'три' = 3; 'четыре' = 4; 'пять' = 5; 'шесть' = 6; 'семь' = 7 }
    $wordRe = [regex]'(?i)(три|четыре|пять|шесть|семь)\s+(-{1,2}\s*)?(коротких\s+)?(операционных\s+)?(файл|правил)'
    $wordHits = 0
    foreach ($f in $docFiles) {
        if ((Split-Path -Leaf $f) -eq '40-lessons.md') { continue }
        $ln = 0
        foreach ($line in (Get-Content $f -Encoding UTF8)) {
            $ln++
            if ($line -match 'check-docs:ignore') { continue }
            $m = $wordRe.Match($line)
            if (-not $m.Success) { continue }
            $wordHits++
            $n = $numberWords[$m.Groups[1].Value.ToLower()]
            if ($n -eq $ruleFiles.Count) { Ok "$(Rel $f):$ln - '$($m.Value.Trim())' совпадает ($n)" }
            else { Bad "$(Rel $f):$ln - сказано '$($m.Value.Trim())', фактически файлов правил $($ruleFiles.Count)" }
        }
    }
    if ($wordHits -eq 0) { Info 'словесных чисел о числе правил в доках не найдено' }
}

# --- 4. Пути и имена файлов, названные в доках --------------------------------
Head 'Пути и файлы, названные в доках'
$pathRe = [regex]'`([A-Za-zА-Яа-яЁё0-9_\-\\/\.]+\.(?:ps1|md|json|epf|feature|toml|hbk|txt|mdc|os))`'
# Файлы вне репозитория: справка установленной платформы и содержимое чужих архивов.
$externalLeaves = @('shcntx_ru.hbk', 'v8-project-guide.md', 'jsonparamsru.md', 'index.md', 'vbparams.json', 'run-behavior-check-session.os')
# Рантайм: появляется после установки, в git не хранится.
$runtimePrefixes = @('.cline\mcp', '.cline\skills', '.vanessa', '.code-index', 'dump', 'logs', 'cache', 'temp', 'analysis', 'skills-vendor', 'docs\jsonparams', 'queue', 'deploy\config.json')
# Имена, которые создаются рантаймом в любом месте (настройки обработки, метка версии,
# настройки внешней интеграции - по умолчанию их нет, они появляются при установке).
$runtimeLeaves = @('params.json', 'version.txt', 'config.json', 'answer.md', 'prompt.txt')
# Индекс имён файлов проекта: некоторые ссылки называют только имя файла.
# Тяжёлые каталоги отсекаются на уровне файловой системы. Get-ChildItem -Recurse по корню
# сначала полностью перечисляет их содержимое (в dump\ - свыше 127 тыс. файлов XML-выгрузки),
# и проверка уходит за минуты, хотя эти файлы всё равно отбрасываются. Обход - свой стек
# по EnumerateDirectories/EnumerateFiles с пропуском каталога целиком, не заходя в него.
$skipDirs = @('.git', 'dump', 'cache', 'logs', 'temp', 'analysis', '.code-index')
$nameIndex = @{}
$scanStack = New-Object System.Collections.Stack
$scanStack.Push($Root)
while ($scanStack.Count -gt 0) {
    $scanDir = $scanStack.Pop()
    foreach ($sub in [System.IO.Directory]::EnumerateDirectories($scanDir)) {
        if ($skipDirs -contains (Split-Path -Leaf $sub)) { continue }
        $scanStack.Push($sub)
    }
    foreach ($file in [System.IO.Directory]::EnumerateFiles($scanDir)) {
        $n = (Split-Path -Leaf $file).ToLower()
        if ($nameIndex.ContainsKey($n)) { $nameIndex[$n] = $nameIndex[$n] + 1 } else { $nameIndex[$n] = 1 }
    }
}
Info "файлов в индексе имён: $($nameIndex.Count) (ссылки ищутся по точному пути, затем по имени файла)"
$seen = @{}
$okPaths = 0; $runtimePaths = 0; $externalPaths = 0; $byNamePaths = 0; $missingPaths = @()
foreach ($f in $docFiles) {
    $ln = 0
    foreach ($line in (Get-Content $f -Encoding UTF8)) {
        $ln++
        if ($line -match 'check-docs:ignore') { continue }
        foreach ($m in $pathRe.Matches($line)) {
            $token = $m.Groups[1].Value
            if ($token -match '[\*<>]') { continue }
            $key = $token.ToLower().Replace('/', '\')
            if ($seen.ContainsKey($key)) { continue }
            $seen[$key] = $true
            $leaf = Split-Path -Leaf $key
            if ($externalLeaves -contains $leaf) { $externalPaths++; continue }
            $isRuntime = $false
            foreach ($rp in $runtimePrefixes) { if ($key.StartsWith($rp)) { $isRuntime = $true } }
            $found = Test-Path (Join-Path $Root $key)
            if (-not $found -and $nameIndex.ContainsKey($leaf)) { $found = $true; $byNamePaths++ }
            if ($found) { $okPaths++; continue }
            if ($isRuntime -or ($runtimeLeaves -contains $leaf)) { $runtimePaths++; continue }
            $missingPaths += "$(Rel $f):$ln - $token"
        }
    }
}
if ($missingPaths.Count -eq 0) { Ok "путей проверено: найдено $okPaths (в том числе по имени файла: $byNamePaths), рантайм $runtimePaths, вне репозитория $externalPaths" }
else { foreach ($mp in $missingPaths) { Bad "не найден файл, названный в доке: $mp" } }

# --- 5. Имена MCP-инструментов ------------------------------------------------
Head 'Имена MCP-инструментов (правила против офлайн-описаний серверов)'
$rulesMcp = Join-Path $Root '.clinerules\10-mcp-and-skills.md'
$nameSourceDirs = @((Join-Path $Root 'mcp'), (Join-Path $Root 'skills-vendor\1c-mcp-toolkit'))
if (-not (Test-Path $rulesMcp)) { Bad 'нет .clinerules\10-mcp-and-skills.md - карта инструментов не проверена' }
else {
    $known = @{}
    $srcCount = 0
    foreach ($d in $nameSourceDirs) {
        if (-not (Test-Path $d)) { continue }
        foreach ($mf in (Get-ChildItem $d -Recurse -File -Include *.md, *.json, *.toml -ErrorAction SilentlyContinue)) {
            $srcCount++
            $text = Get-Content $mf.FullName -Raw -Encoding UTF8
            foreach ($w in [regex]::Matches($text, '[A-Za-z_][A-Za-z0-9_]{2,}')) { $known[$w.Value.ToLower()] = $true }
        }
    }
    if ($srcCount -eq 0) { Warn 'нет офлайн-описаний (mcp\, skills-vendor\1c-mcp-toolkit) - имена инструментов не с чем сверить' }
    else { Info "офлайн-источников имён: $srcCount" }
    # Слова, которые не являются именами инструментов (служебные термины правил).
    $notTools = @('main', 'vanessa', 'globs', 'streamablehttp', 'repo', 'cline', 'config')
    $checkedNames = 0
    $ln = 0
    foreach ($line in (Get-Content $rulesMcp -Encoding UTF8)) {
        $ln++
        foreach ($m in [regex]::Matches($line, '`([a-z][a-z0-9_]{2,})`')) {
            $name = $m.Groups[1].Value
            if ($notTools -contains $name) { continue }
            $checkedNames++
            if (-not $known.ContainsKey($name)) { Bad "$(Rel $rulesMcp):$ln - инструмент '$name' не найден в офлайн-описаниях - проверьте, не выдуман ли он" }
        }
    }
    Info "имён инструментов проверено: $checkedNames"
}

# --- 6. Ревизии вендоров (SOURCES.md) -----------------------------------------
Head 'Ревизии вендоров (SOURCES.md против skills-vendor)'
$sourcesDoc = Join-Path $Root 'SOURCES.md'
$shaRows = 0
if (-not (Test-Path $sourcesDoc)) { Bad 'нет SOURCES.md - ревизии вендоров не проверены' }
else {
    foreach ($line in (Get-Content $sourcesDoc -Encoding UTF8)) {
        if ($line -notmatch 'https://github\.com/([^\s/\|]+/[^\s/\|]+)') { continue }
        $repoName = Split-Path -Leaf $Matches[1].Trim()
        if ($line -notmatch '`([0-9a-f]{40})`') { continue }
        $shaDoc = $Matches[1]
        $shaRows++
        $local = Join-Path $vendorDir $repoName
        $shaDocShort = $shaDoc.Substring(0, 8)
        if (-not (Test-Path $local)) { Info "$repoName - локально не развёрнут, ревизия не сверена" ; continue }
        if (-not (Test-Path (Join-Path $local '.git'))) { Warn "$repoName - локально без .git: сверить нельзя (в SOURCES.md $shaDocShort)" ; continue }
        $head = ((& git -C $local rev-parse HEAD 2>$null) | Out-String).Trim()
        $headShort = $head
        if ($head.Length -ge 8) { $headShort = $head.Substring(0, 8) }
        if ($head -eq $shaDoc) { Ok "${repoName}: $shaDocShort - совпадает с SOURCES.md" }
        else { Warn "${repoName}: в SOURCES.md $shaDocShort, локально $headShort - обновите таблицу или репозиторий" }
    }
    if ($shaRows -eq 0) { Bad 'в SOURCES.md не разобрано ни одной строки с коммитом' }
}

# --- 7. Обязательные записи .gitignore ----------------------------------------
Head 'Обязательные записи .gitignore'
$gitignore = Join-Path $Root '.gitignore'
if (-not (Test-Path $gitignore)) { Bad 'нет .gitignore' }
else {
    $gi = Get-Content $gitignore -Raw -Encoding UTF8
    $required = @('.vanessa/', 'skills-vendor/', '.cline/mcp/', '.cline/skills/', 'dump/', '*.epf', '.code-index/', 'temp/', 'analysis/', 'queue/', 'deploy/config.json', '__pycache__/')
    $missingRules = @()
    foreach ($r in $required) {
        if ($gi -notmatch ('(?m)^\s*' + [regex]::Escape($r) + '\s*$')) { $missingRules += $r }
    }
    if ($missingRules.Count -eq 0) { Ok "все обязательные записи на месте: $($required -join ', ')" }
    else { foreach ($r in $missingRules) { Bad "нет строки в .gitignore: $r" } }
}

# --- 8. Результат анализа и git-дисциплина ------------------------------------
Head 'Результат анализа и git (каталог analysis)'
$analysisScript = Join-Path $Root 'scripts\new-analysis.ps1'
if (Test-Path $analysisScript) { Ok 'скрипт scripts\new-analysis.ps1 на месте' }
else { Bad 'нет scripts\new-analysis.ps1 - результат анализа негде завести' }
$analysisDir = Join-Path $Root 'analysis'
if (Test-Path $analysisDir) {
    $aFiles = @(Get-ChildItem $analysisDir -Filter *.md -File -ErrorAction SilentlyContinue | Sort-Object Name)
    if ($aFiles.Count -gt 0) { Info "файлов анализа: $($aFiles.Count); последний: $($aFiles[-1].Name)" }
    else { Info 'каталог analysis есть, файлов анализа в нем нет' }
}
else { Info 'каталога analysis нет - его создаст scripts\new-analysis.ps1' }
# Требования правил: артефакт анализа, запрет коммита в задачах по базе, отправка правок.
$ruleChecks = @(
    @{ File = '.clinerules\00-contract.md'; Pattern = 'analysis\\';     Hint = 'правило: результат анализа идет в каталог analysis' },
    @{ File = '.clinerules\00-contract.md'; Pattern = 'Не коммитить';  Hint = 'правило: в задачах по базе коммитить нельзя' },
    @{ File = '.clinerules\50-harness.md';  Pattern = 'analysis\\';     Hint = 'правило: результат анализа идет в каталог analysis' },
    @{ File = '.clinerules\50-harness.md';  Pattern = 'git push';       Hint = 'правило: задача по харнессу заканчивается отправкой в origin' }
)
foreach ($rc in $ruleChecks) {
    $rcPath = Join-Path $Root $rc.File
    if (-not (Test-Path $rcPath)) { Bad "нет $(Rel $rcPath) - проверить нечего ($($rc.Hint))" ; continue }
    $rcText = Get-Content $rcPath -Raw -Encoding UTF8
    if ($rcText -match $rc.Pattern) { Ok "$(Rel $rcPath): $($rc.Hint)" }
    else { Bad "$(Rel $rcPath): нет - $($rc.Hint)" }
}

# --- 9. Команда "измени переменную" и флаги чекеров ---------------------------
Head 'Команда "измени переменную" и флаги чекеров'
$commandChecks = @(
    @{ File = 'scripts\set-cline-mcp-path.ps1'; Pattern = 'CLINE_MCP_SETTINGS_PATH';
       Hint = 'скрипт команды: наводит переменную Cline на текущий каталог' },
    @{ File = 'scripts\check-harness.ps1';     Pattern = '\[switch\]\s*\$Health';
       Hint = 'check-harness: пробы живости только с ключом -Health' },
    @{ File = 'scripts\start-harness.ps1';     Pattern = "ValidateSet\(\s*'All',\s*'Index',\s*'Toolkit'\s*\)";
       Hint = 'start-harness: подъем слоя ключом -Layer' },
    @{ File = '.clinerules\00-contract.md';    Pattern = 'измени переменную';
       Hint = 'правило: команда разобрана (короткий формат 1.3)' },
    @{ File = 'START.md';                      Pattern = 'измени переменную';
       Hint = 'START.md: команда названа в протоколе' },
    @{ File = 'README.md';                     Pattern = 'измени переменную';
       Hint = 'README.md: команда описана человеку' },
    @{ File = 'docs\06-troubleshooting.md';    Pattern = 'измени переменную';
       Hint = 'docs\06-troubleshooting.md: команда в лечении "Cline не видит MCP"' }
)
foreach ($cc in $commandChecks) {
    $ccPath = Join-Path $Root $cc.File
    if (-not (Test-Path $ccPath)) { Bad "нет $(Rel $ccPath) - проверить нечего ($($cc.Hint))" ; continue }
    $ccText = Get-Content $ccPath -Raw -Encoding UTF8
    if ($ccText -match $cc.Pattern) { Ok "$(Rel $ccPath): $($cc.Hint)" }
    else { Bad "$(Rel $ccPath): нет - $($cc.Hint)" }
}

Head 'Итог'
if ($script:problems -eq 0) {
    Write-Host 'Доки сходятся с фактом.' -ForegroundColor Green
    Write-Host 'Состояние установки (серверы, базы, прогон) проверяет scripts\check-harness.ps1.' -ForegroundColor DarkGray
    exit 0
}
Write-Host "Расхождений, требующих правки: $script:problems" -ForegroundColor Red
exit 1


