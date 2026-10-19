#Requires -Version 5.1
<#
.SYNOPSIS
  Диагностика харнесса: что установлено, что запущено, чего не хватает.

.DESCRIPTION
  Проверяет:
    - переменную CLINE_MCP_SETTINGS_PATH и наличие .cline\cline_mcp_settings.json;
    - артефакты MCP-серверов внутри проекта;
    - фон индексатора кода и доступность его MCP-сервера;
    - порт 6003 встроенного сервера 1C MCP Toolkit;
    - .v8-project.json и существование баз из него;
    - платформы 1С и наличие файлов справки shcntx_ru.hbk;
    - прогон Gherkin/Vanessa (по требованию задачи): обработка, сценарии, VAParams;
    - учётные данные баз (user/password) для подключения и прогона;
    - занятость клиентских сеансов 1С (лицензия на клиентов);
    - каталог результатов анализа (analysis) и последний разбор;
    - внешнюю интеграцию: файлы слоя, настройки, состояние очереди задач;
    - git: незакоммиченные изменения и неотправленные коммиты (origin);
    - развёрнутость вендорских репозиториев (skills-vendor).

.NOTES
  Ничего не меняет. Код возврата 0 - всё в порядке, 1 - есть замечания.
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
function Bad  ($m) { Write-Host "  [FAIL] $m" -ForegroundColor Red;    $script:problems++ }
function Warn ($m) { Write-Host "  [warn] $m" -ForegroundColor Yellow }
function Info ($m) { Write-Host "  [info] $m" -ForegroundColor DarkGray }
function Head ($m) { Write-Host ''; Write-Host "== $m" -ForegroundColor Cyan }

