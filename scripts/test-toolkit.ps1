#Самопроверка живого слоя 1c-toolkit: health, канал /mcp, REST-зеркало, право записи.
#
#Зачем: после подъема слоя нужно доказать, что он не просто "порт отвечает", а выполняет
#запросы и код. Проверка идет по двум каналам (MCP /mcp и REST /api) и, если не указан
#-SkipWrite, включает одну запись в журнал регистрации - она подтверждает, что сеанс
#поднят с -AllowWrite (без флага execute_code отказывает: "Операция запрещена").
#
#Пример:
#    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-toolkit.ps1
#    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-toolkit.ps1 -SkipWrite
#
#Код возврата: 0 - все шаги прошли, 1 - хотя бы один шаг провален.

[CmdletBinding()]
param(
    [int]$Port = 6003,
    [switch]$SkipWrite,
    [int]$TimeoutSec = 180
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Net.Http
$base = "http://127.0.0.1:$Port"
$script:failed = 0
$script:eventName = 'Харнесс.ПробаКанала'

function Write-Step {
    param([bool]$Ok, [string]$Name, [string]$Detail)
    if ($Ok) {
        Write-Host ("[ok]   {0}: {1}" -f $Name, $Detail)
    } else {
        Write-Host ("[FAIL] {0}: {1}" -f $Name, $Detail) -ForegroundColor Red
        $script:failed++
    }
}

$http = New-Object System.Net.Http.HttpClient
$http.Timeout = [TimeSpan]::FromSeconds($TimeoutSec)

function Send-Http {
    param([string]$Method, [string]$Uri, [string]$Json, [hashtable]$Headers = @{})

    $request = New-Object System.Net.Http.HttpRequestMessage([System.Net.Http.HttpMethod]::$Method, $Uri)
    if ($Json) {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Json)
        $request.Content = New-Object System.Net.Http.ByteArrayContent(, $bytes)
        [void]$request.Content.Headers.TryAddWithoutValidation('Content-Type', 'application/json; charset=utf-8')
    }
    [void]$request.Headers.TryAddWithoutValidation('Accept', 'application/json, text/event-stream')
    foreach ($key in $Headers.Keys) {
        [void]$request.Headers.TryAddWithoutValidation($key, $Headers[$key])
    }

    $response = $http.SendAsync($request).GetAwaiter().GetResult()
    $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    [pscustomobject]@{
        Status  = [int]$response.StatusCode
        Body    = $body
        Headers = $response.Headers
    }
}

# Ответ MCP приходит либо чистым JSON, либо потоком SSE: события разделены пустой строкой,
# полезная нагрузка события - строки "data: ..." (многострочный JSON разложен по строкам).
function Get-JsonPayload {
    param([string]$Body)
    if (-not $Body) { return $null }
    $text = $Body.Trim()
    if ($text.StartsWith('{') -or $text.StartsWith('[')) {
        try { return ($text | ConvertFrom-Json) } catch { }
    }

    $fallback = $null
    foreach ($block in ($text -split "`r?`n`r?`n")) {
        $lines = @($block -split "`r?`n" |
            Where-Object { $_.StartsWith('data:') } |
            ForEach-Object { $_.Substring(5).Trim() } |
            Where-Object { $_ -ne '' })
        if ($lines.Count -eq 0) { continue }
        try { $obj = ($lines -join "`n") | ConvertFrom-Json } catch { continue }
        $names = @($obj.PSObject.Properties.Name)
        if ($names -contains 'result' -or $names -contains 'error') { return $obj }
        if ($null -eq $fallback) { $fallback = $obj }
    }
    return $fallback
}

function Invoke-Mcp {
    param([string]$Method, $Params, [int]$Id, [string]$SessionId)

    $payload = @{ jsonrpc = '2.0'; method = $Method }
    if ($null -ne $Params) { $payload.params = $Params }
    if ($Id -gt 0) { $payload.id = $Id }
    $headers = @{}
    if ($SessionId) { $headers['mcp-session-id'] = $SessionId }

    $json = ConvertTo-Json $payload -Depth 8 -Compress
    $response = Send-Http -Method 'Post' -Uri "$base/mcp" -Json $json -Headers $headers
    [pscustomobject]@{
        Status  = $response.Status
        Headers = $response.Headers
        Json    = (Get-JsonPayload -Body $response.Body)
        Raw     = $response.Body
    }
}

# Результат tools/call: result.content[0].text - строка с JSON {"success":true,"data":...}.
function Get-ToolResult {
    param($Call)
    if (-not $Call.Json -or -not $Call.Json.result) { return $null }
    $content = $Call.Json.result.content
    if (-not $content -or $content.Count -eq 0) { return $null }
    return ($content[0].text | ConvertFrom-Json)
}

function Invoke-Tool {
    param([string]$Name, [hashtable]$Arguments, [string]$SessionId)
    Invoke-Mcp -Method 'tools/call' -Params @{ name = $Name; arguments = $Arguments } -Id 10 -SessionId $SessionId
}

Write-Host ("Самопроверка 1c-toolkit на {0}" -f $base)
Write-Host ''

# 1. Живость сервера.
try {
    $health = Invoke-RestMethod -Uri "$base/health" -TimeoutSec 15 -UseBasicParsing
    $status = [string]$health.status
    Write-Step -Ok ($status -ne 'down' -and $status -ne '') -Name 'health' -Detail ("status=" + $status)
} catch {
    Write-Step -Ok $false -Name 'health' -Detail ("нет ответа: " + $_.Exception.Message)
    Write-Host ''
    Write-Host 'Слой не поднят: scripts\start-toolkit.ps1 [-AllowWrite]'
    exit 1
}

