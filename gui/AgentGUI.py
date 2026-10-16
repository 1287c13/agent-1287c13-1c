# -*- coding: utf-8 -*-
"""Окно задач внешней интеграции: постановка задачи и чтение результата.

Окно для человека, который не работает с Cline напрямую: он заполняет слоты (роль,
что нужно сделать, база, цель), отправляет задачу и читает ответ в том же окне. Своего
протокола у окна нет: оно отправитель и читатель очереди, задача всё равно проходит
через integration\\task.py, поэтому три отправителя (окно, HTTP, файл) дают один текст.

Режим задачи окно не спрашивает - он выводится из роли: «инженер харнесса» означает
задачу по самому харнессу (слот базы не нужен), любая другая роль - задачу по базе
(слот базы обязателен). Ролей и баз может быть много: список баз окно берёт из
.v8-project.json, поэтому выдуманную базу отправить не даст.

Куда отправлять (в очередь рядом или на HTTP-сервер) и адрес сервера - технические
настройки, а не часть задачи: они живут в отдельном окне «Настройки и журнал».
В режиме сервера окно читает результат по HTTP (GET /api/result/<id>), в режиме
очереди - из queue\\outbox. Формулировку контракта и ход доставки показывает окно
подробностей задачи (двойной щелчок по строке): в форме её показывать не нужно.

Запуск:

    py -3 gui\\AgentGUI.py            (или deploy\\run-gui.bat)

Внешний вид собирается из виджетов gui\\ui_kit.py: палитра, карточки, кнопки и
скругления заданы там, зависимостей кроме tkinter нет.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from time import strftime

import tkinter as tk
from tkinter import ttk

import ui_kit as ui
from ui_kit import Banner, Button, Card, Chip, Input, Segmented, TextArea

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_INTEGRATION = os.path.join(_ROOT, 'integration')
if _INTEGRATION not in sys.path:
    sys.path.insert(0, _INTEGRATION)

from task import build_prompt, database_labels, errors_to_text, make_task, validate_task  # noqa: E402
from transport.store import QueueStore, setup_stdio  # noqa: E402

ROLES = ('программист 1С', 'тестировщик 1С', 'аналитик', 'администратор', 'инженер харнесса')
HARNESS_ROLE = 'инженер харнесса'
STATE_FILE = 'gui_state.json'
POLL_MS = 2000
HTTP_TIMEOUT = 8
WATCHER_ALIVE_S = 30
SENT_LIMIT = 200

# Состояние задачи -> подпись для человека и вид строки в таблице.
STATES = {
    'queued': ('в очереди', 'wait'),
    'inbox': ('ждёт агента', 'wait'),
    'processing': ('передаётся', 'wait'),
    'delivered': ('ждёт ответа', 'info'),
    'done': ('готово', 'ok'),
    'error': ('ошибка', 'err'),
    'timeout': ('таймаут', 'err'),
    'unknown': ('нет задачи', 'muted'),
}
TAG_COLORS = {
    'ok': ui.OK_INK,
    'info': ui.INFO_INK,
    'wait': ui.WARN_INK,
    'err': ui.ERR_INK,
    'muted': ui.MUTED,
}


def state_label(state):
    """Подпись состояния задачи для человека."""
    return STATES.get(state or 'unknown', (state or 'неизвестно', 'muted'))[0]


def state_tag(state):
    """Вид строки таблицы: цвет по состоянию задачи."""
    return STATES.get(state or 'unknown', (state or 'unknown', 'muted'))[1]


class AgentGUI(object):
    """Окно постановки задач: форма слева, очередь и ответ справа."""

    def __init__(self, root, root_dir):
        self.root = root
        self.root_dir = root_dir
        self.store = QueueStore(root_dir)
        self.store.ensure()
        self.state_path = os.path.join(self.store.base, STATE_FILE)
        self.state = self._load_state()

        self.role = tk.StringVar(value=self.state.get('role') or ROLES[0])
        self.db = tk.StringVar(value=self.state.get('db') or '')
        self.delivery = tk.StringVar(value=self.state.get('send') or 'queue')
        self.server = tk.StringVar(value=self.state.get('server') or 'http://127.0.0.1:8760')
        self.token = tk.StringVar(value=self.state.get('token') or '')
        self.sent = list(self.state.get('sent') or [])

        self.selected = None
        self.remote_results = {}
        self.remote_states = {}
        self.remote_health = None
        self.remote_error = None
        self.polling = False

        ui.setup_theme(root)
        root.configure(bg=ui.APP_BG)
        root.title('Агент 1С · очередь задач')
        root.geometry(self.state.get('geometry') or '1280x820')
        root.minsize(1080, 700)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        self._build_header()
        content = tk.Frame(root, bg=ui.APP_BG)
        content.grid(row=1, column=0, sticky='nsew', padx=22, pady=(0, 6))
        content.columnconfigure(0, weight=4, minsize=470)
        content.columnconfigure(1, weight=6)
        content.rowconfigure(0, weight=1)
        self._build_form(content)
        self._build_queue(content)
        self._build_footer()

        self._refresh_db_list()
        self._on_role_change()
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.tick()

    # --- состояние окна ------------------------------------------------------

    def _load_state(self):
        """Последние заполненные поля: окно открывается в том же виде, что закрылось."""
        if os.path.isfile(self.state_path):
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                if isinstance(state, dict):
                    return state
            except (ValueError, OSError):
                pass
        return {}

    def _save_state(self):
        payload = {
            'role': self.role.get(),
            'db': self.db.get(),
            'send': self.delivery.get(),
            'server': self.server.get(),
            'token': self.token.get(),
            'sent': self.sent[-SENT_LIMIT:],
            'geometry': self.root.winfo_geometry(),
        }
        try:
            with open(self.state_path, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def close(self):
        self._save_state()
        self.root.destroy()

    # --- шапка и подвал ------------------------------------------------------

    def _build_header(self):
        head = tk.Frame(self.root, bg=ui.APP_BG)
        head.grid(row=0, column=0, sticky='ew', padx=22, pady=(18, 14))
        head.columnconfigure(0, weight=1)
        title = tk.Frame(head, bg=ui.APP_BG)
        title.grid(row=0, column=0, sticky='w')
        tk.Label(title, text='Агент 1С', bg=ui.APP_BG, fg=ui.INK,
                 font=ui.font(17, 'bold')).pack(anchor='w')
        tk.Label(title, text='внешняя очередь задач: поставить задачу и прочитать ответ',
                 bg=ui.APP_BG, fg=ui.MUTED, font=ui.font(9)).pack(anchor='w', pady=(2, 0))
        tools = tk.Frame(head, bg=ui.APP_BG)
        tools.grid(row=0, column=1, sticky='e')
        self.watcher_chip = Chip(tools, 'watcher: проверяю', 'muted', bg_parent=ui.APP_BG)
        self.watcher_chip.pack(side='left', padx=(0, 12))
        self.watcher_button = Button(tools, 'Поднять watcher', kind='secondary', height=34,
                                     bg_parent=ui.APP_BG, command=self.start_watcher)
        self.watcher_button.pack(side='left', padx=(0, 8))
        Button(tools, 'Настройки и журнал', kind='secondary', height=34, bg_parent=ui.APP_BG,
               command=self.open_settings).pack(side='left')

    def _build_footer(self):
        foot = tk.Frame(self.root, bg=ui.APP_BG)
        foot.grid(row=2, column=0, sticky='ew', padx=22, pady=(6, 16))
        self.chips = {}
        for key, text in (('journal', 'журнал'), ('inbox', 'inbox'), ('processing', 'processing'),
                          ('outbox', 'outbox'), ('failed', 'failed'), ('updated', 'обновлено')):
            chip = Chip(foot, '%s: -' % text, 'muted', bg_parent=ui.APP_BG)
            chip.pack(side='left', padx=(0, 8))
            self.chips[key] = chip
        Button(foot, 'Обновить', kind='ghost', height=26, size=9, bg_parent=ui.APP_BG,
               command=self.refresh).pack(side='right')

    # --- форма задачи --------------------------------------------------------

    def _build_form(self, parent):
        self.form = Card(parent, title='Новая задача',
                         subtitle='слоты контракта: режим задачи окно выводит из роли')
        self.form.grid(row=0, column=0, sticky='nsew')
        body = self.form.body
        body.columnconfigure(0, weight=1)

        ui.label(body, 'Роль', bg=ui.CARD, size=9).grid(row=0, column=0, sticky='w')
        self.role_box = ttk.Combobox(body, textvariable=self.role, values=list(ROLES),
                                     style='Modern.TCombobox')
        self.role_box.grid(row=1, column=0, sticky='ew', pady=(4, 3))
        self.role_box.bind('<<ComboboxSelected>>', lambda _event: self._on_role_change())
        self.role_box.bind('<KeyRelease>', lambda _event: self._on_role_change())
        self.role_hint = ui.label(body, '', bg=ui.CARD, size=8)
        self.role_hint.grid(row=2, column=0, sticky='w')

        ui.label(body, 'Что нужно сделать', bg=ui.CARD, size=9).grid(row=3, column=0, sticky='w',
                                                                     pady=(14, 0))
        self.action = TextArea(body, height=7)
        self.action.grid(row=4, column=0, sticky='nsew', pady=(4, 0))
        body.rowconfigure(4, weight=3)

        head = tk.Frame(body, bg=ui.CARD)
        head.grid(row=5, column=0, sticky='ew', pady=(14, 0))
        head.columnconfigure(0, weight=1)
        ui.label(head, 'База', bg=ui.CARD, size=9).grid(row=0, column=0, sticky='w')
        self.db_hint = ui.label(head, '', bg=ui.CARD, size=8, color=ui.MUTED)
        self.db_hint.grid(row=0, column=1, sticky='e')
        self.db_box = ttk.Combobox(body, textvariable=self.db, style='Modern.TCombobox')
        self.db_box.grid(row=6, column=0, sticky='ew', pady=(4, 0))
        self.db_box.bind('<KeyRelease>', lambda _event: self._update_db_hint())

        ui.label(body, 'Цель (не обязательно)', bg=ui.CARD, size=9).grid(row=7, column=0,
                                                                         sticky='w', pady=(14, 0))
        self.goal = TextArea(body, height=4)
        self.goal.grid(row=8, column=0, sticky='nsew', pady=(4, 0))
        body.rowconfigure(8, weight=2)

        self.banner = Banner(body)
        self.banner.grid(row=9, column=0, sticky='ew', pady=(10, 0))
        self.banner.hide()

        buttons = tk.Frame(body, bg=ui.CARD)
        buttons.grid(row=10, column=0, sticky='ew', pady=(12, 0))
        Button(buttons, 'Отправить задачу', kind='primary', command=self.send_task).pack(side='left')
        Button(buttons, 'Очистить', kind='secondary', bg_parent=ui.CARD,
               command=self._clear_form).pack(side='left', padx=(10, 0))

    def _clear_form(self):
        self.action.clear()
        self.goal.clear()
        self.action.text.focus_set()

    # --- роль, база и режим --------------------------------------------------

    def mode(self):
        """Режим задачи выводится из роли: «инженер харнесса» - задача по харнессу."""
        return 'harness' if HARNESS_ROLE in (self.role.get() or '').lower() else 'db'

    def _on_role_change(self):
        harness = self.mode() == 'harness'
        if harness:
            self.role_hint.configure(text='роль «инженер харнесса»: задача по самому инструменту, база не нужна')
            if self.db.get():
                self._db_memory = self.db.get()
                self.db.set('')
        else:
            self.role_hint.configure(text='задача по базе: выберите базу из списка ниже')
            if not self.db.get() and getattr(self, '_db_memory', ''):
                self.db.set(self._db_memory)
        self.db_box.configure(state='disabled' if harness else 'readonly')
        self._update_db_hint()

    def _refresh_db_list(self):
        """Список баз берётся из .v8-project.json: выдуманную базу агент не примет."""
        labels = database_labels(self.root_dir)
        self.db_box.configure(values=labels)
        if labels and not self.db.get():
            self.db.set(labels[0])
        self._update_db_hint()

    def _update_db_hint(self):
        labels = self.db_box.cget('values') or ()
        if self.mode() == 'harness':
            text = 'для этой роли база не требуется'
        elif not labels:
            text = 'нет .v8-project.json: список баз пуст'
        else:
            text = 'баз в .v8-project.json: %d' % len(labels)
        self.db_hint.configure(text=text)

    # --- отправка ------------------------------------------------------------

    def _collect(self):
        """Собрать задачу из полей: тот же код, что у HTTP-сервера и командной строки."""
        mode = self.mode()
        db = None
        if mode == 'db':
            label = (self.db.get() or '').strip()
            db = label.split(' (')[0] if label else ''
        task = make_task(self.role.get(), self.action.get(), self.goal.get(), db, mode,
                         source='gui', deliver='auto')
        return validate_task(self.root_dir, task)

    def _remember_sent(self, task):
        """Помнить, что задача отправлена из окна: в режиме сервера это и есть список задач."""
        self.sent = [item for item in self.sent if item.get('id') != task['id']]
        self.sent.append({
            'id': task['id'],
            'created_at': task.get('created_at') or strftime('%Y-%m-%dT%H:%M:%S'),
            'role': task.get('role') or '',
            'db': task.get('db') or '',
        })
        self.sent = self.sent[-SENT_LIMIT:]
        self._save_state()

    def send_task(self):
        """Проверить форму и отправить задачу: в очередь рядом или на HTTP-сервер."""
        task, errors = self._collect()
        if errors:
            self.banner.show(errors_to_text(task, errors), 'err')
            return
        if self.delivery.get() == 'http':
            self._submit_http(task)
        else:
            self._submit_queue(task)

    def _submit_queue(self, task):
        try:
            self.store.append_journal(task)
        except OSError as exc:
            self.banner.show('очередь недоступна: %s' % exc, 'err')
            return
        self._remember_sent(task)
        self._clear_form()
        alive, _message = self._watcher_state()
        if alive:
            self.banner.show('задача %s записана в журнал; watcher работает - задача уйдёт в Cline'
                             % task['id'], 'ok')
        else:
            self.banner.show('задача %s записана в журнал, но watcher не работает: нажмите '
                             '«Поднять watcher», иначе задача до агента не дойдёт' % task['id'], 'warn')
        self.refresh()

    def _submit_http(self, task):
        url = self.server.get().rstrip('/') + '/api/task'
        payload = json.dumps(task, ensure_ascii=False).encode('utf-8')
        self.banner.show('отправляю задачу на %s...' % url, 'info')

        def worker():
            request = urllib.request.Request(
                url, data=payload,
                headers=self._headers({'Content-Type': 'application/json; charset=utf-8'}))
            try:
                with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
                    body = json.loads(response.read().decode('utf-8'))
                self.root.after(0, lambda: self._http_done(task, body, None))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode('utf-8', 'replace')
                report = 'сервер ответил %s: %s' % (exc.code, detail)
                self.root.after(0, lambda: self._http_done(task, None, report))
            except Exception as exc:
                report = str(exc)
                self.root.after(0, lambda: self._http_done(task, None, report))

        threading.Thread(target=worker, daemon=True).start()

    def _http_done(self, task, body, error):
        if error:
            self.banner.show('задача не отправлена: %s' % error, 'err')
            return
        self._remember_sent(task)
        self._clear_form()
        self.banner.show('задача %s принята сервером (состояние %s); ответ читается с сервера'
                         % (body.get('task_id'), body.get('state')), 'ok')
        self._poll_remote()
        self.refresh()

    def _headers(self, extra=None):
        """Заголовки запроса к серверу: токен нужен, если он задан в настройках."""
        headers = dict(extra or {})
        headers['Accept'] = 'application/json'
        token = (self.token.get() or '').strip()
        if token:
            headers['X-Integration-Token'] = token
        return headers

    # --- очередь и ответ -----------------------------------------------------

    def _build_queue(self, parent):
        right = tk.Frame(parent, bg=ui.APP_BG)
        right.grid(row=0, column=1, sticky='nsew', padx=(16, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=3)
        right.rowconfigure(1, weight=2)

        queue_card = Card(right, title='Задачи',
                          subtitle='двойной щелчок по строке - подробности задачи')
        queue_card.grid(row=0, column=0, sticky='nsew')
        body = queue_card.body
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        columns = ('id', 'created', 'role', 'db', 'state')
        self.tree = ttk.Treeview(body, columns=columns, show='headings', style='Modern.Treeview')
        for name, title, width, stretch in (('id', 'Задача', 200, True),
                                            ('created', 'Создана', 130, False),
                                            ('role', 'Роль', 140, False),
                                            ('db', 'База', 120, False),
                                            ('state', 'Состояние', 130, False)):
            self.tree.heading(name, text=title)
            self.tree.column(name, width=width, anchor='w', stretch=stretch)
        self.tree.grid(row=0, column=0, sticky='nsew')
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', lambda _event: self.show_details())
        for tag, color in TAG_COLORS.items():
            self.tree.tag_configure(tag, foreground=color)
        scroll = ttk.Scrollbar(body, orient='vertical', style='Slim.Vertical.TScrollbar',
                               command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scroll.set)

        tools = tk.Frame(body, bg=ui.CARD)
        tools.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(12, 0))
        Button(tools, 'Подробности задачи', kind='secondary', height=32, size=9, bg_parent=ui.CARD,
               command=self.show_details).pack(side='left')
        Button(tools, 'Каталог очереди', kind='ghost', height=32, size=9, bg_parent=ui.CARD,
               command=self._open_queue_dir).pack(side='left', padx=(8, 0))

        answer_card = Card(right, title='Ответ')
        answer_card.grid(row=1, column=0, sticky='nsew', pady=(16, 0))
        abody = answer_card.body
        abody.columnconfigure(0, weight=1)
        abody.rowconfigure(1, weight=1)
        self.answer_meta = ui.label(abody, 'задача не выбрана', bg=ui.CARD, size=9)
        self.answer_meta.grid(row=0, column=0, sticky='w', pady=(0, 8))
        self.answer = TextArea(abody, height=10, read_only=True)
        self.answer.grid(row=1, column=0, sticky='nsew')

    # --- обновление окна -----------------------------------------------------

    def tick(self):
        """Опрос раз в две секунды: в режиме сервера - сервер, в режиме очереди - каталог."""
        try:
            if self.delivery.get() == 'http':
                self._poll_remote()
            else:
                self.refresh()
        except Exception as exc:  # окно не должно падать из-за недочитанного файла
            self.banner.show('очередь недоступна: %s' % exc, 'warn')
        self.root.after(POLL_MS, self.tick)

    def refresh(self):
        """Перерисовать таблицу задач, подписи состояний и открытый ответ."""
        rows = self._rows()
        seen = []
        for row in rows:
            seen.append(row['id'])
            values = (row['id'], row.get('created') or '', row.get('role') or '',
                      row.get('db') or '', state_label(row.get('state')))
            tag = state_tag(row.get('state'))
            if self.tree.exists(row['id']):
                self.tree.item(row['id'], values=values, tags=(tag,))
            else:
                self.tree.insert('', 'end', iid=row['id'], values=values, tags=(tag,))
        for item in self.tree.get_children():
            if item not in seen:
                self.tree.delete(item)
        self._update_chips()
        if self.selected:
            self.show_result(self.selected)
        else:
            self.answer_meta.configure(text='выберите задачу в списке, чтобы прочитать ответ')

    def _update_chips(self):
        """Строка состояния: счётчики очереди, время обновления и жив ли watcher."""
        if self.delivery.get() == 'http':
            counts = (self.remote_health or {}).get('counts') or {}
            alive, message = self._remote_watcher_state()
        else:
            try:
                counts = self.store.counts()
            except OSError:
                counts = {}
            alive, message = self._watcher_state()
        self.chips['journal'].set('журнал %s байт' % (counts.get('journal_bytes') or 0), 'muted')
        for key in ('inbox', 'processing', 'outbox', 'failed'):
            value = counts.get(key)
            if not value:
                kind = 'muted'
            elif key in ('inbox', 'failed'):
                kind = 'warn'
            else:
                kind = 'info'
            self.chips[key].set('%s: %s' % (key, '-' if value is None else value), kind)
        self.chips['updated'].set('обновлено %s' % strftime('%H:%M:%S'), 'muted')
        prefix = 'сервер' if self.delivery.get() == 'http' else 'watcher'
        self.watcher_chip.set('%s: %s' % (prefix, message), 'ok' if alive else 'err')

    def _watcher_state(self):
        """Жив ли watcher очереди рядом: отметка видна по позиции чтения журнала."""
        try:
            age = self.store.counts().get('watcher_age_s')
        except OSError:
            age = None
        if age is None:
            return False, 'не отвечает'
        if age <= WATCHER_ALIVE_S:
            return True, 'живой (%.0f с назад)' % age
        return False, 'молчит (%.0f с назад)' % age

    def _remote_watcher_state(self):
        """Живость очереди на сервере: поле watcher.alive из GET /api/health."""
        if self.remote_error:
            return False, 'недоступен'
        watcher = (self.remote_health or {}).get('watcher') or {}
        if not watcher:
            return False, 'нет данных'
        message = watcher.get('message') or 'не отвечает'
        if watcher.get('alive') and watcher.get('age_s') is not None:
            message = 'живой (%.0f с назад)' % watcher['age_s']
        return bool(watcher.get('alive')), message

    # --- чтение задач и ответов ----------------------------------------------

    def _rows(self):
        """Строки таблицы: в режиме очереди - журнал рядом, в режиме сервера - итоги сервера."""
        if self.delivery.get() == 'http':
            return self._remote_rows()
        return self._local_rows()

    def _journal_tasks(self, limit=60):
        """Последние задачи из журнала очереди. Читаются только дописанные строки."""
        journal = self.store.dirs['journal']
        tasks = []
        if os.path.isfile(journal):
            with open(journal, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        task = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(task, dict) and task.get('id'):
                        tasks.append(task)
        return tasks[-limit:]

    def _local_state(self, task_id, result):
        """Состояние задачи рядом: записанный итог важнее места в каталогах очереди."""
        if result is not None:
            return result.get('status') or 'done'
        state = self.store.state(task_id)
        # Задача, которую окно видит в журнале, уже принята: unknown здесь означал бы
        # «задача потерялась», а не «ждёт разбора watcher-ом».
        return 'queued' if state == 'unknown' else state

    def _local_rows(self, limit=60):
        rows = []
        for task in reversed(self._journal_tasks(limit)):
            task_id = task['id']
            result = self.store.result(task_id)
            rows.append({'id': task_id, 'created': task.get('created_at') or '',
                         'role': task.get('role') or '', 'db': task.get('db') or '',
                         'state': self._local_state(task_id, result), 'result': result})
        return rows

    def _remote_rows(self):
        """Задачи, отправленные из окна, плюс итоги, которые вернул сервер."""
        rows = []
        known = set()
        for item in reversed(self.sent):
            task_id = item.get('id')
            if not task_id or task_id in known:
                continue
            known.add(task_id)
            result = self.remote_results.get(task_id)
            state = (result or {}).get('status') or self.remote_states.get(task_id) or 'queued'
            rows.append({'id': task_id, 'created': item.get('created_at') or '',
                         'role': item.get('role') or '', 'db': item.get('db') or '',
                         'state': state, 'result': result})
        for task_id, result in self.remote_results.items():
            if task_id in known:
                continue
            known.add(task_id)
            rows.append({'id': task_id, 'created': result.get('written_at') or '',
                         'role': '', 'db': '', 'state': result.get('status') or 'done',
                         'result': result})
        return rows[:80]

    def _on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        self.selected = selection[0]
        self.show_result(self.selected)

    def _row(self, task_id):
        for row in self._rows():
            if row['id'] == task_id:
                return row
        return None

    def show_result(self, task_id):
        """Показать ответ задачи: то, что записано, а не то, что ожидается увидеть."""
        row = self._row(task_id) or {'id': task_id, 'state': 'unknown'}
        result = row.get('result')
        if result is None:
            if self.delivery.get() == 'http':
                hint = 'ответ читается с сервера: %s' % self.server.get()
            else:
                hint = ('ждём watcher: scripts\\start-watcher.ps1, затем Cline заполняет '
                        'queue\\answers\\answer_%s.md и вызывает --write-result' % task_id)
            self.answer_meta.configure(text='%s · %s' % (task_id, state_label(row.get('state'))))
            self.answer.set('результат ещё не записан.\n\n%s' % hint, read_only=True)
            return
        self.answer_meta.configure(text='%s · %s · доставка %s · записано %s'
                                   % (task_id, result.get('status') or '-',
                                      result.get('delivery') or '-', result.get('written_at') or ''))
        self.answer.set(self._answer_text(result), read_only=True)

    def _answer_text(self, result):
        """Текст ответа: преамбула и отчёт из файла ответа плюс свободный текст."""
        head = ('Слой: %s\nMCP: %s\nСкиллы: %s\nПроверка: %s\nСделано: %s\nНе проверено: %s\n---\n'
                % (result.get('layer') or '-', result.get('mcp') or '-', result.get('skills') or '-',
                   result.get('verification') or '-', result.get('done') or '-',
                   result.get('not_verified') or '-'))
        if result.get('message'):
            head += 'сообщение: %s\n\n' % result['message']
        return head + (result.get('answer') or '')

    def _open_queue_dir(self):
        if hasattr(os, 'startfile'):
            os.startfile(self.store.base)

    # --- серверный режим -----------------------------------------------------

    def _http_get(self, path):
        """GET с токеном: разбор JSON-ответа сервера."""
        request = urllib.request.Request(self.server.get().rstrip('/') + path,
                                         headers=self._headers())
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            return json.loads(response.read().decode('utf-8'))

    def _http_result(self, task_id):
        """Итог задачи с сервера: 200 - записан, иначе состояние из тела ответа."""
        url = self.server.get().rstrip('/') + '/api/result/' + urllib.parse.quote(task_id)
        request = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
                return response.status, json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            try:
                return exc.code, json.loads(exc.read().decode('utf-8'))
            except ValueError:
                return exc.code, {}

    def _poll_remote(self):
        """Опрос сервера в фоне: жив ли он, какие итоги есть, в каком состоянии задачи."""
        if self.polling or self.delivery.get() != 'http':
            return
        self.polling = True
        server = self.server.get()

        def worker():
            data = {'health': None, 'results': [], 'states': {}, 'error': None}
            try:
                data['health'] = self._http_get('/api/health')
                listing = self._http_get('/api/tasks?limit=50')
                data['results'] = listing.get('results') or []
                known = set(item.get('task_id') for item in data['results'])
                for task_id in [item.get('id') for item in self.sent[-20:]]:
                    if not task_id or task_id in known:
                        continue
                    code, body = self._http_result(task_id)
                    if code == 200:
                        data['results'].append(body)
                    else:
                        data['states'][task_id] = body.get('state') or 'unknown'
            except Exception as exc:
                data['error'] = str(exc)
            self.root.after(0, lambda: self._apply_remote(server, data))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_remote(self, server, data):
        """Применить ответ сервера: адрес с тех пор не менялся - иначе данные устарели."""
        self.polling = False
        if self.server.get() != server:
            return
        self.remote_error = data.get('error')
        if not self.remote_error:
            self.remote_health = data.get('health')
        self.remote_results = dict((item.get('task_id'), item) for item in data.get('results') or [])
        self.remote_states = data.get('states') or {}
        self.refresh()

    def _on_delivery_change(self):
        """Переключили очередь/сервер: состояние сбрасывается, таблица перерисовывается."""
        self._save_state()
        self.polling = False
        self.remote_error = None
        self.remote_health = None
        self.refresh()

    # --- watcher очереди -----------------------------------------------------

    def start_watcher(self):
        """Поднять watcher фоном: scripts\\start-watcher.ps1 - та же команда, что у агента."""
        script = os.path.join(self.root_dir, 'scripts', 'start-watcher.ps1')
        if not os.path.isfile(script):
            self.banner.show('нет скрипта: %s' % script, 'err')
            return
        if self._run_script(script):
            self.banner.show('watcher поднимается (scripts\\start-watcher.ps1); лог - logs\\watcher.log',
                             'info')
            self.root.after(8000, self.refresh)

    def stop_watcher(self):
        """Погасить watcher: scripts\\stop-watcher.ps1. Очередь не чистится."""
        script = os.path.join(self.root_dir, 'scripts', 'stop-watcher.ps1')
        if os.path.isfile(script) and self._run_script(script):
            self.banner.show('watcher останавливается; задачи в очереди не тронуты', 'info')
            self.root.after(4000, self.refresh)

    def _run_script(self, script):
        """Запустить .ps1 без окна консоли: PowerShell на этой машине требует -ExecutionPolicy Bypass."""
        command = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script]
        try:
            subprocess.Popen(command, cwd=self.root_dir,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except OSError as exc:
            self.banner.show('не удалось запустить %s: %s' % (os.path.basename(script), exc), 'err')
            return False
        return True

    def _task(self, task_id):
        """Полная задача: сначала из журнала, затем из каталогов очереди."""
        for task in self._journal_tasks(500):
            if task['id'] == task_id:
                return task
        for folder in ('archive', 'processing', 'inbox'):
            path = self.store.task_path(folder, task_id)
            if os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (ValueError, OSError):
                    break
        return {'id': task_id}

    def _bridge_tail(self, lines=30):
        """Последние строки журнала доставки: что происходило с задачами."""
        path = os.path.join(self.store.base, 'bridge.jsonl')
        if not os.path.isfile(path):
            return 'журнал доставки пуст: задач ещё не передавали'
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            tail = f.readlines()[-lines:]
        return ''.join(tail)

    # --- окна ----------------------------------------------------------------

    def show_details(self):
        """Подробности задачи: формулировка контракта, доставка и ответ. В форме их нет."""
        task_id = self.selected
        if not task_id:
            selection = self.tree.selection()
            task_id = selection[0] if selection else None
        if not task_id:
            self.banner.show('выберите задачу в списке', 'warn')
            return
        row = self._row(task_id) or {'id': task_id, 'state': 'unknown'}
        task = self._task(task_id)
        window = tk.Toplevel(self.root)
        window.title('Задача %s' % task_id)
        window.configure(bg=ui.APP_BG)
        window.geometry('880x700')
        card = Card(window, title='Задача %s' % task_id,
                    subtitle='формулировка по контракту, доставка и ответ')
        card.pack(fill='both', expand=True, padx=18, pady=18)
        body = card.body
        body.columnconfigure(0, weight=1)
        body.rowconfigure(6, weight=1)

        info = ('роль: %s\nрежим: %s\nбаза: %s\nсостояние: %s\nотправитель: %s\nсоздана: %s'
                % (task.get('role') or '-', task.get('mode') or '-', task.get('db') or '-',
                   state_label(row.get('state')), task.get('client') or '-',
                   task.get('created_at') or '-'))
        tk.Label(body, text=info, bg=ui.CARD, fg=ui.INK, font=ui.font(9), justify='left',
                 anchor='w').grid(row=0, column=0, sticky='w')
        ui.label(body, 'Формулировка по контракту', bg=ui.CARD, size=9).grid(row=1, column=0,
                                                                            sticky='w', pady=(12, 4))
        prompt = TextArea(body, height=3, read_only=True)
        prompt.grid(row=2, column=0, sticky='ew')
        prompt.set(task.get('prompt') or '(формулировка не найдена: задачу убрали из очереди)',
                   read_only=True)
        ui.label(body, 'Ответ очереди', bg=ui.CARD, size=9).grid(row=5, column=0, sticky='w',
                                                                 pady=(12, 4))
        answer = TextArea(body, height=14, read_only=True)
        answer.grid(row=6, column=0, sticky='nsew')
        result = row.get('result')
        answer.set(self._answer_text(result) if result else 'результат ещё не записан',
                   read_only=True)
        Button(body, 'Закрыть', kind='secondary', bg_parent=ui.CARD,
               command=window.destroy).grid(row=7, column=0, sticky='e', pady=(12, 0))

    def open_settings(self):
        """Технические настройки и журнал: доставка, адрес сервера, watcher, журнал доставки."""
        window = tk.Toplevel(self.root)
        window.title('Настройки и журнал')
        window.configure(bg=ui.APP_BG)
        window.geometry('860x780')
        outer = tk.Frame(window, bg=ui.APP_BG)
        outer.pack(fill='both', expand=True, padx=18, pady=18)

        send = Card(outer, title='Куда отправлять задачу',
                    subtitle='переключатель технический: на формулировку задачи он не влияет')
        send.pack(fill='x')
        body = send.body
        body.columnconfigure(0, weight=1)
        Segmented(body, [('queue', 'в очередь рядом'), ('http', 'на сервер (HTTP)')],
                  self.delivery, command=self._on_delivery_change).grid(row=0, column=0, sticky='w')
        ui.label(body, 'Адрес сервера', bg=ui.CARD, size=9).grid(row=1, column=0, sticky='w',
                                                                 pady=(14, 4))
        Input(body, textvariable=self.server).grid(row=2, column=0, sticky='ew')
        ui.label(body, 'Токен доступа (если сервер его требует)', bg=ui.CARD, size=9).grid(
            row=3, column=0, sticky='w', pady=(12, 4))
        Input(body, textvariable=self.token, show='*').grid(row=4, column=0, sticky='ew')
        ui.label(body, 'режим очереди читает ответ из queue\\outbox, режим сервера - запросом '
                       'к /api/result', bg=ui.CARD, size=8).grid(row=5, column=0, sticky='w',
                                                                 pady=(10, 0))

        watch = Card(outer, title='Watcher очереди',
                     subtitle='без него строки журнала не разбираются и задачи не доходят до агента')
        watch.pack(fill='x', pady=(16, 0))
        wbody = watch.body
        wbody.columnconfigure(0, weight=1)
        state_chip = Chip(wbody, 'проверяю', 'muted')
        state_chip.grid(row=0, column=0, sticky='w')
        commands = ('поднять:  powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\start-watcher.ps1\n'
                    'погасить: powershell -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\stop-watcher.ps1')
        tk.Label(wbody, text=commands, bg=ui.CARD, fg=ui.MUTED, font=ui.mono(9), justify='left',
                 anchor='w').grid(row=1, column=0, sticky='w', pady=(10, 0))
        buttons = tk.Frame(wbody, bg=ui.CARD)
        buttons.grid(row=2, column=0, sticky='ew', pady=(12, 0))
        Button(buttons, 'Поднять watcher', kind='primary', height=32, size=9,
               command=self.start_watcher).pack(side='left')
        Button(buttons, 'Остановить watcher', kind='secondary', height=32, size=9,
               bg_parent=ui.CARD, command=self.stop_watcher).pack(side='left', padx=(10, 0))

        log = Card(outer, title='Журнал доставки (queue\\bridge.jsonl)')
        log.pack(fill='both', expand=True, pady=(16, 0))
        lbody = log.body
        lbody.columnconfigure(0, weight=1)
        lbody.rowconfigure(0, weight=1)
        journal = TextArea(lbody, height=10, read_only=True)
        journal.grid(row=0, column=0, sticky='nsew')
        lbuttons = tk.Frame(lbody, bg=ui.CARD)
        lbuttons.grid(row=1, column=0, sticky='ew', pady=(10, 0))
        Button(lbuttons, 'Обновить', kind='secondary', height=32, size=9, bg_parent=ui.CARD,
               command=lambda: self._refresh_settings(journal, state_chip)).pack(side='left')
        Button(lbuttons, 'Каталог очереди', kind='ghost', height=32, size=9, bg_parent=ui.CARD,
               command=self._open_queue_dir).pack(side='left', padx=(8, 0))

        self._refresh_settings(journal, state_chip)

    def _refresh_settings(self, journal, state_chip):
        """Обновить журнал доставки и пилюлю watcher-а в окне настроек."""
        journal.set(self._bridge_tail(), read_only=True)
        alive, message = self._watcher_state()
        state_chip.set('watcher: %s' % message, 'ok' if alive else 'err')


def main(argv=None):
    setup_stdio()
    parser = argparse.ArgumentParser(
        prog='AgentGUI.py',
        description='Окно задач внешней очереди интеграции: поставить задачу и прочитать ответ.')
    parser.add_argument('--root', default=_ROOT,
                        help='корень харнесса (каталог с .v8-project.json и queue); по умолчанию - выше gui')
    args = parser.parse_args(argv)
    root = tk.Tk()
    AgentGUI(root, os.path.abspath(args.root))
    root.mainloop()
    return 0


if __name__ == '__main__':
    sys.exit(main())








