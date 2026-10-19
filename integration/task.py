import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from transport.config import project_root
from transport.schema import format_errors, read_schema, validate
from transport.store import DEFAULT_TIMEOUT_S, host_name, new_task_id, now_iso

MODES = ('db', 'harness')
DELIVER_MODES = ('uri', 'manual', 'echo', 'auto')
DBS_FILE = '.v8-project.json'

PROMPT_DB = 'как {role} сделай {action} в базе {db} чтобы {goal} по START.md'
PROMPT_DB_SHORT = 'как {role} сделай {action} в базе {db} по START.md'
PROMPT_HARNESS = 'как инженер харнесса сделай {action} чтобы {goal} по START.md'
PROMPT_HARNESS_SHORT = 'как инженер харнесса сделай {action} по START.md'


def one_line(text):
    text = (text or '').replace('\r', ' ').replace('\n', ' ')
    return re.sub(r'\s{2,}', ' ', text).strip()


def build_prompt(role, action, goal, db=None, mode='db'):
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
    return read_schema(os.path.join(project_root(root), 'integration', 'schemas',
                                    'task_schema.json'))


def validate_shape(cfg, payload, client):
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
    return task, errors



def validate_task(root, raw):
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


def errors_to_text(task, errors):
    return 'задача %s отклонена: %s' % ((task or {}).get('id', '?'), format_errors(errors))
