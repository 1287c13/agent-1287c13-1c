# -*- coding: utf-8 -*-
"""Сервер разработки: HTTP-интерфейс очереди на стандартном http.server.

Слушает только localhost по умолчанию: это инструмент проверки и локальной работы,
а не публикация в интернет. Для внешних заявок используется WSGI-вариант
(transport\\wsgi.py) за веб-сервером с аутентификацией.

    py -3 integration\\transport\\http_server.py --port 8760
    curl http://127.0.0.1:8760/api/health

Тело запроса ограничено размером (--max-body, по умолчанию 256 КБ): задача - это
несколько строк текста, и большой поток в сокет очередь не обслуживает.
"""

import argparse
import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_HERE = os.path.dirname(os.path.abspath(__file__))
_INTEGRATION = os.path.dirname(_HERE)
if _INTEGRATION not in sys.path:
    sys.path.insert(0, _INTEGRATION)

from transport.api import Api, dumps  # noqa: E402
from transport.store import setup_stdio  # noqa: E402


def build_handler(api, max_body):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'integration-v1'
        protocol_version = 'HTTP/1.1'

        def log_message(self, fmt, *args):
            if not self.server.quiet:
                sys.stderr.write('%s - %s\n' % (self.address_string(), fmt % args))

        def _send(self, status, payload):
            body = b'' if payload is None else dumps(payload, indent=2)
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.end_headers()
            if body and self.command != 'HEAD':
                self.wfile.write(body)

        def _read_body(self):
            length = int(self.headers.get('Content-Length') or 0)
            if length <= 0:
                return None
            if length > max_body:
                return 'too-large'
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                return 'bad-json'

        def _handle(self):
            parsed = urllib.parse.urlparse(self.path)
            payload = self._read_body() if self.command == 'POST' else None
            if payload == 'too-large':
                return self._send(413, {'error': 'тело запроса больше %s байт' % max_body})
            if payload == 'bad-json':
                return self._send(400, {'error': 'тело не разобрано как JSON'})
            try:
                status, obj = api.dispatch(self.command, parsed.path, payload,
                                           urllib.parse.parse_qs(parsed.query),
                                           token=self.headers.get('X-Integration-Token'))
            except Exception as exc:
                # Падение обработчика не должно рвать соединение без ответа:
                # отправитель иначе видит только оборванный сокет, а не причину.
                status, obj = 500, {'error': 'внутренняя ошибка очереди: %s' % exc}
            self._send(status, obj)

        def do_GET(self):
            self._handle()

        def do_HEAD(self):
            self._handle()

        def do_POST(self):
            self._handle()

        def do_OPTIONS(self):
            self._handle()

    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='http_server.py',
        description='HTTP-интерфейс очереди интеграции на http.server (для локальной проверки).')
    parser.add_argument('--root', default=None, help='корень харнесса (по умолчанию - выше integration)')
    parser.add_argument('--host', default='127.0.0.1', help='адрес прослушивания')
    parser.add_argument('--port', type=int, default=8760, help='порт (по умолчанию 8760)')
    parser.add_argument('--max-body', type=int, default=262144, help='предел размера тела запроса, байт')
    parser.add_argument('--quiet', action='store_true', help='не печатать строки доступа')
    args = parser.parse_args(argv)

    setup_stdio()
    api = Api(args.root)
    handler = build_handler(api, args.max_body)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    server.quiet = args.quiet
    print('очередь: %s' % api.store.base)
    print('слушаю http://%s:%s/api/health (Ctrl+C - стоп)' % (args.host, args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('остановлено')
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
