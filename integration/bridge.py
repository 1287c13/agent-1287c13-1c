import os
import subprocess
import sys
import time
import urllib.parse

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from transport import cline
from transport.store import write_text_atomic

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
3. Запиши результат на сервер:
   py -3 integration\\agent.py --write-result --task %(id)s --file "%(answer_file)s"

Пока результат не записан, задача остаётся в работе, а отправитель видит стадию
delivered. Ответ в чате отправителю не виден: читается только с сервера.
"""


def build_prompt_text(task, work_dir):
    return DEFAULT_TEMPLATE % {
        'id': task['id'],
        'client': task.get('client') or 'неизвестен',
        'created_at': task.get('created_at') or '',
        'mode': task.get('mode') or 'db',
        'prompt': task.get('prompt') or task.get('action') or '',
        'answer_file': os.path.join(work_dir, 'answer.md'),
    }


def build_uri(text):
    return URI_TASK + urllib.parse.quote(text or '', safe='')


def short_uri_text(task, prompt_path, answer_path):
    return ('Задача интеграции %s. Формулировка и порядок завершения: %s. '
            'Файл ответа: %s. Записать результат: py -3 integration\\agent.py '
            '--write-result --task %s --file "%s"'
            % (task['id'], prompt_path, answer_path, task['id'], answer_path))


def build_command_line(uri):
    if os.name == 'nt':
        return 'start "" "%s"' % uri
    return 'xdg-open "%s"' % uri


def open_uri(uri):
    try:
        if os.name == 'nt':
            os.startfile(uri)
            return True, 'startfile', 'ссылка передана оболочке Windows'
        if sys.platform == 'darwin':
            subprocess.Popen(['open', uri])
            return True, 'open', 'ссылка передана open'
        subprocess.Popen(['xdg-open', uri])
        return True, 'xdg-open', 'ссылка передана xdg-open'
    except OSError as exc:
        return False, 'ошибка', str(exc)


def deliver(task, work_dir, mode='uri', allow_gui=True, confirm_timeout=None, attempts=3,
            cline_data=None, cline_work_dir=None):
    if mode not in MODES:
        mode = 'uri'
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    prompt_path = os.path.join(work_dir, 'prompt.txt')
    answer_path = os.path.join(work_dir, 'answer.md')
    write_text_atomic(prompt_path, build_prompt_text(task, work_dir))

    result = {
        'mode': mode,
        'status': 'delivered',
        'prompt_file': prompt_path,
        'answer_file': answer_path,
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
        return result

    uri = build_uri(short_uri_text(task, prompt_path, answer_path))
    result['uri'] = uri
    result['command_line'] = build_command_line(uri)
    if mode == 'manual':
        result['cline_note'] = 'режим manual: ссылку открывает человек, подтверждения нет'
        result['message'] = 'режим manual: URI открывает человек строкой запуска'
        return result
    if not allow_gui:
        result['message'] = 'передача оболочке отключена флагом --no-gui: URI не открыт'
        return result

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
        result['message'] = ('%s. Формулировка: %s - вставьте её в чат Cline вручную'
                             % (result['message'], prompt_path))
    return result
