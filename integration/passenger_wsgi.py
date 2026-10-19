import html
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
os.environ.setdefault('INTEGRATION_ROOT', os.path.dirname(HERE))


def _fail(start_response, message):
    body = ('<!doctype html><meta charset="utf-8"><title>Интеграция не запущена</title>'
            '<h1>Интеграция не запущена</h1><pre>%s</pre>' % html.escape(message)
            ).encode('utf-8')
    start_response('500 Internal Server Error', [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(body))),
    ])
    return [body]


def _fix_base_uri(environ):
    base = (environ.get('SCRIPT_NAME') or '').rstrip('/')
    path = environ.get('PATH_INFO') or '/'
    if not base:
        base = (environ.get('PASSENGER_BASE_URI') or '').rstrip('/')
        if base:
            environ['SCRIPT_NAME'] = base
    if base and path.startswith(base):
        environ['PATH_INFO'] = path[len(base):] or '/'
    elif not path:
        environ['PATH_INFO'] = '/'
    return environ


def application(environ, start_response):
    try:
        from transport.wsgi import application as wsgi_application
    except Exception as exc:
        sys.stderr.write('%s\n' % traceback.format_exc())
        return _fail(start_response, '%s: %s\n\nПодробности - в журнале Passenger.'
                     % (type(exc).__name__, exc))
    return wsgi_application(_fix_base_uri(environ), start_response)
