# -*- coding: utf-8 -*-
"""Очередь задач внешней интеграции: атомарные операции над каталогом queue\\.

Раскладка (пути относительно корня харнесса):

    queue\\tasks.jsonl               журнал задач: одна строка - одна задача (append-only)
    queue\\.watch_offset             позиция чтения журнала (ведёт watcher)
    queue\\inbox\\task_<id>.json      задача, разложенная watcher-ом и ждущая агента
    queue\\processing\\task_<id>.json задача, взятая агентом в работу
    queue\\archive\\task_<id>.json    задача, по которой записан итог
    queue\\outbox\\result_<id>.json   итог задачи - его читает GUI и внешний клиент
    queue\\failed\\*                  нечитаемые строки журнала, сбои раскладки
    queue\\answers\\answer_<id>.md    файл ответа агента (скелет делает agent.py --prepare)
    queue\\bridge.jsonl              журнал доставки в Cline (режим, URI, пути, код)

Почему журнал, а не сразу inbox: отправителей несколько (GUI на другом компьютере,
HTTP-сервер, файловый обмен), а единственный, кто раскладывает задачи по каталогам
состояний, - watcher. Один писатель журнала и один разборщик дают порядок без общей
блокировки: отправитель только дописывает строку.

Атомарность. Любой JSON пишется во временный файл `<имя>.tmp` в том же каталоге и
переименовывается `os.replace` - переименование в пределах тома атомарно, поэтому
читатель видит либо старый файл, либо новый целиком. Файлы `*.tmp` читатели
игнорируют: недописанный результат или задачу никто не примет за готовые.
"""

import contextlib
import errno
import json
import os
import random
import sys
import time
from datetime import datetime

DEFAULT_TIMEOUT_S = 1800
LOCK_TIMEOUT_S = 10.0
LOCK_STALE_S = 120.0


class QueueError(Exception):
    """Ошибка очереди: нарушена раскладка каталогов или испорчен файл."""


def now_iso():
    """Местное время в формате схемы: ГГГГ-ММ-ДДTЧЧ:ММ:СС."""
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def new_task_id():
    """Идентификатор задачи: t-<ГГГГММДД>-<ЧЧММСС>-<6 hex>."""
    tail = ''.join(random.choice('0123456789abcdef') for _ in range(6))
    return 't-%s-%s' % (datetime.now().strftime('%Y%m%d-%H%M%S'), tail)


def host_name():
    """Кто отправил задачу: <COMPUTERNAME>\\<USERNAME>."""
    user = os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
    computer = os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or ''
    if computer:
        return '%s\\%s' % (computer, user)
    return user


