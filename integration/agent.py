# -*- coding: utf-8 -*-
"""Агент очереди: взять задачу, доставить в Cline, принять и записать результат.

Роли файла:

    --process      взять самую старую задачу из queue\\inbox, доставить её в Cline
                   выбранным режимом и записать в outbox итог «delivered» (задача
                   передана, ответ ждёт записи);
    --run          то же в цикле плюс разбор застрявших задач (--sweep);
    --prepare      создать файл ответа со скелетом полей для конкретной задачи;
    --write-result записать итог задачи из файла ответа (это делает Cline, выполнив
                   задачу: файл ответа и команда записи описаны в docs\07-external-integration.md);
    --sweep        пометить задачи, по которым результат не записан дольше timeout_s;
    --list         показать, что лежит в очереди.

Почему результат пишет отдельный вызов: Cline работает в другом процессе, и очередь
для него - внешний объект. Обратный путь устроен так же, как прямой: файл ответа плюс
одна команда, которая превращает его в результат для GUI. Итог всегда проходит через
integration\\task.py (схема result_schema.json), поэтому отправитель получает ответ
одной формы, а не текст, зависящий от режима доставки.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import bridge  # noqa: E402
from task import errors_to_text, make_task, project_root, validate_task  # noqa: E402
from transport.schema import read_schema, validate  # noqa: E402
from transport.store import QueueStore, now_iso, read_json, setup_stdio, write_text_atomic  # noqa: E402

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
    """Скелет файла ответа: те же четыре строки преамбулы и три строки отчёта."""
    return ANSWER_SKELETON % {'id': task['id'], 'prompt': task.get('prompt') or ''}


def prepare_answer(store, task):
    """Создать файл ответа, если его ещё нет. Существующий файл не перезаписывается."""
    path = store.answer_path(task['id'])
    if not os.path.isfile(path):
        write_text_atomic(path, answer_skeleton(task))
    return path


def parse_answer_text(text):
    """Разобрать файл ответа: поля отчёта плюс текст целиком.

    Строка вида «Проверка: ...» попадает в поле; всё остальное считается текстом
    ответа. Первое непустое вхождение метки побеждает: скелет уже содержит пустые
    метки, поэтому заполненная строка может стоять ниже.
    """
    fields = {}
    body = []
    for line in (text or '').splitlines():
        matched = False
        for label, key in ANSWER_LABELS:
            head = label + ':'
            if line.strip().startswith(head):
                value = line.strip()[len(head):].strip()
                if value and not fields.get(key):
                    fields[key] = value
                matched = True
                break
        if not matched:
            body.append(line)
    fields['answer'] = (text or '').strip()
    return fields


def build_result(task, status, store, delivery=None, fields=None, message=''):
    """Собрать итог задачи по схеме result_schema.json."""
    delivery = delivery or {}
    fields = fields or {}
    result = {
        'task_id': task['id'],
        'status': status,
        'written_at': now_iso(),
        'started_at': task.get('_started_at') or '',
        'prompt_file': delivery.get('prompt_file') or '',
        'answer_file': delivery.get('answer_file') or store.rel(store.answer_path(task['id'])),
        'answer': fields.get('answer') or message or 'ответ не записан',
        'message': message,
    }
    if delivery.get('mode'):
        result['delivery'] = delivery['mode']
    for key in ('layer', 'mcp', 'skills', 'verification', 'done', 'not_verified'):
        if fields.get(key):
            result[key] = fields[key]
    started = task.get('_started_ts')
    if started:
        result['duration_s'] = round(max(0.0, time.time() - started), 1)
    return result


def check_result(store, result):
    """Проверить итог по схеме. Ошибки возвращаются списком, запись не отменяется."""
    schema = read_schema(os.path.join(store.root, 'integration', 'schemas', 'result_schema.json'))
    return validate(result, schema, 'результат')


def process_once(store, deliver_mode='uri', webhook_url=None, allow_gui=True):
    """Взять одну задачу из inbox, доставить в Cline и записать итог «delivered»."""
    task = store.claim()
    if task is None:
        return None
    source = store.task_path('processing', task['id'])
    task['_started_at'] = now_iso()
    task['_started_ts'] = time.time()
    mode = deliver_mode
    if task.get('deliver') and task['deliver'] != 'auto' and deliver_mode == 'auto':
        mode = task['deliver']
    prepare_answer(store, task)
    delivery = bridge.deliver(task, mode, store, webhook_url=webhook_url, allow_gui=allow_gui)
    status = 'delivered' if delivery.get('status') == 'delivered' else 'error'
    result = build_result(task, status, store, delivery, message=delivery.get('message') or '')
    result['delivered_at'] = now_iso()
    problems = check_result(store, result)
    if problems:
        result['schema_errors'] = problems
    store.complete(result)
    return result


def sweep(store, timeout_s=None):
    """Задачи в processing без результата дольше timeout_s: пометить как timeout."""
    stale = store.stale_processing(timeout_s or 0)
    done = []
    for task_id, age, path in stale:
        try:
            task = read_json(path)
        except (ValueError, OSError):
            continue
        limit = int(task.get('timeout_s') or 0)
        if limit and age < limit:
            continue
        task['_started_ts'] = time.time() - age
        task['_started_at'] = datetime.fromtimestamp(time.time() - age).strftime('%Y-%m-%dT%H:%M:%S')
        result = build_result(task, 'timeout', store, {},
                              message='результат не записан за %.0f с; задача помечена timeout' % age)
        store.complete(result)
        done.append(result)
    return done


def write_result(store, task_id, answer_path=None, status='done', message='', quiet=False):
    """Записать итог задачи: из файла ответа."""
    path = answer_path or store.answer_path(task_id)
    if not os.path.isfile(path):
        raise SystemExit('файл ответа не найден: %s' % path)
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    task = {'id': task_id}
    source = store.task_path('processing', task_id)
    if os.path.isfile(source):
        try:
            task = read_json(source)
        except (ValueError, OSError):
            task = {'id': task_id}
        task['_started_ts'] = os.path.getmtime(source)
        task['_started_at'] = datetime.fromtimestamp(task['_started_ts']).strftime('%Y-%m-%dT%H:%M:%S')
    fields = parse_answer_text(text)
    previous = store.result(task_id) or {}
    result = build_result(task, status, store, {}, fields=fields, message=message)
    result['answer_file'] = store.rel(path)
    # Доставка уже отмечена в итоге, записанном при передаче задачи: сохраняем её,
    # иначе окончательный результат терял бы режим доставки и время передачи.
    for key in ('delivery', 'prompt_file', 'delivered_at', 'started_at', 'duration_s'):
        if not result.get(key) and previous.get(key):
            result[key] = previous[key]
    if not result.get('started_at'):
        result.pop('started_at', None)
    problems = check_result(store, result)
    if problems:
        result['schema_errors'] = problems
    store.complete(result)
    if not quiet:
        print('результат записан: %s' % store.rel(store.result_path(task_id)))
        print('статус: %s' % status)
    return result


def describe_queue(store, limit=20):
    """Состояние очереди: счётчики и последние итоги."""
    counts = store.counts()
    print('каталог очереди: %s' % store.base)
    print('журнал: %s байт, прочитано watcher-ом до байта %s' % (
        counts['journal_bytes'], counts['watch_offset']))
    age = counts['watcher_age_s']
    print('watcher: %s' % ('отметки нет' if age is None else 'последний проход %.1f с назад' % age))
    print('inbox=%s processing=%s outbox=%s archive=%s failed=%s' % (
        counts['inbox'], counts['processing'], counts['outbox'],
        counts['archive'], counts['failed']))
    results = store.recent_results(limit)
    if results:
        print('последние итоги:')
        for item in results:
            print('  %s  %-10s %s' % (item.get('task_id'), item.get('status'),
                                      (item.get('message') or '')[:60]))
    return counts


def load_task(store, task_id):
    """Найти задачу по идентификатору в processing, inbox или archive."""
    for folder in ('processing', 'inbox', 'archive'):
        path = store.task_path(folder, task_id)
        if os.path.isfile(path):
            try:
                return read_json(path)
            except (ValueError, OSError):
                break
    return {'id': task_id, 'prompt': ''}


def emit(result, as_json):
    """Печать итога: компактная строка для человека или полный JSON для проверок."""
    if result is None:
        print('очередь пуста: задач в inbox нет')
        return
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print('задача %s: %s (%s)' % (result.get('task_id'), result.get('status'),
                                      result.get('message') or ''))


def build_parser():
    parser = argparse.ArgumentParser(
        prog='agent.py',
        description='Агент очереди интеграции: доставка задач в Cline и запись результатов.')
    parser.add_argument('--root', default=None,
                        help='корень харнесса (по умолчанию - каталог выше integration)')
    parser.add_argument('--deliver', default='uri', choices=('uri', 'lg-task', 'manual', 'echo', 'auto'),
                        help='режим доставки: uri (по умолчанию), lg-task, manual, echo, auto')
    parser.add_argument('--webhook-url', default=None, help='адрес вебхука Cline для режима lg-task')
    parser.add_argument('--no-gui', action='store_true',
                        help='не открывать URI в оболочке Windows (проверка цепочки без Cline)')
    parser.add_argument('--process', action='store_true', help='взять одну задачу из inbox и доставить её')
    parser.add_argument('--run', action='store_true', help='цикл: доставка задач и разбор застрявших')
    parser.add_argument('--interval', type=float, default=2.0, help='пауза между проходами цикла, с')
    parser.add_argument('--prepare', action='store_true', help='создать файл ответа для задачи --task')
    parser.add_argument('--write-result', action='store_true', help='записать итог задачи из файла ответа')
    parser.add_argument('--task', default=None, help='идентификатор задачи: t-...')
    parser.add_argument('--file', default=None, help='файл ответа (по умолчанию queue\\answers\\answer_<id>.md)')
    parser.add_argument('--status', default='done', choices=('done', 'error'), help='статус итога при --write-result')
    parser.add_argument('--message', default='', help='короткое пояснение к итогу')
    parser.add_argument('--sweep', action='store_true', help='пометить застрявшие задачи как timeout')
    parser.add_argument('--timeout', type=float, default=None, help='порог застревания, с')
    parser.add_argument('--list', action='store_true', help='показать состояние очереди')
    parser.add_argument('--limit', type=int, default=20, help='сколько последних итогов показать')
    parser.add_argument('--json', action='store_true', help='печатать результат как JSON')
    parser.add_argument('--quiet', action='store_true', help='печатать только суть')
    parser.add_argument('--submit', action='store_true',
                        help='поставить задачу из командной строки: нужен --action; --goal необязателен')
    parser.add_argument('--role', default='программист 1С', help='роль для --submit (роль задаёт и режим задачи)')
    parser.add_argument('--action', default=None, help='слот <действие> для --submit')
    parser.add_argument('--goal', default=None, help='слот <цель> для --submit (необязателен)')
    parser.add_argument('--db', default=None, help='слот <база> для --submit')
    parser.add_argument('--mode', default='db', choices=('db', 'harness'), help='режим задачи для --submit')
    parser.add_argument('--source', default='cli', choices=('cli', 'gui', 'http', 'file'),
                        help='отправитель задачи для --submit')
    return parser


def main(argv=None):
    setup_stdio()
    args = build_parser().parse_args(argv)
    root = args.root or project_root()
    store = QueueStore(root)
    store.ensure()
    acted = False

    if args.submit:
        if not args.action:
            raise SystemExit('--submit требует --action <что нужно сделать>; '
                             'слот <цель> (--goal) необязателен')
        task = make_task(args.role, args.action, args.goal, args.db, args.mode,
                         source=args.source, deliver=args.deliver)
        task, errors = validate_task(root, task)
        if errors:
            print(errors_to_text(task, errors))
            return 1
        store.append_journal(task)
        print('задача отправлена: %s' % task['id'])
        print('формулировка: %s' % task['prompt'])
        print('журнал: %s' % store.rel(store.dirs['journal']))
        acted = True

    if args.prepare:
        if not args.task:
            raise SystemExit('--prepare требует --task <идентификатор>')
        task = load_task(store, args.task)
        path = prepare_answer(store, task)
        print('файл ответа: %s' % store.rel(path))
        acted = True

    if args.write_result:
        if not args.task:
            raise SystemExit('--write-result требует --task <идентификатор>')
        result = write_result(store, args.task, args.file, args.status, args.message, args.quiet)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        acted = True

    if args.sweep:
        marked = sweep(store, args.timeout)
        print('помечено timeout: %s' % len(marked))
        acted = True

    if args.run:
        print('цикл агента: режим %s, интервал %.1f с (прерывание - Ctrl+C)' % (args.deliver, args.interval))
        acted = True
        try:
            while True:
                emit(process_once(store, args.deliver, args.webhook_url, not args.no_gui), args.json)
                sweep(store, args.timeout)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print('остановлено')
        return 0

    if args.process:
        emit(process_once(store, args.deliver, args.webhook_url, not args.no_gui), args.json)
        acted = True

    if args.list or not acted:
        describe_queue(store, args.limit)
    return 0


if __name__ == '__main__':
    sys.exit(main())
