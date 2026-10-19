import json
import os
import sys
import traceback
import urllib.parse

_HERE = os.path.dirname(os.path.abspath(__file__))
_INTEGRATION = os.path.dirname(_HERE)
if _INTEGRATION not in sys.path:
    sys.path.insert(0, _INTEGRATION)

from transport.api import Api, Response

REASONS = {
    200: 'OK', 202: 'Accepted', 204: 'No Content', 400: 'Bad Request',
    401: 'Unauthorized', 403: 'Forbidden', 404: 'Not Found', 405: 'Method Not Allowed',
    409: 'Conflict', 413: 'Payload Too Large', 500: 'Internal Server Error',
    503: 'Service Unavailable',
}

_STATE = {}


def get_api(root=None, config_path=None):
    root = root or os.environ.get('INTEGRATION_ROOT') or None
    config_path = config_path or os.environ.get('INTEGRATION_CONFIG') or None
    key = (os.path.abspath(root) if root else '', os.path.abspath(config_path) if config_path else '')
    if key not in _STATE:
        _STATE[key] = Api(root=root, config_path=config_path)
    return _STATE[key]


def _cors(api, environ):
    origin = (api.config.get('server') or {}).get('cors_origin') or '*'
    return [
        ('Access-Control-Allow-Origin', origin),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, X-Integration-Token, Authorization'),
        ('Access-Control-Max-Age', '600'),
    ]


def _read_json(environ, max_body):
    try:
        length = int(environ.get('CONTENT_LENGTH') or 0)
    except (TypeError, ValueError):
        length = 0
    if length <= 0:
        return None, None
    if length > max_body:
        return None, 'тело запроса больше %d байт' % max_body
    raw = environ.get('wsgi.input').read(length)
    if not raw:
        return None, None
    try:
        return json.loads(raw.decode('utf-8')), None
    except (ValueError, UnicodeDecodeError):
        return None, 'тело не разобрано как JSON'


def _error_response(status, message):
    return Response(status, payload={'error': message})


def handle(api, environ):
    method = environ.get('REQUEST_METHOD') or 'GET'
    path = environ.get('PATH_INFO') or '/'
    base = environ.get('SCRIPT_NAME') or ''
    if base and path.startswith(base):
        path = path[len(base):] or '/'
    query = urllib.parse.parse_qs(environ.get('QUERY_STRING') or '')
    headers = {}
    for key, value in environ.items():
        if key.startswith('HTTP_'):
            headers[key[5:].lower().replace('_', '-')] = value
    max_body = int((api.config.get('server') or {}).get('max_body') or 262144)
    payload, problem = _read_json(environ, max_body)
    if problem:
        status = 413 if 'больше' in problem else 400
        return _error_response(status, problem)
    return api.dispatch(method, path, payload, query, headers)


def make_app(root=None, config_path=None, debug=False):

    def application(environ, start_response):
        try:
            api = get_api(root, config_path)
            response = handle(api, environ)
        except Exception as exc:
            sys.stderr.write('%s\n' % traceback.format_exc())
            if debug:
                message = 'внутренняя ошибка сервера интеграции: %s' % exc
            else:
                message = 'внутренняя ошибка сервера интеграции (подробности в журнале)'
            response = _error_response(500, message)
            try:
                api = get_api(root, config_path)
            except Exception:
                api = None
        body = response.to_bytes()
        headers = [
            ('Content-Type', response.content_type),
            ('Content-Length', str(len(body))),
            ('Cache-Control', 'no-store'),
        ]
        try:
            if api is not None:
                headers.extend(_cors(api, environ))
        except Exception:
            pass
        headers.extend(response.headers.items())
        status_line = '%d %s' % (response.status,
                                 REASONS.get(response.status, 'OK'))
        start_response(status_line, headers)
        if (environ.get('REQUEST_METHOD') or 'GET').upper() == 'HEAD':
            return [b'']
        return [body]

    return application


application = make_app()
