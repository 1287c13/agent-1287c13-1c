import argparse
import json
import os
import shutil
import sys
import time
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import agent
import bridge
from transport.client import ClientError, IntegrationClient
from transport.config import agent_name, load_config, project_root
from transport.store import setup_stdio

DEFAULT_INTERVAL_S = 2.0
DEFAULT_IDLE_S = 15.0
LOCK_STALE_S = 120.0
RECLAIM_EVERY_S = 60.0
PROGRESS_EVERY_S = 30.0


class WatcherLock(object):

    def __init__(self, root):
        self.path = os.path.join(root, 'temp', 'queue', '.watcher.lock')

    def acquire(self, stale=LOCK_STALE_S):
        folder = os.path.dirname(self.path)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        if os.path.isfile(self.path):
            try:
                if time.time() - os.path.getmtime(self.path) < stale:
                    return False
                os.remove(self.path)
            except OSError:
                return False
        try:
            with open(self.path, 'w', encoding='ascii') as f:
                f.write('pid=%s\n' % os.getpid())
        except OSError:
            return False
        return True

    def touch(self):
        try:
            os.utime(self.path, None)
        except OSError:
            pass

    def release(self):
        try:
            os.remove(self.path)
        except OSError:
            pass


def task_work_dir(root, task_id):
    return os.path.join(root, 'temp', 'queue', task_id)


def drop_work_dir(path):
    shutil.rmtree(path, ignore_errors=True)


def handle_task(client, cfg, task, mode, root, allow_gui=True):
    task_id = task['id']
    agent_id = agent_name(cfg)
    work = task_work_dir(root, task_id)
    agent.prepare_answer_file(work, task)

    delivery = bridge.deliver(task, work, mode,
                              allow_gui=allow_gui,
                              confirm_timeout=None,
                              attempts=3,
                              cline_data=None,
                              cline_work_dir=agent.cline_work_dir(root))
    print('задача %s: доставка %s (%s)' % (task_id, delivery.get('status'),
                                           delivery.get('message') or ''))

    if delivery.get('status') != 'delivered':
        client.result(task_id, agent_id, 'error', '', {'delivery': delivery.get('mode') or mode},
                      delivery.get('message') or 'доставка не выполнена')
        drop_work_dir(work)
        return {'task_id': task_id, 'state': 'error', 'message': delivery.get('message') or ''}

    fields = {'delivery': delivery.get('mode') or mode,
              'confirmed': bool(delivery.get('confirmed')),
              'cline_session': delivery.get('cline_session') or '',
              'cline_note': delivery.get('cline_note') or ''}
    client.progress(task_id, agent_id, 'delivered',
                    delivery.get('message') or 'задача передана в Cline')

    if mode == 'echo':
        answer = ('режим echo: задача %s прошла цепочку сервер -> watcher -> рабочий каталог. '
                  'Cline не вызывался, ответ сформирован watcher-ом для проверки.'
                  % task_id)
        client.result(task_id, agent_id, 'done', answer, fields,
                      'режим echo: проверка цепочки без Cline')
        drop_work_dir(work)
        return {'task_id': task_id, 'state': 'done', 'message': 'echo'}

    return wait_for_result(client, cfg, task, work, fields)



def wait_for_result(client, cfg, task, work, fields):
    task_id = task['id']
    agent_id = agent_name(cfg)
    answer_path = os.path.join(work, 'answer.md')
    limit = int(task.get('timeout_s') or 0) or 1800
    deadline = time.time() + limit
    last_touch = 0.0
    while time.time() < deadline:
        current = None
        try:
            current = client.status(task_id)
        except ClientError as exc:
            print('состояние задачи %s не прочитано: %s' % (task_id, exc))
        if current and current.get('state') in ('done', 'error', 'failed', 'timeout'):
            drop_work_dir(work)
            return {'task_id': task_id, 'state': current.get('state'),
                    'message': current.get('message') or ''}
        if time.time() - last_touch >= PROGRESS_EVERY_S:
            try:
                client.progress(task_id, agent_id, 'running', 'агент выполняет задачу')
            except ClientError as exc:
                print('стадия running не отправлена: %s' % exc)
            last_touch = time.time()
        time.sleep(5.0)

    print('задача %s: результат не записан за %d с, файл ответа %s'
          % (task_id, limit, answer_path))
    return {'task_id': task_id, 'state': 'waiting', 'message': 'результат не записан'}


