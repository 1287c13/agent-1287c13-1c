# Источники вендорных файлов

Всё в этом каталоге скачано из открытых репозиториев и **не правилось**.
Повторное скачивание: `scripts\install-vendor-skills.ps1`.
Разложить скиллы для Cline: `scripts\install-skills.ps1`.
Дата снимков — 2026-10-11.

## Скиллы

| Каталог | Источник | Лицензия | Состав |
|---|---|---|---|
| `1c-mcp-toolkit\` | https://github.com/ROCTUP/1c-mcp-toolkit → папка `skills/` | GPL-3.0 | 2 скилла: `calling-1c-rest-api-via-curl`, `composing-1c-queries` (со `references/`) |
| `cc-1c-skills\` | https://github.com/Nikolay-Shirokov/cc-1c-skills (zip ветки `main`) | MIT, © 2025-2026 Nick Shirokov | 81 скилл в `.claude\skills\`, плюс авторские `docs\`, `scripts\`, `README.md`, `LICENSE` |
| `Vanessa_for_AI\` | https://github.com/andrejkaxz/Vanessa_for_AI (zip ветки `main`) | **CC BY 4.0**, © 2026 @andrejkaxz | 2 скилла: `vanessa-feature-authoring`, `vanessa-project-bootstrap` + авторские `knowledge\`, `LICENSE` |
| `va-ai-autotests\` | https://github.com/shevchenko-dl/va-ai-autotests (zip ветки `main`) | MIT | 1 скилл: `va-scenario-generator` (Turbo Gherkin для Vanessa Automation, работа через MCP VA) + `docs\`, `prompts\` |
| `product-analyst\` | https://github.com/gsulamanidzebdoge/product-analyst (zip ветки `main`, `SKILL.md` в корне) | MIT | 1 скилл: `product-analyst` — ТЗ/ЧТЗ/SRS (ГОСТ 34.602, ISO/IEC/IEEE 29148), реестр требований, FIT/GAP, 1С:ERP-анализ |

Тексты лицензий лежат в самих наборах (`cc-1c-skills\LICENSE`,
`Vanessa_for_AI\LICENSE`, `va-ai-autotests\LICENSE`, `product-analyst\LICENSE`).

**Атрибуция CC BY 4.0** (`Vanessa_for_AI`, обязательна при распространении):

> Based on Vanessa_for_AI by @andrejkaxz: https://github.com/andrejkaxz/Vanessa_for_AI
> Licensed under CC BY 4.0. Changes: файлы скопированы без изменений.


## Документация по инструментам (вендор-docs)

| Каталог | Источник | Лицензия |
|---|---|---|
| `..\mcp\code-index-mcp\vendor-docs\` | https://github.com/Regsorm/code-index-mcp (`README_RU.md`, `docs/*.md`) | MIT |

## Сами MCP-серверы (бинарник и обработка)

| Файл | Источник | Лицензия |
|---|---|---|
| `..\mcp\code-index-mcp\bsl-indexer.exe` | Regsorm/code-index-mcp, релиз `bsl-indexer-windows-x64.zip` | MIT |
| `..\mcp\1c-mcp-toolkit\MCP_Toolkit.epf` | ROCTUP/1c-mcp-toolkit | GPL-3.0 |

## Кандидаты, которые не устанавливались (выключены)

| Компонент | Источник | Лицензия |
|---|---|---|
| `mcp-1c` | https://github.com/feenlace/mcp-1c | MIT |
| `mcp-rsv-data` | https://github.com/prepod2003/mcp-rsv-data | MIT |
| `bsl-language-server` | https://github.com/1c-syntax/bsl-language-server | см. репозиторий |
| `unica` (плагин Codex/Claude Code) | https://github.com/IngvarConsulting/unica | см. репозиторий |
| `cursor-1c-skills` (120 скиллов Cursor) | https://github.com/Desko77/cursor-1c-skills | см. репозиторий |
