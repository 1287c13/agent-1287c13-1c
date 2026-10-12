# Установка MCP-слоя

## Слой 1 — code-index-mcp (код и метаданные по XML-выгрузке)

Бинарник `bsl-indexer.exe` играет две роли: **демон индексации** (`daemon run`,
единственный писатель) и **MCP-сервер** (`serve`, тонкий read-only клиент).

1. Скачать: `scripts\install-mcp.ps1` (или архив `bsl-indexer-windows-x64.zip`
   со страницы релизов вручную) → в `mcp\code-index-mcp\`.
2. Настроить и запустить: `scripts\setup-code-index.ps1`.
   Скрипт ставит `CODE_INDEX_HOME`, пишет `daemon.toml` и поднимает оба процесса.
3. Проверка:

```powershell
C:\w\1c\агент\mcp\code-index-mcp\bsl-indexer.exe --version
C:\w\1c\агент\mcp\code-index-mcp\bsl-indexer.exe daemon status
```

Ожидаемо: папка `C:/w/1c/агент/dump` со статусом `[ready]`.
Пока индекс не готов, инструменты отвечают `daemon_offline` / `not_started`.

**Ключевые параметры:**

| Что | Значение |
|---|---|
| `CODE_INDEX_HOME` | `C:\w\1c\агент\mcp\code-index-mcp` |
| Конфиг папок | `mcp\code-index-mcp\daemon.toml` (`[[paths]] path/alias`) |
| HTTP-порт демона | 8015 |
| MCP endpoint | `http://127.0.0.1:8011/mcp` |
| Индекс | `<папка выгрузки>\.code-index\index.db` |

**Важно:** MCP-сервер только читает индекс. Если демон не запущен — любой вызов
вернёт `daemon_offline`, даже когда индекс уже построен. Демон должен работать.

## Слой 2 — 1c-mcp-toolkit (живые данные и запросы)

1. `scripts\install-mcp.ps1` скачивает `MCP_Toolkit.epf` в `mcp\1c-mcp-toolkit\`
   (проще всего — вручную из папки `build` репозитория ROCTUP/1c-mcp-toolkit).
2. Открыть `.epf` в 1С:Предприятие → включить режим **«Встроенный сервер»** →
   «Запустить сервер». Публикация базы и COM не нужны, конфигурация не меняется.
3. Cline подключается как `streamableHttp` к `http://localhost:6003/mcp`.

Проверка REST-каналом (скилл `calling-1c-rest-api-via-curl` или напрямую):

```sh
curl -sS http://localhost:6003/health
curl -sS -H 'Content-Type: application/json' \
  -d '{"query":"ВЫБРАТЬ ПЕРВЫЕ 5 Ссылка ИЗ Справочник.Номенклатура"}' \
  http://localhost:6003/api/execute_query
```

## Опциональные модули

| Модуль | Когда включать | Как |
|---|---|---|
| `mcp-1c` | база опубликована на IIS/Apache | `install-mcp.ps1 -Optional`, затем `mcp-1c --install "путь_к_базе"` и снять `"disabled": true` у `1c-live` |
| `mcp-rsv-data` | аналитик, строгий read-only, Windows | `install-mcp.ps1 -Optional`, установить `RSVData.cfe`, запустить `rsvdata-bridge.exe`, снять `disabled` у `1c-rsv` |

## Подключение к Cline

`serve` отдаёт MCP по HTTP: `http://127.0.0.1:8011/mcp`. Готовый блок —
`mcp\cline_mcp_settings.example.json` (сервер `1c-code`, `"type": "streamableHttp"`).
Вставьте `mcpServers` в файл настроек Cline
(`~/.cline/data/settings/cline_mcp_settings.json` для CLI) и перезапустите Cline.
Демон и `serve` держит `scripts\start-code-index.ps1`.

Альтернатива — stdio: клиент запускает `serve` сам (`command` + `args`
`["serve","--path","ar208=<путь к dump>"]` + `env.CODE_INDEX_HOME`); тогда отдельный
процесс `serve` не нужен, но демон обязателен (см. `docs/05-cline-from-scratch.md`).
