# -*- coding: utf-8 -*-
"""Виджеты и палитра окна задач: современный вид на чистом tkinter.

Смысл файла - внешний вид, а не логика: окно задач (gui\\AgentGUI.py) собирается из
этих виджетов, поэтому цвета, шрифты и форма контролов заданы в одном месте. Системная
тема не используется: ttk-тема clam перекрашивается целиком, а кнопки, карточки и
статусные пилюли рисуются на Canvas (скругления, подсветка при наведении, состояния).

Зависимостей, кроме tkinter, нет: ничего доустанавливать не нужно.
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# --- палитра: светлая схема, как у современных веб-приложений ---------------------
APP_BG = '#f4f6fb'
CARD = '#ffffff'
CARD_ALT = '#f2f4f7'
INK = '#101828'
MUTED = '#667085'
BORDER = '#e4e7ec'
BORDER_STRONG = '#d0d5dd'
ACCENT = '#4f46e5'
ACCENT_HOVER = '#4338ca'
ACCENT_ACTIVE = '#3730a3'
ACCENT_SOFT = '#eef2ff'
OK = '#12b76a'
OK_SOFT = '#ecfdf3'
OK_INK = '#027a48'
WARN = '#f79009'
WARN_SOFT = '#fffaeb'
WARN_INK = '#b54708'
ERR = '#f04438'
ERR_SOFT = '#fef3f2'
ERR_INK = '#b42318'
INFO = '#2e90fa'
INFO_SOFT = '#eff8ff'
INFO_INK = '#175cd3'

FAMILY = 'Segoe UI'
MONO = 'Consolas'

# Действия с буфером обмена по аппаратному коду клавиши (event.keycode - код Windows,
# он не зависит от раскладки). Tk обрабатывает Ctrl+C сам только при латинской раскладке:
# при русской клавиша даёт keysym Cyrillic_es, и виртуальное событие <<Copy>> не приходит.
CLIPBOARD_KEYS = {65: 'select_all', 67: 'copy', 86: 'paste', 88: 'cut', 89: 'redo', 90: 'undo'}
LATIN_KEYSYMS = ('a', 'c', 'v', 'x', 'y', 'z', 'A', 'C', 'V', 'X', 'Y', 'Z')


def font(size=10, weight='normal'):
    """Шрифт интерфейса: один семейный ряд на всё окно."""
    return (FAMILY, size, weight)


def mono(size=9):
    """Моноширинный шрифт: тексты задач, журнал, технические детали."""
    return (MONO, size)


def label(master, text, bg=CARD, size=10, color=MUTED, weight='normal', wrap=None, mono_space=False):
    """Подпись поля: серый мелкий текст над контролом."""
    widget = tk.Label(master, text=text, bg=bg, fg=color, anchor='w', justify='left',
                      font=mono(size) if mono_space else font(size, weight))
    if wrap:
        widget.configure(wraplength=wrap)
    return widget


def rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Скруглённый прямоугольник на Canvas: polygon со сглаживанием вершин."""
    radius = max(0, min(radius, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# --- буфер обмена -----------------------------------------------------------------

def selection_text(widget):
    """Выделенный текст поля: у Text это диапазон sel, у Entry - selection."""
    try:
        if isinstance(widget, tk.Text):
            return widget.get('sel.first', 'sel.last') if widget.tag_ranges('sel') else ''
        return widget.selection_get() if widget.selection_present() else ''
    except tk.TclError:
        return ''


def drop_selection(widget):
    """Убрать выделение - для вырезания и вставки поверх выделенного."""
    try:
        if isinstance(widget, tk.Text):
            if widget.tag_ranges('sel'):
                widget.delete('sel.first', 'sel.last')
        elif widget.selection_present():
            widget.delete('sel.first', 'sel.last')
    except tk.TclError:
        pass


def clipboard_action(widget, action):
    """Выполнить действие с буфером обмена. Пустой буфер - не ошибка интерфейса."""
    try:
        if action in ('copy', 'cut'):
            text = selection_text(widget)
            if text:
                widget.clipboard_clear()
                widget.clipboard_append(text)
                if action == 'cut':
                    drop_selection(widget)
            return
        if action == 'paste':
            if str(widget.cget('state')) == 'disabled':
                return
            data = widget.clipboard_get()
            if data:
                drop_selection(widget)
                widget.insert('insert', data)
            return
        if action == 'select_all':
            if isinstance(widget, tk.Text):
                widget.tag_add('sel', '1.0', 'end-1c')
                widget.mark_set('insert', '1.0')
            else:
                widget.selection_range(0, 'end')
    except tk.TclError:
        pass


def control_action(keysym, keycode):
    """Действие для Ctrl+<клавиша> или None, если сочетание не наше.

    Разбор идёт по коду клавиши, а не по keysym: при русской раскладке Ctrl+C даёт
    keysym Cyrillic_es, и сочетание не опознаётся. Латинские keysym не перехватываются -
    их обрабатывает сам Tk, иначе действие выполнялось бы дважды.
    """
    if keysym in LATIN_KEYSYMS:
        return None
    return CLIPBOARD_KEYS.get(keycode)


def bind_clipboard(widget):
    """Ctrl+A/C/V/X на поле: работает и при русской раскладке."""
    def on_control(event):
        action = control_action(event.keysym, event.keycode)
        if not action:
            return None
        clipboard_action(widget, action)
        return 'break'

    widget.bind('<Control-KeyPress>', on_control, add='+')


class Card(tk.Frame):
    """Карточка: скруглённая панель с заголовком. Дети кладутся в .body."""

    def __init__(self, master, title='', subtitle='', padding=18, radius=14,
                 bg=CARD, app_bg=APP_BG, border=BORDER):
        tk.Frame.__init__(self, master, bg=app_bg)
        self.radius = radius
        self.padding = padding
        self.bg = bg
        self.border = border
        self.canvas = tk.Canvas(self, bg=app_bg, highlightthickness=0, bd=0)
        self.canvas.pack(fill='both', expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window(padding, padding, anchor='nw', window=self.inner)
        self.canvas.bind('<Configure>', self._on_resize)
        if title:
            head = tk.Frame(self.inner, bg=bg)
            head.pack(fill='x', pady=(0, 14))
            tk.Label(head, text=title, bg=bg, fg=INK, font=font(13, 'bold')).pack(anchor='w')
            if subtitle:
                tk.Label(head, text=subtitle, bg=bg, fg=MUTED, font=font(9)).pack(anchor='w', pady=(3, 0))
        self.body = tk.Frame(self.inner, bg=bg)
        self.body.pack(fill='both', expand=True)

    def _on_resize(self, event):
        self.canvas.delete('card_bg')
        rounded_rect(self.canvas, 0.5, 0.5, event.width - 1, event.height - 1, self.radius,
                     fill=self.bg, outline=self.border, width=1, tags='card_bg')
        self.canvas.tag_lower('card_bg')
        self.canvas.itemconfigure(self._window, width=max(1, event.width - 2 * self.padding),
                                  height=max(1, event.height - 2 * self.padding))



class Button(tk.Canvas):
    """Кнопка со скруглением и подсветкой: primary, secondary, ghost, danger."""

    KINDS = {
        'primary': dict(bg=ACCENT, fg='#ffffff', hover=ACCENT_HOVER, active=ACCENT_ACTIVE, border=ACCENT),
        'secondary': dict(bg=CARD, fg='#344054', hover=CARD_ALT, active=BORDER, border=BORDER_STRONG),
        'ghost': dict(bg=APP_BG, fg=MUTED, hover='#eceff5', active=BORDER, border=APP_BG),
        'danger': dict(bg=ERR, fg='#ffffff', hover='#d92d20', active='#b42318', border=ERR),
    }

    def __init__(self, master, text='', command=None, kind='primary', width=None, height=36,
                 radius=10, size=10, bg_parent=APP_BG):
        tk.Canvas.__init__(self, master, highlightthickness=0, bd=0, bg=bg_parent,
                           height=height, width=width or 120, takefocus=1)
        self._command = command
        self._kind = kind if kind in self.KINDS else 'primary'
        self._text = text
        self._height = height
        self._radius = radius
        self._font = tkfont.Font(family=FAMILY, size=size,
                                 weight='bold' if self._kind == 'primary' else 'normal')
        self._width = width or (self._font.measure(text) + 34)
        self._hover = False
        self._pressed = False
        self._enabled = True
        self.configure(width=self._width)
        self.bind('<Configure>', lambda _event: self._draw())
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<Return>', lambda _event: self._invoke())
        self.bind('<space>', lambda _event: self._invoke())
        self._draw()

    def _on_enter(self, _event):
        self._hover = True
        self._draw()

    def _on_leave(self, _event):
        self._hover = False
        self._pressed = False
        self._draw()

    def _on_press(self, _event):
        if self._enabled:
            self._pressed = True
            self._draw()

    def _on_release(self, _event):
        if not self._enabled:
            return
        self._pressed = False
        self._draw()
        if 0 <= self.winfo_pointerx() - self.winfo_rootx() <= self.winfo_width():
            self._invoke()

    def _invoke(self):
        if self._enabled and self._command:
            self._command()

    def set_text(self, text, keep_width=False):
        """Сменить подпись; по умолчанию кнопка не сужается под короткий текст."""
        self._text = text
        if not keep_width:
            self._width = max(self._width, self._font.measure(text) + 34)
            self.configure(width=self._width)
        self._draw()

    def set_kind(self, kind):
        if kind in self.KINDS and kind != self._kind:
            self._kind = kind
            self._font.configure(weight='bold' if kind == 'primary' else 'normal')
            self._draw()

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        if not self._enabled:
            self._hover = False
            self._pressed = False
        self._draw()

    def _draw(self):
        self.delete('all')
        style = self.KINDS[self._kind]
        if not self._enabled:
            fill, ink = CARD_ALT, '#98a2b3'
        elif self._pressed:
            fill, ink = style['active'], style['fg']
        elif self._hover:
            fill, ink = style['hover'], style['fg']
        else:
            fill, ink = style['bg'], style['fg']
        width = max(self.winfo_width(), self._width)
        height = max(self.winfo_height(), self._height)
        rounded_rect(self, 0.5, 0.5, width - 1, height - 1, self._radius, fill=fill,
                     outline=style['border'] if self._enabled else BORDER)
        self.create_text(width / 2.0, height / 2.0, text=self._text, fill=ink, font=self._font)


class Chip(tk.Canvas):
    """Пилюля состояния: цветная точка и текст. Виды: ok, warn, err, info, muted."""

    KINDS = {
        'ok': (OK, OK_SOFT, OK_INK),
        'warn': (WARN, WARN_SOFT, WARN_INK),
        'err': (ERR, ERR_SOFT, ERR_INK),
        'info': (INFO, INFO_SOFT, INFO_INK),
        'muted': (MUTED, CARD_ALT, MUTED),
    }

    def __init__(self, master, text='', kind='muted', bg_parent=CARD, height=26):
        self._font = tkfont.Font(family=FAMILY, size=9)
        self._height = height
        self._text = text
        self._kind = kind
        tk.Canvas.__init__(self, master, highlightthickness=0, bd=0, bg=bg_parent,
                           width=self._font.measure(text) + 34, height=height)
        self._draw()

    def set(self, text, kind='muted'):
        """Показать новое состояние. Ширина подстраивается под текст."""
        self._text = text
        self._kind = kind if kind in self.KINDS else 'muted'
        self.configure(width=self._font.measure(text) + 34)
        self._draw()

    def _draw(self):
        self.delete('all')
        dot, soft, ink = self.KINDS[self._kind]
        width = max(self.winfo_width(), self._font.measure(self._text) + 34)
        height = self._height
        rounded_rect(self, 0.5, 0.5, width - 1, height - 1, height / 2.0, fill=soft, outline=soft)
        radius = 3
        self.create_oval(12, height / 2.0 - radius, 12 + 2 * radius, height / 2.0 + radius,
                         fill=dot, outline=dot)
        self.create_text(12 + 2 * radius + 7, height / 2.0, text=self._text, anchor='w',
                         fill=ink, font=self._font)


class Input(tk.Frame):
    """Однострочное поле: плоская рамка, подсветка при фокусе, без системного вида."""

    def __init__(self, master, textvariable=None, bg=CARD, width=None, show=None):
        tk.Frame.__init__(self, master, bg=bg, bd=0, highlightthickness=1,
                          highlightbackground=BORDER_STRONG, highlightcolor=ACCENT)
        self.var = textvariable if textvariable is not None else tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.var, relief='flat', bd=0, bg=bg, fg=INK,
                              insertbackground=INK, font=font(10), highlightthickness=0,
                              selectbackground=ACCENT_SOFT, selectforeground=INK)
        if show:
            self.entry.configure(show=show)
        if width:
            self.entry.configure(width=width)
        self.entry.pack(fill='x', padx=10, pady=7)
        bind_clipboard(self.entry)
        self.entry.bind('<FocusIn>', lambda _event: self.configure(highlightbackground=ACCENT))
        self.entry.bind('<FocusOut>', lambda _event: self.configure(highlightbackground=BORDER_STRONG))
        self.bind('<Button-1>', lambda _event: self.entry.focus_set())

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

    def focus_set(self):
        self.entry.focus_set()


class TextArea(tk.Frame):
    """Многострочное поле: та же рамка, что у Input, плюс тонкая полоса прокрутки."""

    def __init__(self, master, height=5, bg=CARD, scroll=True, wrap='word', read_only=False):
        tk.Frame.__init__(self, master, bg=bg, bd=0, highlightthickness=1,
                          highlightbackground=BORDER_STRONG, highlightcolor=ACCENT)
        self.text = tk.Text(self, height=height, wrap=wrap, relief='flat', bd=0, bg=bg, fg=INK,
                            insertbackground=INK, font=font(10), highlightthickness=0,
                            selectbackground=ACCENT_SOFT, selectforeground=INK,
                            padx=10, pady=8, spacing1=2, spacing3=2)
        self.text.pack(side='left', fill='both', expand=True)
        if scroll:
            bar = ttk.Scrollbar(self, orient='vertical', style='Slim.Vertical.TScrollbar',
                                command=self.text.yview)
            bar.pack(side='right', fill='y', padx=(0, 4), pady=6)
            self.text.configure(yscrollcommand=bar.set)
        bind_clipboard(self.text)
        self.text.bind('<FocusIn>', lambda _event: self.configure(highlightbackground=ACCENT))
        self.text.bind('<FocusOut>', lambda _event: self.configure(highlightbackground=BORDER_STRONG))
        if read_only:
            self.text.configure(state='disabled')

    def get(self):
        return self.text.get('1.0', 'end')

    def set(self, value, read_only=False):
        """Показать текст: поле на время записи включается, потом снова блокируется."""
        self.text.configure(state='normal')
        self.text.delete('1.0', 'end')
        self.text.insert('1.0', value or '')
        self.text.see('1.0')
        self.text.configure(state='disabled' if read_only else 'normal')

    def clear(self):
        self.set('')


class Segmented(tk.Frame):
    """Переключатель из нескольких вариантов: активный выделен цветом."""

    def __init__(self, master, options, variable, command=None, bg=CARD):
        tk.Frame.__init__(self, master, bg=bg)
        self.var = variable
        self._command = command
        self._buttons = {}
        for value, text in options:
            button = Button(self, text=text, kind='secondary', height=32, radius=8, size=9,
                            bg_parent=bg, command=lambda v=value: self._choose(v))
            button.pack(side='left', padx=(0, 8))
            self._buttons[value] = button
        self.var.trace_add('write', lambda *_args: self._sync())
        self._sync()

    def _choose(self, value):
        self.var.set(value)
        if self._command:
            self._command()

    def _sync(self):
        for value, button in self._buttons.items():
            button.set_kind('primary' if self.var.get() == value else 'secondary')


class Banner(tk.Frame):
    """Строка-сообщение: успех, предупреждение или ошибка вместо модального окна."""

    KINDS = {
        'ok': (OK_SOFT, OK_INK),
        'warn': (WARN_SOFT, WARN_INK),
        'err': (ERR_SOFT, ERR_INK),
        'info': (INFO_SOFT, INFO_INK),
        'muted': (CARD_ALT, MUTED),
    }

    def __init__(self, master, bg=CARD):
        tk.Frame.__init__(self, master, bg=bg, bd=0, highlightthickness=1, highlightbackground=bg)
        self._label = tk.Label(self, text='', bg=bg, fg=MUTED, font=font(9), anchor='w',
                               justify='left', wraplength=460)
        self._label.pack(fill='x', padx=12, pady=8)
        self.bind('<Configure>',
                  lambda event: self._label.configure(wraplength=max(200, event.width - 28)))

    def show(self, message, kind='info'):
        """Показать сообщение: виджет уже размещён в родителе через grid."""
        soft, ink = self.KINDS.get(kind, self.KINDS['info'])
        self.configure(bg=soft, highlightbackground=soft)
        self._label.configure(text=message, bg=soft, fg=ink)
        self.grid()

    def hide(self):
        self._label.configure(text='')
        self.grid_remove()


def setup_theme(root):
    """Перекрасить ttk под палитру окна: тема clam красится целиком, в отличие от vista."""
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass

    list_font = tkfont.Font(family=FAMILY, size=10)
    root.option_add('*TCombobox*Listbox.background', CARD)
    root.option_add('*TCombobox*Listbox.foreground', INK)
    root.option_add('*TCombobox*Listbox.selectBackground', ACCENT_SOFT)
    root.option_add('*TCombobox*Listbox.selectForeground', INK)
    root.option_add('*TCombobox*Listbox.font', list_font.name)
    root.option_add('*TCombobox*Listbox.borderWidth', 0)

    style.configure('Modern.TCombobox', fieldbackground=CARD, background=CARD, foreground=INK,
                    bordercolor=BORDER_STRONG, lightcolor=BORDER_STRONG, darkcolor=BORDER_STRONG,
                    arrowcolor=MUTED, arrowsize=14, padding=(8, 6), relief='flat')
    style.map('Modern.TCombobox',
              bordercolor=[('focus', ACCENT)],
              fieldbackground=[('readonly', CARD), ('disabled', CARD_ALT)],
              foreground=[('disabled', MUTED)])

    style.configure('Modern.Treeview', background=CARD, fieldbackground=CARD, foreground=INK,
                    font=font(10), rowheight=32, borderwidth=0, relief='flat')
    style.map('Modern.Treeview', background=[('selected', ACCENT_SOFT)],
              foreground=[('selected', INK)])
    style.configure('Modern.Treeview.Heading', background=CARD, foreground=MUTED,
                    font=font(9, 'bold'), relief='flat', borderwidth=0, padding=(10, 10))
    style.map('Modern.Treeview.Heading', background=[('active', CARD_ALT)])
    style.layout('Modern.Treeview', [('Modern.Treeview.treearea', {'sticky': 'nswe'})])

    # Полоса прокрутки: у неё должен быть видный и подвижный ползунок. Стрелки убраны
    # (slim), а ползунок тёмный - на светлом фоне он иначе не отличается от желоба,
    # и поле выглядит как поле без прокрутки.
    style.configure('Slim.Vertical.TScrollbar', background='#98a2b3', troughcolor=CARD,
                    bordercolor=CARD, lightcolor='#98a2b3', darkcolor='#98a2b3',
                    arrowcolor=CARD, relief='flat', arrowsize=1, width=12)
    style.map('Slim.Vertical.TScrollbar',
              background=[('pressed', ACCENT), ('active', MUTED)])
    style.layout('Slim.Vertical.TScrollbar', [
        ('Vertical.Scrollbar.trough', {
            'children': [('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})],
            'sticky': 'ns',
        }),
    ])
    return style