def setup_stdio():
    """Печать в UTF-8 независимо от кодовой страницы консоли.

    Иначе русский текст в cmd с кодовой страницей 866 приходит кракозябрами, а
    обёртки в deploy\\ задают ту же кодировку. Ошибки кодировки не критичны:
    скрипт продолжает работать, просто печатает заменяющие символы.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError, OSError):
            pass


def write_json_atomic(path, payload):
    """Записать JSON атомарно: временный файл рядом плюс os.replace."""
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=2))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_text_atomic(path, text):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


@contextlib.contextmanager
def file_lock(path, timeout=LOCK_TIMEOUT_S, stale=LOCK_STALE_S):
    """Замок на файле: O_EXCL плюс снятие зависшего замка по возрасту.

    Нужен единственному писателю журнала: два процесса, дописывающие журнал
    одновременно, могут смешать строки. Замок, оставшийся от убитого процесса,
    снимается по возрасту, иначе очередь встала бы навсегда.
    """
    deadline = time.time() + timeout
    fd = None
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            try:
                if time.time() - os.path.getmtime(path) > stale:
                    os.remove(path)
                    continue
            except OSError:
                pass
            if time.time() > deadline:
                raise QueueError('не удалось взять блокировку %s за %.0f с' % (path, timeout))
            time.sleep(0.05)
    try:
        os.write(fd, str(os.getpid()).encode('ascii'))
        yield
    finally:
        os.close(fd)
        try:
            os.remove(path)
        except OSError:
            pass


def append_line(path, payload):
    """Дописать строку в журнал: один вызов - одна строка, с блокировкой и fsync."""
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    line = json.dumps(payload, ensure_ascii=False) + '\n'
    with file_lock(path + '.lock'):
        with open(path, 'a', encoding='utf-8', newline='\n') as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())


class QueueStore(object):
    """Каталог queue\\ как очередь задач: журнал, inbox, processing, archive, outbox."""

    def __init__(self, root):
        self.root = os.path.abspath(root)
        base = os.path.join(self.root, 'queue')
        self.base = base
        self.dirs = {
            'base': base,
            'journal': os.path.join(base, 'tasks.jsonl'),
            'offset': os.path.join(base, '.watch_offset'),
            'inbox': os.path.join(base, 'inbox'),
            'processing': os.path.join(base, 'processing'),
            'archive': os.path.join(base, 'archive'),
            'outbox': os.path.join(base, 'outbox'),
            'failed': os.path.join(base, 'failed'),
            'answers': os.path.join(base, 'answers'),
            'prompts': os.path.join(base, 'prompts'),
            'bridge': os.path.join(base, 'bridge.jsonl'),
        }

    # --- раскладка -----------------------------------------------------------

    def ensure(self):
        """Создать каталоги очереди. Идемпотентно."""
        for key in ('base', 'inbox', 'processing', 'archive', 'outbox', 'failed', 'answers', 'prompts'):
            path = self.dirs[key]
            if not os.path.isdir(path):
                os.makedirs(path)

    def task_path(self, folder, task_id):
        return os.path.join(self.dirs[folder], 'task_%s.json' % task_id)

    def result_path(self, task_id, folder='outbox'):
        return os.path.join(self.dirs[folder], 'result_%s.json' % task_id)

    def answer_path(self, task_id):
        return os.path.join(self.dirs['answers'], 'answer_%s.md' % task_id)

    def rel(self, path):
        """Путь относительно корня - так его читает человек и записывает агент."""
        try:
            return os.path.relpath(path, self.root)
        except ValueError:
            return path

    # --- журнал --------------------------------------------------------------

    def append_journal(self, task):
        """Дописать задачу в журнал. Отправитель пользуется только этим методом."""
        self.ensure()
        append_line(self.dirs['journal'], task)

    def journal_read(self, offset=0, max_bytes=1048576):
        """Прочитать журнал с позиции offset, не больше max_bytes за проход.

        Возвращает (строки, новая_позиция). Неполная последняя строка не берётся:
        писатель мог успеть записать её наполовину, позиция останется прежней, и
        строка будет прочитана следующим проходом. Порция нужна, чтобы новый
        проход начинался после обработанной части журнала, а не после всего файла.
        """
        path = self.dirs['journal']
        if not os.path.isfile(path):
            return [], offset
        with open(path, 'rb') as f:
            f.seek(offset)
            data = f.read(max_bytes)
        end = data.rfind(b'\n')
        if end < 0:
            return [], offset
        chunk = data[:end + 1]
        lines = [raw.decode('utf-8') for raw in chunk.split(b'\n') if raw.strip()]
        return lines, offset + end + 1

    def read_offset(self):
        path = self.dirs['offset']
        if not os.path.isfile(path):
            return 0
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return int((f.read() or '0').strip())
        except (ValueError, OSError):
            return 0

    def write_offset(self, offset):
        self.ensure()
        write_text_atomic(self.dirs['offset'], str(int(offset)))

    def offset_age_s(self):
        """Сколько секунд назад watcher подавал признаки жизни. None - признаков нет.

        Признак - замок queue\\.watcher.lock: watcher обновляет его каждый проход, в том
        числе когда новых строк в журнале нет. Возраст позиции чтения (.watch_offset) для
        этого не годится: она пишется только при появлении строк, поэтому живой watcher на
        простое выглядел бы молчащим. Из двух отметок берётся свежая.
        """
        marks = [os.path.join(self.base, '.watcher.lock'), self.dirs['offset']]
        ages = []
        for path in marks:
            if os.path.isfile(path):
                ages.append(max(0.0, time.time() - os.path.getmtime(path)))
        if not ages:
            return None
        return min(ages)


    # --- состояния задачи ----------------------------------------------------

    def enqueue(self, task):
        """Положить задачу в inbox: её берёт агент."""
        self.ensure()
        write_json_atomic(self.task_path('inbox', task['id']), task)
        return self.task_path('inbox', task['id'])

    def claim(self):
        """Взять самую старую задачу из inbox и перенести её в processing.

        Испорченный файл не блокирует очередь: он уезжает в failed, берётся следующий.
        """
        self.ensure()
        names = sorted(n for n in os.listdir(self.dirs['inbox'])
                       if n.startswith('task_') and n.endswith('.json'))
        for name in names:
            src = os.path.join(self.dirs['inbox'], name)
            dst = os.path.join(self.dirs['processing'], name)
            try:
                os.replace(src, dst)
            except OSError:
                continue
            try:
                return read_json(dst)
            except (ValueError, OSError) as exc:
                bad = os.path.join(self.dirs['failed'], name)
                try:
                    os.replace(dst, bad)
                except OSError:
                    pass
                self.log_bridge({'event': 'bad_task', 'file': os.path.basename(bad), 'error': str(exc)})
        return None

    def complete(self, result):
        """Записать итог в outbox и перенести задачу в archive."""
        self.ensure()
        path = self.result_path(result['task_id'], 'outbox')
        write_json_atomic(path, result)
        src = self.task_path('processing', result['task_id'])
        if os.path.isfile(src):
            os.replace(src, self.task_path('archive', result['task_id']))
        return path

    def result(self, task_id):
        """Итог задачи или None. Читаются только полностью записанные файлы."""
        for folder in ('outbox', 'archive'):
            path = self.result_path(task_id, folder)
            if os.path.isfile(path):
                try:
                    return read_json(path)
                except (ValueError, OSError):
                    return None
        return None

    def state(self, task_id):
        """Где задача находится прямо сейчас."""
        if self.result(task_id) is not None:
            return 'done'
        if os.path.isfile(self.task_path('processing', task_id)):
            return 'processing'
        if os.path.isfile(self.task_path('inbox', task_id)):
            return 'pending'
        if os.path.isfile(self.task_path('archive', task_id)):
            return 'archived'
        return 'unknown'

    def journal_has(self, task_id):
        """Была ли задача вообще записана в журнал."""
        path = self.dirs['journal']
        if not os.path.isfile(path):
            return False
        marker = '"id": "%s"' % task_id
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if marker in line:
                    return True
        return False

    def stale_processing(self, timeout_s=DEFAULT_TIMEOUT_S):
        """Задачи в processing, по которым результат не записан дольше timeout_s."""
        self.ensure()
        stale = []
        moment = time.time()
        for name in sorted(os.listdir(self.dirs['processing'])):
            if not (name.startswith('task_') and name.endswith('.json')):
                continue
            path = os.path.join(self.dirs['processing'], name)
            age = moment - os.path.getmtime(path)
            if age > timeout_s:
                stale.append((name[len('task_'):-len('.json')], age, path))
        return stale

    # --- прочее --------------------------------------------------------------

    def log_bridge(self, record):
        """Запись в журнал доставки (режим, URI, пути, коды)."""
        self.ensure()
        append_line(self.dirs['bridge'], record)

    def counts(self):
        """Сколько задач в каждом состоянии - для /api/health и строки состояния GUI."""
        self.ensure()
        result = {}
        for key in ('inbox', 'processing', 'archive', 'outbox', 'failed', 'answers'):
            folder = self.dirs[key]
            result[key] = len([n for n in os.listdir(folder) if not n.endswith('.tmp')])
        journal = self.dirs['journal']
        result['journal_bytes'] = os.path.getsize(journal) if os.path.isfile(journal) else 0
        result['watch_offset'] = self.read_offset()
        result['watcher_age_s'] = self.offset_age_s()
        return result

    def recent_results(self, limit=20):
        """Последние итоги: свежие сверху. Основа для таблицы в GUI."""
        self.ensure()
        items = []
        for name in os.listdir(self.dirs['outbox']):
            if not (name.startswith('result_') and name.endswith('.json')):
                continue
            path = os.path.join(self.dirs['outbox'], name)
            items.append((os.path.getmtime(path), path))
        items.sort(reverse=True)
        out = []
        for _, path in items[:limit]:
            try:
                out.append(read_json(path))
            except (ValueError, OSError):
                continue
        return out
