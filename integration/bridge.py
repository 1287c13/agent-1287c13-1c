# -*- coding: utf-8 -*-
"""Доставка задачи в Cline: URI-протокол VS Code, вебхук, ручной режим и echo.

Мостик к Cline - встроенный обработчик URI расширения saoudrizwan.claude-dev:

    vscode://saoudrizwan.claude-dev/task?prompt=<текст>

Обработчик создаёт новую задачу Cline с этим текстом, то есть человеку в чат писать
не нужно. Ограничения, из которых следует устройство файла:

- **длина.** URI передаётся через реестр Windows и командную строку, поэтому в нём
  едет только короткая ссылка на файл формулировки, а полный текст лежит в
  queue\\prompts\\prompt_<id>.txt;
- **кодирование.** Пробел обязан быть %20, знак + в URI - литерал, а не пробел:
  текст кодируется quote(safe='') целиком;
- **один сеанс - одна задача.** Cline не ведёт две задачи одновременно, поэтому
  очередь строго последовательная, а следующий шаг начинается после записи
  результата (см. integration\\agent.py).

Режимы (ключ --deliver у agent.py и watcher.py):

    uri      открыть URI - задача создаётся в Cline автоматически (по умолчанию);
    lg-task  то же плюс POST в вебхук Cline, если задан адрес --webhook-url;
    manual   ничего не открывать: напечатать URI и строку запуска - их применяет человек;
    echo     не трогать Cline совсем: только файлы и журналы (проверка цепочки).

Результат delivery - словарь: режим, статус, URI, путь файла формулировки, путь файла
ответа, строка запуска и пояснение. Он попадает в queue\\bridge.jsonl и в итоговый
result_<id>.json.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from transport.store import now_iso, write_text_atomic  # noqa: E402

URI_TASK = 'vscode://saoudrizwan.claude-dev/task?prompt='
MODES = ('uri', 'lg-task', 'manual', 'echo')
DEFAULT_TEMPLATE = """Задача внешней очереди %(id)s
Отправитель: %(client)s, создана %(created_at)s, режим %(mode)s.
Формулировка (формат контракта):
%(prompt)s

Завершение задачи:
1. Выполни формулировку как обычную задачу протокола START.md: преамбула, слои,
   проверка, отчёт.
2. Заполни файл ответа %(answer_file)s - строки Слой:, MCP:, Скиллы:, Проверка:,
   Сделано:, Не проверено:, ниже текст ответа.
3. Запиши результат в очередь:
   py -3 integration\\agent.py --write-result --task %(id)s --file "%(answer_file)s"

Пока результат не записан, задача остаётся в queue\\processing, а отправитель видит
состояние processing. Ответ в чате отправителю не виден: читается только из очереди.
"""


def build_prompt_text(task, store):
    """Полный текст задачи для Cline: формулировка, файл ответа и команда записи."""
    return DEFAULT_TEMPLATE % {
        'id': task['id'],
        'client': task.get('client') or 'неизвестен',
        'created_at': task.get('created_at') or '',
        'mode': task.get('mode') or 'db',
        'prompt': task.get('prompt') or '',
        'answer_file': store.rel(store.answer_path(task['id'])),
    }


def short_uri_text(task, prompt_rel):
    """Короткий текст для URI: ссылка на файл плюс напоминание про протокол."""
    return 'Задача %s из внешней очереди. Полный текст: %s. Выполни по START.md.' % (
        task['id'], prompt_rel)


def build_uri(text):
    """URI расширения Cline. Кодирование quote(safe=''): пробел - %20, плюс - %2B."""
    return URI_TASK + urllib.parse.quote(text, safe='')


def build_command_line(uri):
    """Строка запуска для режима manual: то, что человек вставит в терминал."""
    return 'code --open-url "%s"' % uri


def post_webhook(url, payload, timeout=10):
    """POST в вебхук Cline. Возвращает (успех, пояснение). Молчащий хост - не сбой очереди."""
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    request = urllib.request.Request(url, data=body,
                                     headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 300, 'вебхук ответил %s' % response.status
    except urllib.error.URLError as exc:
        return False, 'вебхук недоступен: %s' % exc
    except OSError as exc:
        return False, 'вебхук: ошибка соединения: %s' % exc


def deliver(task, mode, store, webhook_url=None, allow_gui=True):
    """Передать задачу в Cline выбранным режимом. Возвращает словарь доставки."""
    if mode == 'auto' or mode not in MODES:
        mode = 'uri'
    store.ensure()
    prompt_path = os.path.join(store.dirs['prompts'], 'prompt_%s.txt' % task['id'])
    write_text_atomic(prompt_path, build_prompt_text(task, store))
    prompt_rel = store.rel(prompt_path)
    result = {
        'mode': mode,
        'status': 'delivered',
        'prompt_file': prompt_rel,
        'answer_file': store.rel(store.answer_path(task['id'])),
        'uri': '',
        'command_line': '',
        'message': '',
    }

    if mode == 'echo':
        result['message'] = 'режим echo: Cline не вызывается, проверяется файловая цепочка'
    else:
        uri = build_uri(short_uri_text(task, prompt_rel))
        result['uri'] = uri
        result['command_line'] = build_command_line(uri)
        if mode == 'manual':
            result['message'] = 'режим manual: URI открывает человек строкой запуска'
        elif not hasattr(os, 'startfile'):
            result['status'] = 'error'
            result['message'] = 'режим %s требует Windows: os.startfile недоступен' % mode
        elif not allow_gui:
            result['message'] = 'передача оболочке отключена флагом --no-gui: URI не открыт'
        else:
            try:
                os.startfile(uri)
                result['message'] = 'URI передан оболочке Windows'
            except Exception as exc:  # отказ ассоциации протокола - тоже сбой доставки
                result['status'] = 'error'
                result['message'] = 'не удалось открыть URI: %s' % exc
        if mode == 'lg-task':
            if webhook_url:
                ok, message = post_webhook(webhook_url, {'prompt': task.get('prompt') or '',
                                                         'taskId': task['id']})
                result['webhook_ok'] = ok
                result['message'] = '%s; %s' % (result['message'], message)
            else:
                result['webhook_ok'] = False
                result['message'] = '%s; вебхук не задан (--webhook-url): режим равен uri' % result['message']

    record = dict(result)
    record['event'] = 'deliver'
    record['task_id'] = task['id']
    record['delivered_at'] = now_iso()
    store.log_bridge(record)
    return result
