import os
import shutil
import sqlite3
import tempfile
import time
from datetime import datetime, timezone

DEFAULT_DIR = os.path.join(os.path.expanduser('~'), '.cline', 'data')
COLUMNS = ('session_id', 'source', 'pid', 'started_at', 'ended_at', 'status', 'prompt', 'cwd')


def now_utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def data_dir(explicit=None):
    for candidate in (explicit, os.environ.get('CLINE_DATA_DIR'), DEFAULT_DIR):
        if candidate:
            return os.path.abspath(candidate)
    return None


def db_path(directory=None):
    directory = directory or data_dir()
    return None if not directory else os.path.join(directory, 'db', 'sessions.db')


def read_sessions(directory=None, work_dir=None, limit=200):
    source = db_path(directory)
    if not source or not os.path.isfile(source):
        return [], 'база сессий Cline не найдена: %s' % (source or 'каталог данных не определён')
    work = work_dir or tempfile.mkdtemp(prefix='cline-db-')
    free_work = work_dir is None
    try:
        if not os.path.isdir(work):
            os.makedirs(work)
        for name in os.listdir(work):
            try:
                os.remove(os.path.join(work, name))
            except OSError:
                pass
        for suffix in ('', '-wal'):
            part = source + suffix
            if os.path.isfile(part):
                shutil.copy2(part, os.path.join(work, os.path.basename(part)))
        connection = sqlite3.connect(os.path.join(work, os.path.basename(source)))
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                'SELECT %s FROM sessions ORDER BY started_at DESC LIMIT ?' % ', '.join(COLUMNS),
                (int(limit),)).fetchall()
        finally:
            connection.close()
        return [dict(row) for row in rows], 'сессий прочитано: %d' % len(rows)
    except (OSError, sqlite3.Error) as exc:
        return [], 'база сессий Cline не прочитана: %s' % exc
    finally:
        if free_work:
            shutil.rmtree(work, ignore_errors=True)


def find_session(marker, since=None, directory=None, work_dir=None, limit=200):
    if not marker:
        return None
    rows, _note = read_sessions(directory, work_dir, limit)
    for row in rows:
        if marker not in (row.get('prompt') or ''):
            continue
        if since and (row.get('started_at') or '') < since:
            continue
        return row
    return None


def wait_for_task(marker, timeout_s=15.0, interval=1.5, since=None, directory=None,
                  work_dir=None):
    timeout_s = max(0.0, float(timeout_s or 0.0))
    deadline = time.time() + timeout_s
    note = 'ожидание не выполнялось: время ожидания нулевое'
    while True:
        row = find_session(marker, since, directory, work_dir)
        if row:
            return row, 'задача подтверждена сессией Cline %s' % row.get('session_id')
        rows, note = read_sessions(directory, work_dir)
        if rows:
            note = 'новых сессий Cline с этим идентификатором нет (%s)' % note
        if time.time() >= deadline:
            break
        time.sleep(max(0.2, min(interval, 5.0)))
    return None, 'задача в Cline не появилась за %.0f с: %s' % (timeout_s, note)
