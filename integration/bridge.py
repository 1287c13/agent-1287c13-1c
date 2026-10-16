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

    uri      открыть URI - задача создаётся в Cline (по умолчанию);
    manual   ничего не открывать: напечатать URI и строку запуска - их применяет человек;
    echo     не трогать Cline совсем: только файлы и журналы (проверка цепочки).

Доставка не заканчивается открытием ссылки. Обработчик URI у Cline работает только при
видимой панели Cline (`getVisibleInstance` в расширении), поэтому «ссылка принята
оболочкой» - не результат. После открытия задача ищется в журнале сессий Cline
(transport\\cline.py): появилась сессия с идентификатором задачи - доставка
подтверждена; не появилась - попытка повторяется (открытие панели и повтор дают ей
шанс пройти), а в итоге отправитель получает явное «не подтверждено» и путь к файлу
формулировки, чтобы вставить текст в чат руками.

Результат delivery - словарь: режим, статус, URI, путь файла формулировки, путь файла
ответа, строка запуска, число попыток, признак подтверждения, сессия Cline и пояснение.
Он попадает в queue\\bridge.jsonl и в итоговый result_<id>.json.
"""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from transport import cline  # noqa: E402
from transport.store import now_iso, write_text_atomic  # noqa: E402

URI_TASK = 'vscode://saoudrizwan.claude-dev/task?prompt='
MODES = ('uri', 'manual', 'echo')
DEFAULT_CONFIRM_S = 12.0
RETRY_PAUSE_S = 3.0

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


def open_uri(uri):
    """Открыть URI задачи. Возвращает (успех, чем_открывали, пояснение).

    Основной путь - ассоциация протокола Windows (`os.startfile`): на этой машине
    `vscode://` зарегистрирован как `Code.exe --open-url`. Второй путь - команда `code`
    (для систем без os.startfile). Успех означает только «ссылка принята»: создана ли
    задача, показывает подтверждение в transport\\cline.py.
    """
    if hasattr(os, 'startfile'):
        try:
            os.startfile(uri)
            return True, 'os.startfile', 'URI передан оболочке Windows'
        except OSError as exc:
            first_error = 'os.startfile: %s' % exc
    else:
        first_error = 'os.startfile недоступен (не Windows)'
    code = shutil.which('code')
    if code:
        try:
            done = subprocess.run([code, '--open-url', uri], capture_output=True, timeout=30)
            if done.returncode == 0:
                return True, 'code --open-url', 'VS Code принял ссылку'
            tail = (done.stderr or b'').decode('utf-8', 'replace').strip()[:200]
            return False, 'code --open-url', 'code ответил %s: %s' % (done.returncode, tail)
        except (OSError, subprocess.SubprocessError) as exc:
            return False, 'code --open-url', 'code не запустился: %s' % exc
    return False, 'нет', 'открыть URI нечем: %s; команда code не найдена' % first_error



def deliver(task, mode, store, allow_gui=True, attempts=3, confirm_timeout=None,
            cline_data=None, cline_work_dir=None):
    """Передать задачу в Cline выбранным режимом. Возвращает словарь доставки.

    Режим uri открывает ссылку и ждёт подтверждения: обработчик URI у Cline работает
    только при видимой панели Cline, поэтому попытка повторяется - панель открывается
    первой же ссылкой. Режим manual ссылку не открывает (её применяет человек), echo
    не трогает Cline вовсе.
    """
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
        'attempts': 0,
        'confirmed': False,
        'cline_session': '',
        'cline_note': '',
        'opened_with': '',
    }

    if mode == 'echo':
        result['message'] = 'режим echo: Cline не вызывается, проверяется файловая цепочка'
    else:
        uri = build_uri(short_uri_text(task, prompt_rel))
        result['uri'] = uri
        result['command_line'] = build_command_line(uri)
        if mode == 'manual':
            result['cline_note'] = 'режим manual: ссылку открывает человек, подтверждения нет'
            result['message'] = 'режим manual: URI открывает человек строкой запуска'
        elif not allow_gui:
            result['message'] = 'передача оболочке отключена флагом --no-gui: URI не открыт'
        else:
            timeout = DEFAULT_CONFIRM_S if confirm_timeout is None else float(confirm_timeout)
            total = max(1, int(attempts or 1))
            since = cline.now_utc()
            for attempt in range(1, total + 1):
                result['attempts'] = attempt
                opened, how, note = open_uri(uri)
                result['opened_with'] = how
                if not opened:
                    result['status'] = 'error'
                    result['message'] = 'ссылка не открыта (%s): %s' % (how, note)
                    break
                session, cline_note = cline.wait_for_task(task['id'], timeout, since=since,
                                                          directory=cline_data,
                                                          work_dir=cline_work_dir)
                result['cline_note'] = cline_note
                if session:
                    result['confirmed'] = True
                    result['cline_session'] = session.get('session_id') or ''
                    result['message'] = 'задача создана в Cline: сессия %s (%s)' % (
                        result['cline_session'] or 'идентификатор не прочитан', how)
                    break
                result['message'] = ('ссылка открыта (%s), но задача в Cline не появилась: '
                                     'панель Cline должна быть открыта в окне VS Code' % how)
                if attempt < total:
                    time.sleep(RETRY_PAUSE_S)
            if result['status'] != 'error' and not result['confirmed']:
                result['message'] = ('%s. Формулировка: %s - вставьте её в чат Cline вручную '
                                     'или повторите доставку (integration\\agent.py '
                                     '--redeliver --task %s)'
                                     % (result['message'], prompt_rel, task['id']))

    record = dict(result)
    record['event'] = 'deliver'
    record['task_id'] = task['id']
    record['delivered_at'] = now_iso()
    store.log_bridge(record)
    if result['status'] == 'delivered' and not result['confirmed'] and mode != 'manual':
        store.log_bridge({'event': 'deliver_unconfirmed', 'task_id': task['id'],
                          'attempts': result['attempts'], 'message': result['message']})
    return result
