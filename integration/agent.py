import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from transport.client import ClientError, IntegrationClient
from transport.config import agent_name, load_config, project_root
from transport.store import setup_stdio, write_text_atomic

ANSWER_LABELS = (
    ('Слой', 'layer'),
    ('MCP', 'mcp'),
    ('Скиллы', 'skills'),
    ('Проверка', 'verification'),
    ('Сделано', 'done'),
    ('Не проверено', 'not_verified'),
)

ANSWER_SKELETON = """# Ответ на задачу %(id)s

%(prompt)s

Слой:
MCP:
Скиллы:
Проверка:
Сделано:
Не проверено:

---
Здесь текст ответа: что сделано, какие средства проверки вызваны и какой вывод получен.
Поля выше заполняет агент, выполнивший задачу; ниже - свободный текст отчёта.
"""


def answer_skeleton(task):
    return ANSWER_SKELETON % {'id': task.get('id') or '', 'prompt': task.get('prompt') or ''}


def prepare_answer_file(work_dir, task):
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    path = os.path.join(work_dir, 'answer.md')
    if not os.path.isfile(path):
        write_text_atomic(path, answer_skeleton(task))
    return path


def parse_answer_text(text):
    fields = {}
    for line in (text or '').splitlines():
        for label, key in ANSWER_LABELS:
            head = label + ':'
            if line.strip().startswith(head):
                value = line.strip()[len(head):].strip()
                if value and not fields.get(key):
                    fields[key] = value
                break
    fields['answer'] = (text or '').strip()
    return fields


def cline_work_dir(root):
    path = os.path.join(root, 'temp', 'cline-db')
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def work_dir_for(root, task_id):
    return os.path.join(root, 'temp', 'queue', task_id)


def make_client(cfg, args):
    url = args.server or cfg['agent']['server_url']
    key = args.key if args.key is not None else cfg['agent']['key']
    if not url:
        raise SystemExit('не задан адрес сервера: agent.server_url в deploy\\config.json '
                         'или ключ --server')
    if not key:
        raise SystemExit('не задан ключ доступа: agent.key в deploy\\config.json '
                         'или ключ --key')
    return IntegrationClient(url, key)


def print_status(item):
    if not item:
        print('задачи нет')
        return
    print('задача:   %s' % item.get('task_id'))
    print('стадия:   %s - %s' % (item.get('state'), item.get('wait_hint') or ''))
    print('создана:  %s, в работе %s с' % (item.get('created_at'), item.get('elapsed_s')))
    if item.get('agent'):
        print('агент:    %s' % item.get('agent'))
    print('клиент:   %s, режим %s, база %s' % (item.get('client'), item.get('mode'),
                                              item.get('db') or '-'))
    print('задача:   %s' % (item.get('prompt') or ''))
    if item.get('message'):
        print('пояснение: %s' % item.get('message'))
    for step in item.get('progress') or []:
        print('  %s  %-10s %s' % (step.get('at'), step.get('stage'), step.get('message') or ''))


def cmd_submit(client, args):
    if not args.action:
        raise SystemExit('--submit требует --action <что нужно сделать>; '
                         'слот <цель> (--goal) необязателен')
    payload = {
        'role': args.role,
        'action': args.action,
        'goal': args.goal,
        'mode': args.mode,
        'deliver': args.deliver,
        'timeout_s': args.timeout,
        'note': args.note,
    }
    if args.mode == 'db':
        payload['db'] = args.db
    response = client.submit(payload)
    print('задача поставлена: %s' % response.get('task_id'))
    print('формулировка: %s' % response.get('prompt'))
    print('состояние: %s' % response.get('state'))
    return 0


def cmd_write_result(client, cfg, args, root):
    path = args.file or os.path.join(work_dir_for(root, args.task), 'answer.md')
    if not os.path.isfile(path):
        raise SystemExit('файл ответа не найден: %s' % path)
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    fields = parse_answer_text(text)
    response = client.result(args.task, agent_name(cfg), args.status, text,
                             {key: fields.get(key) for key in
                              ('layer', 'mcp', 'skills', 'verification', 'done', 'not_verified')
                              if fields.get(key)},
                             args.message)
    print('результат записан: %s, состояние %s' % (args.task, response.get('state')))
    if response.get('duration_s') is not None:
        print('в работе: %s с' % response.get('duration_s'))
    return 0

    return os.path.join(root, 'temp', 'queue', task_id)


def cmd_prepare(client, args, root):
    item = client.status(args.task)
    path = prepare_answer_file(work_dir_for(root, args.task), item)
    print('файл ответа: %s' % path)
    return 0


def cmd_status(client, args):
    print_status(client.status(args.task))
    return 0


