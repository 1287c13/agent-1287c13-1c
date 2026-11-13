param(
	[string]$Tool = 'execute_query',
	[string]$CodeFile = '',
	[string]$QueryFile = '',
	[string]$ArgsFile = '',
	[int]$Port = 6003,
	[int]$TimeoutSec = 300,
	[string]$Out = ''
)
# Вызов инструмента обработки 1C MCP Toolkit по REST-зеркалу.
# REST - рабочий канал, когда сервер поднят после старта VS Code и Cline инструменты
# не регистрирует. Тело отправляется БАЙТАМИ UTF-8: Invoke-WebRequest со строкой в
# -Body кодирует ASCII, и кириллица уходит в "???????" (см. .clinerules\40-lessons.md, п.3).
$ErrorActionPreference = 'Stop'
$uri = "http://127.0.0.1:$Port/api/$Tool"

function Read-Utf8([string]$path) {
	return [string](Get-Content -Path $path -Raw -Encoding UTF8)
}

$args_ = [ordered]@{}
if ($ArgsFile -ne '') {
	$body = Read-Utf8 $ArgsFile
}
else {
	if ($CodeFile -ne '') { $args_['code'] = Read-Utf8 $CodeFile }
	if ($QueryFile -ne '') { $args_['query'] = Read-Utf8 $QueryFile }
	$body = ($args_ | ConvertTo-Json -Compress)
}
$bytes = [Text.Encoding]::UTF8.GetBytes($body)

try {
	$r = Invoke-WebRequest -Uri $uri -Method Post -Body $bytes `
		-ContentType 'application/json; charset=utf-8' -UseBasicParsing -TimeoutSec $TimeoutSec
	$text = [Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
	$code = $r.StatusCode
}
catch {
	$resp = $_.Exception.Response
	$code = if ($resp) { [int]$resp.StatusCode } else { -1 }
	$text = $_.Exception.Message
}

$ok = $false
try { $ok = ($text | ConvertFrom-Json).success -eq $true } catch { $ok = $false }
if ($Out -ne '') {
	[IO.File]::WriteAllText($Out, $text, (New-Object System.Text.UTF8Encoding($false)))
	Write-Output ("http=" + $code + " success=" + $ok + " -> " + $Out)
}
else {
	Write-Output ("http=" + $code + " success=" + $ok)
	Write-Output $text
}
if (-not $ok) { exit 1 }
