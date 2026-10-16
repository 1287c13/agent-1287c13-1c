# -*- coding: utf-8 -*-
"""HTTP-интерфейс очереди: одна логика для сервера разработки и для WSGI.

Маршруты (те же и у http_server.py, и у wsgi.py):

    GET  /api/health          состояние очереди: счётчики, позиция журнала, жив ли watcher
    POST /api/task            принять задачу: тело - объект task_schema.json; ответ 202
    GET  /api/result/<id>     результат задачи: 200 с result_schema.json либо 404 с состоянием
    GET  /api/answer/<id>     ответ задачи файлом: markdown агента (format=md) или
                              страница HTML по нему (format=html, по умолчанию)
    GET  /api/tasks           последние результаты и счётчики

Почему приём задачи не кладёт её сразу в inbox: сервер и watcher - разные процессы, а
порядок разбора очереди держит один watcher. Сервер дописывает строку в журнал и
отвечает 202, а задача появляется в inbox следующим проходом watcher-а. Это делает
поведение одинаковым для HTTP, файлового обмена и ручной правки журнала.

413 и 400 различаются: пустое тело или необъект JSON - 400, несоответствие схеме -
400 с перечнем ошибок, слишком большое тело - 413 (проверяет транспорт).
"""

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_INTEGRATION = os.path.dirname(_HERE)
if _INTEGRATION not in sys.path:
    sys.path.insert(0, _INTEGRATION)

from task import errors_to_text, save_rejected, validate_task  # noqa: E402
from transport.store import QueueStore  # noqa: E402

import md_to_html  # noqa: E402

WATCHER_ALIVE_S = 15.0


class Api(object):
    """Логика HTTP-интерфейса поверх QueueStore."""

    def __init__(self, root=None, token=None):
        self.root = os.path.abspath(root or os.path.dirname(_INTEGRATION))
        self.store = QueueStore(self.root)
        self.store.ensure()
        # Токен доступа: если задан, любой маршрут требует его в заголовке
        # X-Integration-Token или в параметре token. Нужен на хостинге: открытый
        # POST /api/task пускает чужой текст прямо в задачу агента.
        self.token = token if token is not None else (os.environ.get('INTEGRATION_TOKEN') or None)

    # --- маршруты ------------------------------------------------------------

    def health(self):
        counts = self.store.counts()
        age = counts.get('watcher_age_s')
        if age is None:
            watcher = {'alive': False, 'message': 'отметки нет: watcher не проходил ни разу'}
        else:
            alive = age <= WATCHER_ALIVE_S
            watcher = {'alive': alive, 'age_s': round(age, 1),
                       'message': 'watcher отвечает' if alive else 'watcher молчит: задачи не разбираются'}
        return 200, {
            'status': 'ok',
            'root': self.root,
            'queue': self.store.rel(self.store.base),
            'watcher': watcher,
            'counts': counts,
        }

    def submit(self, payload, source='http'):
        """Принять задачу: проверка, строка в журнал, ответ 202."""
        if not isinstance(payload, dict):
            return 400, {'error': 'тело запроса должно быть объектом JSON'}
        payload.setdefault('source', source)
        task, errors = validate_task(self.root, payload)
        if errors:
            save_rejected(self.store, task, errors, payload)
            self.store.log_bridge({'event': 'rejected', 'task_id': task.get('id'),
                                   'errors': errors, 'source': source})
            return 400, {'error': 'задача не принята', 'task_id': task.get('id'),
                         'errors': errors, 'text': errors_to_text(task, errors)}
        self.store.append_journal(task)
        self.store.log_bridge({'event': 'submitted', 'task_id': task['id'], 'source': source})
        return 202, {
            'task_id': task['id'],
            'state': 'queued',
            'prompt': task['prompt'],
            'result_url': '/api/result/%s' % task['id'],
            'hint': 'watcher разложит задачу в inbox и передаст её в Cline; результат - по result_url',
        }

    def result(self, task_id):
        found = self.store.result(task_id)
        if found is not None:
            return 200, found
        state = self.store.state(task_id)
        if state == 'unknown' and not self.store.journal_has(task_id):
            return 404, {'task_id': task_id, 'state': 'unknown',
                         'message': 'задачи с таким идентификатором нет'}
        return 404, {'task_id': task_id, 'state': state,
                     'message': 'результат ещё не записан'}

    def answer(self, task_id, kind='html'):
        """Ответ задачи файлом: markdown агента или страница HTML по нему.

        Формат ответа агента - markdown (queue\\answers\\answer_<id>.md): он читается
        человеком и правится руками. HTML собирается по нему здесь, в момент запроса -
        страница нужна для скачивания, а не для хранения.
        """
        kind = 'md' if (kind or '').lower() in ('md', 'markdown') else 'html'
        text = ''
        source = self.store.answer_path(task_id)
        if os.path.isfile(source):
            with open(source, 'r', encoding='utf-8') as f:
                text = f.read()
        if not text:
            result = self.store.result(task_id) or {}
            text = result.get('answer') or ''
        if not text:
            return 404, {'task_id': task_id, 'state': self.store.state(task_id),
                         'error': 'ответ ещё не записан'}
        if kind == 'html':
            content = md_to_html.render(text, title='Ответ задачи %s' % task_id,
                                       source='задача %s из очереди интеграции' % task_id)
        else:
            content = text
        return 200, {'task_id': task_id, 'format': kind,
                     'file_name': md_to_html.answer_file_name(task_id, kind),
                     'content': content}

    def tasks(self, limit=20):
        return 200, {'counts': self.store.counts(), 'results': self.store.recent_results(limit)}

    def dispatch(self, method, path, payload=None, query=None, token=None):
        """Маршрутизация. Возвращает (код, объект ответа)."""
        method = (method or 'GET').upper()
        clean = '/' + (path or '/').strip('/')
        if self.token and method != 'OPTIONS':
            given = token or ((query or {}).get('token') or [None])[0]
            if given != self.token:
                return 401, {'error': 'нужен заголовок X-Integration-Token'}
        if clean == '/api/health' and method in ('GET', 'HEAD'):
            return self.health()
        if clean == '/api/task' and method == 'POST':
            return self.submit(payload)
        if clean == '/api/tasks' and method == 'GET':
            limit = 20
            try:
                limit = int((query or {}).get('limit', ['20'])[0])
            except (ValueError, TypeError, IndexError):
                limit = 20
            return self.tasks(max(1, min(200, limit)))
        prefix = '/api/result/'
        if clean.startswith(prefix) and method in ('GET', 'HEAD'):
            return self.result(clean[len(prefix):])
        prefix = '/api/answer/'
        if clean.startswith(prefix) and method in ('GET', 'HEAD'):
            kind = ((query or {}).get('format') or ['html'])[0]
            return self.answer(clean[len(prefix):], kind)
        if method == 'OPTIONS':
            return 204, None
        return 404, {'error': 'неизвестный маршрут', 'path': clean, 'method': method}


def dumps(obj, indent=None):
    """JSON в UTF-8 байтах: кириллица не экранируется."""
    return json.dumps(obj, ensure_ascii=False, indent=indent).encode('utf-8')
