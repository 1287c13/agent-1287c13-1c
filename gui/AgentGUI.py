# -*- coding: utf-8 -*-
"""GUI внешней интеграции: постановка задачи в харнесс и чтение результата.

Окно для человека, который не работает с Cline напрямую: он заполняет слоты
контракта (роль, действие, база, цель), видит получившуюся формулировку и получает
ответ в том же окне. Роль этого файла - отправитель задачи и читатель очереди;
своего протокола у него нет.

Как задача попадает к агенту (переключатель «Отправка»):

    в очередь    - строка дописывается в queue\\tasks.jsonl (тот же журнал, что и у
                   HTTP-транспорта). Нужен запущенный watcher: deploy\\run-watcher.bat;
    на сервер    - POST /api/task на адрес из поля «Адрес сервера». Сервер может жить
                   на другой машине: он пишет в свою очередь, а окно читает результат
                   из своей.

Результат читается только из очереди (queue\\outbox): окно показывает то, что записано
агентом, а не то, что нарисовано в интерфейсе. Недописанные файлы (суффикс .tmp)
игнорируются - их пишет атомарная замена.

Запуск:

    py -3 gui\\AgentGUI.py            (или deploy\\run-gui.bat)
"""

import argparse
import json
import os
import sys
import threading
import urllib.error
import urllib.request

import tkinter as tk
from tkinter import messagebox, ttk

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
STATE_FILE = 'gui_state.json'
POLL_MS = 2000
HTTP_TIMEOUT = 8


