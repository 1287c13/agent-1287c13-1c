# MCP: `code-index-mcp` (слой кода и метаданных)

## Роли процессов

| Процесс | Команда | Что делает |
|---|---|---|
| Индексатор (единственный писатель) | `bsl-indexer.exe daemon run` | читает выгрузку, строит/обновляет `.code-index\index.db` |
| MCP-сервер (read-only) | `bsl-indexer.exe serve ...` | отвечает на запросы Cline |

Оба находят друг друга через `CODE_INDEX_HOME`. **Если демон не запущен, любой
вызов вернёт `daemon_offline`, даже когда индекс уже построен.**

## Проверка

```powershell
$home = 'C:\w\1c\агент\mcp\code-index-mcp'
& "$home\bsl-indexer.exe" --version      # ожидаем: code-index 1.8.6
& "$home\bsl-indexer.exe" daemon status
```

Статус папки должен стать `[ready]`. Пока идёт первая индексация — ждать,
журнал `daemon.log`.

## Папки в индексе

`daemon.toml`:

```toml
[[paths]]
path = "C:/w/1c/агент/dump"
alias = "ar208"
```

Алиас указывается клиентом в каждом вызове (при одном репозитории — неявно).
Добавили папку — `bsl-indexer daemon reload`.

## Обновление индекса после правок

Индексатор сам следит за файлами. Если правили `dump\` вручную или выгружали
заново — изменений достаточно, перезапуск не нужен. При сомнении:

```powershell
& "$home\bsl-indexer.exe" daemon reload
```

## Частые ошибки

* `daemon_offline` — демон не запущен или разный `CODE_INDEX_HOME`.
* `not_started` — папки нет в `daemon.toml`.
* `unknown_repo` — неверный алиас.
* `os error 10048` — порт занят (8011/8015).

## Ограничение
Индекс — это **снимок выгрузки**. Правки в базе, не отражённые в `dump\`, для
агента невидимы: обновите выгрузку (`scripts\dump-config.ps1`).
