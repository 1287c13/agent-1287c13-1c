# -*- coding: utf-8 -*-
"""Watcher очереди: журнал задач -> inbox -> доставка в Cline.

Единственный процесс, который раскладывает задачи по состояниям. Отправители
(GUI, HTTP-сервер, файловый обмен) только дописывают строку в queue\\tasks.jsonl;
watcher читает журнал с сохранённой позиции (queue\\.watch_offset), проверяет каждую
строку по схеме задачи и кладёт принятые в queue\\inbox, а отклонённые - в
queue\\failed с причиной.

Почему через журнал, а не сразу в inbox: отправитель на другом компьютере не может
создать файл атомарно в чужом каталоге, а дозапись строки в общий журнал - операция,
которую умеет любой протокол (файловый обмен, HTTP, ручная правка). Разбор очереди
остаётся в одном месте - здесь.

Проход watcher-а:

    1. читает порцию журнала с позиции .watch_offset (неполная строка не берётся);
    2. каждую строку проверяет (схема плюс разрешение базы) и кладёт в inbox или failed;
    3. сдвигает позицию ровно на прочитанную часть;
    4. по ключу --process берёт задачи из inbox через agent.py и доставляет их в Cline.

Два watcher-а одновременно - ошибка: они разложили бы одну строку дважды. Поэтому
процесс держит замок queue\\.watcher.lock, обновляя его отметку каждый проход: замок
живого процесса не снимается, а замок убитого через две минуты можно отобрать.

Watcher живёт до явной остановки: сбой отдельного прохода (битая строка, занятый файл,
ошибка доставки) не завершает процесс, а пишется в stderr и в queue\\bridge.jsonl
(событие watcher_error). Остановка - Ctrl+C в своём окне либо scripts\\stop-watcher.ps1,
если процесс поднят фоном (scripts\\start-watcher.ps1).
"""

import argparse
import json
import os
import sys
import time
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import agent  # noqa: E402
from task import errors_to_text, project_root, save_rejected, validate_task  # noqa: E402
from transport.store import QueueStore, now_iso, setup_stdio, write_text_atomic  # noqa: E402

BATCH_BYTES = 65536
LOCK_STALE_S = 120.0


class WatcherLock(object):
    """Замок на единственный экземпляр watcher-а: отметка обновляется каждым проходом."""

    def __init__(self, store):
        self.path = os.path.join(store.base, '.watcher.lock')

    def acquire(self, stale=LOCK_STALE_S):
        if os.path.isfile(self.path):
            age = time.time() - os.path.getmtime(self.path)
            if age < stale:
                return False
            try:
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


def reject_line(store, line, index, offset, error_text):
    """Отложить непринятую строку журнала: отправитель должен увидеть причину."""
    path = os.path.join(store.dirs['failed'], 'badline_%d.json' % (offset + index))
    write_text_atomic(path, json.dumps({'line': line, 'error': error_text},
                                       ensure_ascii=False, indent=2))
    store.log_bridge({'event': 'bad_line', 'file': os.path.basename(path), 'error': error_text})


def process_journal(store, quiet=False):
    """Разложить новые строки журнала по inbox и failed. Возвращает (принято, отклонено)."""
    offset = store.read_offset()
    accepted = 0
    rejected = 0
    while True:
        lines, new_offset = store.journal_read(offset, BATCH_BYTES)
        if not lines:
            break
        for index, line in enumerate(lines):
            try:
                raw = json.loads(line)
            except ValueError as exc:
                reject_line(store, line, index, offset, 'строка не разобрана как JSON: %s' % exc)
                rejected += 1
                continue
            if not isinstance(raw, dict):
                reject_line(store, line, index, offset,
                            'ожидается объект JSON, пришло %s' % type(raw).__name__)
                rejected += 1
                continue
            task, errors = validate_task(store.root, raw)
            if errors:
                save_rejected(store, task, errors, raw)
                store.log_bridge({'event': 'rejected', 'task_id': task.get('id'),
                                  'errors': errors, 'text': errors_to_text(task, errors)})
                rejected += 1
                continue
            store.enqueue(task)
            store.log_bridge({'event': 'enqueue', 'task_id': task['id'],
                              'source': task.get('source'), 'mode': task.get('mode'),
                              'prompt': task.get('prompt')})
            accepted += 1
        store.write_offset(new_offset)
        offset = new_offset
    if not quiet and (accepted or rejected):
        print('журнал: принято %s, отклонено %s, позиция %s'
              % (accepted, rejected, store.read_offset()))
    return accepted, rejected


