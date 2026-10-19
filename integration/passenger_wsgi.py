# -*- coding: utf-8 -*-
"""Точка входа Passenger: Integration\\ - корень приложения WSGI.

Панель Passenger ищет файл passenger_wsgi.py в корне приложения. Поэтому файл лежит
здесь, а не в transport\\: корень приложения - integration\\, и модуль transport
импортируется из него.

Два свойства, из-за которых файл не сводится к одной строке:

- **базовый URI.** Сайт может быть опубликован не в корне домена, а по адресу
  /agent (PassengerBaseURI). Passenger кладёт префикс в SCRIPT_NAME; если его нет,
  но есть PASSENGER_BASE_URI, префикс выставляется здесь, а PATH_INFO очищается -
  иначе маршрут /api/health превратился бы в /agent/api/health и дал 404;
- **читаемая ошибка импорта.** Если зависимости не установлены или в коде опечатка,
  Passenger покажет панель с 500, а в журнал уйдёт трассировка. Пользователь должен
  увидеть текст причины, а не пустую страницу.

Переменные окружения: INTEGRATION_ROOT (корень харнесса) и INTEGRATION_CONFIG (файл
настроек), если они отличаются от integration\\..\\deploy\\config.json.
"""

import html
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
os.environ.setdefault('INTEGRATION_ROOT', os.path.dirname(HERE))


def _fail(start_response, message):
    """500 с читаемой причиной: без импорта transport ответить больше нечем."""
    body = ('<!doctype html><meta charset="utf-8"><title>Интеграция не запущена</title>'
            '<h1>Интеграция не запущена</h1><pre>%s</pre>' % html.escape(message)
            ).encode('utf-8')
    start_response('500 Internal Server Error', [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(body))),
    ])
    return [body]


def _fix_base_uri(environ):
    """Выставить SCRIPT_NAME, если Passenger передал базовый URI только в PASSENGER_BASE_URI."""
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
    except Exception as exc:  # noqa: BLE001 - причина должна дойти до человека
        sys.stderr.write('%s\n' % traceback.format_exc())
        return _fail(start_response, '%s: %s\n\nПодробности - в журнале Passenger.'
                     % (type(exc).__name__, exc))
    return wsgi_application(_fix_base_uri(environ), start_response)
