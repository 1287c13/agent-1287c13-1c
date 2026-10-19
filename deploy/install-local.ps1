param(
    [string]$Root = '',
    [switch]$NoShortcuts
)

$ErrorActionPreference = 'Stop'

if (-not $Root) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}
$Root = (Resolve-Path $Root).Path

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
    throw 'не найден py -3'
}

$required = @(
    'integration\passenger_wsgi.py', 'integration\task.py', 'integration\md_to_html.py',
    'integration\transport\__init__.py', 'integration\transport\wsgi.py',
    'integration\transport\api.py', 'integration\transport\store.py',
    'integration\transport\config.py', 'integration\transport\schema.py',
    'integration\transport\http_server.py',
    'integration\schemas\task_schema.json',
    'integration\web\index.html', 'integration\web\app.js', 'integration\web\style.css',
    'integration\watcher.py', 'integration\bridge.py', 'integration\agent.py',
    'integration\transport\client.py', 'integration\transport\cline.py'
)
$missing = @($required | Where-Object { -not (Test-Path (Join-Path $Root $_)) })
if ($missing.Count -gt 0) {
    throw "нет файлов интеграции: $($missing -join ', ')"
}

$configPath = Join-Path $Root 'deploy\config.json'
if (-not (Test-Path $configPath)) {
    Copy-Item (Join-Path $Root 'deploy\config.example.json') $configPath
    Write-Host "создан $configPath"
}

$config = $null
try { $config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { }
if ($config -and $config.server -and -not @($config.server.clients).Count) {
    Write-Warning 'в server.clients нет ни одного клиента: сервер ответит 503'
}
if ($config -and $config.server -and @($config.server.clients | Where-Object { $_.key -like 'change-me*' }).Count -gt 0) {
    Write-Warning 'замените ключи change-me... в deploy\config.json'
}

if (-not $NoShortcuts) {
    $shell = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath('Desktop')
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
