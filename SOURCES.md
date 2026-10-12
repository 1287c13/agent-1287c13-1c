# Источники решения

Всё, что взято извне, и на какой версии зафиксировано. Вендорские репозитории
клонируются скриптом `scripts/install-vendor-repos.ps1`, бинарники MCP
скачиваются `scripts/install-mcp.ps1`.

## Вендорские репозитории (скиллы, правила, комплект toolkit)

Клонируются в `skills-vendor\` (в git не хранятся; разворачиваются скриптом
`install-vendor-repos.ps1`). Коммиты на момент развёртывания - для воспроизводимости.

| Репозиторий | Коммит | Что берём |
|-------------|--------|-----------|
| https://github.com/Nikolay-Shirokov/cc-1c-skills | `b102d9dad19304f35e1d0639aa719a60b5ab9f49` (2026-10-11) | 81 скилл: конфигурация, объекты, формы, роли, СКД, макеты, XDTO, расширения, обработки, базы, веб-публикация, валидаторы, справка платформы |
| https://github.com/Desko77/cursor-1c-skills | `0f71a5d89fb6e5ee79f083f3b77b7804dbd50b45` (2026-09-30) | 120 скиллов (`1c-*`), 40 правил `.mdc`, маршрутизатор `1c-config-router`, `1c-bsl-validate`, `1c-code-review` |
| https://github.com/Desko77/mcp-bsl-platform-help-context | `49c48bc40e0b8af1b516b542db2c107955cc9108` (2026-09-21) | исходники MCP-сервера справки API платформы (Python, ставится в venv) |
| https://github.com/andrejkaxz/Vanessa_for_AI | `ad6e6aea97e5aba1ce3a50922383586fff857f81` (2026-08-27) | 2 скилла: авторство и подъём Vanessa-проекта |
| https://github.com/shevchenko-dl/va-ai-autotests | `58fcec9cd8ce6f8d05b979eec3f69a818ed898a4` (2026-10-07) | генератор Gherkin-сценариев `va-scenario-generator` |
| https://github.com/gsulamanidzebdoge/product-analyst | `356f4b88503010014f84a581aaf64da804f5caf5` (2026-09-17) | скилл продуктовой аналитики |
| https://github.com/ROCTUP/1c-mcp-toolkit | `dba3f22e292f576e745ea6ed76773d18a512557a` (2026-10-11) | `build/MCP_Toolkit.epf` (встроенный MCP-сервер 1С), 2 скилла |

## Бинарники MCP-серверов

| Что | Источник | Куда |
|-----|----------|------|
| `bsl-indexer.exe` (code-index-mcp, сборка с поддержкой 1С, 33 инструмента) | release `bsl-indexer-windows-x64.zip` из https://github.com/Regsorm/code-index-mcp | `.cline\mcp\code-index-mcp\` |
| `MCP_Toolkit.epf` | `build/` из https://github.com/ROCTUP/1c-mcp-toolkit | `.cline\mcp\1c-mcp-toolkit\` |
| `mcp-bsl-context` (venv) | `py -3 -m venv` + `pip install` исходников из `skills-vendor\mcp-bsl-platform-help-context` | `.cline\mcp\bsl-platform-help-context\.venv\` |

Версия code-index-mcp записывается в `.cline\mcp\code-index-mcp\VERSION.txt`.

## Что отброшено и почему

| Кандидат | Причина отказа |
|----------|----------------|
| `1C_SyntaxChecker` (Docker) | на машине нет Docker |
| Docker-режим `1c-mcp-toolkit` (proxy) | используется встроенный сервер обработки, Docker не нужен |
| `77MCP` | на машине нет платформы 1С 7.7 |
| `ai-edt` (AI-EDT, Cursor-плагин) | требует 1С:EDT, недоступен как MCP-сервер на этой машине |
| `1c-naparnik` | требует внешнего сервиса, доступность не подтверждена |
| npm-обёртка `@regsorm/code-index-mcp` | на машине нет Node.js; используется нативный бинарник |
| `mcp-remote` | на машине нет Node.js |
| semantic-режим `mcp-bsl-platform-help-context` (`.[local]`) | требует `torch` + модели-эмбеддер (гигабайты); keyword-режима достаточно |

## Ссылки на документацию, использованную при проектировании

- Cline, скиллы: https://docs.cline.bot/features/skills
- Cline, настройка MCP-серверов: https://docs.cline.bot/mcp/configuring-mcp-servers
- Cline, правила: https://docs.cline.bot/features/cline-rules
- Формат `.v8-project.json`: `skills-vendor\cc-1c-skills\docs\v8-project-guide.md`
- Установка code-index-mcp вручную: https://github.com/Regsorm/code-index-mcp/blob/main/docs/manual-install.md
- 1C MCP Toolkit (встроенный сервер): https://github.com/ROCTUP/1c-mcp-toolkit
