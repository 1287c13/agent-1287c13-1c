# -*- coding: utf-8 -*-
"""Задача внешней интеграции: сборка из слотов, проверка формы и разрешение базы.

Проверка разделена по машинам, потому что разделены знания:

    validate_shape (сервер)   слоты, режим, отправитель, режим доставки. База
                              сверяется с server.databases из deploy\\config.json -
                              это перечисление для формы, а не путь к базе;
    validate_task  (агент)    смысл задачи на машине харнесса: слот <база>
                              разрешается по .v8-project.json, чтобы агент и не
                              начинал работу с несуществующей базой.

Формулировка контракта строится одной функцией build_prompt - и сервер, и
командная строка, и агент дают один и тот же текст задачи.
"""

import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from transport.config import project_root  # noqa: E402
from transport.schema import format_errors, read_schema, validate  # noqa: E402
from transport.store import DEFAULT_TIMEOUT_S, host_name, new_task_id, now_iso  # noqa: E402

MODES = ('db', 'harness')
DELIVER_MODES = ('uri', 'manual', 'echo', 'auto')
DBS_FILE = '.v8-project.json'

PROMPT_DB = 'как {role} сделай {action} в базе {db} чтобы {goal} по START.md'
PROMPT_DB_SHORT = 'как {role} сделай {action} в базе {db} по START.md'
PROMPT_HARNESS = 'как инженер харнесса сделай {action} чтобы {goal} по START.md'
PROMPT_HARNESS_SHORT = 'как инженер харнесса сделай {action} по START.md'


def one_line(text):
    """Формулировка задачи - одна строка: переводы строк и кратные пробелы схлопываются."""
    text = (text or '').replace('\r', ' ').replace('\n', ' ')
    return re.sub(r'\s{2,}', ' ', text).strip()


def build_prompt(role, action, goal, db=None, mode='db'):
    """Текст задачи в формате контракта.

    Для mode='harness' слот базы не ставится. Пустая цель - не ошибка: формулировка
    тогда заканчивается действием, а не оборванным «чтобы».
    """
    action = one_line(action)
    goal = one_line(goal)
    if mode == 'harness':
        if goal:
            return PROMPT_HARNESS.format(action=action, goal=goal)
        return PROMPT_HARNESS_SHORT.format(action=action)
    if goal:
        return PROMPT_DB.format(role=one_line(role), action=action, db=one_line(db), goal=goal)
    return PROMPT_DB_SHORT.format(role=one_line(role), action=action, db=one_line(db))


def make_task(role, action, goal, db=None, mode='db', source='http', deliver='auto',
              timeout_s=DEFAULT_TIMEOUT_S, note=None, client=None, task_id=None):
    """Собрать задачу: идентификатор, время, отправитель, формулировка контракта."""
    mode = mode if mode in MODES else 'db'
    if mode == 'harness':
        db = None
    task = {
        'id': task_id or new_task_id(),
        'created_at': now_iso(),
        'source': source,
        'client': client or host_name(),
        'mode': mode,
        'role': one_line(role),
        'action': one_line(action),
        'db': db or None,
        'prompt': build_prompt(role, action, goal, db, mode),
        'deliver': deliver if deliver in DELIVER_MODES else 'auto',
        'timeout_s': int(timeout_s),
    }
    if one_line(goal):
        task['goal'] = one_line(goal)
    if note:
        task['note'] = one_line(note)
    return task


def task_schema(root):
    """Схема задачи из integration\\schemas."""
    return read_schema(os.path.join(project_root(root), 'integration', 'schemas',
                                    'task_schema.json'))


def validate_shape(cfg, payload, client):
    """Проверить форму задачи на сервере. Возвращает (задача, список ошибок).

    Форму присылает браузер или внешний клиент: слоты контракта, режим и необязательный
    режим доставки. Идентификатор, время, отправитель и формулировку присваивает сервер -
    клиент их не задаёт, иначе он мог бы подменить отправителя в журнале.
    """
    if not isinstance(payload, dict):
        return None, ['тело запроса должно быть объектом JSON']
    client = client or {}
    mode = payload.get('mode') if payload.get('mode') in MODES else 'db'
    task = make_task(
        payload.get('role') or 'программист 1С',
        payload.get('action'),
        payload.get('goal'),
        payload.get('db') if mode == 'db' else None,
        mode=mode,
        source='http',
        deliver=payload.get('deliver') if payload.get('deliver') in DELIVER_MODES else 'auto',
        timeout_s=payload.get('timeout_s') or DEFAULT_TIMEOUT_S,
        note=payload.get('note'),
        client=client.get('name') or None,
    )
    errors = list(validate(task, task_schema(cfg.get('project_root')), 'задача'))

    if mode == 'harness':
        if not client.get('allow_harness'):
            errors.append('режим harness: клиенту «%s» задачи по инструменту агента не разрешены'
                          % (client.get('name') or '?'))
    else:
        if not task.get('db'):
            errors.append('режим db: не заполнен слот базы')
        else:
            known = [str(x).strip().lower() for x in
                     (cfg.get('server') or {}).get('databases') or []]
            if known and task['db'].strip().lower() not in known:
                errors.append('режим db: базы «%s» нет в server.databases (%s)'
                              % (task['db'], ', '.join(known)))
    return task, errors