def cmd_answer(client, args, root):
    kind = 'html' if args.html else 'md'
    response = client.answer(args.task, kind)
    content = response.get('content') or ''
    if args.out:
        target = args.out
    elif kind == 'html':
        folder = os.path.join(root, 'temp')
        if not os.path.isdir(folder):
            os.makedirs(folder)
        target = os.path.join(folder, response.get('file_name') or ('answer_%s.html' % args.task))
    else:
        print(content)
        return 0
    with open(target, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(content)
    print('ответ: %s' % target)
    return 0


def cmd_list(client, args):
    data = client.history(args.limit)
    counts = data.get('counts') or {}
    print('очередь: ждут %s, в работе %s, готово %s, сбоев %s, агентов живо %s'
          % (counts.get('queued'), counts.get('processing'), counts.get('done'),
             counts.get('failed'), counts.get('agents_alive')))
    for item in data.get('items') or []:
        print('  %s  %-9s %-18s %s' % (item.get('task_id'), item.get('state'),
                                       item.get('agent') or '-',
                                       (item.get('prompt') or '')[:70]))
    return 0


def cmd_health(client):
    data = client.health()
    queue = data.get('queue') or {}
    print('сервер: %s, версия %s' % (data.get('status'), data.get('version')))
    print('очередь: ждут %s, в работе %s, готово %s, сбоев %s'
          % (queue.get('queued'), queue.get('processing'), queue.get('done'),
             queue.get('failed')))
    for item in data.get('agents') or []:
        print('агент %s: %s, задача %s, отметка %s с назад%s'
              % (item.get('name'), item.get('state'), item.get('task_id') or '-',
                 item.get('age_s'), '' if item.get('alive') else ' (молчит)'))
    for note in data.get('notes') or []:
        print('настройки: %s' % note)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog='agent.py',
        description='Командная строка интеграции: задачи, результаты и состояние очереди.')
    parser.add_argument('--root', default=None,
                        help='корень харнесса (по умолчанию - каталог выше integration)')
    parser.add_argument('--config', default=None, help='файл настроек (deploy\\config.json)')
    parser.add_argument('--server', default=None, help='адрес сервера (agent.server_url)')
    parser.add_argument('--key', default=None, help='ключ доступа (agent.key)')
    parser.add_argument('--task', default=None, help='идентификатор задачи')
    parser.add_argument('--file', default=None, help='файл ответа для --write-result')
    parser.add_argument('--status', default='done',
                        choices=('done', 'error', 'failed'),
                        help='статус результата для --write-result')
    parser.add_argument('--message', default='', help='пояснение к результату')
    parser.add_argument('--json', action='store_true', help='печатать ответ сервера как JSON')

    parser.add_argument('--submit', action='store_true', help='поставить задачу')
    parser.add_argument('--role', default='программист 1С', help='слот <роль>')
    parser.add_argument('--action', default=None, help='слот <действие>')
    parser.add_argument('--goal', default=None, help='слот <цель> (необязателен)')
    parser.add_argument('--db', default=None, help='слот <база>')
    parser.add_argument('--mode', default='db', choices=('db', 'harness'),
                        help='db - задача по базе, harness - по инструменту агента')
    parser.add_argument('--deliver', default='auto',
                        choices=('uri', 'manual', 'echo', 'auto'),
                        help='режим доставки в Cline')
    parser.add_argument('--timeout', type=int, default=1800,
                        help='сколько секунд ждать результат (по умолчанию 1800)')
    parser.add_argument('--note', default=None, help='пометка отправителя')

    parser.add_argument('--prepare', action='store_true', help='создать файл ответа')
    parser.add_argument('--write-result', action='store_true', help='записать итог задачи')
    parser.add_argument('--status-task', dest='status_task', action='store_true',
                        help='показать состояние задачи')
    parser.add_argument('--answer', dest='answer', action='store_true', help='скачать ответ')
    parser.add_argument('--html', action='store_true', help='ответ страницей HTML')
    parser.add_argument('--out', default=None, help='файл для --answer')
    parser.add_argument('--list', action='store_true', help='последние задачи')
    parser.add_argument('--limit', type=int, default=20, help='сколько задач в --list')
    parser.add_argument('--health', action='store_true', help='состояние сервера')
    return parser


def main(argv=None):
    setup_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    root = project_root(args.root)
    cfg, notes = load_config(root, args.config)
    if args.server:
        cfg['agent']['server_url'] = args.server
    if args.key:
        cfg['agent']['key'] = args.key

    try:
        client = make_client(cfg, args)
        if args.submit:
            return cmd_submit(client, args)
        if args.write_result:
            if not args.task:
                raise SystemExit('--write-result требует --task <идентификатор>')
            return cmd_write_result(client, cfg, args, root)
        if args.prepare:
            if not args.task:
                raise SystemExit('--prepare требует --task <идентификатор>')
            return cmd_prepare(client, args, root)
        if args.status_task:
            if not args.task:
                raise SystemExit('--status-task требует --task <идентификатор>')
            return cmd_status(client, args)
        if args.answer:
            if not args.task:
                raise SystemExit('--answer требует --task <идентификатор>')
            return cmd_answer(client, args, root)
        if args.list:
            return cmd_list(client, args)
        if args.health:
            return cmd_health(client)
        print('не задано действие: --submit, --write-result, --prepare, --status-task, '
              '--answer, --list, --health')
        for note in notes:
            print('настройки: %s' % note)
        return 1
    except ClientError as exc:
        print('ошибка интеграции: %s' % exc)
        return 1


if __name__ == '__main__':
    sys.exit(main())
