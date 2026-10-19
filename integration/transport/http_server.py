import argparse
import os
import sys
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, make_server

_HERE = os.path.dirname(os.path.abspath(__file__))
_INTEGRATION = os.path.dirname(_HERE)
if _INTEGRATION not in sys.path:
    sys.path.insert(0, _INTEGRATION)

from transport.store import setup_stdio
from transport.wsgi import get_api, make_app


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):

    daemon_threads = True


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
    args = parser.parse_args(argv)

    setup_stdio()
    app = make_app(args.root, args.config, debug=True)
    instance = get_api(args.root, args.config)
    host = args.host or instance.config['server']['host']
    port = args.port or instance.config['server']['port']

    server = make_server(host, port, app, server_class=ThreadingWSGIServer)
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
