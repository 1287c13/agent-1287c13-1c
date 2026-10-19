import json
import socket
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_TIMEOUT_S = 60.0


class ClientError(Exception):
    pass


class IntegrationClient(object):

    def __init__(self, base_url, key='', timeout=DEFAULT_TIMEOUT_S):
        base = (base_url or '').strip().rstrip('/')
        if not base:
            raise ClientError('не задан адрес сервера: agent.server_url в deploy\\config.json')
        self.base = base
        self.key = key or ''
        self.timeout = timeout


    def _request(self, method, path, payload=None, query=None):
        url = self.base + path
        if query:
            clean = {k: v for k, v in query.items() if v is not None}
            if clean:
                url += '?' + urllib.parse.urlencode(clean)
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header('Accept', 'application/json')
        if data is not None:
            request.add_header('Content-Type', 'application/json; charset=utf-8')
        if self.key:
            request.add_header('X-Integration-Token', self.key)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.getcode(), self._decode(response.read())
        except urllib.error.HTTPError as exc:
            body = exc.read() if hasattr(exc, 'read') else b''
            return exc.code, self._decode(body)
        except (urllib.error.URLError, socket.timeout, OSError) as exc:
            reason = getattr(exc, 'reason', exc)
            raise ClientError('сервер %s недоступен: %s' % (self.base, reason))

    @staticmethod
    def _decode(raw):
        if not raw:
            return {}
        try:
            return json.loads(raw.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return {'raw': raw.decode('utf-8', 'replace')}

    def _call(self, method, path, payload=None, query=None, expect=(200, 202)):
        status, body = self._request(method, path, payload, query)
        if status not in expect:
            message = ''
            if isinstance(body, dict):
                message = body.get('error') or body.get('message') or ''
                errors = body.get('errors')
                if errors:
                    message = '%s (%s)' % (message, '; '.join(errors))
            raise ClientError('HTTP %s: %s' % (status, message or 'запрос отклонён'))
        return body


    def auth(self):
        return self._call('POST', '/api/auth', {'key': self.key})

    def health(self):
        return self._call('GET', '/api/health')

    def submit(self, fields):
        return self._call('POST', '/api/task', fields, expect=(202,))

    def claim(self, agent, ttl_s=None):
        return self._call('POST', '/api/agent/claim',
                          {'agent': agent, 'ttl_s': ttl_s})

    def progress(self, task_id, agent, stage, message=''):
        return self._call('POST', '/api/agent/progress',
                          {'id': task_id, 'agent': agent, 'stage': stage,
                           'message': message})

    def result(self, task_id, agent, status='done', answer='', fields=None, message=''):
        payload = {'id': task_id, 'agent': agent, 'status': status,
                   'answer': answer, 'message': message}
        payload.update(fields or {})
        return self._call('POST', '/api/agent/result', payload)

    def reclaim(self):
        return self._call('POST', '/api/agent/reclaim', {})

    def status(self, task_id):
        return self._call('GET', '/api/status/%s' % urllib.parse.quote(task_id))

    def statuses(self, task_ids):
        return self._call('GET', '/api/status', query={'ids': ','.join(task_ids or [])})

    def history(self, limit=20):
        return self._call('GET', '/api/history', query={'limit': limit})

    def answer(self, task_id, kind='md'):
        return self._call('GET', '/api/answer/%s' % urllib.parse.quote(task_id),
                          query={'format': kind})

    def agents(self):
        return self._call('GET', '/api/agents')
