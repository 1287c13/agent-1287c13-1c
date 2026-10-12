# Чек-лист: с нуля до первой задачи

## A. Платформа и база

- [ ] Установлена платформа 1С (здесь: `C:\Program Files\1cv8\8.3.27.2214`)
- [ ] Есть файловая или серверная ИБ (`C:\Users\kraft\Documents\1C\ARAutomation208`)
- [ ] Известна учётка с правами администратора ИБ (хранится в `.v8-project.json` — реестре баз вендорских скиллов, вне git)
- [ ] Достаточно места на диске: XML-выгрузка (гигабайты) + индекс `.code-index` (несколько ГБ). Мало места — выгрузка оборвётся

## B. Слой кода (обязательный)

- [ ] `scripts\install-mcp.ps1` → появился `mcp\code-index-mcp\bsl-indexer.exe`
- [ ] `scripts\install-vendor-skills.ps1` → 5 наборов в `skills-vendor\`, доки в `mcp\*\vendor-docs\`
- [ ] `scripts\fix-encoding.ps1` (один раз, чтобы .ps1 читались в PowerShell 5.1)
- [ ] Выгрузка конфигурации в `dump\` (вендорский скилл `db-dump-xml`)
- [ ] Выгрузка целая: `dump\Configuration.xml` не обрывается, в `daemon.log` нет `WARN parse_configuration_file`
- [ ] `scripts\setup-code-index.ps1` → демон запущен, папка `[ready]`
- [ ] Проверка: `bsl-indexer.exe daemon status`

## C. Слой данных (по желанию)

- [ ] `mcp\1c-mcp-toolkit\MCP_Toolkit.epf` открыт в 1С → «Встроенный сервер» → «Запустить сервер»
- [ ] Проверка: скилл `calling-1c-rest-api-via-curl` (или `curl http://localhost:6003/health`)

## D. Cline

- [ ] Установлен VS Code + расширение Cline
- [ ] Настроен провайдер модели и ключ
- [ ] `mcpServers` из `mcp\cline_mcp_settings.example.json` вставлен в настройки Cline
- [ ] Cline перезапущен, инструменты видны (MCP Servers → список)
- [ ] `scripts\install-skills.ps1` → 87 вендорских скиллов в `~\.cline\skills` (или `-Scope Project -ProjectDir <проект>`)
- [ ] Заведён `docs\context.local.md` (тип базы, права, что можно и чего нельзя)

## E. Первая задача

- [ ] Определены роль и границы (только чтение / расширение `.cfe` / без UpdateDBCfg основной конфигурации)
- [ ] Задача сформулирована с периодом/разрезом и критерием проверки
- [ ] Получен результат и проверен по критерию
