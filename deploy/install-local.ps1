<#
.SYNOPSIS
    Локальная установка внешней интеграции: проверка окружения, настройки, ярлык watcher-а.

.DESCRIPTION
    Скрипт ничего не публикует и не меняет правила харнесса. Он проверяет, что на машине
    есть python 3 и файлы сервера (страница задач, точка входа Passenger), кладёт
    deploy\config.json из образца и по ключу -Shortcuts делает ярлык на рабочем столе
    для watcher-а очереди.

    Каталог очереди создаётся самим сервером (QueueStore.ensure) при первом запросе -
    заранее его заводить не нужно: очередь живёт там, где указано server.root.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File deploy\install-local.ps1
    powershell -ExecutionPolicy Bypass -File deploy\install-local.ps1 -NoShortcuts
#>
param(
    [string]$Root = '',
    [switch]$NoShortcuts
)

$ErrorActionPreference = 'Stop'

if (-not $Root) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}
$Root = (Resolve-Path $Root).Path
Write-Host "корень харнесса: $Root"

function Test-Python {
    param([string]$Command = 'py', [string[]]$Args = @('-3'))
    try {
        $out = & $Command @Args --version 2>&1
        return ($LASTEXITCODE -eq 0) -and $out
    } catch {
        return $false
    }
}

if (-not (Test-Python)) {
    throw 'не найден py -3: внешняя интеграция запускается интерпретатором Python 3'
}
Write-Host 'python: ok'

$required = @(
    'integration\agent.py', 'integration\watcher.py', 'integration\bridge.py',
    'integration\passenger_wsgi.py', 'integration\transport\api.py',
    'integration\transport\wsgi.py', 'integration\transport\store.py',
    'integration\transport\config.py', 'integration\transport\client.py',
    'integration\web\index.html', 'integration\web\app.js', 'integration\web\style.css'
)
$missing = @($required | Where-Object { -not (Test-Path (Join-Path $Root $_)) })
if ($missing.Count -gt 0) {
    throw "нет файлов интеграции: $($missing -join ', ')"
}
Write-Host 'файлы интеграции: ok'

$configPath = Join-Path $Root 'deploy\config.json'
if (-not (Test-Path $configPath)) {
    Copy-Item (Join-Path $Root 'deploy\config.example.json') $configPath
    Write-Host "создан $configPath (правьте копию: в git она не уходит)"
} else {
    Write-Host "config.json уже есть: $configPath"
}

$config = $null
try { $config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { }
if ($config -and $config.server -and -not @($config.server.clients).Count) {
    Write-Warning 'в server.clients нет ни одного клиента: сервер ответит 503, пока ключи не заданы'
}
if ($config -and $config.server -and @($config.server.clients | Where-Object { $_.key -like 'change-me*' }).Count -gt 0) {
    Write-Warning 'ключи из образца (change-me...) не годятся для публикации: замените их в deploy\config.json'
}
if ($config -and $config.server -and $config.server.root) {
    Write-Host "каталог очереди: $(Join-Path $Root $config.server.root)"
}

if (-not $NoShortcuts) {
    $shell = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath('Desktop')
    # Ярлык ведёт на скрипт, а не на .bat: скрипт поднимает watcher фоном (окно
    # консоли не нужно) и сам проверяет, что процесс взял замок.
    $targets = @(
        @{ Name = 'Агент 1С - watcher очереди'; Target = 'powershell.exe'
           Args = '-NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $Root 'scripts\start-watcher.ps1') + '"' }
    )
    foreach ($item in $targets) {
        $link = $shell.CreateShortcut((Join-Path $desktop ($item.Name + '.lnk')))
        $link.TargetPath = $item.Target
        $link.Arguments = $item.Args
        $link.WorkingDirectory = $Root
        $link.Save()
        Write-Host "ярлык: $($item.Name)"
    }
}

Write-Host ''
Write-Host 'Дальше:'
Write-Host '  1) deploy\run-server.bat - локальный сервер очереди (на хостинге его заменяет Passenger:'
Write-Host '     корень приложения integration\, точка входа integration\passenger_wsgi.py)'
Write-Host '  2) scripts\start-watcher.ps1 - поднять watcher очереди фоном (живёт до scripts\stop-watcher.ps1)'
Write-Host '  3) страница задач: адрес сервера, вход по ключу клиента, задача и её стадии'
Write-Host '  4) интеграция из 1С: POST /api/task - docs\07-external-integration.md'
