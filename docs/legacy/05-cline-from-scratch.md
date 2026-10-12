# Cline с нуля: настройка того же инструментария

## 1. Cline

1. Установите VS Code (или используйте Cline CLI).
2. Установите расширение **Cline** из Marketplace.
3. Откройте панель Cline → настройка провайдера и ключа модели.
4. Откройте нужную папку как рабочее пространство. Для работы агента удобно
   открывать `C:\w\1c\агент`.

## 2. MCP-серверы

Настройки MCP у расширения открываются так: панель Cline → иконка **MCP Servers**
→ вкладка **Configure** → **Configure MCP Servers**. Откроется JSON, допишите в
него блок `mcpServers` из `mcp\cline_mcp_settings.example.json`.

Для Cline CLI файл настроек: `~/.cline/data/settings/cline_mcp_settings.json`
(переопределяется переменной `CLINE_MCP_SETTINGS_PATH`). Добавить сервер можно и
командой:

```powershell
cline mcp add 1c-toolkit http://localhost:6003/mcp --transport http --yes
```

### Формы записи серверов

`code-index-mcp` умеет два транспорта: HTTP (`serve --transport http`) и stdio
(по умолчанию). В проекте используется HTTP — один общий процесс `serve`.

**Основной вариант — HTTP** (процесс держит `scripts\start-code-index.ps1`):

```json
{
  "mcpServers": {
    "1c-code": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8011/mcp",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Альтернатива — stdio** (Cline сам поднимает `serve`; папка должна быть в
`daemon.toml`, алиас задаётся в `--path`):

```json
{
  "mcpServers": {
    "1c-code-stdio": {
      "command": "C:\\w\\1c\\агент\\mcp\\code-index-mcp\\bsl-indexer.exe",
      "args": ["serve", "--path", "ar208=C:\\w\\1c\\агент\\dump"],
      "env": { "CODE_INDEX_HOME": "C:\\w\\1c\\агент\\mcp\\code-index-mcp" },
      "disabled": true,
      "autoApprove": []
    }
  }
}
```

**Слой живой базы** (`.epf`-сервер toolkit) — включайте, когда обработка открыта:

```json
{
  "mcpServers": {
    "1c-toolkit": { "type": "streamableHttp", "url": "http://localhost:6003/mcp", "disabled": true }
  }
}
```

`type` указывайте явно: без него Cline берёт устаревший `sse`.

### Что проверить

* все серверы в списке — зелёные;
* у `1c-code` в списке инструментов есть `get_object_structure`, `read_file`, `bsl_sql`;
* у `1c-toolkit` — инструменты метаданных и запросов;
* если сервер красный — смотрите `docs\04-troubleshooting.md`.

## 3. Skills

Скиллы Cline — это папки с `SKILL.md`:

```
my-skill/
├── SKILL.md          # frontmatter: name (совпадает с папкой), description
├── docs/             # опционально
├── templates/        # опционально
└── scripts/          # опционально
```

`description` (до 1024 символов) — по нему Cline решает, когда скилл включить.
Вызвать принудительно можно слэш-командой `/имя-скилла`.

Установка: `scripts\install-skills.ps1` — раскладывает **вендорские** скиллы в
каталог, откуда их читает Cline:

* глобально `~/.cline/skills` (на этой машине `C:\Users\kraft\.cline\skills`);
* в проекте — `-Scope Project -ProjectDir <путь>` (тогда `<проект>/.cline/skills`).

Скиллов 83 (2 от авторов `1c-mcp-toolkit` + 81 набор `cc-1c-skills`), все скачаны
с GitHub — см. `skills-vendor\SOURCES.md`. Своих скиллов в проекте нет.

Проверка: панель Cline → иконка Skills → вкладка **Skills** → в списке 83 скилла.

## 4. Воспроизведение с нуля на другой машине

1. Установить 1С-платформу и развернуть/получить базу.
2. Скопировать папку `C:\w\1c\агент` на новую машину.
3. `install-mcp.ps1` → `install-vendor-skills.ps1` → `fix-encoding.ps1` → `setup-code-index.ps1`.
4. Выгрузить конфигурацию в `dump\` вендорским скиллом `db-dump-xml`, дождаться статуса `[ready]`.
5. Вставить `mcpServers` в Cline, перезапустить, затем `install-skills.ps1`.
6. Заполнить `docs\context.local.md` и `.v8-project.json` (реестр баз для вендорских скиллов).

## 5. Автозапуск (чтобы не поднимать вручную)

```powershell
.\scripts\start-code-index.ps1
```

Скрипт поднимает демон и MCP-сервер скрытыми. Для автозапуска положите ярлык
на него в папку `shell:startup` (Win+R → `shell:startup`). Ярлыку можно задать
аргумент `-ExecutionPolicy Bypass`.