class AgentGUI(object):
    """Окно постановки задач: форма сверху, очередь и результат снизу."""

    def __init__(self, root, root_dir):
        self.root = root
        self.root_dir = root_dir
        self.store = QueueStore(root_dir)
        self.store.ensure()
        self.state_path = os.path.join(self.store.base, STATE_FILE)
        self.state = self._load_state()

        root.title('1C-агент: задачи из внешнего окна')
        root.geometry('1120x760')
        root.minsize(920, 620)

        self.mode = tk.StringVar(value=self.state.get('mode') or 'db')
        self.role = tk.StringVar(value=self.state.get('role') or ROLES[0])
        self.db = tk.StringVar(value=self.state.get('db') or '')
        self.delivery = tk.StringVar(value=self.state.get('send') or 'queue')
        self.server = tk.StringVar(value=self.state.get('server') or 'http://127.0.0.1:8760')
        self.hint = tk.StringVar(value='')
        self.status = tk.StringVar(value='')
        self.selected = None

        self._build_form()
        self._build_queue()
        self._refresh_db_list()
        self._on_mode_change()
        self.tick()

    # --- состояние окна ------------------------------------------------------

    def _load_state(self):
        if os.path.isfile(self.state_path):
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (ValueError, OSError):
                pass
        return {}

    def _save_state(self):
        payload = {
            'role': self.role.get(),
            'db': self.db.get(),
            'send': self.delivery.get(),
            'server': self.server.get(),
            'mode': self.mode.get(),
        }
        try:
            with open(self.state_path, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except OSError:
            pass


    # --- форма ---------------------------------------------------------------

    def _build_form(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        form = ttk.LabelFrame(self.root, text='Задача')
        form.grid(row=0, column=0, sticky='nsew', padx=8, pady=6)
        form.columnconfigure(1, weight=1)

        row = 0
        ttk.Label(form, text='Режим задачи:').grid(row=row, column=0, sticky='w', padx=6, pady=3)
        box = ttk.Frame(form)
        box.grid(row=row, column=1, columnspan=2, sticky='w')
        ttk.Radiobutton(box, text='по базе 1С', value='db', variable=self.mode,
                        command=self._on_mode_change).pack(side='left')
        ttk.Radiobutton(box, text='по харнессу (без базы)', value='harness', variable=self.mode,
                        command=self._on_mode_change).pack(side='left', padx=12)

        row += 1
        ttk.Label(form, text='Роль:').grid(row=row, column=0, sticky='w', padx=6, pady=3)
        self.role_box = ttk.Combobox(form, textvariable=self.role, values=list(ROLES), width=46)
        self.role_box.grid(row=row, column=1, columnspan=2, sticky='we', padx=6)
        self.role_box.bind('<KeyRelease>', lambda _event: self._update_preview())

        row += 1
        ttk.Label(form, text='Действие:').grid(row=row, column=0, sticky='nw', padx=6, pady=3)
        self.action = tk.Text(form, height=3, wrap='word', font=('Segoe UI', 9))
        self.action.grid(row=row, column=1, columnspan=2, sticky='we', padx=6)
        self.action.bind('<KeyRelease>', lambda _event: self._update_preview())

        row += 1
        ttk.Label(form, text='База:').grid(row=row, column=0, sticky='w', padx=6, pady=3)
        self.db_box = ttk.Combobox(form, textvariable=self.db, width=46)
        self.db_box.grid(row=row, column=1, sticky='we', padx=6)
        self.db_box.bind('<<ComboboxSelected>>', lambda _event: self._update_preview())
        ttk.Button(form, text='Обновить список', command=self._refresh_db_list).grid(row=row, column=2, padx=6)

        row += 1
        ttk.Label(form, text='Цель (критерий готовности):').grid(row=row, column=0, sticky='nw', padx=6, pady=3)
        self.goal = tk.Text(form, height=2, wrap='word', font=('Segoe UI', 9))
        self.goal.grid(row=row, column=1, columnspan=2, sticky='we', padx=6)
        self.goal.bind('<KeyRelease>', lambda _event: self._update_preview())

        row += 1
        ttk.Separator(form, orient='horizontal').grid(row=row, column=0, columnspan=3, sticky='we', pady=5)

        row += 1
        ttk.Label(form, text='Отправка:').grid(row=row, column=0, sticky='w', padx=6, pady=3)
        box = ttk.Frame(form)
        box.grid(row=row, column=1, columnspan=2, sticky='w')
        ttk.Radiobutton(box, text='в очередь (файл, нужен watcher)', value='queue',
                        variable=self.delivery).pack(side='left')
        ttk.Radiobutton(box, text='на сервер (HTTP)', value='http',
                        variable=self.delivery).pack(side='left', padx=12)

        row += 1
        ttk.Label(form, text='Адрес сервера:').grid(row=row, column=0, sticky='w', padx=6, pady=3)
        ttk.Entry(form, textvariable=self.server, width=46).grid(row=row, column=1, columnspan=2,
                                                                 sticky='we', padx=6)

        row += 1
        ttk.Label(form, text='Формулировка по контракту:').grid(row=row, column=0, sticky='nw', padx=6, pady=3)
        self.preview = tk.Text(form, height=2, wrap='word', font=('Consolas', 9), state='disabled')
        self.preview.grid(row=row, column=1, columnspan=2, sticky='we', padx=6)

        row += 1
        buttons = ttk.Frame(form)
        buttons.grid(row=row, column=0, columnspan=3, sticky='we', pady=6)
        ttk.Button(buttons, text='Отправить задачу', command=self.send_task).pack(side='left', padx=6)
        ttk.Button(buttons, text='Очистить', command=self.clear_form).pack(side='left', padx=6)
        ttk.Label(buttons, textvariable=self.hint).pack(side='left', padx=12)


    # --- очередь и результат -------------------------------------------------

    def _build_queue(self):
        pane = ttk.LabelFrame(self.root, text='Очередь задач (queue)')
        pane.grid(row=1, column=0, sticky='nsew', padx=8, pady=6)
        pane.columnconfigure(0, weight=3)
        pane.columnconfigure(1, weight=2)
        pane.rowconfigure(0, weight=1)

        columns = ('id', 'created', 'role', 'mode', 'state')
        self.tree = ttk.Treeview(pane, columns=columns, show='headings', height=8)
        for name, title, width in (('id', 'Задача', 190), ('created', 'Создана', 130),
                                   ('role', 'Роль', 130), ('mode', 'Режим', 90),
                                   ('state', 'Состояние', 110)):
            self.tree.heading(name, text=title)
            self.tree.column(name, width=width, anchor='w')
        self.tree.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        scroll = ttk.Scrollbar(pane, orient='vertical', command=self.tree.yview)
        scroll.grid(row=0, column=0, sticky='nse', pady=4)
        self.tree.configure(yscrollcommand=scroll.set)

        side = ttk.Frame(pane)
        side.grid(row=0, column=1, sticky='nsew', padx=4, pady=4)
        side.rowconfigure(1, weight=1)
        side.columnconfigure(0, weight=1)
        ttk.Label(side, text='Результат (queue\\outbox)').grid(row=0, column=0, sticky='w')
        self.answer = tk.Text(side, wrap='word', font=('Segoe UI', 9), state='disabled')
        self.answer.grid(row=1, column=0, sticky='nsew')

        ttk.Label(self.root, textvariable=self.status).grid(row=2, column=0, sticky='we', padx=10, pady=2)

    def _refresh_db_list(self):
        """Список баз берётся из .v8-project.json: выдуманную базу агент не примет."""
        labels = database_labels(self.root_dir)
        self.db_box.configure(values=labels)
        if labels and not self.db.get():
            self.db.set(labels[0])

    def _on_mode_change(self):
        harness = self.mode.get() == 'harness'
        self.db_box.configure(state='disabled' if harness else 'normal')
        self._update_preview()

    def _update_preview(self):
        mode = self.mode.get()
        db = None if mode == 'harness' else (self.db.get().split(' (')[0] if self.db.get() else '')
        prompt = build_prompt(self.role.get(), self.action.get('1.0', 'end'),
                              self.goal.get('1.0', 'end'), db, mode)
        self.preview.configure(state='normal')
        self.preview.delete('1.0', 'end')
        self.preview.insert('1.0', prompt)
        self.preview.configure(state='disabled')

    def clear_form(self):
        self.action.delete('1.0', 'end')
        self.goal.delete('1.0', 'end')
        self.hint.set('')
        self._update_preview()


    # --- отправка ------------------------------------------------------------

    def _collect(self):
        """Собрать задачу из полей. Возвращает (задача, ошибки)."""
        mode = self.mode.get()
        db = None
        if mode == 'db':
            label = self.db.get().strip()
            db = label.split(' (')[0] if label else ''
        task = make_task(self.role.get(), self.action.get('1.0', 'end'),
                         self.goal.get('1.0', 'end'), db, mode,
                         source='gui', deliver='auto')
        return validate_task(self.root_dir, task)

    def send_task(self):
        task, errors = self._collect()
        if errors:
            messagebox.showwarning('Задача не принята', errors_to_text(task, errors))
            self.hint.set('задача не отправлена: проверьте поля')
            return
        self._save_state()
        if self.delivery.get() == 'http':
            self._submit_http(task)
        else:
            self._submit_queue(task)

    def _submit_queue(self, task):
        try:
            self.store.append_journal(task)
        except Exception as exc:
            messagebox.showerror('Ошибка очереди', str(exc))
            return
        self.clear_form()
        self.hint.set('задача %s записана в журнал' % task['id'])
        self.status.set('отправлено в очередь: %s - ждём watcher (deploy\\run-watcher.bat)' % task['id'])

    def _submit_http(self, task):
        url = self.server.get().rstrip('/') + '/api/task'
        payload = json.dumps(task, ensure_ascii=False).encode('utf-8')
        self.hint.set('отправка на %s...' % url)

        def worker():
            request = urllib.request.Request(url, data=payload,
                                             headers={'Content-Type': 'application/json; charset=utf-8'})
            try:
                with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
                    body = json.loads(response.read().decode('utf-8'))
                self.root.after(0, lambda: self._http_done(body, None))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode('utf-8', 'replace')
                self.root.after(0, lambda: self._http_done(None, 'код %s: %s' % (exc.code, detail)))
            except Exception as exc:
                self.root.after(0, lambda: self._http_done(None, str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _http_done(self, body, error):
        if error:
            self.hint.set('сервер отклонил задачу')
            messagebox.showwarning('Ответ сервера', error)
            return
        self.clear_form()
        self.hint.set('задача %s принята сервером' % body.get('task_id'))
        self.status.set('принята сервером: %s (состояние %s)' % (body.get('task_id'), body.get('state')))


    # --- чтение очереди ------------------------------------------------------

    def tick(self):
        """Опрос очереди раз в две секунды: обновить таблицу и строку состояния."""
        try:
            self.refresh()
        except Exception as exc:  # окно не должно падать из-за недочитанного файла
            self.status.set('очередь недоступна: %s' % exc)
        self.root.after(POLL_MS, self.tick)

    def load_tasks(self, limit=60):
        """Задачи из журнала плюс состояние каждой. Читаются только готовые записи."""
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
        tasks = tasks[-limit:]
        rows = []
        for task in reversed(tasks):
            rows.append((task, self._state(task['id']), self.store.result(task['id'])))
        return rows

    def _state(self, task_id):
        """Состояние задачи для таблицы: результат важнее места в каталогах."""
        result = self.store.result(task_id)
        if result is not None:
            return result.get('status') or 'done'
        state = self.store.state(task_id)
        # Задача, которую окно видит в журнале, уже принята: состояние unknown здесь
        # означало бы «задача потерялась», а не «ждёт разбора watcher-ом».
        return 'queued' if state == 'unknown' else state

    def refresh(self):
        rows = self.load_tasks()
        seen = []
        for task, state, _result in rows:
            seen.append(task['id'])
            values = (task['id'], task.get('created_at') or '', task.get('role') or '',
                      task.get('mode') or '', state)
            if self.tree.exists(task['id']):
                for index, value in enumerate(values):
                    if self.tree.set(task['id'], self.tree['columns'][index]) != value:
                        self.tree.item(task['id'], values=values)
                        break
            else:
                self.tree.insert('', 'end', iid=task['id'], values=values)
        for item in self.tree.get_children():
            if item not in seen:
                self.tree.delete(item)

        counts = self.store.counts()
        age = counts.get('watcher_age_s')
        watcher = 'отметки нет' if age is None else ('%.0f с назад' % age)
        self.status.set('журнал %s байт | inbox %s | processing %s | outbox %s | failed %s | watcher: %s'
                        % (counts['journal_bytes'], counts['inbox'], counts['processing'],
                           counts['outbox'], counts['failed'], watcher))
        if self.selected:
            self.show_result(self.selected)

    def _on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        self.selected = selection[0]
        self.show_result(self.selected)

    def show_result(self, task_id):
        """Показать итог задачи: то, что записано в outbox, а не то, что ждём увидеть."""
        result = self.store.result(task_id)
        self.answer.configure(state='normal')
        self.answer.delete('1.0', 'end')
        if result is None:
            state = self._state(task_id)
            self.answer.insert('1.0', 'результат ещё не записан\nсостояние: %s\n\n'
                                      'ждём watcher: deploy\\run-watcher.bat\n'
                                      'затем Cline заполняет файл ответа и вызывает\n'
                                      'py -3 integration\\agent.py --write-result --task %s'
                                      % (state, task_id))
        else:
            header = ('задача: %s\nсостояние: %s\nрежим доставки: %s\nзаписано: %s\n'
                      '---\nСлой: %s\nMCP: %s\nСкиллы: %s\nПроверка: %s\nСделано: %s\nНе проверено: %s\n---\n'
                      % (result.get('task_id'), result.get('status'), result.get('delivery') or '-',
                         result.get('written_at') or '', result.get('layer') or '-',
                         result.get('mcp') or '-', result.get('skills') or '-',
                         result.get('verification') or '-', result.get('done') or '-',
                         result.get('not_verified') or '-'))
            self.answer.insert('1.0', header + (result.get('answer') or ''))
        self.answer.configure(state='disabled')


def main(argv=None):
    setup_stdio()
    parser = argparse.ArgumentParser(prog='AgentGUI.py',
                                     description='Окно постановки задач во внешнюю очередь интеграции.')
    parser.add_argument('--root', default=_ROOT, help='корень харнесса')
    args = parser.parse_args(argv)
    root = tk.Tk()
    try:
        ttk.Style().theme_use('vista')
    except tk.TclError:
        pass
    AgentGUI(root, os.path.abspath(args.root))
    root.mainloop()
    return 0


if __name__ == '__main__':
    sys.exit(main())
