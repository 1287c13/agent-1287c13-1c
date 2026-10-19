# -*- coding: utf-8 -*-
"""Сервер разработки: то же WSGI-приложение на стандартном wsgiref.

Нужен, когда Passenger на этой машине недоступен (Windows, локальная проверка).
Ничего своего в маршрутах нет: приложение берётся из transport\\wsgi.py, поэтому
локальная проверка и хостинг исполняют один код.

    py -3 integration\\transport\\http_server.py --port 8760
    curl http://127.0.0.1:8760/api/health

Слушает только localhost по умолчанию: это инструмент проверки, а не публикация.
"""

import argparse
import os
import sys
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

_HERE = os.path.dirname(os.path.abspath(__file__))
_INTEGRATION = os.path.dirname(_HERE)
if _INTEGRATION not in sys.path:
    sys.path.insert(0, _INTEGRATION)

from transport.store import setup_stdio  # noqa: E402
from transport.wsgi import get_api, make_app  # noqa: E402


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    """Запросы обрабатываются параллельно: без этого долгий ответ держит весь сервер."""

    daemon_threads = True


class RequestHandler(WSGIRequestHandler):
    """Строки доступа в stderr, отключаются ключом --quiet."""

    def log_message(self, fmt, *args):
        if not getattr(self.server, 'quiet', False):
            sys.stderr.write('%s - %s\n' % (self.address_string(), fmt % args))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='http_server.py',
        description='Сервер интеграции на wsgiref (локальная проверка).')
    parser.add_argument('--root', default=None,
                        help='корень харнесса (по умолчанию - выше integration)')
    parser.add_argument('--config', default=None,
                        help='файл настроек (по умолчанию deploy\\config.json)')
    parser.add_argument('--host', default=None, help='адрес прослушивания')
    parser.add_argument('--port', type=int, default=None, help='порт')
    parser.add_argument('--quiet', action='store_true', help='не печатать строки доступа')
    args = parser.parse_args(argv)

    setup_stdio()
    app = make_app(args.root, args.config, debug=True)
    instance = get_api(args.root, args.config)
    host = args.host or instance.config['server']['host']
    port = args.port or instance.config['server']['port']

    server = make_server(host, port, app, server_class=ThreadingWSGIServer,
                         handler_class=RequestHandler)
    server.quiet = args.quiet
    print('очередь: %s' % instance.store.base)
    print('слушаю http://%s:%d/ (Ctrl+C - стоп)' % (host, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('остановлено')
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
