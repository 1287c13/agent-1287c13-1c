import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_INTEGRATION = os.path.dirname(_HERE)
if _INTEGRATION not in sys.path:
    sys.path.insert(0, _INTEGRATION)

import md_to_html
from task import errors_to_text, validate_shape
from transport.config import (client_by_key, load_config, project_root,
                              public_server_view)
from transport.store import (DEFAULT_CLAIM_TTL_S, QueueStore, preview,
                             safe_name)

WEB_DIR = os.path.join(_INTEGRATION, 'web')
STATIC_TYPES = {
    'index.html': 'text/html; charset=utf-8',
    'app.js': 'application/javascript; charset=utf-8',
    'style.css': 'text/css; charset=utf-8',
}
MAX_STATUS_IDS = 100


class Response(object):

    def __init__(self, status=200, payload=None, body=None,
                 content_type='application/json; charset=utf-8', headers=None):
        self.status = status
        self.payload = payload
        self.body = body
        self.content_type = content_type
        self.headers = dict(headers or {})

    def to_bytes(self):
        if self.body is not None:
            return self.body
        if self.payload is None:
            return b''
        return json.dumps(self.payload, ensure_ascii=False, indent=2).encode('utf-8')



class Api(object):

    def __init__(self, root=None, config=None, config_path=None):
        self.root = project_root(root)
        if config is None:
            config, _notes = load_config(self.root, config_path)
        self.config = config
        self.store = QueueStore(config['server']['root'])
        self.store.ensure()


    def _origin(self):
        return (self.config.get('server') or {}).get('cors_origin') or '*'

    def _json(self, status, payload):
        return Response(status, payload=payload)

    @staticmethod
    def _token(headers, query):
        headers = headers or {}
        token = headers.get('x-integration-token') or headers.get('X-Integration-Token') or ''
        if not token:
            auth = headers.get('authorization') or headers.get('Authorization') or ''
            if auth.lower().startswith('bearer '):
                token = auth[7:].strip()
        if not token:
            token = ((query or {}).get('token') or [''])[0]
        return token

    def _client(self, headers, query):
        clients = (self.config.get('server') or {}).get('clients') or []
        if not clients:
            return None, self._json(503, {
                'error': 'сервер не настроен: в deploy\\config.json нет server.clients',
                'hint': 'скопируйте deploy\\config.example.json и задайте ключи клиентов'})
        client = client_by_key(self.config, self._token(headers, query))
        if client is None:
            return None, self._json(401, {
                'error': 'ключ доступа не подходит',
                'hint': 'заголовок X-Integration-Token или Authorization: Bearer'})
        return client, None


    def health(self):
        counts = self.store.counts()
        agents = [{k: a.get(k) for k in ('name', 'state', 'task_id', 'updated_at', 'age_s', 'alive')}
                  for a in self.store.agents()]
        return self._json(200, {
            'status': 'ok',
            'version': 'integration-v2',
            'queue': counts,
            'agents': agents,
            'notes': list(self.config.get('notes') or []),
        })

    def auth(self, payload):
        clients = (self.config.get('server') or {}).get('clients') or []
        if not clients:
            return self._json(503, {'ok': False,
                                     'error': 'на сервере не задан ни один клиентский ключ'})
        key = ''
        if isinstance(payload, dict):
            key = str(payload.get('key') or '')
        client = client_by_key(self.config, key)
        if client is None:
            return self._json(401, {'ok': False, 'error': 'ключ доступа не подходит'})
        view = public_server_view(self.config)
        view.update({'ok': True, 'client': client.get('name'),
                     'allow_harness': bool(client.get('allow_harness'))})
        return self._json(200, view)

    def agents(self):
        return self._json(200, {'items': self.store.agents()})

    def events(self, query):
        try:
            limit = int(((query or {}).get('limit') or ['50'])[0])
        except (ValueError, TypeError, IndexError):
            limit = 50

    def submit(self, payload, client):
        task, errors = validate_shape(self.config, payload, client)
        if errors:
            task_id = (task or {}).get('id')
            self.store.reject(payload, errors, task_id)
            return self._json(400, {
                'error': 'задача не принята',
                'task_id': task_id,
                'errors': errors,
                'text': errors_to_text(task, errors),
            })
        stored = self.store.enqueue(task)
        return self._json(202, {
            'task_id': stored['id'],
            'state': stored.get('state'),
            'prompt': stored.get('prompt'),
            'created_at': stored.get('created_at'),
            'status_url': '/api/status/%s' % stored['id'],
        })

    def status(self, task_id):
        item = self.store.status(task_id)
        if item is None:
            return self._json(404, {'error': 'задачи с таким идентификатором нет',
                                    'task_id': task_id})
        return self._json(200, item)

    def statuses(self, query):
        raw = ((query or {}).get('ids') or [''])[0]
        ids = [x.strip() for x in raw.split(',') if x.strip()][:MAX_STATUS_IDS]
        if not ids:
            return self._json(400, {'error': 'не задан параметр ids'})
        items = self.store.statuses(ids)
        found = set(item['task_id'] for item in items)
        return self._json(200, {'items': items,
                                'missing': [x for x in ids if x not in found]})

    def history(self, query):
        try:
            limit = int(((query or {}).get('limit') or ['20'])[0])
        except (ValueError, TypeError, IndexError):
            limit = 20
        limit = max(1, min(200, limit))
        return self._json(200, {'counts': self.store.counts(),
                                'items': self.store.recent(limit)})

    def answer(self, task_id, query):
        kind = (((query or {}).get('format') or ['md'])[0] or 'md').lower()
        kind = 'html' if kind in ('html', 'page') else 'md'
        result = self.store.result(task_id)
        if not result:
            current = self.store.status(task_id)
            if current is None:
                return self._json(404, {'error': 'задачи с таким идентификатором нет'})
            return self._json(404, {'error': 'ответ ещё не записан',
                                    'task_id': task_id, 'state': current.get('state')})
        text = result.get('answer') or ''
        if kind == 'html':
            content = md_to_html.render(text, title='Ответ задачи %s' % task_id,
                                        source='задача %s из очереди интеграции' % task_id)
        else:
            content = text
        return self._json(200, {'task_id': task_id, 'format': kind,
                                'file_name': md_to_html.answer_file_name(task_id, kind),
                                'content': content})



    def claim(self, payload, client):
        payload = payload if isinstance(payload, dict) else {}
        agent = safe_name(str(payload.get('agent') or client.get('name') or 'agent'))
        try:
            ttl = int(payload.get('ttl_s') or DEFAULT_CLAIM_TTL_S)
        except (TypeError, ValueError):
            ttl = DEFAULT_CLAIM_TTL_S
        ttl = max(30, min(3600, ttl))
        task = self.store.claim(agent, ttl)
        if task is None:
            return self._json(200, {'task': None, 'agent': agent, 'retry_after_s': 5})
        task['claim'] = {'agent': agent, 'expires_ts': task.get('claim_expires_ts'),
                         'ttl_s': task.get('claim_ttl_s'),
                         'attempts': task.get('attempts')}
        return self._json(200, {'task': task, 'agent': agent})

    def progress(self, payload, client):
        payload = payload if isinstance(payload, dict) else {}
        task_id = str(payload.get('id') or '')
        stage = str(payload.get('stage') or '')
        agent = safe_name(str(payload.get('agent') or client.get('name') or 'agent'))
        accepted, note, task = self.store.progress(task_id, agent, stage,
                                                   str(payload.get('message') or ''))
        if task is None:
            return self._json(404, {'error': note or 'задача не найдена', 'task_id': task_id})
        state = (task or {}).get('state') or ''
        if accepted and state in ('done', 'error', 'failed', 'timeout'):
            return self._json(409, {'error': 'задача уже завершена: %s' % state,
                                    'task_id': task_id, 'state': state})
        return self._json(200, {'task_id': task_id, 'state': state, 'accepted': accepted,
                                'note': note})

    def result(self, payload, client):
        payload = payload if isinstance(payload, dict) else {}
        task_id = str(payload.get('id') or '')
        agent = safe_name(str(payload.get('agent') or client.get('name') or 'agent'))
        status = str(payload.get('status') or 'done').lower()
        if status not in ('done', 'error', 'failed', 'timeout'):
            return self._json(400, {'error': 'недопустимый статус результата: %s' % status,
                                    'task_id': task_id})
        fields = {key: payload.get(key) for key in
                  ('layer', 'mcp', 'skills', 'verification', 'done', 'not_verified',
                   'delivery', 'confirmed', 'cline_session', 'cline_note')
                  if payload.get(key) is not None}
        stored = self.store.complete(task_id, agent, status,
                                     str(payload.get('answer') or ''),
                                     fields, str(payload.get('message') or ''))
        if stored is None:
            return self._json(409, {'error': 'задача не найдена или уже завершена',
                                    'task_id': task_id})
        return self._json(200, {'task_id': task_id, 'state': stored.get('status'),
                                'finished_at': stored.get('finished_at'),
                                'duration_s': stored.get('duration_s')})

    def reclaim(self):
        actions = self.store.reclaim_stale()
        timed_out = self.store.sweep_timeouts()
        return self._json(200, {'reclaimed': actions, 'timed_out': timed_out})



    def _static(self, name):
        path = os.path.join(WEB_DIR, name)
        if not os.path.isfile(path):
            return None
        with open(path, 'rb') as f:
            body = f.read()
        return Response(200, body=body,
                        content_type=STATIC_TYPES.get(name, 'application/octet-stream'))


    def dispatch(self, method, path, payload=None, query=None, headers=None):
        method = (method or 'GET').upper()
        clean = '/' + (path or '/').strip('/')
        if method == 'OPTIONS':
            return Response(204)
        if method in ('GET', 'HEAD'):
            if clean in ('/', '/index.html'):
                page = self._static('index.html')
                if page is not None:
                    return page
                return Response(404, body=('нет файла страницы задач: integration\\web\\index.html'
                                           ).encode('utf-8'),
                                content_type='text/plain; charset=utf-8')
            for name in ('app.js', 'style.css'):
                if clean == '/' + name:
                    found = self._static(name)
                    if found is not None:
                        return found
            if clean == '/favicon.ico':
                return Response(204)
        if clean == '/api/health' and method in ('GET', 'HEAD'):
            return self.health()
        if clean == '/api/auth' and method == 'POST':
            return self.auth(payload)
        if not clean.startswith('/api/'):
            return self._json(404, {'error': 'неизвестный маршрут',
                                    'path': clean, 'method': method})

        client, error = self._client(headers, query)
        if error is not None:
            return error

        if clean == '/api/task' and method == 'POST':
            return self.submit(payload, client)
        if clean == '/api/history' and method in ('GET', 'HEAD'):
            return self.history(query)
        if clean == '/api/status' and method in ('GET', 'HEAD'):
            return self.statuses(query)
        if clean == '/api/agents' and method in ('GET', 'HEAD'):
            return self.agents()
        if clean == '/api/events' and method in ('GET', 'HEAD'):
            return self.events(query)
        prefix = '/api/status/'
        if clean.startswith(prefix) and method in ('GET', 'HEAD'):
            return self.status(clean[len(prefix):])
        prefix = '/api/answer/'
        if clean.startswith(prefix) and method in ('GET', 'HEAD'):
            return self.answer(clean[len(prefix):], query)
        if clean == '/api/agent/claim' and method == 'POST':
            return self.claim(payload, client)
        if clean == '/api/agent/progress' and method == 'POST':
            return self.progress(payload, client)
        if clean == '/api/agent/result' and method == 'POST':
            return self.result(payload, client)
        if clean == '/api/agent/reclaim' and method == 'POST':
            return self.reclaim()
        return self._json(404, {'error': 'неизвестный маршрут',
                                'path': clean, 'method': method})