def validate_task(root, raw):
    """Проверить задачу на машине агента: схема плюс разрешение слота <база>.

    Здесь и только здесь есть .v8-project.json, поэтому только здесь проверяется,
    что база существует. Ошибка означает, что задачу нельзя выполнять: агенту
    нечего открывать.
    """
    task = normalize_task(raw)
    errors = list(validate(task, task_schema(root), 'задача'))
    if task.get('mode') == 'db':
        if not task.get('db'):
            errors.append('режим db: не заполнен слот базы')
        else:
            entry, message = resolve_db(root, task['db'])
            if entry is None:
                errors.append('режим db: %s' % message)
    return task, errors


def normalize_task(raw):
    """Достроить поля, которые агент мог получить не полностью. Исходный словарь не меняется."""
    task = dict(raw or {})
    task.setdefault('id', new_task_id())
    task.setdefault('created_at', now_iso())
    task.setdefault('source', 'http')
    task['mode'] = task.get('mode') if task.get('mode') in MODES else 'db'
    if task['mode'] == 'harness':
        task['db'] = None
    for name in ('role', 'action', 'goal', 'db', 'prompt', 'note'):
        if isinstance(task.get(name), str):
            task[name] = one_line(task[name])
    if not task.get('goal'):
        task.pop('goal', None)
    if not task.get('prompt') and task.get('action'):
        task['prompt'] = build_prompt(task.get('role') or 'инженер харнесса',
                                      task['action'], task.get('goal'), task.get('db'),
                                      task['mode'])
    if task.get('deliver') not in DELIVER_MODES:
        task['deliver'] = 'auto'
    if not task.get('timeout_s'):
        task['timeout_s'] = DEFAULT_TIMEOUT_S
    return task


def load_databases(root):
    """Записи баз из .v8-project.json. Пустой список - файла нет или он нечитаем."""
    path = os.path.join(project_root(root), DBS_FILE)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (ValueError, OSError):
        return []
    return list(config.get('databases') or [])


def resolve_db(root, value):
    """Найти запись базы по id, имени, алиасу или пути.

    Возвращает пару (запись_или_None, пояснение). Отправитель задачу по этому правилу
    не отклоняет: список баз у сервера - перечисление для формы, а путь к базе есть
    только на машине агента.
    """
    if not value:
        return None, 'слот базы пуст'
    probe = one_line(value)
    if probe.lower().startswith('file='):
        probe = probe[5:].strip().strip('"')
    low = probe.lower().replace('/', '\\').rstrip('\\')
    for entry in load_databases(root):
        names = [entry.get('id'), entry.get('name')]
        names += list(entry.get('aliases') or [])
        for name in names:
            if name and str(name).strip().lower() == low:
                return entry, 'база найдена по id, имени или алиасу'
        path = (entry.get('path') or '').replace('/', '\\').rstrip('\\')
        if path and path.lower() == low:
            return entry, 'база найдена по пути'
    return None, 'базы "%s" нет в %s' % (probe, DBS_FILE)


def database_choices(root):
    """Записи баз для формы: label (что видно), value (id для задачи), path."""
    choices = []
    for entry in load_databases(root):
        value = entry.get('id') or entry.get('name') or ''
        name = entry.get('name') or ''
        label = value if (not name or name == value) else '%s - %s' % (value, name)
        choices.append({'label': label, 'value': value,
                        'path': entry.get('path') or entry.get('ref') or
                                entry.get('server') or ''})
    return choices


def errors_to_text(task, errors):
    """Сообщение о непринятой задаче - одной строкой, с идентификатором."""
    return 'задача %s отклонена: %s' % ((task or {}).get('id', '?'), format_errors(errors))
