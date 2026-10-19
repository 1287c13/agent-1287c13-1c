import contextlib
import errno
import json
import os
import random
import re
import sys
import time
from datetime import datetime

DEFAULT_TIMEOUT_S = 1800
DEFAULT_CLAIM_TTL_S = 300
MAX_ATTEMPTS = 3
MAX_PROGRESS = 50
LOCK_TIMEOUT_S = 10.0
LOCK_STALE_S = 120.0

STAGE_ORDER = {'queued': 0, 'claimed': 1, 'delivered': 2, 'running': 3}
TERMINAL = ('done', 'error', 'failed', 'timeout')
RESULT_STATUSES = ('done', 'error', 'failed', 'timeout')

HINTS = {
    'queued': 'задача ждёт агента',
    'claimed': 'агент взял задачу и готовит доставку',
    'delivered': 'задача передана в Cline, ждём ответа',
    'running': 'агент выполняет задачу',
    'done': 'ответ получен',
    'error': 'сбой доставки: задача не выполнена',
    'failed': 'задача не выполнена',
    'timeout': 'истекло время ожидания результата',
}


class QueueError(Exception):
    pass


def now_iso(moment=None):
    return datetime.fromtimestamp(moment or time.time()).strftime('%Y-%m-%dT%H:%M:%S')


def new_task_id(moment=None):
    tail = ''.join(random.choice('0123456789abcdef') for _ in range(6))
    return 't-%s-%s' % (datetime.fromtimestamp(moment or time.time()).strftime('%Y%m%d-%H%M%S'), tail)


def host_name():
    user = os.environ.get('USERNAME') or os.environ.get('USER') or 'unknown'
    computer = os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or ''
    return '%s\\%s' % (computer, user) if computer else user


def setup_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError, OSError):
            pass



def write_json_atomic(path, payload):
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
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    line = json.dumps(payload, ensure_ascii=False) + '\n'
    with file_lock(path + '.lock'):
        with open(path, 'a', encoding='utf-8', newline='\n') as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())


def safe_name(name):
    clean = re.sub(r'[^A-Za-z0-9_.@-]+', '_', (name or 'agent').strip())
    return clean.strip('._')[:80] or 'agent'


def preview(text, limit=240):
    value = re.sub(r'\s+', ' ', (text or '')).strip()
    return value if len(value) <= limit else value[:limit - 1] + '…'



