# -*- coding: utf-8 -*-
"""Настройки интеграции: один файл deploy\\config.json на все роли.

Файл читают и сервер (очередь, ключи клиентов, список баз для формы), и агент
(адрес сервера, свой ключ, режим доставки). Разделение по секциям:

    server  host, port, public_url, root (каталог очереди), cors_origin, max_body,
            databases (перечисление для проверки формы), clients[] (ключи доступа);
    agent   name, server_url, key, deliver, interval, idle_interval, claim_ttl_s.

Почему базы в настройках сервера, а не в .v8-project.json: сервер стоит на хостинге,
где выгрузки и файла проекта нет. Список баз здесь - подсказка форме и грубая проверка
опечатки отправителя; настоящее разрешение слота <база> (id -> путь, платформа) делает
агент на своей машине по .v8-project.json.

Ключи клиентов сравниваются hmac.compare_digest: обычное == выходит из цикла на первом
несовпавшем байте и по времени ответа выдаёт префикс ключа.
"""

import hmac
import json
import os

SERVER_DEFAULTS = {
    'host': '127.0.0.1',
    'port': 8760,
    'public_url': '',
    'root': '',
    'cors_origin': '*',
    'max_body': 262144,
    'databases': [],
    'clients': [],
}

AGENT_DEFAULTS = {
    'name': '',
    'server_url': '',
    'key': '',
    'deliver': 'uri',
    'interval': 2.0,
    'idle_interval': 15.0,
    'claim_ttl_s': 300,
    'timeout_s': 1800,
}


def project_root(path=None):
    """Корень харнесса: каталог выше integration\\."""
    base = path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.basename(base) == 'integration':
        return os.path.dirname(base)
    return base


def config_path(root=None, explicit=None):
    """Путь к файлу настроек: аргумент, затем INTEGRATION_CONFIG, затем deploy\\config.json."""
    if explicit:
        return os.path.abspath(explicit)
    env = os.environ.get('INTEGRATION_CONFIG')
    if env:
        return os.path.abspath(env)
    return os.path.join(project_root(root), 'deploy', 'config.json')


def _as_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_clients(raw, notes):
    """Ключи клиентов: имя, ключ, разрешение задач по харнессу."""
    clients = []
    seen = set()
    for index, item in enumerate(raw or []):
        if not isinstance(item, dict):
            notes.append('server.clients[%d]: ожидается объект, запись пропущена' % index)
            continue
        name = str(item.get('name') or '').strip() or 'client-%d' % (index + 1)
        key = str(item.get('key') or '')
        if not key:
            notes.append('клиент «%s» без ключа: войти под ним нельзя' % name)
        if key and key in seen:
            notes.append('ключ клиента «%s» повторяется: оставлена первая запись' % name)
            continue
        if key:
            seen.add(key)
        clients.append({'name': name, 'key': key,
                        'allow_harness': bool(item.get('allow_harness'))})
    return clients



def load_config(root=None, path=None):
    """Прочитать настройки. Возвращает (словарь, список замечаний).

    Отсутствие файла - не исключение: сервер поднимется и скажет, что клиентских
    ключей нет, а не упадёт на старте Passenger с невнятной ошибкой 500.
    """
    root = project_root(root)
    target = config_path(root, path)
    notes = []
    data = {}
    if os.path.isfile(target):
        try:
            with open(target, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                notes.append('файл настроек не объект JSON: %s' % target)
                data = {}
        except (ValueError, OSError) as exc:
            notes.append('файл настроек не прочитан (%s): %s' % (target, exc))
            data = {}
    else:
        notes.append('файла настроек нет: %s (образец - deploy\\config.example.json)' % target)

    raw_server = data.get('server') if isinstance(data.get('server'), dict) else {}
    server = dict(SERVER_DEFAULTS)
    server['host'] = str(raw_server.get('host') or SERVER_DEFAULTS['host'])
    server['port'] = _as_int(raw_server.get('port'), SERVER_DEFAULTS['port'])
    server['public_url'] = str(raw_server.get('public_url') or '').rstrip('/')
    server['cors_origin'] = str(raw_server.get('cors_origin') or '*')
    server['max_body'] = max(4096, _as_int(raw_server.get('max_body'), SERVER_DEFAULTS['max_body']))
    server['databases'] = [str(x) for x in (raw_server.get('databases') or []) if str(x).strip()]
    server['clients'] = _normalize_clients(raw_server.get('clients'), notes)

    queue_root = str(raw_server.get('root') or '').strip()
    if not queue_root:
        queue_root = os.path.join(root, 'queue')
    elif not os.path.isabs(queue_root):
        queue_root = os.path.join(root, queue_root)
    server['root'] = os.path.abspath(queue_root)

    raw_agent = data.get('agent') if isinstance(data.get('agent'), dict) else {}
    agent = dict(AGENT_DEFAULTS)
    agent['name'] = str(raw_agent.get('name') or '').strip()
    agent['server_url'] = str(raw_agent.get('server_url') or '').rstrip('/')
    agent['key'] = str(raw_agent.get('key') or '')
    deliver = str(raw_agent.get('deliver') or 'uri')
    agent['deliver'] = deliver if deliver in ('uri', 'manual', 'echo', 'auto') else 'uri'
    agent['interval'] = max(0.5, _as_float(raw_agent.get('interval'), AGENT_DEFAULTS['interval']))
    agent['idle_interval'] = max(
        agent['interval'],
        _as_float(raw_agent.get('idle_interval'), AGENT_DEFAULTS['idle_interval']))
    agent['claim_ttl_s'] = max(30, _as_int(raw_agent.get('claim_ttl_s'), AGENT_DEFAULTS['claim_ttl_s']))
    agent['timeout_s'] = max(60, _as_int(raw_agent.get('timeout_s'), AGENT_DEFAULTS['timeout_s']))

    cfg = {
        'path': target,
        'project_root': root,
        'python': str(data.get('python') or 'py -3'),
        'server': server,
        'agent': agent,
        'notes': notes,
    }
    return cfg, notes


def client_by_key(cfg, key):
    """Клиент по ключу доступа. None - ключ не подходит."""
    if not key:
        return None
    given = str(key)
    for client in cfg.get('server', {}).get('clients') or []:
        known = client.get('key') or ''
        if known and hmac.compare_digest(given.encode('utf-8'), known.encode('utf-8')):
            return client
    return None


def agent_name(cfg):
    """Имя агента: из настроек, иначе <COMPUTERNAME>\\<USERNAME>."""
    name = (cfg.get('agent') or {}).get('name') or ''
    if name:
        return name
    user = os.environ.get('USERNAME') or os.environ.get('USER') or 'agent'
    computer = os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or ''
    return '%s@%s' % (user, computer) if computer else user


def public_server_view(cfg):
    """Что сервер рассказывает о себе после входа: без ключей и путей."""
    server = cfg.get('server') or {}
    return {
        'databases': list(server.get('databases') or []),
        'public_url': server.get('public_url') or '',
        'version': 'integration-v2',
    }
