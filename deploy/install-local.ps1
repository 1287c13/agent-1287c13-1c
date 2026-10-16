<#
.SYNOPSIS
    Локальная установка внешней интеграции: проверка окружения, каталог очереди, ярлыки.

.DESCRIPTION
    Скрипт ничего не публикует и не меняет правила харнесса. Он проверяет, что на машине
    есть python и tkinter, создаёт каталоги очереди (queue\ в корне харнесса), кладёт
    deploy\config.json из примера и по ключу -Shortcuts делает ярлыки на рабочем столе
    для окна задач и watcher-а.

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

$tk = & py -3 -c "import tkinter; print('tkinter', tkinter.TkVersion)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warning 'tkinter недоступен: окно задач (deploy\run-gui.bat) работать не будет, очередь и HTTP - будут'
} else {
    Write-Host "$tk: ok"
}

# Каталоги очереди создаёт сам агент: QueueStore.ensure() при первом обращении.
& py -3 (Join-Path $Root 'integration\agent.py') --root $Root --list | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw 'не удалось создать каталог очереди - см. вывод integration\agent.py --list'
}
Write-Host 'очередь: каталоги готовы'

$configPath = Join-Path $Root 'deploy\config.json'
if (-not (Test-Path $configPath)) {
    Copy-Item (Join-Path $Root 'deploy\config.example.json') $configPath
    Write-Host "создан $configPath (правьте копию: в git она не уходит)"
} else {
    Write-Host "config.json уже есть: $configPath"
}

if (-not $NoShortcuts) {
    $shell = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath('Desktop')
    $targets = @(
        @{ Name = 'Агент 1С - окно задач'; File = 'run-gui.bat' },
        @{ Name = 'Агент 1С - watcher очереди'; File = 'run-watcher.bat' }
    )
    foreach ($item in $targets) {
        $link = $shell.CreateShortcut((Join-Path $desktop ($item.Name + '.lnk')))
        $link.TargetPath = (Join-Path $Root ('deploy\' + $item.File))
        $link.WorkingDirectory = $Root
        $link.Save()
        Write-Host "ярлык: $($item.Name)"
    }
}

Write-Host ''
Write-Host 'Дальше:'
Write-Host '  1) deploy\run-watcher.bat - оставить окно открытым (разбор очереди и передача задач)'
Write-Host '  2) deploy\run-gui.bat - поставить задачу и прочитать результат'
Write-Host '  3) интеграция из 1С: POST /api/task или строка в queue\tasks.jsonl - docs\07-external-integration.md'