class QueueStore(object):

    def __init__(self, base):
        self.base = os.path.abspath(base)
        self.dirs = {name: os.path.join(self.base, name) for name in
                     ('inbox', 'processing', 'archive', 'outbox', 'failed', 'agents')}
        self.events = os.path.join(self.base, 'events.jsonl')


    def ensure(self):
        if not os.path.isdir(self.base):
            os.makedirs(self.base)
        for path in self.dirs.values():
            if not os.path.isdir(path):
                os.makedirs(path)

    def task_path(self, folder, task_id):
        return os.path.join(self.dirs[folder], 'task_%s.json' % task_id)

    def result_path(self, task_id):
        return os.path.join(self.dirs['outbox'], 'result_%s.json' % task_id)

    def rel(self, path):
        try:
            return os.path.relpath(path, self.base)
        except ValueError:
            return path

    def event(self, kind, **fields):
        try:
            self.ensure()
            record = {'event': kind, 'at': now_iso(), 'ts': round(time.time(), 3)}
            record.update(fields)
            append_line(self.events, record)
        except (OSError, QueueError, ValueError):
            pass


    def _locate(self, task_id):
        if not task_id:
            return None, None
        for folder in ('processing', 'inbox', 'archive'):
            path = self.task_path(folder, task_id)
            if os.path.isfile(path):
                return folder, path
        return None, None

    def task(self, task_id):
        _folder, path = self._locate(task_id)
        if not path:
            return None
        try:
            return read_json(path)
        except (ValueError, OSError):
            return None

    def result(self, task_id):
        path = self.result_path(task_id)
        if not os.path.isfile(path):
            return None
        try:
            return read_json(path)
        except (ValueError, OSError):
            return None

    def _remember(self, task, stage, message=''):
        items = list(task.get('progress') or [])
        items.append({'stage': stage, 'at': now_iso(), 'message': preview(message, 400)})
        task['progress'] = items[-MAX_PROGRESS:]
        task['state'] = stage
        task['stage'] = stage
        task['updated_at'] = now_iso()
        task['updated_ts'] = round(time.time(), 3)

    def _touch_claim(self, task, ttl_s=None):
        ttl = int(ttl_s or task.get('claim_ttl_s') or DEFAULT_CLAIM_TTL_S)
        task['claim_ttl_s'] = ttl


    def enqueue(self, task):
        self.ensure()
        task = dict(task)
        task.setdefault('id', new_task_id())
        task.setdefault('created_at', now_iso())
        task['created_ts'] = round(time.time(), 3)
        task['attempts'] = int(task.get('attempts') or 0)
        self._remember(task, 'queued', 'задача поставлена в очередь')
        write_json_atomic(self.task_path('inbox', task['id']), task)
        self.event('task_created', task_id=task['id'], client=task.get('client'),
                   mode=task.get('mode'), db=task.get('db'), source=task.get('source'))
        return task

    def reject(self, payload, errors, task_id=None):
        self.ensure()
        task_id = task_id or new_task_id()
        path = os.path.join(self.dirs['failed'], 'rejected_%s.json' % task_id)
        write_json_atomic(path, {'task': payload, 'errors': list(errors),
                                 'rejected_at': now_iso()})
        self.event('rejected', task_id=task_id, errors=list(errors),
                   client=(payload or {}).get('client') if isinstance(payload, dict) else None)
        return path


    def claim(self, agent, ttl_s=DEFAULT_CLAIM_TTL_S):
        self.ensure()
        self.reclaim_stale()
        self.sweep_timeouts()
        names = []
        for name in os.listdir(self.dirs['inbox']):
            if not (name.startswith('task_') and name.endswith('.json')):
                continue
            try:
                created = float(read_json(os.path.join(self.dirs['inbox'], name))
                                .get('created_ts') or 0)
            except (ValueError, OSError):
                created = 0.0
            names.append((created, name))
        names.sort()
        now = time.time()
        for _created, name in names:
            src = os.path.join(self.dirs['inbox'], name)
            dst = os.path.join(self.dirs['processing'], name)
            try:
                os.replace(src, dst)
            except OSError:
                continue
            try:
                task = read_json(dst)
            except (ValueError, OSError) as exc:
                try:
                    os.replace(dst, os.path.join(self.dirs['failed'], name))
                except OSError:
                    pass
                self.event('bad_task', file=name, error=str(exc))
                continue
            task['attempts'] = int(task.get('attempts') or 0) + 1
            task['agent'] = agent
            task['claimed_at'] = now_iso(now)
            task['claimed_ts'] = round(now, 3)
            task['claim_ttl_s'] = int(ttl_s)
            task['claim_expires_ts'] = round(now + int(ttl_s), 3)
            task['deadline_ts'] = round(now + int(task.get('timeout_s') or DEFAULT_TIMEOUT_S), 3)
            self._remember(task, 'claimed', 'задачу взял агент %s' % agent)
            try:
                write_json_atomic(dst, task)
            except OSError as exc:
                self.event('claim_write_error', task_id=task.get('id'), error=str(exc))
            self.event('claimed', task_id=task.get('id'), agent=agent,
                       attempts=task['attempts'])
            self.touch_agent(agent, {'state': 'busy', 'task_id': task.get('id')})
            return task
        self.touch_agent(agent, {'state': 'idle', 'task_id': None})
        return None


    def progress(self, task_id, agent, stage, message=''):
        self.ensure()
        if stage not in STAGE_ORDER:
            return False, 'недопустимая стадия: %s' % stage, None
        folder, path = self._locate(task_id)
        if not path:
            return False, 'задача не найдена', None
        try:
            task = read_json(path)
        except (ValueError, OSError) as exc:
            return False, 'файл задачи не прочитан: %s' % exc, None
        state = task.get('state') or 'queued'
        if state in TERMINAL:
            return False, 'задача уже завершена (%s)' % state, task
        current = task.get('stage') or state
        accepted = STAGE_ORDER.get(stage, 0) >= STAGE_ORDER.get(current, 0)
        if accepted:
            self._remember(task, stage, message or HINTS.get(stage, ''))
        self._touch_claim(task)
        try:
            write_json_atomic(path, task)
        except OSError as exc:
            return False, 'файл задачи не записан: %s' % exc, task
        self.event('progress', task_id=task_id, agent=agent, stage=stage,
                   accepted=accepted, message=preview(message, 200))
        if agent:
            self.touch_agent(agent, {'state': 'busy', 'task_id': task_id})
        if not accepted:
            return True, 'стадия %s уже пройдена' % stage, task
        return True, '', task

    def complete(self, task_id, agent=None, status='done', answer='', fields=None,
                 message=''):
        self.ensure()
        status = status if status in RESULT_STATUSES else 'error'
        folder, path = self._locate(task_id)
        if not path:
            return None
        try:
            task = read_json(path)
        except (ValueError, OSError):
            return None
        if (task.get('state') or '') in TERMINAL:
            return None
        now = time.time()
        fields = fields or {}
        result = {
            'task_id': task_id,
            'status': status,
            'state': status,
            'written_at': now_iso(now),
            'finished_at': now_iso(now),
            'finished_ts': round(now, 3),
            'created_at': task.get('created_at') or '',
            'claimed_at': task.get('claimed_at') or '',
            'agent': agent or task.get('agent') or '',
            'client': task.get('client') or '',
            'mode': task.get('mode') or '',
            'db': task.get('db') or '',
            'role': task.get('role') or '',
            'prompt': task.get('prompt') or '',
            'attempts': task.get('attempts') or 0,
            'answer': answer or message or 'ответ не записан',
            'message': message or '',
        }
        for key in ('layer', 'mcp', 'skills', 'verification', 'done', 'not_verified',
                    'delivery', 'confirmed', 'cline_session', 'cline_note'):
            if fields.get(key) is not None and fields.get(key) != '':
                result[key] = fields[key]
        if task.get('claimed_ts'):
            result['duration_s'] = round(max(0.0, now - float(task['claimed_ts'])), 1)
        write_json_atomic(self.result_path(task_id), result)

        task['agent'] = result['agent']
        task['finished_ts'] = result['finished_ts']
        task['finished_at'] = result['finished_at']
        self._remember(task, status, message or HINTS.get(status, ''))
        write_json_atomic(path, task)
        archive = self.task_path('archive', task_id)
        if folder != 'archive':
            try:
                os.replace(path, archive)
            except OSError as exc:
                self.event('archive_error', task_id=task_id, error=str(exc))
        self.event('finished', task_id=task_id, status=status, agent=result['agent'],
                   message=preview(message, 200))
        if result['agent']:
            self.touch_agent(result['agent'], {'state': 'idle', 'task_id': None})
        return result



    def reclaim_stale(self):
        self.ensure()
        now = time.time()
        actions = []
        for name in sorted(os.listdir(self.dirs['processing'])):
            if not (name.startswith('task_') and name.endswith('.json')):
                continue
            path = os.path.join(self.dirs['processing'], name)
            try:
                task = read_json(path)
            except (ValueError, OSError):
                continue
            if (task.get('state') or '') in TERMINAL:
                continue
            expires = task.get('claim_expires_ts')
            if not expires or float(expires) > now:
                continue
            task_id = task.get('id') or name[len('task_'):-len('.json')]
            agent = task.get('agent') or ''
            if int(task.get('attempts') or 0) >= MAX_ATTEMPTS:
                self.complete(task_id, agent, 'failed', '',
                              message='агент не завершил задачу за %d попытки' % MAX_ATTEMPTS)
                actions.append({'task_id': task_id, 'action': 'failed'})
                continue
            task['agent'] = None
            task['claimed_ts'] = 0
            task['claim_expires_ts'] = 0
            self._remember(task, 'queued', 'claim истёк: задача возвращена в очередь')
            try:
                write_json_atomic(path, task)
                os.replace(path, self.task_path('inbox', task_id))
            except OSError as exc:
                self.event('reclaim_error', task_id=task_id, error=str(exc))
                continue
            self.event('reclaimed', task_id=task_id, agent=agent)
            actions.append({'task_id': task_id, 'action': 'requeued'})
        return actions

    def sweep_timeouts(self):
        self.ensure()
        now = time.time()
        done = []
        for name in sorted(os.listdir(self.dirs['processing'])):
            if not (name.startswith('task_') and name.endswith('.json')):
                continue
            path = os.path.join(self.dirs['processing'], name)
            try:
                task = read_json(path)
            except (ValueError, OSError):
                continue
            if (task.get('state') or '') in TERMINAL:
                continue
            deadline = task.get('deadline_ts')
            if not deadline or float(deadline) > now:
                continue
            task_id = task.get('id') or name[len('task_'):-len('.json')]
            limit = int(task.get('timeout_s') or DEFAULT_TIMEOUT_S)
            result = self.complete(task_id, task.get('agent'), 'timeout', '',
                                   message='истекло время ожидания результата (timeout_s=%d)' % limit)
            if result:
                done.append(task_id)
        return done



    def status(self, task_id):
        folder, path = self._locate(task_id)
        result = self.result(task_id)
        if not path and not result:
            return None
        task = None
        if path:
            try:
                task = read_json(path)
            except (ValueError, OSError):
                task = None
        task = task or {}
        result = result or {}
        state = task.get('state') or result.get('status') or 'done'
        created_ts = float(task.get('created_ts') or result.get('created_ts') or 0)
        finished_ts = float(task.get('finished_ts') or result.get('finished_ts') or 0)
        moment = finished_ts or time.time()
        items = task.get('progress') or []
        last = items[-1] if items else {}
        return {
            'task_id': task_id,
            'state': state,
            'stage': state,
            'wait_hint': HINTS.get(state, ''),
            'created_at': task.get('created_at') or result.get('created_at') or '',
            'updated_at': task.get('updated_at') or result.get('finished_at') or '',
            'claimed_at': task.get('claimed_at') or result.get('claimed_at') or '',
            'finished_at': task.get('finished_at') or result.get('finished_at') or '',
            'agent': task.get('agent') or result.get('agent') or '',
            'client': task.get('client') or result.get('client') or '',
            'mode': task.get('mode') or result.get('mode') or '',
            'db': task.get('db') or result.get('db') or '',
            'prompt': task.get('prompt') or result.get('prompt') or '',
            'message': result.get('message') or last.get('message') or '',
            'elapsed_s': round(max(0.0, moment - created_ts), 1) if created_ts else 0.0,
            'attempts': task.get('attempts') or result.get('attempts') or 0,
            'progress': items,
            'answer_available': bool(result.get('answer')),
            'terminal': state in TERMINAL,
        }

    def statuses(self, task_ids):
        items = []
        for task_id in task_ids or []:
            item = self.status(task_id)
            if item:
                items.append(item)
        return items

    def _summary(self, task_id, payload):
        state = payload.get('state') or payload.get('status') or ''
        created_ts = float(payload.get('created_ts') or 0)
        moment = float(payload.get('finished_ts') or payload.get('updated_ts') or 0)
        return {
            'task_id': task_id,
            'state': state,
            'created_at': payload.get('created_at') or '',
            'updated_at': payload.get('finished_at') or payload.get('updated_at') or '',
            'agent': payload.get('agent') or '',
            'client': payload.get('client') or '',
            'mode': payload.get('mode') or '',
            'db': payload.get('db') or '',
            'prompt': preview(payload.get('prompt'), 160),
            'message': preview(payload.get('message'), 200),
            'elapsed_s': round(max(0.0, moment - created_ts), 1) if (created_ts and moment) else 0.0,
            'answer_available': bool(payload.get('answer')),
            'terminal': state in TERMINAL,
        }


    def recent(self, limit=20):
        self.ensure()
        items = []
        seen = set()
        for name in os.listdir(self.dirs['outbox']):
            if not (name.startswith('result_') and name.endswith('.json')):
                continue
            try:
                payload = read_json(os.path.join(self.dirs['outbox'], name))
            except (ValueError, OSError):
                continue
            task_id = payload.get('task_id') or name[len('result_'):-len('.json')]
            seen.add(task_id)
            items.append((float(payload.get('finished_ts') or 0), task_id, payload))
        for folder in ('processing', 'inbox'):
            for name in os.listdir(self.dirs[folder]):
                if not (name.startswith('task_') and name.endswith('.json')):
                    continue
                try:
                    payload = read_json(os.path.join(self.dirs[folder], name))
                except (ValueError, OSError):
                    continue
                task_id = payload.get('id') or name[len('task_'):-len('.json')]
                if task_id in seen:
                    continue
                items.append((float(payload.get('updated_ts') or 0), task_id, payload))
        items.sort(key=lambda row: row[0], reverse=True)
        return [self._summary(task_id, payload) for _ts, task_id, payload in items[:max(1, limit)]]

    def counts(self):
        self.ensure()
        outbox = [n for n in os.listdir(self.dirs['outbox'])
                  if n.startswith('result_') and n.endswith('.json')]
        done = 0
        bad = 0
        for name in outbox:
            try:
                status = read_json(os.path.join(self.dirs['outbox'], name)).get('status')
            except (ValueError, OSError):
                continue
            if status == 'done':
                done += 1
            else:
                bad += 1
        return {
            'queued': len([n for n in os.listdir(self.dirs['inbox'])
                           if n.startswith('task_') and n.endswith('.json')]),
            'processing': len([n for n in os.listdir(self.dirs['processing'])
                               if n.startswith('task_') and n.endswith('.json')]),
            'done': done,
            'failed': bad + len([n for n in os.listdir(self.dirs['failed'])
                                 if n.endswith('.json')]),
            'agents_alive': len([a for a in self.agents() if a.get('alive')]),
        }


    def touch_agent(self, name, info=None):
        if not name:
            return
        self.ensure()
        data = {'name': name, 'updated_at': now_iso(), 'updated_ts': round(time.time(), 3)}
        for key, value in (info or {}).items():
            if value is not None:
                data[key] = value
        try:
            write_json_atomic(os.path.join(self.dirs['agents'], safe_name(name) + '.json'), data)
        except OSError:
            pass

    def agents(self, alive_s=60.0):
        self.ensure()
        now = time.time()
        items = []
        for name in os.listdir(self.dirs['agents']):
            if not name.endswith('.json'):
                continue
            try:
                data = read_json(os.path.join(self.dirs['agents'], name))
            except (ValueError, OSError):
                continue
            age = now - float(data.get('updated_ts') or 0)
            data['age_s'] = round(max(0.0, age), 1)
            data['alive'] = age <= alive_s
            items.append(data)
        items.sort(key=lambda row: row.get('name') or '')
        return items


    def events_tail(self, limit=50):
        if not os.path.isfile(self.events):
            return []
        rows = []
        with open(self.events, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
        return rows[-max(1, limit):]

        task['claim_expires_ts'] = round(time.time() + ttl, 3)
