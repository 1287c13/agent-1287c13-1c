# Слой справки: 1c-platform-help

## Что это

MCP-сервер `mcp-bsl-context` (Python) читает **файл справки платформы**
`shcntx_ru.hbk` из каталога установки 1С и отдаёт агенту синтакс-помощник и
стандарты разработки: поиск по методам, свойствам и конструкторам, описание типа,
руководство по коду, типизацию. База 1С и данные не нужны - серверу требуется
только каталог платформы, поэтому слой работает без запущенной 1С.

## Установка

Всё делает `scripts\install-mcp.ps1` (шаг 3 в README харнесса):

| Что | Откуда | Куда |
|-----|--------|------|
| исходники | `skills-vendor\mcp-bsl-platform-help-context` (шаг 2, `install-vendor-repos.ps1`) | - |
| venv | `py -3 -m venv` + `pip install` каталога исходников | `.cline\mcp\bsl-platform-help-context\.venv` |
| точка входа | - | `.cline\mcp\bsl-platform-help-context\.venv\Scripts\mcp-bsl-context.exe` |

Сборка venv тянет `fastmcp`, `qdrant-client`, `grpcio` и идёт **несколько минут**.
Повторный запуск без `-Force` уже собранный venv не трогает. Если venv не
собирается на текущей версии Python, задайте лаунчер явно:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-mcp.ps1 -Force -PythonLauncher 'py -3.12'
```

## Подключение к Cline

Блок `1c-platform-help` уже есть в `.cline\cline_mcp_settings.json` (образец -
`mcp\cline_mcp_settings.example.json`): `stdio`, Cline запускает `.exe` сам при
первом вызове инструмента, `timeout` 120 с.

```json
"1c-platform-help": {
  "command": "<КОРЕНЬ>\\.cline\\mcp\\bsl-platform-help-context\\.venv\\Scripts\\mcp-bsl-context.exe",
  "args": ["-p", "C:\\Program Files\\1cv8\\8.3.27.2130\\bin", "-m", "stdio"],
  "type": "stdio"
}
```

`-p` - каталог платформы, в котором лежит `shcntx_ru.hbk` (именно подкаталог
`bin`, не корень `1cv8`). Тот же путь должен стоять в `v8path` в
`.v8-project.json`. Путь в файле конфига **абсолютный**: если харнесс лежит не в
`C:\_works\1c-ai\agent`, замените его (шаг 1 в README харнесса).

## Файл справки

| Платформа | `shcntx_ru.hbk` |
|-----------|-----------------|
| 8.3.27 | есть - `C:\Program Files\1cv8\8.3.27.2130\bin\shcntx_ru.hbk` (около 39 МБ) |
| 8.3.25 | файла нет: слой справки на этой платформе не работает |
| 8.3.24 | есть |

Без файла справки `check-harness.ps1` печатает `[warn] нет shcntx_ru.hbk в v8path`:
слой молчит, остальные два сервера работают.

## Проверка

```powershell
# точка входа на месте?
Test-Path .\.cline\mcp\bsl-platform-help-context\.venv\Scripts\mcp-bsl-context.exe

# файл справки на месте? (путь - как в args -p конфига)
Test-Path 'C:\Program Files\1cv8\8.3.27.2130\bin\shcntx_ru.hbk'

# общий отчёт по харнессу
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-harness.ps1
```

В Cline список виден в панели **MCP Servers**; инструменты этого сервера отвечают
без обращения к базе.

## Инструменты

`search`, `info`, `get_member`, `get_members`, `get_constructors`,
`get_platform_info`, `get_coding_guideline`, `get_strict_typing_info`,
`search_strict_typing` - все девять добавлены в `autoApprove`: операции только на
чтение, подтверждать каждую незачем.

Режимы поиска: `keyword` (по умолчанию, внешних зависимостей нет), `semantic` и
`hybrid` - требуют `torch` и модели-эмбеддер (гигабайты), поэтому **намеренно не
включены** (см. `SOURCES.md`).

## Частые ошибки

* `[FAIL] 1c-platform-help / mcp-bsl-context.exe - нет файла` - не собран venv:
  выполните `install-mcp.ps1` (при необходимости с `-Force` и `-PythonLauncher`).
* Сервер сразу падает - чаще всего неверный `-p`: нужен каталог `bin` платформы,
  в котором есть `shcntx_ru.hbk`.
* Ответы пустые, хотя сервер поднят - включён `semantic`-режим без моделей:
  вернитесь к `keyword`.

## Ограничение

Сервер знает **только установленную платформу**: методов и свойств, которых нет в
`shcntx_ru.hbk` этой версии (например, из более нового релиза), он не найдёт. Для
вопросов о конкретной конфигурации нужен слой живой базы (`1c-toolkit`).
