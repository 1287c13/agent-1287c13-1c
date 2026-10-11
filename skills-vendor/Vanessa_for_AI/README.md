# Vanessa_for_AI

Правила, Agent Skills и автономный каталог шагов для разработки сценариев [Vanessa Automation](https://github.com/Pr-Mex/vanessa-automation) с помощью Codex, Claude Code, OpenCode и других ИИ-агентов.

> [!IMPORTANT]
> Проект не использует и не требует MCP. Агент работает с файлами проекта, локальным каталогом шагов и материалами пользователя, но не получает доступ к интерфейсу 1С или Vanessa Automation.

Репозиторий не содержит сценариев конкретной конфигурации 1С. Он задаёт переносимый рабочий процесс: пользователь передаёт запись действий Vanessa Automation или проверенный аналог, агент исследует структуру проекта, согласует её при необходимости и только затем создаёт или изменяет сценарии.

## Что входит

- `AGENTS.md` — общие правила для Codex, OpenCode и других агентов.
- `CLAUDE.md` — подключение тех же правил в Claude Code.
- `vanessa-project-bootstrap` — skill для согласования структуры чистого проекта.
- `vanessa-feature-authoring` — skill для создания, проверки и диагностики Turbo Gherkin.
- `knowledge/vanessa-automation/steps-library.json` — автономный справочник стандартных шагов Vanessa Automation.
- `tools/build_steps_catalog.py` — воспроизводимая сборка справочника из локального checkout Vanessa Automation.

## Предпосылки

До начала работы должны быть установлены и настроены:

1. платформа 1С:Предприятие;
2. Vanessa Automation;
3. TestClient и тестовая информационная база;
4. один из поддерживаемых ИИ-агентов.

Этот репозиторий не устанавливает Vanessa Automation, не запускает 1С и не подключается к тестовой базе. Официальные инструкции находятся в [документации Vanessa Automation](https://pr-mex.github.io/vanessa-automation/dev/).

## Быстрый старт: новый проект

1. Создайте проект из этого GitHub Template или клонируйте репозиторий.
2. Откройте корень проекта в выбранном агенте.
3. Передайте бизнес-цель, ожидаемые проверки и запись Vanessa Automation либо проверенный аналог.
4. Если структуры ещё нет, попросите агента сначала применить `vanessa-project-bootstrap`.
5. Согласуйте предложенное дерево каталогов.
6. Попросите создать сценарий с помощью `vanessa-feature-authoring`.
7. Запустите сценарий в Vanessa Automation и верните агенту результат или диагностику.

Пример запроса:

```text
Проект пока пуст. Используй skill vanessa-project-bootstrap, предложи минимальную
структуру и дождись моего подтверждения. После этого используй
vanessa-feature-authoring. Цель проверки: <цель>. Вот запись Vanessa: <запись>.
```

## Подключение к существующему проекту

Скопируйте в корень проекта:

- `AGENTS.md` или аккуратно объедините его с существующими правилами;
- `CLAUDE.md`, если используется Claude Code;
- `.agents/skills/`;
- `.claude/skills/`, если используется Claude Code;
- `knowledge/vanessa-automation/`.

Не заменяйте существующие проектные правила вслепую. Ближайшие к сценариям README и локальные соглашения должны сохранять приоритет.

## Совместимость

| Агент | Правила | Skills | Явный вызов |
|---|---|---|---|
| Codex | `AGENTS.md` | `.agents/skills/` | `$vanessa-feature-authoring` |
| Claude Code | `CLAUDE.md` → `AGENTS.md` | `.claude/skills/` | `/vanessa-feature-authoring` |
| OpenCode | `AGENTS.md` | `.agents/skills/` | через skill tool или по описанию задачи |
| Другие Agent Skills-клиенты | согласно клиенту | открытый формат `SKILL.md` | согласно клиенту |

Формат skills соответствует [Agent Skills Specification](https://agentskills.io/specification). Пути проверены по документации [Codex](https://learn.chatgpt.com/docs/build-skills), [Claude Code](https://code.claude.com/docs/en/skills) и [OpenCode](https://opencode.ai/docs/skills/).

## Как агент выбирает источник

Источники применяются в таком порядке:

1. запись пользователя из текущего окружения;
2. runtime-проверенный сценарий текущего проекта;
3. каталог шагов, собранный для версии Vanessa Automation пользователя;
4. встроенный каталог версии `1.2.043.28` как справочный fallback.

Каталог подтверждает синтаксис и наличие стандартного шага в указанной версии. Он не подтверждает заголовки окон, имена элементов и колонок, навигационные ссылки или поведение конкретной конфигурации 1С.

Искать шаги следует точечно, например:

```powershell
rg -n -i 'жду открытия окна' knowledge/vanessa-automation/steps-library.json
```

Сборка каталога для другой версии:

```powershell
python tools/build_steps_catalog.py `
  --source .\vendor\vanessa-automation `
  --version 1.2.043.28 `
  --commit f3a01778a14d29b38204685deea0131274d438ff `
  --output knowledge/vanessa-automation/steps-library.json
```

Скрипт читает исходные BSL-модули. Он не запускает 1С, Vanessa Automation или MCP.

## Ограничения и честный runtime-цикл

- Агент не должен придумывать UI-факты и способы взаимодействия.
- Неизвестная деталь блокирует только затронутые шаги: агент запрашивает минимальную запись или диагностику.
- Создание файла не означает успешный runtime-прогон.
- Пользователь запускает сценарий в Vanessa Automation и возвращает результат агенту.
- В документацию проекта заносятся только факты, подтверждённые текущим окружением.

## Разработка набора

Локальная проверка:

```powershell
python -m unittest discover -s tests -v
python tools/validate_repository.py --distribution
```

Правила вкладов описаны в [CONTRIBUTING.md](CONTRIBUTING.md).

## Лицензии и атрибуция

Оригинальные правила, skills и документация Vanessa_for_AI доступны по лицензии [CC BY 4.0](LICENSE). Каталог шагов производен от Vanessa Automation и сопровождается отдельным уведомлением BSD-3-Clause в [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

При переиспользовании укажите:

> Основано на Vanessa_for_AI автора [@andrejkaxz](https://github.com/andrejkaxz): https://github.com/andrejkaxz/Vanessa_for_AI, лицензия CC BY 4.0. Изменения: \<описание\>.
