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
# <КОРЕНЬ> - каталог харнесса (там, где README.md и scripts\)
$home = '<КОРЕНЬ>\.cline\mcp\code-index-mcp'
$env:CODE_INDEX_HOME = "$home\home"
& "$home\bsl-indexer.exe" --version      # ожидаем строку версии индексатора
& "$home\bsl-indexer.exe" daemon status
```

Статус папки должен стать `[ready]`. Пока идёт первая индексация — ждать,
журнал `daemon.log`.

## Папки в индексе

`daemon.toml` (лежит в `.cline\mcp\code-index-mcp\home\daemon.toml`, создаёт
`scripts\enable-mcp.ps1`):

```toml
[[paths]]
path = "C:/path/to/dump"
alias = "main"
```

`path` - каталог выгрузки конфигурации (прямые слэши), `alias` - короткое имя
папки в вызовах. По умолчанию `enable-mcp.ps1` прописывает сюда корень харнесса
с алиасом `main`: если выгрузка лежит в стороне, замените `path`.
Добавили папку - `bsl-indexer daemon reload`.

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
Индекс - это **снимок выгрузки**. Правки в базе, не отражённые в каталоге
выгрузки, для агента невидимы: обновите выгрузку (скилл `1c-db-dump-xml`) -
демон сам подхватит изменённые файлы.
