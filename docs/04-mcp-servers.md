# MCP-серверы харнесса

Три сервера. Все - внутри проекта. Конфигурация: `.cline/cline_mcp_settings.json`.
Подключение: `scripts/enable-mcp.ps1`.

## Как Cline находит этот конфиг

Cline читает MCP только из глобального файла. Цепочка разрешения пути:

1. `CLINE_MCP_SETTINGS_PATH` (переменная окружения) - **используется в харнессе**;
2. `CLINE_DATA_DIR\settings\cline_mcp_settings.json`;
3. `CLINE_DIR\data\settings\cline_mcp_settings.json`;
4. `~\.cline\data\settings\cline_mcp_settings.json`.

`scripts\set-cline-mcp-path.ps1` наводит `CLINE_MCP_SETTINGS_PATH` на
`<проект>\.cline\cline_mcp_settings.json`; тот же скрипт - короткая команда
**"измени переменную"**, если харнесс открыт в другом каталоге. `enable-mcp.ps1` вызывает
его в составе установки. Перезапуск VS Code обязателен - переменная читается при старте.

Форматов транспорта, которые понимает Cline, три: `stdio`, `sse`, `streamableHttp`
(синонимы `http` и `streamable-http` тоже принимаются). Подтверждено по
`dist/extension.js`.

## 1. `1c-toolkit` - живая база 1С

| | |
|---|---|
| Транспорт | `streamableHttp` |
| Адрес | `http://127.0.0.1:6003/mcp` |
| Артефакт | `.cline\mcp\1c-mcp-toolkit\MCP_Toolkit.epf` |
| Запуск | `scripts\start-toolkit.ps1` - автозапуск обработки (`/C "startup;mode=embedded;port=6003"`), база из `.v8-project.json`; остановка - `scripts\stop-toolkit.ps1`. Скрипт идемпотентен: если `/health` отвечает или сеанс с обработкой уже запущен, новый клиент не поднимается (повторный запуск - только `-Force`). Вручную тоже можно: открыть `.epf` в базе 1С -> режим «Встроенный сервер» -> «Запустить сервер» |

Встроенный сервер работает **внутри** обработки 1С: Python и Docker не нужны.
Конфигурацию базы менять не требуется, публикация базы не требуется.

Инструменты (имена - по документации вендора; точный перечень отдаёт сам сервер):

| Инструмент | Назначение |
|-----------|-----------|
| `execute_query` | выполнить запрос к базе |
| `execute_code` | выполнить код BSL в контексте базы |
| `get_metadata` | состав и структура метаданных |
| `get_event_log` | журнал регистрации |
| `get_access_rights` | права доступа |
| `get_object_by_link` / `get_link_of_object` | навигация по ссылкам |
| `find_references_to_object` | кто ссылается на объект |
| `get_bsl_syntax_help` | подсказка по синтаксису BSL |
| `restart_1c_session` / `close_1c_session` | управление сессией |

Из дополнительных возможностей: изоляция каналов (`?channel=<id>`), ограничение
прав, анонимизация данных, REST-зеркало `/api/*` (см. навык
`.cline\skills\calling-1c-rest-api-via-curl`).

**Одно ограничение, которое важно помнить:** сервер поднят на одну базу. Работа с
другой базой - переключение сервера.

## 2. `1c-code-index` - структурный поиск по выгрузке

| | |
|---|---|
| Транспорт | `stdio` (Cline запускает сам) |
| Команда | `bsl-indexer.exe serve --config <проект>\.cline\mcp\code-index-mcp\home\daemon.toml` |
| Переменная | `CODE_INDEX_HOME=<проект>\.cline\mcp\code-index-mcp\home` |
| Фоновый демон | `bsl-indexer.exe daemon run` (обязателен) |
| Конфиг демона | `daemon.toml`, секция `[[paths]]`, алиас репозитория `main` |
| Индекс | `<каталог выгрузки>\.code-index\index.db` |

MCP-сервер только читает индекс; индексацию ведёт отдельный демон. Если демон не
запущен, любой вызов вернёт `daemon_offline`. Демон поднимает
`scripts/start-harness.ps1 -Layer Index` (только индекс, без живого слоя), оба слоя -
`scripts/start-harness.ps1`.

