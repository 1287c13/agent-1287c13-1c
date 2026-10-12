# Скиллы

## Что это и как работает

Скилл (Agent Skill) - каталог с файлом `SKILL.md`, у которого во frontmatter есть
`name` (совпадает с именем каталога) и `description`. Cline держит в контексте
только метаданные скиллов и подгружает `SKILL.md` целиком, когда скилл релевантен
задаче. Дополнительные файлы внутри каталога (`references/`, `scripts/`,
`*.json`) скилл читает сам по своим инструкциям.

Каталог: `.cline\skills\`. Количество: **206**.

## Источники (шесть вендорских наборов)

| Набор | Скиллов | Стиль имён |
|-------|---------|-----------|
| `cc-1c-skills` (Nikolay-Shirokov) | 81 | без префикса: `cf-edit`, `db-load-xml` |
| `cursor-1c-skills` (Desko77) | 120 | с префиксом `1c-*`: `1c-cf-edit`, `1c-config-router` |
| `Vanessa_for_AI` (andrejkaxz) | 2 | `vanessa-feature-authoring`, `vanessa-project-bootstrap` |
| `va-ai-autotests` (shevchenko-dl) | 1 | `va-scenario-generator` |
| `1c-mcp-toolkit` (ROCTUP) | 2 | `calling-1c-rest-api-via-curl`, `composing-1c-queries` |
| `product-analyst` | 1 | `product-analyst` |

Порядок применения - в `scripts\install-vendor-skills.ps1`. Поздний источник
перекрывает ранний при совпадении имени каталога; cursor-набор идёт последним.
Практически пересечение оказалось единственным: `composing-1c-queries`.

Исходные репозитории лежат в `skills-vendor\` (не в git, ставятся скриптом).

## Точки входа по задачам

| Задача | Скилл |
|--------|-------|
| Не знаю, каким скиллом решать | `1c-config-router` |
| Проиндексировать конфигурацию для остальных валидаторов | `1c-config-index` |
| Объект метаданных: создать / разобрать / править | `meta-compile` / `meta-decompile` / `meta-edit`, `1c-meta-*` |
| Управляемая форма | `form-compile` / `form-edit` / `form-info` / `form-validate`, `1c-form-*` |
| Роль | `role-compile` / `role-edit` / `role-validate` |
| Схема компоновки данных | `skd-compile` / `skd-decompile` / `skd-edit` / `skd-validate` |
| Макет | `mxl-compile` / `mxl-decompile` / `mxl-validate` |
| Подсистема | `subsystem-compile` / `subsystem-edit` / `subsystem-validate` |
| XDTO-пакет | `xdto-compile` / `xdto-edit` / `xdto-validate` |
| Расширение конфигурации | `cfe-init` / `cfe-borrow` / `cfe-patch-method` / `cfe-validate`, `1c-cfe-full-cycle` |
| Внешняя обработка / отчёт | `epf-build` / `epf-init` / `epf-dump` / `erf-build` / `erf-dump` |
| База: список, создать, выгрузить, загрузить, обновить | `db-list` / `db-create` / `db-dump-xml` / `db-load-xml` / `db-update` |
| Запустить базу, поставить расширение в базу | `db-run`, `db-cfe-admin` |
| Хранилище конфигурации | `db-repo` |
| Веб-публикация базы | `web-publish` / `web-info` / `web-unpublish` / `web-stop` |
| Тест в браузере | `web-test`, `1c-web-test` |
| **Gherkin-сценарии и Vanessa** | `va-scenario-generator`, `vanessa-feature-authoring`, `vanessa-project-bootstrap`, `1c-vanessa-steps` |
| Валидация BSL офлайн | `1c-bsl-validate` |
| Ревью кода | `1c-code-review` |
| Справочник API БСП | `1c-bsp-api` |
| Прикладные сценарии БСП | `1c-ssl-patterns` |
| Справка по API платформы (скилл-обёртка) | `1c-platform-docs` |
| Справочник ЗУП | `zup-hr-api-reference` |
| Продуктовое ТЗ, требования | `product-analyst` |
| REST-зеркало 1C MCP Toolkit | `calling-1c-rest-api-via-curl` |
| Составление запросов 1С | `composing-1c-queries` |

Полный перечень: `Get-ChildItem .cline\skills -Directory | Select-Object Name`.

## Слой Gherkin / Vanessa (для задач автотестов)

Это отдельная ветка, заслуживающая внимания, потому что задачи вида «напиши
Gherkin-тест и запусти его в базе» закрываются именно ей.

| Скилл | Что внутри |
|-------|-----------|
| `va-scenario-generator` | генерация `.feature` под конкретную демо-базу; `erp-demo-notes.md` |
| `vanessa-feature-authoring` | каталог шагов, условные блоки, переменные, окна и ожидания, негативные сообщения, диагностика, UI-подтверждения |
| `vanessa-project-bootstrap` | чеклист подъёма Vanessa-проекта (`bootstrap-checklist.md`) |
| `1c-vanessa-steps` | библиотека шагов с индексом: `steps-library.json`, `indexer.py`, `search_steps.py`, `validate.py`, `semantic_matcher.py` - поиск и валидация шагов по каталогу, а не по памяти |

Благодаря `1c-vanessa-steps` шаги сценария берутся из JSON-каталога и проверяются
скриптом, а не сочиняются. Это ровно тот случай, когда скилл заменяет
«уверенное» выдумывание.

## Вендорские правила (не подключены постоянно)

`skills-vendor\cursor-1c-skills\rules\*.mdc` - 40 правил (стандарты BSL,
антипаттерны, требования EDT, транзакции и блокировки, оптимизация запросов, БСП,
безопасность git, кириллица в Windows и др.).

Они **намеренно не скопированы** в `.clinerules\`: Cline не поддерживает
`globs`/`alwaysApply` и подключил бы все 40 разом как постоянные - это сотни
килобайт в каждом запросе.

Правило работы: агент читает нужный `.mdc` **по одному под задачу**. Наиболее
употребимые:

| Файл | Когда нужен |
|------|-------------|
| `1c-coding-standards.mdc` | перед написанием BSL |
| `anti_patterns.mdc` | перед написанием BSL |
| `query-optimization-tips.mdc` | запросы к базе |
| `code-review-checklist.mdc` | ревью |
| `1c-cyrillic-windows.mdc` | кириллица в путях, запуск платформы |
| `testing-patterns.mdc` | автотесты |
| `1c-transactions-and-locks.mdc` | работа с транзакциями |
| `1c-extension-patterns.mdc` | расширения |
| `form_module_rules.mdc`, `forms_events.mdc` | модули форм |
| `text-formatting.mdc` | запрещённые символы в генерируемом тексте |

## Валидация набора

После сборки скрипт `install-vendor-skills.ps1` проверяет у каждого скилла, что
поле `name` во frontmatter совпадает с именем каталога. Несовпадение - код
возврата 2 и список проблемных скиллов.

Ручная проверка:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-vendor-skills.ps1
```
