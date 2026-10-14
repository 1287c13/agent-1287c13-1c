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
    Warn 'порт 6003 не отвечает - поднимите сервер: scripts\start-toolkit.ps1 (или scripts\start-harness.ps1)'
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
$featuresDir = Join-Path $Root 'features'
if (Test-Path $featuresDir) {
    $fCount = @(Get-ChildItem $featuresDir -Recurse -Filter *.feature -File -ErrorAction SilentlyContinue).Count
    if ($fCount -gt 0) { Ok "$fCount сценариев .feature в features\" }
    else { Info 'каталог features\ есть, но .feature в нём нет' }
}
else { Info 'нет каталога features\ - сюда кладутся сценарии для scripts\vanessa-run.ps1' }
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

# --- 10. Вендорские репозитории ---------------------------------------------
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

Head 'Итог'
if ($script:problems -eq 0) { Write-Host 'Проблем не найдено.' -ForegroundColor Green; exit 0 }
Write-Host "Замечаний, требующих действия: $script:problems" -ForegroundColor Red
exit 1