def run_once(client, cfg, mode, root, allow_gui=True):
    agent_id = agent_name(cfg)
    claimed = client.claim(agent_id, (cfg.get('agent') or {}).get('claim_ttl_s'))
    task = claimed.get('task')
    if not task:
        return False
    result = handle_task(client, cfg, task, mode, root, allow_gui=allow_gui)
    print('задача %s: %s' % (task['id'], result.get('state')))
    return True



def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='watcher.py',
        description='Watcher очереди: забирает задачи с сервера и передаёт их в Cline.')
    parser.add_argument('--root', default=None, help='корень харнесса')
    parser.add_argument('--config', default=None, help='файл настроек (deploy\\config.json)')
    parser.add_argument('--server', default=None, help='адрес сервера (agent.server_url)')
    parser.add_argument('--key', default=None, help='ключ агента (agent.key)')
    parser.add_argument('--agent', default=None, help='имя агента (agent.name)')
    parser.add_argument('--run', action='store_true', help='работать циклом, а не одним проходом')
    parser.add_argument('--deliver', default=None,
                        choices=('uri', 'manual', 'echo', 'auto'),
                        help='режим доставки: uri (по умолчанию), manual, echo')
    parser.add_argument('--interval', type=float, default=0, help='пауза при работе, с')
    parser.add_argument('--idle-interval', type=float, default=0,
                        help='пауза, когда очередь пуста, с')
    parser.add_argument('--no-gui', action='store_true', help='не открывать URI (проверка)')
    return parser.parse_args(argv)


def main(argv=None):
    setup_stdio()
    args = parse_args(argv)
    root = project_root(args.root)
    cfg, _notes = load_config(root, args.config)
    if args.server:
        cfg['agent']['server_url'] = args.server
    if args.key:
        cfg['agent']['key'] = args.key
    if args.agent:
        cfg['agent']['name'] = args.agent
    if not cfg['agent']['server_url']:
        raise SystemExit('не задан адрес сервера: agent.server_url в deploy\\config.json '
                         'или ключ --server')
    client = IntegrationClient(cfg['agent']['server_url'], cfg['agent']['key'])
    mode = args.deliver or cfg['agent']['deliver']
    if mode == 'auto':
        mode = 'uri'
    interval = args.interval or cfg['agent']['interval'] or DEFAULT_INTERVAL_S
    idle = args.idle_interval or cfg['agent']['idle_interval'] or DEFAULT_IDLE_S
    allow_gui = not args.no_gui

    if not args.run:
        worked = run_once(client, cfg, mode, root, allow_gui=allow_gui)
        if not worked:
            print('очередь пуста: задач нет')
        return 0

    lock = WatcherLock(root)
    if not lock.acquire():
        print('watcher уже запущен: замок %s свежий' % lock.path)
        print('если процесс убит, замок снимается сам через две минуты')
        return 1
    print('watcher запущен: сервер %s, агент %s, режим %s, пауза %.0f/%.0f с (Ctrl+C - стоп)'
          % (cfg['agent']['server_url'], agent_name(cfg), mode, interval, idle))
    passes = 0
    idle_passes = 0
    last_reclaim = 0.0
    try:
        while True:
            try:
                worked = run_once(client, cfg, mode, root, allow_gui=allow_gui)
                lock.touch()
            except ClientError as exc:
                print('%s сервер недоступен: %s' % (time.strftime('%H:%M:%S'), exc))
                worked = False
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                print('%s проход не выполнен: %s' % (time.strftime('%H:%M:%S'), exc))
                sys.stderr.write('%s\n' % traceback.format_exc())
                worked = False
            passes += 1
            if worked:
                idle_passes = 0
                time.sleep(max(0.5, interval))
                continue
            idle_passes += 1
            if time.time() - last_reclaim >= RECLAIM_EVERY_S:
                last_reclaim = time.time()
                try:
                    client.reclaim()
                except ClientError:
                    pass
            time.sleep(min(idle, interval * (2 ** min(idle_passes - 1, 3))))
    except KeyboardInterrupt:
        print('остановлено: проходов %s' % passes)
    finally:
        lock.release()
    return 0


if __name__ == '__main__':
    sys.exit(main())