def run_once(store, args):
    """Один проход: журнал плюс (по ключу --process) доставка задач из inbox."""
    accepted, rejected = process_journal(store, args.quiet)
    delivered = 0
    if args.process:
        while True:
            result = agent.process_once(store, args.deliver, args.webhook_url, not args.no_gui)
            if result is None:
                break
            delivered += 1
            if not args.quiet:
                print('задача %s: %s (%s)' % (result['task_id'], result['status'],
                                              result.get('message') or ''))
    if args.sweep or args.process:
        marked = agent.sweep(store, args.timeout)
        if marked and not args.quiet:
            print('помечено timeout: %s' % len(marked))
    return {'accepted': accepted, 'rejected': rejected, 'delivered': delivered}


def report_pass_error(store, exc):
    """Записать сбой прохода в поток и в журнал доставки: watcher не умирает молча."""
    detail = traceback.format_exc()
    sys.stderr.write('%s проход не выполнен: %s\n%s' % (now_iso(), exc, detail))
    sys.stderr.flush()
    try:
        store.log_bridge({'event': 'watcher_error',
                          'error': '%s: %s' % (type(exc).__name__, exc),
                          'traceback': detail[-2000:]})
    except Exception:
        # Журнал недоступен (например, отобрали каталог) - это не повод падать.
        pass


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog='watcher.py',
        description='Watcher очереди: строки журнала queue\\tasks.jsonl превращает в задачи inbox.')
    parser.add_argument('--root', default=None, help='корень харнесса (по умолчанию - выше integration)')
    parser.add_argument('--run', action='store_true', help='работать циклом, а не одним проходом')
    parser.add_argument('--interval', type=float, default=2.0, help='пауза между проходами цикла, с')
    parser.add_argument('--process', action='store_true', help='доставлять задачи из inbox в Cline')
    parser.add_argument('--deliver', default='uri', choices=('uri', 'lg-task', 'manual', 'echo', 'auto'),
                        help='режим доставки: uri (по умолчанию), lg-task, manual, echo, auto')
    parser.add_argument('--webhook-url', default=None, help='адрес вебхука Cline для режима lg-task')
    parser.add_argument('--no-gui', action='store_true', help='не открывать URI (проверка без Cline)')
    parser.add_argument('--sweep', action='store_true', help='разбирать застрявшие задачи даже без --process')
    parser.add_argument('--timeout', type=float, default=None, help='порог застревания, с')
    parser.add_argument('--quiet', action='store_true', help='печатать только итоговые строки')
    return parser.parse_args(argv)


def main(argv=None):
    setup_stdio()
    args = parse_args(argv)
    store = QueueStore(args.root or project_root())
    store.ensure()
    lock = WatcherLock(store)

    if not args.run:
        result = run_once(store, args)
        print('проход завершён: %s' % json.dumps(result, ensure_ascii=False))
        return 0

    if not lock.acquire():
        print('watcher уже запущен: замок %s свежий' % lock.path)
        print('если процесс убит, замок снимается сам через две минуты')
        return 1
    print('watcher запущен: журнал %s, режим %s, интервал %.1f с (Ctrl+C - стоп)'
          % (store.dirs['journal'], args.deliver, args.interval))
    passes = 0
    try:
        while True:
            try:
                result = run_once(store, args)
                lock.touch()
                passes += 1
                if not args.quiet and (result['accepted'] or result['delivered'] or result['rejected']):
                    print('%s проход %s: %s' % (now_iso(), passes, json.dumps(result, ensure_ascii=False)))
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                # Сбой одного прохода не завершает watcher: задача, отправленная из окна,
                # иначе молча остаётся в журнале. Процесс живёт, пока его не погасят явно.
                report_pass_error(store, exc)
                if not os.path.isfile(lock.path) and not lock.acquire():
                    print('замок %s перехвачен другим watcher-ом: останавливаюсь' % lock.path)
                    return 1
            time.sleep(max(0.2, args.interval))
    except KeyboardInterrupt:
        print('остановлено: проходов %s' % passes)
    finally:
        lock.release()
    return 0


if __name__ == '__main__':
    sys.exit(main())
