# MCP-серверы харнесса

Три сервера. Все - внутри проекта. Конфигурация: `.cline/cline_mcp_settings.json`.
Подключение: `scripts/enable-mcp.ps1`.

## Как Cline находит этот конфиг

Cline читает MCP только из глобального файла. Цепочка разрешения пути:

1. `CLINE_MCP_SETTINGS_PATH` (переменная окружения) - **используется в харнессе**;
2. `CLINE_DATA_DIR\settings\cline_mcp_settings.json`;
3. `CLINE_DIR\data\settings\cline_mcp_settings.json`;
4. `~\.cline\data\settings\cline_mcp_settings.json`.

`enable-mcp.ps1` выставляет `CLINE_MCP_SETTINGS_PATH` на
`<проект>\.cline\cline_mcp_settings.json`. Перезапуск VS Code обязателен -
переменная читается при старте.

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
`scripts/start-harness.ps1`.

Инструменты: `get_object_structure`, `get_object_profile`, `get_form_handlers`,
`get_event_subscriptions`, `get_register_writers`, `find_references`,
`get_data_links`, `find_data_path`, `get_role_rights`, `find_path_bsl`,
`search_terms`, `bsl_sql` (read-only SQL по метаданным и графам), а также общие
`read_file`, `list_files`, `stat_file`, `grep_code`, `grep_body`, `search_text`,
`get_stats`, `health`.

Репозиторий задаётся алиасом: в вызове передаётся `repo: "main"`. Алиасы видны в
`daemon.toml` и в выводе `scripts\check-harness.ps1` (вместе со статусами путей из
`/health` демона).

`get_stats` - самый дорогой инструмент сервера: он считает статистику по базе индекса
(замер: 9,0 с по корню проекта, 6,6 с по выгрузке КА) и без параметра `repo` обходит все
репозитории сразу. Для вопроса «какие репозитории есть и жив ли индекс» он не нужен:
список даёт `daemon.toml`, состояния - `/health` демона (`scripts\check-harness.ps1`).

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

## Проверка подключения

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-harness.ps1
```

Ожидаемое: три артефакта на месте, индексатор отвечает, порт 6003 отвечает.
В Cline список инструментов виден в панели MCP Servers.

## Ручная переустановка

```powershell
# только бинарники MCP
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-mcp.ps1 -Force
```

`-Force` переустанавливает всё, включая venv сервера справки. Без `-Force`
существующие артефакты не трогаются.
