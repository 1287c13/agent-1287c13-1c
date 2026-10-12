# 1С × Cline: открытый MCP + вендорские скиллы

Цель проекта — превратить Cline в 1С-разработчика и 1С-аналитика на **чужих готовых
компонентах**: открытый специализированный MCP для 1С и скиллы, написанные людьми и
опубликованные на GitHub. Свои скиллы здесь не пишутся: происхождение каждого файла
проверяется в исходном репозитории (список — `skills-vendor\SOURCES.md`).

---

## 1. Выбранный MCP (и почему)

| Слой | Компонент | Репозиторий | Лицензия | ★ | Что даёт |
|---|---|---|---|---|---|
| Код и метаданные | `code-index-mcp` (`bsl-indexer.exe`) | [Regsorm/code-index-mcp](https://github.com/Regsorm/code-index-mcp) | MIT | 141 | 32 MCP-инструмента (12 — для 1С/BSL): индекс по XML-выгрузке конфигурации — структура объектов, формы и обработчики, подписки на события, граф вызовов, права ролей, поиск по коду |
| Живая база | `1c-mcp-toolkit` (`MCP_Toolkit.epf`) | [ROCTUP/1c-mcp-toolkit](https://github.com/ROCTUP/1c-mcp-toolkit) | GPL-3.0 | 304 | MCP + REST API сервер: метаданные и данные живой базы, выполнение запросов. HTTP-сервер поднимается внутри 1С — публикация базы и COM не нужны |

Почему два: код конфигурации читается только из разобранной выгрузки (XML), а данные
требуют канала в живую базу; ни один открытый MCP не закрывает обе задачи сразу.

Опциональные модули (не установлены, выключены):

| Компонент | Репозиторий | Лицензия | ★ | Когда включать |
|---|---|---|---|---|
| `mcp-1c` | [feenlace/mcp-1c](https://github.com/feenlace/mcp-1c) | MIT | 242 | база опубликована на IIS/Apache: 11 инструментов, один бинарник |
| `mcp-rsv-data` | [prepod2003/mcp-rsv-data](https://github.com/prepod2003/mcp-rsv-data) | MIT | 59 | строгий read-only и обезличивание ПДн (Windows, COM) |
| `bsl-language-server` | [1c-syntax/bsl-language-server](https://github.com/1c-syntax/bsl-language-server) | см. репозиторий | — | статический анализ BSL по стандартам (нужна JVM) |

Где что лежит:

* `mcp\code-index-mcp\bsl-indexer.exe` — демон индексации (`127.0.0.1:8015`) и
  MCP-сервер (`http://127.0.0.1:8011/mcp`);
* `mcp\1c-mcp-toolkit\MCP_Toolkit.epf` — открыть в 1С:Предприятие, режим
  «Встроенный сервер» → «Запустить сервер» (порт 6003).

---

## 2. Скиллы: 87 шт., все — вендорские

| Набор | Источник | Лицензия | Скиллов | Зачем |
|---|---|---|---|---|
| Скиллы авторов выбранного MCP | [ROCTUP/1c-mcp-toolkit → `skills/`](https://github.com/ROCTUP/1c-mcp-toolkit/tree/main/skills) | GPL-3.0 | 2 | работа через MCP/REST toolkit: `calling-1c-rest-api-via-curl`, `composing-1c-queries` |
| Разработка 1С | [Nikolay-Shirokov/cc-1c-skills](https://github.com/Nikolay-Shirokov/cc-1c-skills) | MIT (© 2025-2026 Nick Shirokov) | 81 | EPF/ERF, формы, MXL, СКД, роли, XDTO, расширения (CFE), подсистемы, метаданные, базы (`db-*`), публикация на Apache, тесты через веб-клиент |
| Vanessa Automation | [andrejkaxz/Vanessa_for_AI](https://github.com/andrejkaxz/Vanessa_for_AI) | CC BY 4.0 (© 2026 @andrejkaxz) | 2 | `vanessa-feature-authoring` — написание фич, `vanessa-project-bootstrap` — каркас проекта тестов |
| Gherkin-сценарии Vanessa | [shevchenko-dl/va-ai-autotests](https://github.com/shevchenko-dl/va-ai-autotests) | MIT | 1 | `va-scenario-generator` — Turbo Gherkin, доводка записи рекордера, справочник шагов; работает через MCP Vanessa |
| Аналитика: ТЗ/ФТ/ФД | [gsulamanidzebdoge/product-analyst](https://github.com/gsulamanidzebdoge/product-analyst) | MIT | 1 | `product-analyst` — ТЗ/ЧТЗ/SRS (ГОСТ 34.602, ISO/IEC/IEEE 29148), реестр требований, FIT/GAP, анализ 1С:ERP |

Складываются как есть, файлы не правятся. Обязательная атрибуция CC BY 4.0 для
`Vanessa_for_AI` — в `skills-vendor\SOURCES.md`.

Чем закрываются типовые задачи:

| Задача | Скиллы |
|---|---|
| Понять, что делает нажатая кнопка | `form-info`, `form-edit`, `interface-*` + MCP-инструмент `get_form_handlers` (code-index) |
| Написать запрос | `composing-1c-queries` (MCP/REST toolkit), `skd-*` (СКД) |
| Gherkin-сценарий для Vanessa | `va-scenario-generator`, `vanessa-feature-authoring` |
| Доработать конфигурацию по ТЗ | `cfe-*` (расширения), `meta-*`, `form-*`, `role-*`, `skd-*`, `cf-edit`, `support-edit` |
| Написать ТЗ (ФТ/ФД) по БФТ | `product-analyst` (опирается на выгрузку в `dump\` и MCP-метаданные) |

Группы набора `cc-1c-skills` (как у автора): `epf-*`, `erf-*`, `form-*`, `meta-*`,
`mxl-*`, `skd-*`, `role-*`, `xdto-*`, `interface-*`, `subsystem-*`, `cfe-*`, `cf-*`,
`db-*`, `web-*`, `support-edit`, `template-add/remove`, `help-add`, `img-grid`,
`v8-xsd-fetch`.

---

## 3. Порядок установки

Нужно: Windows, PowerShell 5.1, платформа 1С 8.3 (Конфигуратор), VS Code + Cline
(или Cline CLI), ~20 ГБ свободного места на диске.

```powershell
cd C:\w\1c\агент

.\scripts\install-mcp.ps1            # 1. скачать MCP: code-index-mcp + 1c-mcp-toolkit
.\scripts\install-vendor-skills.ps1  # 2. скачать вендорские скиллы и документацию
.\scripts\fix-encoding.ps1           # 3. .ps1 -> UTF-8 с BOM (для PowerShell 5.1)
.\scripts\setup-code-index.ps1       # 4. демон индексации + MCP-сервер (ждём [ready])
.\scripts\install-skills.ps1         # 5. разложить скиллы для Cline
```

Шаг 4 индексирует папку `dump\`. Выгрузку конфигурации делают **вендорские скиллы**
(`db-dump-xml`, `db-dump-cf`), а не наш код: выгружайте в `C:\w\1c\агент\dump`. Если
папка другая — поправьте `[[paths]] path` в `mcp\code-index-mcp\daemon.toml` и вызовите
`bsl-indexer.exe daemon reload`.

Дальше:

6. MCP в Cline: блок из `mcp\cline_mcp_settings.example.json` → в файл настроек
   (CLI: `~/.cline/data/settings/cline_mcp_settings.json`; IDE: MCP Servers →
   Configure → Configure MCP Servers), затем перезапустить Cline.
7. Слой живой базы (по желанию): открыть `mcp\1c-mcp-toolkit\MCP_Toolkit.epf` →
   «Встроенный сервер» → «Запустить сервер»; в настройках Cline снять
   `"disabled": true` у сервера `1c-toolkit`.

Проверка:

```powershell
.\mcp\code-index-mcp\bsl-indexer.exe daemon status    # у папки dump должно быть [ready]
```

и в Cline: Skills → вкладка Skills → в списке 87 скиллов.

---

## 4. Как пользоваться скиллами в Cline

Откуда Cline читает скиллы (документация Cline → Config):

* глобально: `~/.cline/skills` (на этой машине `C:\Users\kraft\.cline\skills`);
* в проекте: `<проект>\.cline\skills` —
  `.\scripts\install-skills.ps1 -Scope Project -ProjectDir <путь>`;
* скилл = каталог с `SKILL.md`; поле `name` во frontmatter совпадает с именем каталога.

Как вызвать: панель Cline → иконка **Skills** → вкладка **Skills** → включить нужные;
затем в чате `/имя-скилла` (например `/db-dump-xml`, `/epf-build`,
`/va-scenario-generator`) либо просто описать задачу — Cline подберёт скилл по полю
`description`.

Особенности наборов (их писали под Claude Code — отсюда нюансы):

* `${CLAUDE_SKILL_DIR}` в командах запуска скриптов — в Cline подставляйте абсолютный
  путь к каталогу скилла, например
  `C:\Users\kraft\.cline\skills\epf-init\scripts\init.ps1`;
* поле `allowed-tools` во frontmatter Cline не использует;
* наборы опираются на проектные файлы-конвенции авторов — прежде всего
  `.v8-project.json` (реестр баз): `skills-vendor\cc-1c-skills\docs\v8-project-guide.md`;
* спецификации форматов (EPF, ERF, форм, справки, ролей, СКД, MXL, XDTO, подсистем,
  расширений, пакетный режим конфигуратора) — в `skills-vendor\cc-1c-skills\docs\`;
* справка по шагам/формам Vanessa — в `skills-vendor\va-ai-autotests\` и
  `skills-vendor\Vanessa_for_AI\knowledge\`.

---

## 5. Перенос всего стека на другую машину (Cline)

1. Скопировать папку `C:\w\1c\агент`. Тяжёлое можно не тащить: `dump\`, `logs\`,
   `mcp\code-index-mcp\bsl-indexer.exe` — скачается заново скриптом.
2. Установить VS Code + Cline, платформу 1С 8.3, развернуть базу.
3. `.\scripts\install-mcp.ps1` → `.\scripts\install-vendor-skills.ps1` →
   `.\scripts\fix-encoding.ps1`.
4. Заполнить `.v8-project.json` (реестр баз для вендорских скиллов; формат —
   `skills-vendor\cc-1c-skills\docs\v8-project-guide.md`).
5. Выгрузить конфигурацию в `dump\` вендорским скиллом `db-dump-xml`, затем
   `.\scripts\setup-code-index.ps1` и дождаться статуса `[ready]`.
6. `.\scripts\install-skills.ps1` (глобально) и/или `-Scope Project`.
7. Прописать `mcpServers` в `~/.cline/data/settings/cline_mcp_settings.json` (путь
   переопределяется переменной `CLINE_MCP_SETTINGS_PATH`), перезапустить Cline.
8. Автозапуск демона и MCP-сервера: ярлык на `.\scripts\start-code-index.ps1` в папку
   `shell:startup` (Win+R → `shell:startup`).

Что придётся поправить на новой машине: букву диска и `$HOME` — в
`mcp\code-index-mcp\daemon.toml` (`[[paths]] path`) и в настройках MCP Cline (URL
`http://127.0.0.1:8011/mcp` не меняется).

### Как перенести сам репозиторий

Репозиторий инициализирован (`git init`, ветка `main`). Выгрузка `dump/`, логи,
бинарники MCP и `.epf` в него не попадают — см. `.gitignore`. Два способа переноса:

* **через remote** (GitHub/GitLab): `git remote add origin <url>` → `git push -u origin main`,
  на новой машине `git clone <url>`;
* **локально, без сети**: `git bundle create repo.bundle --all`, перенести файл и на новой
  машине `git clone repo.bundle "<папка>"`.

После клонирования порядок тот же: `scripts\install-mcp.ps1` →
`install-vendor-skills.ps1` → `fix-encoding.ps1` → выгрузка в `dump\` →
`setup-code-index.ps1` → `install-skills.ps1`.

---

## 6. Эксплуатация

| Что | Значение |
|---|---|
| Демон индексации | `bsl-indexer.exe daemon run` (единственный писатель индекса) |
| MCP-сервер кода | `bsl-indexer.exe serve --transport http --port 8011 --config daemon.toml` |
| Оба процесса сразу | `.\scripts\start-code-index.ps1` (скрыто, для автозапуска) |
| Статус / логи | `bsl-indexer.exe daemon status`; `mcp\code-index-mcp\daemon.log`, `serve.log` |
| Порты | демон `8015`, MCP `8011`; слой данных `.epf` — `6003` |
| Скиллы | `~/.cline/skills` (глобально) и `<проект>/.cline/skills` |
| Диск | выгрузка — гигабайты, индекс `.code-index\index.db` крупной конфигурации — несколько ГБ. Если место кончилось, выгрузка обрывается: проверяйте `dump\Configuration.xml` и строки `WARN parse_configuration_file` в `daemon.log` |

---

## 7. Границы проекта (что здесь специально отсутствует)

* **Нет скиллов, написанных агентом.** Только вендорские наборы; если возможностей
  не хватает — ищем и добавляем набор с GitHub (см. `skills-vendor\SOURCES.md`), а не
  пишем свой.
* **Нет собственных 1С-скриптов** (dump/load/update/check/run). Они удалены как
  дублирующие вендорские скиллы: выгрузка/загрузка CF·XML·DT, обновление и запуск —
  это `db-*`, проверка/создание объектов — `meta-verify`/`*-validate`, запуск
  предприятия — `db-run`. В `scripts\` остались только скрипты инфраструктуры MCP и
  скиллов.

Дополнительно: архитектура — `docs\01-architecture.md`, диагностика —
`docs\04-troubleshooting.md`, границы возможностей — `docs\07-capabilities-and-limits.md`.

