# -*- coding: utf-8 -*-
"""Задача внешней интеграции: сборка из слотов, нормализация и проверка по схеме.

Один и тот же код собирает задачу в трёх местах: в GUI при нажатии «Отправить»,
на HTTP-сервере при POST /api/task и в watcher-e при разборе строки журнала. Поэтому
формулировка контракта строится функцией build_prompt, а не руками в каждом месте:
иначе три отправителя дадут три разных текста задачи.

Проверка - двухслойная: сначала формальная (схема task_schema.json через
transport.schema), затем смысловая - режим задачи и разрешение слота <база> по
.v8-project.json. База, которой нет в конфиге, - ошибка отправителя, а не проблема
агента: задача до Cline не доходит.
"""

import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from transport.schema import read_schema, validate, format_errors  # noqa: E402
from transport.store import DEFAULT_TIMEOUT_S, host_name, new_task_id, now_iso, write_text_atomic  # noqa: E402

MODES = ('db', 'harness')
DBS_FILE = '.v8-project.json'

# Слоты контракта: «как <роль> сделай <действие> в базе <база> чтобы <цель> по START.md».
# Слот <цель> необязателен: без него формулировка обходится без «чтобы <цель>»,
# потому что цель нужна не всякой задаче, а форм у отправителя должно быть меньше.
PROMPT_DB = 'как {role} сделай {action} в базе {db} чтобы {goal} по START.md'
PROMPT_DB_SHORT = 'как {role} сделай {action} в базе {db} по START.md'
PROMPT_HARNESS = 'как инженер харнесса сделай {action} чтобы {goal} по START.md'
PROMPT_HARNESS_SHORT = 'как инженер харнесса сделай {action} по START.md'


def project_root(path=None):
    """Корень харнесса: каталог выше integration\\."""
    base = path or os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(base) == 'integration':
        return os.path.dirname(base)
    return base


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


def make_task(role, action, goal, db=None, mode='db', source='cli', deliver='auto',
              timeout_s=DEFAULT_TIMEOUT_S, note=None, prompt=None, client=None):
    """Собрать задачу: идентификатор, время, отправитель, формулировка контракта."""
    mode = mode if mode in MODES else 'db'
    if mode == 'harness':
        db = None
    task = {
        'id': new_task_id(),
        'created_at': now_iso(),
        'source': source,
        'client': client or host_name(),
        'mode': mode,
        'role': one_line(role),
        'action': one_line(action),
        'db': db,
        'prompt': one_line(prompt) or build_prompt(role, action, goal, db, mode),
        'deliver': deliver,
        'timeout_s': int(timeout_s),
    }
    if one_line(goal):
        # Пустую цель в задачу не кладём: схема проверяет длину только у присутствующего поля.
        task['goal'] = one_line(goal)
    if note:
        task['note'] = one_line(note)
    return task


def normalize_task(raw):
    """Достроить поля, которые отправитель мог не заполнить. Исходный словарь не меняется."""
    task = dict(raw or {})
    if not task.get('id'):
        task['id'] = new_task_id()
    if not task.get('created_at'):
        task['created_at'] = now_iso()
    if not task.get('source'):
        task['source'] = 'file'
    if not task.get('client'):
        task['client'] = host_name()
    if task.get('mode') not in MODES:
        task['mode'] = 'db'
    for name in ('role', 'action', 'goal', 'db', 'prompt', 'note'):
        if isinstance(task.get(name), str):
            task[name] = one_line(task[name])
    if task['mode'] == 'harness':
        task['db'] = None
    if not task.get('goal'):
        task.pop('goal', None)
    if not task.get('prompt') and task.get('action'):
        task['prompt'] = build_prompt(task.get('role') or 'инженер харнесса',
                                      task['action'], task.get('goal'), task.get('db'), task['mode'])
    if not task.get('deliver'):
        task['deliver'] = 'auto'
    if not task.get('timeout_s'):
        task['timeout_s'] = DEFAULT_TIMEOUT_S
    return task


def load_databases(root):
    """Записи баз из .v8-project.json. Пустой список - файла нет или он нечитаем."""
    path = os.path.join(root, DBS_FILE)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (ValueError, OSError):
        return []
    return list(config.get('databases') or [])


def database_labels(root):
    """Строки для выпадающего списка GUI: id плюс алиасы."""
    labels = []
    for entry in load_databases(root):
        aliases = entry.get('aliases') or []
        label = entry.get('id') or entry.get('name') or ''
        if aliases:
            label = '%s (%s)' % (label, ', '.join(aliases))
        labels.append(label)
    return labels


def resolve_db(root, value):
    """Найти запись базы по id, имени, алиасу или пути.

    Возвращает пару (запись_или_None, пояснение). Агент в задаче базу разрешает по
    тому же правилу, поэтому проверка отправителя и работа агента не расходятся.
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


def validate_task(root, raw):
    """Нормализовать и проверить задачу. Возвращает (задача, список ошибок)."""
    task = normalize_task(raw)
    errors = []
    schema = read_schema(os.path.join(root, 'integration', 'schemas', 'task_schema.json'))
    errors.extend(validate(task, schema, 'задача'))
    if task.get('mode') == 'db':
        if not task.get('db'):
            errors.append('режим db: не заполнен слот базы')
        else:
            entry, message = resolve_db(root, task['db'])
            if entry is None:
                errors.append('режим db: %s' % message)
    elif task.get('mode') == 'harness' and task.get('db'):
        errors.append('режим harness: слот базы должен быть пустым')
    return task, errors


def errors_to_text(task, errors):
    """Сообщение о непринятой задаче - одной строкой, с идентификатором."""
    return 'задача %s отклонена: %s' % (task.get('id', '?'), format_errors(errors))


def save_rejected(store, task, errors, payload=None):
    """Положить отклонённую задачу в queue\\failed - отправитель должен увидеть причину."""
    path = os.path.join(store.dirs['failed'], 'rejected_%s.json' % task.get('id', 'unknown'))
    write_text_atomic(path, json.dumps({'task': payload if payload is not None else task,
                                        'errors': errors}, ensure_ascii=False, indent=2))
    return path