# 2. MCP-канал: initialize отдает заголовок сеанса.
$init = Invoke-Mcp -Method 'initialize' -Params @{
    protocolVersion = '2024-11-05'
    capabilities    = @{}
    clientInfo      = @{ name = 'harness-self-test'; version = '1.0' }
} -Id 1
$sessionId = ''
$serverName = ''
if ($init.Status -eq 200 -and $init.Json) {
    $serverName = [string]$init.Json.result.serverInfo.name
    foreach ($header in $init.Headers) {
        if ($header.Key -eq 'mcp-session-id') { $sessionId = [string]($header.Value -join '') }
    }
}
$sessionText = 'нет'
if ($sessionId) { $sessionText = 'есть' }
Write-Step -Ok ([bool]$sessionId) -Name 'initialize' -Detail ("server=" + $serverName + ' session=' + $sessionText)

if (-not $sessionId) {
    Write-Host ''
    Write-Host 'MCP-канал не отдал сеанс: дальше проверять нечего.'
    exit 1
}
[void](Invoke-Mcp -Method 'notifications/initialized' -Params $null -Id 0 -SessionId $sessionId)

# 3. tools/list без заголовка сеанса отвергается, с заголовком - отдает инструменты.
$noSession = Invoke-Mcp -Method 'tools/list' -Params @{} -Id 2
Write-Step -Ok ($noSession.Status -eq 400) -Name 'tools/list без сеанса' -Detail ("код " + $noSession.Status)

$list = Invoke-Mcp -Method 'tools/list' -Params @{} -Id 3 -SessionId $sessionId
$tools = @()
if ($list.Json -and $list.Json.result) { $tools = @($list.Json.result.tools | ForEach-Object { $_.name }) }
$required = @('execute_query', 'execute_code', 'get_metadata', 'get_event_log')
$missing = @($required | Where-Object { $tools -notcontains $_ })
$listDetail = 'инструментов ' + $tools.Count
if ($missing.Count -gt 0) { $listDetail = $listDetail + ', нет: ' + ($missing -join ', ') }
Write-Step -Ok ($list.Status -eq 200 -and $missing.Count -eq 0) -Name 'tools/list' -Detail $listDetail

# 4. execute_query через MCP-канал.
$query = Invoke-Tool -Name 'execute_query' -Arguments @{ query = 'ВЫБРАТЬ 1 КАК Один' } -SessionId $sessionId
$queryResult = Get-ToolResult -Call $query
$queryOk = ($null -ne $queryResult -and $queryResult.success -eq $true -and ([string]$queryResult.data) -match '1')
$queryDetail = 'ответ: ' + $query.Raw
if ($queryOk) { $queryDetail = 'success=true' }
Write-Step -Ok $queryOk -Name 'execute_query (MCP)' -Detail $queryDetail

# 5. REST-зеркало: тело уходит байтами UTF-8, запрос с кириллицей не портится.
try {
    $restBody = '{"query":"ВЫБРАТЬ 1 КАК МеткаКириллица"}'
    $rest = Send-Http -Method 'Post' -Uri "$base/api/execute_query" -Json $restBody
    $restOk = ($rest.Status -eq 200 -and $rest.Body -match 'success"\s*:\s*true' -and $rest.Body -match 'МеткаКириллица')
    $restDetail = 'код ' + $rest.Status + ', тело: ' + $rest.Body
    if ($restOk) { $restDetail = 'код 200, кириллица цела' }
    Write-Step -Ok $restOk -Name 'execute_query (REST)' -Detail $restDetail
} catch {
    Write-Step -Ok $false -Name 'execute_query (REST)' -Detail $_.Exception.Message
}

# 6. Право записи: запись в журнал регистрации через execute_code.
if ($SkipWrite) {
    Write-Host '[--]   execute_code (запись) пропущен: -SkipWrite'
} else {
    $code = 'ЗаписьЖурналаРегистрации("' + $script:eventName + '", УровеньЖурналаРегистрации.Информация, , , "проба канала toolkit"); Результат = "записан";'
    $write = Invoke-Tool -Name 'execute_code' -Arguments @{ code = $code } -SessionId $sessionId
    $writeResult = Get-ToolResult -Call $write
    $writeOk = ($null -ne $writeResult -and $writeResult.success -eq $true)
    if ($write.Raw -match 'запрещена') { $writeOk = $false }
    $writeDetail = 'ответ: ' + $write.Raw
    if ($writeOk) { $writeDetail = 'success=true, фильтр записи не сработал' }
    Write-Step -Ok $writeOk -Name 'execute_code (запись)' -Detail $writeDetail

    # 7. Запись видна в журнале регистрации - действие дошло до базы.
    $log = Invoke-Tool -Name 'get_event_log' -Arguments @{ events = @($script:eventName); limit = 3 } -SessionId $sessionId
    $logResult = Get-ToolResult -Call $log
    $logOk = ($null -ne $logResult -and $logResult.success -eq $true -and ([string]$logResult.data) -match [regex]::Escape($script:eventName))
    $logDetail = 'ответ: ' + $log.Raw
    if ($logOk) { $logDetail = 'запись события найдена' }
    Write-Step -Ok $logOk -Name 'get_event_log' -Detail $logDetail
}

Write-Host ''
if ($script:failed -eq 0) {
    Write-Host 'Слой toolkit исправен.'
    exit 0
}

Write-Host ("Провалено шагов: " + $script:failed)
exit 1
