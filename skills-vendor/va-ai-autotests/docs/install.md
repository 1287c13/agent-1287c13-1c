# Установка и настройка

## Что нужно

- 1С:Предприятие 8.3 / 8.5 и тестируемая база (клиент тестирования).
- [Vanessa Automation](https://github.com/Pr-Mex/vanessa-automation) с MCP-сервером (проверено на 1.2.043.42) и расширение VAExtension той же версии в базе клиента тестирования.
- Расширение `client_mcp` из [onec-client-mcp-devkit](https://github.com/1c-neurofish/onec-client-mcp-devkit) в базе менеджера тестирования (проверено на 0.6.5).
- В обоих расширениях снять защиту от опасных действий и безопасный режим.
- Claude Code (CLI или расширение VS Code).

Менеджер и клиент тестирования лучше держать в разных базах: так базу клиента можно восстанавливать из выгрузки перед прогоном.

## Skill

Скопируйте папку `skill/va-scenario-generator` в одно из мест:

- `<проект>/.claude/skills/va-scenario-generator/` — только для этого проекта;
- `~/.claude/skills/va-scenario-generator/` — для всех проектов.

Проверка: в новой сессии спросите агента, какие skills ему доступны.

## MCP-сервер VA

1. Файл настроек сервера, например `mcp.json`:

   ```json
   { "port": 9874, "timeout": 1800 }
   ```

2. Запуск VA в режиме менеджера тестирования с MCP:

   ```
   "C:\Program Files\1cv8\<версия>\bin\1cv8c.exe" ENTERPRISE /TESTMANAGER /F "<база менеджера>" /Execute "<путь>\vanessa-automation.epf" /C "runMcp=<путь>\mcp.json"
   ```

3. В рабочем каталоге Claude Code — `.mcp.json`:

   ```json
   { "mcpServers": { "VA": { "type": "http", "url": "http://localhost:9874/mcp" } } }
   ```

4. В VA подключите клиента тестирования и откройте любую фичу (без открытой фичи `get_vanessa_automation_state` падает). В Claude Code проверьте `/mcp`.

## Разрешения по этапам (`.claude/settings.local.json`)

Генерация A и доводка C+ — без MCP (в каталоге нет `.mcp.json`):

```json
{ "permissions": { "allow": ["Read","Edit","Write","Glob","Grep","Bash","PowerShell","Skill"], "deny": ["mcp__VA"], "defaultMode": "acceptEdits" } }
```

Прогон A — только синтаксис, прогон и результаты, без интроспекции формы:

```json
{ "permissions": {
    "allow": ["mcp__VA__get_vanessa_automation_state","mcp__VA__open_feature_file","mcp__VA__check_syntax","mcp__VA__run_scenario","mcp__VA__get_test_results","mcp__VA__get_window_screenshot_os","mcp__VA__window_management","mcp__VA__manage_test_client","Read","Edit","Write","Bash","PowerShell"],
    "deny": ["mcp__VA__get_form_analysis","mcp__VA__get_object_attributes","mcp__VA__get_table_data","mcp__VA__manage_form_elements","mcp__VA__execute_form_actions","mcp__VA__user_actions_recording","mcp__VA__search_for_steps_by_keywords","mcp__VA__frequently_used_steps","mcp__VA__get_data_from_knowledge_base","mcp__VA__get_form_element_data","mcp__VA__get_active_window_data","Skill"],
    "defaultMode": "acceptEdits" },
  "enabledMcpjsonServers": ["VA"] }
```

Вариант B — все инструменты VA, без skills:

```json
{ "permissions": { "allow": ["mcp__VA","Read","Edit","Write","Glob","Grep","Bash","PowerShell"], "deny": ["Skill"], "defaultMode": "acceptEdits" }, "enabledMcpjsonServers": ["VA"] }
```

Прогон C+ — все инструменты VA, кроме записи действий:

```json
{ "permissions": { "allow": ["mcp__VA","Read","Edit","Write","Glob","Grep","Bash","PowerShell"], "deny": ["mcp__VA__user_actions_recording"], "defaultMode": "acceptEdits" }, "enabledMcpjsonServers": ["VA"] }
```

Правила `deny` действуют в любом режиме разрешений. После смены настроек откройте новую сессию Claude Code.
