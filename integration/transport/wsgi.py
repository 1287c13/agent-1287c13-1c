# -*- coding: utf-8 -*-
"""WSGI-приложение очереди: точка входа для хостинга (Passenger, waitress, IIS).

HTTP-интерфейс тот же, что у сервера разработки, потому что логика у них общая
(transport\\api.py). Разница в способе подключения: здесь приложение - вызываемый
объект `application(environ, start_response)`, его поднимает веб-сервер.

Корень харнесса задаётся переменной окружения INTEGRATION_ROOT (иначе - каталог выше
integration). Токен доступа - INTEGRATION_TOKEN: если он задан, запросы без заголовка
X-Integration-Token получают 401. На публичном хостинге токен обязателен.

Запуск для проверки без веб-сервера:

    py -3 -m wsgiref.simple_server  # не требуется: используйте transport\\http_server.py
"""

import json
import os
import sys
import urllib.parse

_HERE = os.path.dirname(os.path.abspath(__file__))
_INTEGRATION = os.path.dirname(_HERE)
if _INTEGRATION not in sys.path:
    sys.path.insert(0, _INTEGRATION)

from transport.api import Api, dumps  # noqa: E402

MAX_BODY = 262144
_APIS = {}


def api_for(root):
    """Один объект Api на процесс: очередь читается с диска, состояние не кэшируется."""
    key = os.path.abspath(root)
    if key not in _APIS:
        _APIS[key] = Api(key)
    return _APIS[key]


def respond(start_response, status, payload):
    """Ответ в формате WSGI: JSON в UTF-8, без экранирования кириллицы."""
    body = b'' if payload is None else dumps(payload, indent=2)
    headers = [
        ('Content-Type', 'application/json; charset=utf-8'),
        ('Content-Length', str(len(body))),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Headers', 'Content-Type, X-Integration-Token'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
    ]
    start_response('%s %s' % (status, _reason(status)), headers)
    return [body]


def _reason(status):
    return {200: 'OK', 202: 'Accepted', 204: 'No Content', 400: 'Bad Request',
            401: 'Unauthorized', 404: 'Not Found', 413: 'Payload Too Large',
            500: 'Internal Server Error'}.get(status, 'OK')


def application(environ, start_response):
    """Точка входа WSGI: разбор запроса, вызов Api, JSON-ответ."""
    root = environ.get('INTEGRATION_ROOT') or os.environ.get('INTEGRATION_ROOT') or \
        os.path.dirname(_INTEGRATION)
    api = api_for(root)
    method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    query = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''))
    token = environ.get('HTTP_X_INTEGRATION_TOKEN')

    payload = None
    if method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH') or 0)
        except (ValueError, TypeError):
            length = 0
        if length > MAX_BODY:
            return respond(start_response, 413, {'error': 'тело запроса больше %s байт' % MAX_BODY})
        body = environ['wsgi.input'].read(length) if length > 0 else b''
        if body:
            try:
                payload = json.loads(body.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                return respond(start_response, 400, {'error': 'тело не разобрано как JSON'})

    try:
        status, obj = api.dispatch(method, path, payload, query, token=token)
    except Exception as exc:  # приложение не должно отдавать трассировку клиенту
        status, obj = 500, {'error': 'внутренняя ошибка очереди: %s' % exc}
    return respond(start_response, status, obj)