Инструменты: `get_object_structure`, `get_object_profile`, `get_form_handlers`,
`get_event_subscriptions`, `get_register_writers`, `find_references`,
`get_data_links`, `find_data_path`, `get_role_rights`, `find_path_bsl`,
`search_terms`, `bsl_sql` (read-only SQL по метаданным и графам), а также общие
`read_file`, `list_files`, `stat_file`, `grep_code`, `grep_body`, `search_text`,
`get_stats`, `health`.

Репозиторий задаётся алиасом: в вызове передаётся `repo: "main"`. Алиасы видны в
`daemon.toml` и в выводе `scripts\check-harness.ps1 -Health` (вместе со статусами путей из
`/health` демона).

`get_stats` - самый дорогой инструмент сервера: он считает статистику по базе индекса
(замер: 9,0 с по корню проекта, 6,6 с по выгрузке КА) и без параметра `repo` обходит все
репозитории сразу. Для вопроса «какие репозитории есть и жив ли индекс» он не нужен:
список даёт `daemon.toml`, состояния - `/health` демона (`scripts\check-harness.ps1 -Health`).

## 3. `1c-platform-help` - справка API платформы

| | |
|---|---|
| Транспорт | `stdio` |
| Команда | `<проект>\.cline\mcp\bsl-platform-help-context\.venv\Scripts\mcp-bsl-context.exe -p "C:\Program Files\1cv8\8.3.27.2130\bin" -m stdio` |
| Источник данных | `shcntx_ru.hbk` из каталога платформы |

Инструменты: `search`, `info`, `get_member`, `get_members`, `get_constructors`,
`get_platform_info`, `get_coding_guideline`, `get_strict_typing_info`,
`search_strict_typing`.

Все девять добавлены в `autoApprove` - это read-only операции, подтверждение по
каждой только мешает.

Reжимы поиска: `keyword` (по умолчанию, без внешних зависимостей), `semantic` и
`hybrid` (требуют `torch` и модели-эмбеддер; не включены намеренно).

## Какие инструменты видны модели

Схема каждого инструмента уходит в запрос, поэтому длинный хвост редких инструментов
оплачивается каждым обращением. Замер по этому харнессу (2026-10-14, 10 сессий, 5 234
вызова инструментов) - `1c-toolkit`: 13 инструментов, 53 032 символа схем; `1c-code-index`:
33 инструмента, 49 998 символов; `1c-platform-help`: 9 инструментов, 6 292 символа.

Отключены ключом `disabledTools` в `.cline/cline_mcp_settings.json` (механизм тот же, что у
галочек в панели MCP; в 4.1.24 список инструментов сборки задачи фильтруется по имени -
`filter(i => !disabled.has(i.name))`):

| Сервер | Отключены | Почему |
|--------|-----------|--------|
| `1c-code-index` | `get_imports`, `get_class`, `search_class`, `get_callees`, `find_path`, `get_call_tree` | ноль вызовов за 10 сессий, возможности дублируются (`find_symbol`, `grep_code`, `get_callers`, `find_path_bsl`) |
| `1c-toolkit` | `submit_for_deanonymization`, `close_1c_session` | ноль вызовов; сеанс гасит `scripts\stop-toolkit.ps1` через REST `/api/close_1c_session` |

Остальное оставлено сознательно, хотя часть инструментов тоже не вызывалась:
`get_access_rights`, `get_form_handlers`, `get_register_writers`, `get_role_rights`,
`find_references`, `get_data_links`, `get_dcs_schema`, `get_bsl_syntax_help` - это
инструменты задач **по базе**, а замеренные сессии были в основном про сам харнесс.

Вернуть инструмент: убрать имя из `disabledTools` и переподключить сервер в панели MCP
(`Restart`): список инструментов клиент сам не перечитывает. Проверить, что реально видит
модель, можно пробой `temp\probe-tools.ps1` или ключом `-Mcp` у `scripts\check-context.ps1`.

## Проверка подключения

```powershell
# установка: артефакты, конфиги, переменная Cline (порты не опрашиваются)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-harness.ps1

# живость слоев - по явному указанию: порт 8015 демона и порт 6003 toolkit
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-harness.ps1 -Health
```

Ожидаемое: три артефакта на месте, переменная указывает на проект; с ключом `-Health` -
демон индекса в `ready` и сервер 6003 отвечает. В Cline список инструментов виден в панели
MCP Servers.

## Ручная переустановка

```powershell
# только бинарники MCP
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-mcp.ps1 -Force
```

`-Force` переустанавливает всё, включая venv сервера справки. Без `-Force`
существующие артефакты не трогаются.