# Грубая проверка JS на обрыв: баланс скобок вне строк, комментариев и regex-литералов.
# Полный разбор не нужен: ловится потерянная "}" или незакрытая строка - файл внешне
# на месте, а страница не работает вовсе (SyntaxError в консоли браузера).
function Get-JsSourceProblem {
    param([string] $Text)
    $round = 0; $curly = 0; $square = 0
    $state = 'code'
    $prev = ''
    $line = 1
    $problem = ''
    $inClass = $false
    $i = 0
    while ($i -lt $Text.Length) {
        $ch = $Text[$i]
        $next = ''
        if ($i + 1 -lt $Text.Length) { $next = $Text[$i + 1] }
        if ($ch -eq "`n") {
            $line++
            if ($state -eq 'line') { $state = 'code' }
            $i++
            continue
        }
        if ($state -eq 'line') { $i++; continue }
        if ($state -eq 'block') {
            if ($ch -eq '*' -and $next -eq '/') { $state = 'code'; $i += 2; continue }
            $i++
            continue
        }
        if ($state -eq 'single' -or $state -eq 'double' -or $state -eq 'template') {
            if ($ch -eq '\') { $i += 2; continue }
            $quote = ''''
            if ($state -eq 'double') { $quote = '"' }
            if ($state -eq 'template') { $quote = '`' }
            if ($ch -eq $quote) { $state = 'code' }
            $i++
            continue
        }
        if ($state -eq 'regex') {
            if ($ch -eq '\') { $i += 2; continue }
            if ($ch -eq '[') { $inClass = $true }
            elseif ($ch -eq ']') { $inClass = $false }
            elseif ($ch -eq '/' -and -not $inClass) { $state = 'code'; $prev = '/' }
            $i++
            continue
        }
        if ($ch -eq '/' -and $next -eq '/') { $state = 'line'; $i += 2; continue }
        if ($ch -eq '/' -and $next -eq '*') { $state = 'block'; $i += 2; continue }
        if ($ch -eq "'") { $state = 'single'; $i++; continue }
        if ($ch -eq '"') { $state = 'double'; $i++; continue }
        if ($ch -eq '`') { $state = 'template'; $i++; continue }
        if ($ch -eq '/' -and ($prev -eq '' -or '=(:,[!&|?{};+-*%^~<>'.IndexOf($prev) -ge 0)) {
            $state = 'regex'; $inClass = $false; $i++
            continue
        }
        if ($ch -eq '{') { $curly++ }
        elseif ($ch -eq '}') { $curly--; if ($curly -lt 0 -and -not $problem) { $problem = "лишняя } на строке $line" } }
        elseif ($ch -eq '(') { $round++ }
        elseif ($ch -eq ')') { $round--; if ($round -lt 0 -and -not $problem) { $problem = "лишняя ) на строке $line" } }
        elseif ($ch -eq '[') { $square++ }
        elseif ($ch -eq ']') { $square--; if ($square -lt 0 -and -not $problem) { $problem = "лишняя ] на строке $line" } }
        if (-not [string]::IsNullOrWhiteSpace([string]$ch)) { $prev = [string]$ch }
        $i++
    }
    if (-not $problem -and $state -ne 'code') { $problem = 'файл обрывается внутри строки или комментария' }
    if (-not $problem -and ($curly -ne 0 -or $round -ne 0 -or $square -ne 0)) {
        $problem = "не сходятся скобки: { = $curly, ( = $round, [ = $square"
    }
    return $problem
}


Write-Host "Харнесс: $Root"

# --- 1. Файл настроек MCP ---------------------------------------------------
Head 'Конфигурация MCP'
$settings = Join-Path $Root '.cline\cline_mcp_settings.json'
if (Test-Path $settings) { Ok "конфиг на месте: $settings" } else { Bad "нет $settings" }

$envPath = [Environment]::GetEnvironmentVariable('CLINE_MCP_SETTINGS_PATH', 'User')
if ($envPath -eq $settings) {
    Ok 'CLINE_MCP_SETTINGS_PATH указывает на проект'
}
elseif ([string]::IsNullOrWhiteSpace($envPath)) {
    Bad 'CLINE_MCP_SETTINGS_PATH не задана - выполните scripts\enable-mcp.ps1'
}
else {
    Bad "CLINE_MCP_SETTINGS_PATH указывает в другое место: $envPath"
}

# --- 2. Артефакты серверов --------------------------------------------------
Head 'Артефакты MCP-серверов (внутри проекта)'
$checks = @(
    @{ Name = '1c-code-index / bsl-indexer.exe'; Path = '.cline\mcp\code-index-mcp\bsl-indexer.exe' },
    @{ Name = '1c-toolkit / MCP_Toolkit.epf';    Path = '.cline\mcp\1c-mcp-toolkit\MCP_Toolkit.epf' },
    @{ Name = '1c-platform-help / mcp-bsl-context.exe'; Path = '.cline\mcp\bsl-platform-help-context\.venv\Scripts\mcp-bsl-context.exe' }
)
foreach ($c in $checks) {
    if (Test-Path (Join-Path $Root $c.Path)) { Ok $c.Name } else { Bad "$($c.Name) - нет файла $($c.Path)" }
}

# --- 3. Индексатор кода -----------------------------------------------------
Head 'Индексатор кода (1c-code-index)'
$indexer = Join-Path $Root '.cline\mcp\code-index-mcp\bsl-indexer.exe'
$indexHome = Join-Path $Root '.cline\mcp\code-index-mcp\home'
if (Test-Path $indexer) {
    $env:CODE_INDEX_HOME = $indexHome
    $st = & $indexer daemon status 2>&1 | Out-String
    if ($st -match 'ready|индекс|daemon|ok|running|файл') { Ok 'индексатор отвечает' } else { Warn 'индексатор не отвечает - запустите scripts\start-harness.ps1' }
    if (Test-Path (Join-Path $indexHome 'daemon.toml')) { Ok 'daemon.toml на месте' } else { Bad 'нет daemon.toml - выполните enable-mcp.ps1' }
    if (Test-Path (Join-Path $Root '.code-index\index.db')) { Ok 'индекс построен (.code-index\index.db)' } else { Warn 'индекс ещё не построен (идёт первичная индексация?)' }

    # Репозитории индекса: список - из daemon.toml, состояния - из /health демона (8015).
    # Это дешёвая замена MCP-вызову get_stats: около 0,05 с против ~9 с на репозиторий.
    # Ради этой строки агент больше не вызывает get_stats ради «какие репо есть».
    $daemonCfg = Join-Path $indexHome 'daemon.toml'
    if (Test-Path $daemonCfg) {
        $aliases = @(Select-String -Path $daemonCfg -Pattern '^\s*alias\s*=\s*"([^"]+)"' -Encoding UTF8 | ForEach-Object { $_.Matches[0].Groups[1].Value })
        if ($aliases.Count -gt 0) { Info ('репозитории индекса (daemon.toml): ' + ($aliases -join ', ')) }
        else { Warn 'в daemon.toml не разобрано ни одной секции [[paths]] с alias' }
    }
    try {
        $hRaw = Invoke-WebRequest -Uri 'http://127.0.0.1:8015/health' -UseBasicParsing -TimeoutSec 5
        $hText = [System.Text.Encoding]::UTF8.GetString($hRaw.RawContentStream.ToArray())
        $h = $hText | ConvertFrom-Json
        $states = @($h.paths | ForEach-Object { (Split-Path -Leaf $_.path) + ' = ' + $_.status })
        Ok ('демон индекса: ' + ($states -join '; '))
        $notReady = @($h.paths | Where-Object { $_.status -ne 'ready' })
        if ($notReady.Count -gt 0) { Info 'путь не в ready - идёт индексация: инструменты по нему недоступны, надо ждать' }
    }
    catch { Warn 'демон индекса (8015) не отвечает - запустите scripts\start-harness.ps1' }
}
else {
    Bad 'индексатор не установлен - выполните scripts\install-mcp.ps1'
}

# --- 4. Встроенный сервер 1C MCP Toolkit ------------------------------------
Head 'Живая база (1c-toolkit, порт 6003)'
try {
    $r = Invoke-WebRequest 'http://127.0.0.1:6003/health' -UseBasicParsing -TimeoutSec 5
    Ok "сервер отвечает ($($r.StatusCode))"
}
catch {
    # Сеанс уже запущен, но сервер ещё не ответил: это не повод поднимать второй сеанс
    # (лицензия на клиентов базы ограничена, порт 6003 занят).
    $tk = @(Get-CimInstance Win32_Process -Filter "Name='1cv8.exe' or Name='1cv8c.exe' or Name='1cv8s.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and ($_.CommandLine -like '*MCP_Toolkit*') })
    if ($tk.Count -gt 0) {
        $tkPids = ($tk | ForEach-Object { [string] $_.ProcessId }) -join ', '
        Warn "порт 6003 не отвечает, но сеанс toolkit уже запущен (PID $tkPids) - второй сеанс не поднимать: scripts\start-toolkit.ps1 ждёт готовности этого"
    }
    else { Warn 'порт 6003 не отвечает - поднимите сервер: scripts\start-toolkit.ps1 (или scripts\start-harness.ps1)' }
}

# --- 5. Проект 1С -----------------------------------------------------------
Head 'Проект 1С (.v8-project.json)'
$v8proj = Join-Path $Root '.v8-project.json'
if (Test-Path $v8proj) {
    Ok '.v8-project.json на месте'
    $cfg = Get-Content $v8proj -Raw -Encoding UTF8 | ConvertFrom-Json
    Write-Host "     v8path: $($cfg.v8path)"
    if (Test-Path $cfg.v8path) { Ok 'каталог платформы существует' } else { Bad "нет каталога платформы: $($cfg.v8path)" }
    if (Test-Path (Join-Path $cfg.v8path 'shcntx_ru.hbk')) { Ok 'shcntx_ru.hbk есть (справка платформы доступна)' } else { Warn 'нет shcntx_ru.hbk в v8path - сервер справки может не найти данные' }
    foreach ($db in $cfg.databases) {
        if ($db.type -eq 'file') {
            if (Test-Path $db.path) { Ok "база $($db.id): $($db.path)" } else { Warn "база $($db.id): путь не найден - $($db.path)" }
        }
        else { Ok "база $($db.id): серверная ($($db.server)\$($db.ref))" }
    }
}
else { Bad 'нет .v8-project.json в корне проекта' }

# --- 6. Скиллы --------------------------------------------------------------
Head 'Скиллы (.cline\skills)'
$skillsDir = Join-Path $Root '.cline\skills'
if (Test-Path $skillsDir) {
    $n = (Get-ChildItem $skillsDir -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
    if ($n -gt 0) { Ok "$n скиллов с SKILL.md" } else { Bad 'скиллы не собраны - выполните scripts\install-vendor-skills.ps1' }
}
else { Bad 'нет каталога .cline\skills - выполните scripts\install-vendor-skills.ps1' }

# --- 7. Прогон Gherkin/Vanessa (по требованию задачи) ------------------------
Head 'Прогон Gherkin/Vanessa (запускается только по требованию задачи)'
$epf = Join-Path $Root '.vanessa\vanessa-automation-single.epf'
if (Test-Path $epf) { Ok 'внешняя обработка развёрнута (.vanessa\vanessa-automation-single.epf)' }
else { Info 'нет .vanessa\vanessa-automation-single.epf - его развернёт сам scripts\vanessa-run.ps1' }
Info 'сеанс toolkit под прогон освобождает и возвращает сам: scripts\vanessa-run.ps1 -FreeToolkit'
$featuresLegacy = Join-Path $Root 'features'
if (Test-Path $featuresLegacy) {
    Warn 'каталог features\ в корне: сценарии .feature - временный артефакт задачи, их место temp\features\ (каталог удалить, .gitignore его закрывает)'
}
$featuresDir = Join-Path $Root 'temp\features'
if (Test-Path $featuresDir) {
    $fFiles = @(Get-ChildItem $featuresDir -Recurse -Filter *.feature -File -ErrorAction SilentlyContinue)
    if ($fFiles.Count -gt 0) {
        $oldest = $fFiles | Sort-Object LastWriteTime | Select-Object -First 1
        Info "сценариев .feature в temp\features: $($fFiles.Count); самый старый - $($oldest.LastWriteTime.ToString('dd.MM.yyyy')); за собой их убирают (temp\ - не склад)"
    }
    else { Info 'каталог temp\features\ есть, .feature в нём нет' }
}
else { Info 'нет temp\features\ - сюда создаётся сценарий под задачу (дефолт scripts\vanessa-run.ps1)' }
if (Test-Path (Join-Path $Root '.vanessa\VAParams.json')) { Ok 'VAParams.json собран (остался от прошлого прогона)' }
else { Info 'VAParams.json ещё не собран - его готовит scripts\vanessa-run.ps1 перед прогоном' }

# --- 8. Учётные данные баз ---------------------------------------------------
Head 'Учётные данные баз (для подключения и прогона)'
if (Test-Path $v8proj) {
    $cfgU = Get-Content $v8proj -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($db in $cfgU.databases) {
        $hasUser = -not [string]::IsNullOrWhiteSpace($db.user)
        $hasPass = $db.PSObject.Properties.Name -contains 'password'
        if (-not $hasUser) {
            Warn "база $($db.id): нет поля user - без /N платформа ответит 'Пользователь ИБ не идентифицирован'"
        }
        elseif ($hasPass) {
            Ok "база $($db.id): user='$($db.user)', поле password задано (пустое - нормально)"
        }
        else {
            Warn "база $($db.id): user='$($db.user)', поля password нет - добавьте его, даже пустым"
        }
    }
}
else { Warn '.v8-project.json не найден - проверка учётных данных баз пропущена' }

# --- 9. Клиентские сеансы 1С -------------------------------------------------
Head 'Клиентские сеансы 1С (лицензия на клиентов)'
$procs = @(Get-Process -Name '1cv8', '1cv8c', '1cv8s' -ErrorAction SilentlyContinue)
if ($procs.Count -eq 0) { Ok 'процессов 1С не запущено - базы свободны для прогона' }
else { Warn "процессов 1С: $($procs.Count) - прогону Vanessa нужны ДВА клиента одной базы; закройте чужие сеансы, включая 1C MCP Toolkit (порт 6003)" }

# --- 10. Временные файлы задачи ----------------------------------------------
Head 'Временные файлы (temp)'
$tempDir = Join-Path $Root 'temp'
if (Test-Path $tempDir) { Ok 'каталог temp на месте - единственное место временных файлов задачи' }
else { Warn 'нет каталога temp - создайте его: временные файлы задачи (разовые скрипты, логи, черновики) хранятся только здесь' }
if (Test-Path (Join-Path $Root '.tmp')) { Warn 'остался старый каталог .tmp - временные файлы должны лежать в temp\, каталог .tmp удалите' }

# --- 11. Результаты анализа --------------------------------------------------
Head 'Результаты анализа (analysis)'
$analysisDir = Join-Path $Root 'analysis'
if (Test-Path $analysisDir) {
    $aFiles = @(Get-ChildItem $analysisDir -Filter *.md -File -ErrorAction SilentlyContinue | Sort-Object Name)
    if ($aFiles.Count -gt 0) { Ok "файлов анализа: $($aFiles.Count); последний: $($aFiles[-1].Name)" }
    else { Info 'каталог analysis есть, файлов анализа в нем нет - разборов еще не сохраняли' }
}
else { Info 'каталога analysis нет - его создаст scripts\new-analysis.ps1 при первом разборе' }
if (Test-Path (Join-Path $Root 'scripts\new-analysis.ps1')) { Ok 'скрипт scripts\new-analysis.ps1 на месте' }
else { Warn 'нет scripts\new-analysis.ps1 - результат анализа негде завести' }

# --- 12. Git: изменения и отправка -------------------------------------------
Head 'Git (изменения и отправка в origin)'
if (Test-Path (Join-Path $Root '.git')) {
    $branch = ((& git -C $Root rev-parse --abbrev-ref HEAD 2>$null) | Out-String).Trim()
    $head = ((& git -C $Root rev-parse --short HEAD 2>$null) | Out-String).Trim()
    if ($branch) { Info "ветка: $branch, HEAD: $head" }
    $dirty = @(& git -C $Root status --porcelain 2>$null)
    if ($dirty.Count -gt 0) {
        Warn "незакоммиченных изменений: $($dirty.Count) - задача по харнессу заканчивается коммитом и отправкой"
    }
    else { Ok 'рабочее дерево чистое' }
    $sb = ((& git -C $Root status -sb 2>$null) | Out-String)
    if ($sb -match 'ahead (\d+)') {
        Warn "не отправлено коммитов: $($Matches[1]) - выполните git push --quiet origin main и сверьте git ls-remote origin refs/heads/main с git rev-parse HEAD"
    }
    else { Info 'неотправленных коммитов нет' }
}
else { Warn 'каталога .git нет - состояние синхронизации с GitHub не проверить' }

# --- 13. Вендорские репозитории ---------------------------------------------
Head 'Вендорские репозитории (skills-vendor)'
$vendorDir = Join-Path $Root 'skills-vendor'
$vendorRepos = @('cc-1c-skills', 'cursor-1c-skills', 'mcp-bsl-platform-help-context', 'Vanessa_for_AI', 'va-ai-autotests', 'product-analyst', '1c-mcp-toolkit')
if (Test-Path $vendorDir) {
    foreach ($v in $vendorRepos) {
        $vp = Join-Path $vendorDir $v
        if (-not (Test-Path $vp)) { Warn "$v - каталога нет (разверните scripts\install-vendor-repos.ps1)" }
        elseif (Test-Path (Join-Path $vp '.git')) { Ok "$v развёрнут (ревизию сверяет scripts\check-docs.ps1)" }
        else { Warn "$v - каталог без .git: ревизию сверить нельзя, обновить скриптом тоже" }
    }
}
else { Bad 'нет каталога skills-vendor - выполните scripts\install-vendor-repos.ps1' }

# --- 14. Внешняя интеграция (очередь задач) -----------------------------------
Head 'Внешняя интеграция (очередь задач)'
$layerFiles = @('integration\agent.py', 'integration\watcher.py', 'integration\bridge.py',
    'integration\passenger_wsgi.py', 'integration\task.py', 'integration\md_to_html.py',
    'integration\transport\__init__.py', 'integration\transport\store.py',
    'integration\transport\api.py', 'integration\transport\config.py',
    'integration\transport\schema.py', 'integration\transport\cline.py',
    'integration\transport\client.py', 'integration\transport\wsgi.py',
    'integration\transport\http_server.py',
    'integration\schemas\task_schema.json',
    'integration\web\index.html', 'integration\web\app.js', 'integration\web\style.css',
    'deploy\install-local.ps1', 'deploy\config.example.json',
    'scripts\start-watcher.ps1', 'scripts\stop-watcher.ps1')
$layerMissing = @($layerFiles | Where-Object { -not (Test-Path (Join-Path $Root $_)) })
if ($layerMissing.Count -eq 0) { Ok 'файлы слоя на месте (сервер, страница задач, агент, watcher, установка)' }
else { Bad "нет файлов внешней интеграции: $($layerMissing -join ', ')" }

$pageScript = Join-Path $Root 'integration\web\app.js'
if (Test-Path $pageScript) {
    $jsProblem = Get-JsSourceProblem (Get-Content $pageScript -Raw -Encoding UTF8)
    if ($jsProblem) { Bad "страница задач не разберётся браузером: app.js - $jsProblem" }
    else { Ok 'страница задач: скобки и строки app.js сходятся' }
}

$deployConfig = Join-Path $Root 'deploy\config.json'
$serverRoot = ''
if (Test-Path $deployConfig) {
    Ok 'настройки интеграции созданы: deploy\config.json (правьте копию, в git она не уходит)'
    try {
        $integrationConfig = Get-Content $deployConfig -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($integrationConfig.server -and $integrationConfig.server.root) {
            $serverRoot = [string]$integrationConfig.server.root
        }
        if ($integrationConfig.server -and -not @($integrationConfig.server.clients).Count) {
            Warn 'в server.clients нет ни одного ключа: сервер ответит 503 (deploy\config.json)'
        }
        if ($integrationConfig.server -and @($integrationConfig.server.clients |
                Where-Object { [string]$_.key -like 'change-me*' }).Count -gt 0) {
            Warn 'ключи из образца (change-me...) не заменены: так публиковать нельзя'
        }
    } catch { Warn "deploy\config.json не разобран: $deployConfig" }
}
else { Info 'настроек интеграции нет: deploy\config.json создает deploy\install-local.ps1 (слой необязательный)' }

if ($serverRoot) {
    if ([System.IO.Path]::IsPathRooted($serverRoot)) { $queueDir = $serverRoot }
    else { $queueDir = Join-Path $Root $serverRoot }
    if (-not (Test-Path $queueDir)) {
        Info "каталога очереди нет: $queueDir (создаст сервер при первом запросе)"
    }
    else {
        $queueCounts = @{}
        foreach ($sub in @('inbox', 'processing', 'outbox', 'failed', 'agents')) {
            $folder = Join-Path $queueDir $sub
            $queueCounts[$sub] = 0
            if (Test-Path $folder) {
                $queueCounts[$sub] = @(Get-ChildItem $folder -File -Filter *.json -ErrorAction SilentlyContinue).Count
            }
        }
        Ok ("очередь ${queueDir}: ждут $($queueCounts['inbox']), в работе $($queueCounts['processing']), " +
            "итогов $($queueCounts['outbox']), сбоев $($queueCounts['failed']), агентов $($queueCounts['agents'])")
    }
    $legacyJournal = Join-Path $Root 'queue\tasks.jsonl'
    if (Test-Path $legacyJournal) {
        Warn 'остался журнал прежней схемы queue\tasks.jsonl: он больше не читается (задачи переносятся вручную)'
    }
}

$watcherPidFile = Join-Path $Root 'temp\queue\watcher.pid'
if (Test-Path $watcherPidFile) {
    try {
        $watcherPid = (Get-Content $watcherPidFile -Raw -Encoding UTF8 | ConvertFrom-Json).pid
        if ($watcherPid -and (Get-Process -Id $watcherPid -ErrorAction SilentlyContinue)) {
            Ok "watcher поднят фоном: pid $watcherPid (стоп - scripts\stop-watcher.ps1)"
        } else { Info "pid-файл остался от остановленного watcher-а: $watcherPidFile" }
    } catch { Warn "pid-файл watcher-а не читается: $watcherPidFile" }
}
else { Info 'watcher не поднят фоном: задачи берёт только запущенный вручную процесс' }

$watcherLock = Join-Path $Root 'temp\queue\.watcher.lock'
if (Test-Path $watcherLock) {
    $lockAge = [math]::Round(((Get-Date) - (Get-Item $watcherLock).LastWriteTime).TotalSeconds, 0)
    if ($lockAge -le 60) { Ok "watcher очереди: последний проход ${lockAge} с назад" }
    else { Warn "замок watcher-а не обновлялся ${lockAge} с: процесс, вероятно, не работает" }
}
else { Info 'отметки проходов watcher-а нет: он ещё не запускался' }

if (Test-Path (Join-Path $Root '.git')) {
    & git -C $Root check-ignore -q -- 'queue' 2>$null
    if ($LASTEXITCODE -eq 0) { Ok 'каталог queue закрыт .gitignore (состояние обмена в git не хранится)' }
    else { Warn 'queue не в .gitignore: состояние очереди может попасть в коммит' }
}


# --- 15. Промпт-бюджет (всегда-инжектируемый префикс) -------------------------
# Файлы .clinerules\, AGENTS.md и метаданные скиллов уходят в каждый запрос целиком.
# Бюджет и разбор по файлам - в scripts\check-context.ps1 (там же ключ -Mcp).
Head 'Промпт-бюджет (что уходит в каждый запрос)'
$ctxScript = Join-Path $Root 'scripts\check-context.ps1'
if (Test-Path $ctxScript) {
    $ctxOut  = & powershell -NoProfile -ExecutionPolicy Bypass -File $ctxScript -Quiet -Root $Root 2>&1 | Out-String
    $ctxCode = $LASTEXITCODE
    if ($ctxCode -eq 0) { Ok $ctxOut.Trim() }
    else {
        foreach ($ln in ($ctxOut -split "`r?`n" | Where-Object { $_.Trim() -ne '' })) { Bad $ln.Trim() }
    }
    Info 'подробно (по файлам и бюджетам): powershell -File scripts\check-context.ps1'
}
else { Bad 'нет scripts\check-context.ps1 - бюджет префикса не проверяется' }

Head 'Итог'
if ($script:problems -eq 0) { Write-Host 'Проблем не найдено.' -ForegroundColor Green; exit 0 }
Write-Host "Замечаний, требующих действия: $script:problems" -ForegroundColor Red
exit 1
