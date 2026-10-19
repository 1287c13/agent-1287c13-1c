'use strict';

/*
 * Страница очереди: вход по ключу, постановка задачи, ожидание стадий, история.
 *
 * Политика опроса: браузер не опрашивает сервер на простое. Запросы идут при загрузке
 * страницы (проверка сохранённого ключа), при входе, при отправке задачи и пока
 * поставленная задача не завершена. Интервал ожидания растёт 3 -> 5 -> 10 -> 20 -> 30 с,
 * на скрытой вкладке опрос замирает, после возврата - сразу один запрос.
 * Ни SSE, ни WebSocket: каждый открытый поток занимает процесс Passenger, а очередь
 * меняется редко и адресно - по идентификатору своей задачи.
 */

(function () {
  var STORE = {
    keys: 'integration.keys',
    active: 'integration.activeKey',
    url: 'integration.serverUrl'
  };
  var POLL_DELAYS = [3000, 5000, 10000, 20000, 30000];
  var state = {
    url: '',
    key: '',
    client: '',
    allowHarness: false,
    databases: [],
    currentId: '',
    lastId: '',
    pollStep: 0,
    timer: null
  };

  function el(id) { return document.getElementById(id); }

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function formatDuration(seconds) {
    var total = Math.max(0, Math.round(Number(seconds) || 0));
    if (total < 60) { return total + ' с'; }
    var minutes = Math.floor(total / 60);
    if (minutes < 60) { return minutes + ' мин ' + (total % 60) + ' с'; }
    return Math.floor(minutes / 60) + ' ч ' + (minutes % 60) + ' мин';
  }

  function setText(id, text, kind) {
    var node = el(id);
    if (!node) { return; }
    node.textContent = text || '';
    node.className = 'state' + (kind ? ' ' + kind : '');
  }

  // --- сохранённые ключи ----------------------------------------------------

  function readJson(name, fallback) {
    try {
      var raw = localStorage.getItem(name);
      return raw ? JSON.parse(raw) : fallback;
    } catch (error) {
      return fallback;
    }
  }

  function writeJson(name, value) {
    try { localStorage.setItem(name, JSON.stringify(value)); } catch (error) { /* режим приватности */ }
  }

  function savedKeys() {
    var list = readJson(STORE.keys, []);
    return Array.isArray(list) ? list : [];
  }

  function rememberKey(key) {
    if (!key) { return; }
    var list = savedKeys().filter(function (item) { return item !== key; });
    list.unshift(key);
    writeJson(STORE.keys, list.slice(0, 10));
  }

  function maskKey(key) {
    if (!key) { return ''; }
    if (key.length <= 8) { return key[0] + '…' + key[key.length - 1]; }
    return key.slice(0, 4) + '…' + key.slice(-4);
  }

  function renderKeys() {
    var box = el('keys-box');
    box.innerHTML = '';
    var list = savedKeys();
    if (!list.length) {
      box.innerHTML = '<span class="state">сохранённых ключей нет</span>';
      return;
    }
    list.forEach(function (key) {
      var chip = document.createElement('span');
      chip.className = 'key-chip' + (key === state.key ? ' active' : '');
      var label = document.createElement('span');
      label.textContent = maskKey(key);
      label.title = 'войти под этим ключом';
      label.addEventListener('click', function () {
        el('api-key').value = key;
        state.key = key;
        connect(false);
      });
      var drop = document.createElement('button');
      drop.type = 'button';
      drop.textContent = '×';
      drop.title = 'удалить ключ из браузера';
      drop.addEventListener('click', function () { forgetKey(key); });
      chip.appendChild(label);
      chip.appendChild(drop);
      box.appendChild(chip);
    });
    var forget = document.createElement('button');
    forget.type = 'button';
    forget.className = 'ghost';
    forget.textContent = 'Забыть все ключи';
    forget.addEventListener('click', forgetAll);
    box.appendChild(forget);
  }

  function forgetKey(key) {
    writeJson(STORE.keys, savedKeys().filter(function (item) { return item !== key; }));
    if (state.key === key) {
      state.key = '';
      localStorage.removeItem(STORE.active);
      el('api-key').value = '';
      disconnect('ключ удалён из браузера');
    }
    renderKeys();
  }

  function forgetAll() {
    if (!window.confirm('Удалить все сохранённые ключи из этого браузера? Восстановить их будет нельзя.')) {
      return;
    }
    localStorage.removeItem(STORE.keys);
    localStorage.removeItem(STORE.active);
    state.key = '';
    el('api-key').value = '';
    disconnect('все ключи удалены из браузера');
    renderKeys();
  }

  // --- сеть -----------------------------------------------------------------

  function api(path, options) {
    options = options || {};
    var headers = { 'Accept': 'application/json' };
    if (options.body !== undefined) {
      headers['Content-Type'] = 'application/json; charset=utf-8';
    }
    if (state.key) {
      headers['X-Integration-Token'] = state.key;
    }
    return fetch(state.url + path, {
      method: options.method || 'GET',
      headers: headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body)
    }).then(function (response) {
      return response.text().then(function (text) {
        var data = {};
        try { data = text ? JSON.parse(text) : {}; } catch (error) { data = { error: text }; }
        if (!response.ok) {
          var message = data.error || ('HTTP ' + response.status);
          if (data.errors && data.errors.length) {
            message += ': ' + data.errors.join('; ');
          }
          var failure = new Error(message);
          failure.status = response.status;
          failure.data = data;
          throw failure;
        }
        return data;
      });
    });
  }

  function serverUrl() {
    return (el('server-url').value || '').trim().replace(/\/+$/, '');


  // --- вход и форма ---------------------------------------------------------

  function connect(silent) {
    state.url = serverUrl();
    state.key = el('api-key').value || '';
    if (!state.url) {
      setText('conn-state', 'укажите адрес сервера', 'bad');
      return Promise.resolve(false);
    }
    localStorage.setItem(STORE.url, state.url);
    setText('conn-state', 'проверяю ключ…');
    return api('/api/auth', { method: 'POST', body: { key: state.key } }).then(function (data) {
      state.client = data.client || '';
      state.allowHarness = Boolean(data.allow_harness);
      state.databases = data.databases || [];
      localStorage.setItem(STORE.active, state.key);
      rememberKey(state.key);
      renderKeys();
      renderDatabases();
      renderMode();
      setText('conn-state', 'вход выполнен: ' + state.client, 'ok');
      el('submit-card').hidden = false;
      el('history-card').hidden = false;
      setText('submit-state', '');
      if (!silent) { loadHistory(); }
      return true;
    }).catch(function (error) {
      setText('conn-state', 'вход не выполнен: ' + error.message, 'bad');
      return false;
    });
  }

  function disconnect(reason) {
    state.client = '';
    state.currentId = '';
    clearTimeout(state.timer);
    setText('conn-state', reason || 'не подключено');
    el('submit-card').hidden = true;
    el('history-card').hidden = true;
  }

  function renderDatabases() {
    var list = el('db-list');
    list.innerHTML = '';
    state.databases.forEach(function (name) {
      var option = document.createElement('option');
      option.value = name;
      list.appendChild(option);
    });
    if (!el('task-db').value && state.databases.length) {
      el('task-db').value = state.databases[0];
    }
  }

  function renderMode() {
    var harness = el('task-mode').value === 'harness';
    el('db-field').hidden = harness;
    var option = el('task-mode').querySelector('option[value="harness"]');
    option.disabled = !state.allowHarness;
    if (harness && !state.allowHarness) {
      el('task-mode').value = 'db';
      el('db-field').hidden = false;
    }
  }

  function submitTask(event) {
    event.preventDefault();
    if (!state.client) {
      setText('submit-state', 'сначала войдите по ключу', 'bad');
      return;
    }
    var mode = el('task-mode').value;
    var body = {
      mode: mode,
      role: el('task-role').value.trim(),
      action: el('task-action').value.trim(),
      goal: el('task-goal').value.trim(),
      deliver: el('task-deliver').value,
      timeout_s: Number(el('task-timeout').value) || 1800
    };
    if (mode === 'db') { body.db = el('task-db').value.trim(); }
    setText('submit-state', 'отправляю…');
    el('btn-submit').disabled = true;
    api('/api/task', { method: 'POST', body: body }).then(function (data) {
      setText('submit-state', 'задача ' + data.task_id + ' поставлена', 'ok');
      el('task-action').value = '';
      el('task-goal').value = '';
      el('status-card').hidden = false;
      state.lastId = data.task_id;
      startPolling(data.task_id);
    }).catch(function (error) {
      setText('submit-state', 'задача не принята: ' + error.message, 'bad');
    }).then(function () {
      el('btn-submit').disabled = false;
    });
  }

  // --- ожидание стадий ------------------------------------------------------

  function startPolling(taskId) {
    state.currentId = taskId;
    state.lastId = taskId;
    state.pollStep = 0;
    pollOnce();
  }

  function schedulePoll(delay) {
    clearTimeout(state.timer);
    state.timer = setTimeout(pollOnce, delay);
  }

  function pollOnce() {
    if (!state.currentId) { return; }
    if (document.hidden) {
      schedulePoll(POLL_DELAYS[POLL_DELAYS.length - 1]);
      return;
    }
    var taskId = state.currentId;
    api('/api/status/' + encodeURIComponent(taskId)).then(function (item) {
      renderStatus(item);
      if (item.terminal) {
        state.currentId = '';
        loadHistory();
        return;
      }
      var delay = POLL_DELAYS[Math.min(state.pollStep, POLL_DELAYS.length - 1)];
      state.pollStep += 1;
      schedulePoll(delay);
    }).catch(function (error) {
      el('status-hint').textContent = 'состояние не прочитано: ' + error.message;
      schedulePoll(POLL_DELAYS[POLL_DELAYS.length - 1]);
    });
  }

  function renderStatus(item) {
    el('status-card').hidden = false;
    state.lastId = item.task_id || state.lastId;
    el('status-id').textContent = item.task_id || '';
    var badge = el('status-badge');
    badge.textContent = item.state || '';
    badge.className = 'badge ' + (item.state || '');
    el('status-hint').textContent = item.wait_hint || '';
    el('status-agent').textContent = item.agent || '-';
    el('status-elapsed').textContent = formatDuration(item.elapsed_s);
    el('status-message').textContent = item.message || '-';
    var list = el('status-progress');
    list.innerHTML = '';
    (item.progress || []).forEach(function (step) {
      var row = document.createElement('li');
      row.innerHTML = '<b>' + escapeHtml(step.stage) + '</b> ' +
        escapeHtml(step.at || '') + ' - ' + escapeHtml(step.message || '');
      list.appendChild(row);
    });
    el('btn-answer-md').disabled = !item.answer_available;
    el('btn-answer-html').disabled = !item.answer_available;
  }



  // --- ответ и история ------------------------------------------------------

  function loadAnswer(kind) {
    var taskId = state.lastId;
    if (!taskId) { return; }
    api('/api/answer/' + encodeURIComponent(taskId) + '?format=' + kind).then(function (data) {
      var name = data.file_name || ('answer_' + taskId + '.' + (kind === 'html' ? 'html' : 'md'));
      if (kind === 'html') {
        var page = new Blob([data.content || ''], { type: 'text/html;charset=utf-8' });
        var url = URL.createObjectURL(page);
        window.open(url, '_blank');
        setTimeout(function () { URL.revokeObjectURL(url); }, 60000);
        return;
      }
      var file = new Blob([data.content || ''], { type: 'text/markdown;charset=utf-8' });
      var link = document.createElement('a');
      link.href = URL.createObjectURL(file);
      link.download = name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(function () { URL.revokeObjectURL(link.href); }, 10000);
    }).catch(function (error) {
      setText('submit-state', 'ответ не получен: ' + error.message, 'bad');
    });
  }

  function loadHistory() {
    if (!state.client) { return; }
    setText('history-state', 'загружаю…');
    api('/api/history?limit=20').then(function (data) {
      renderHistory(data.items || []);
      var counts = data.counts || {};
      setText('history-state', 'ждут ' + (counts.queued || 0) + ', в работе ' +
        (counts.processing || 0) + ', готово ' + (counts.done || 0) +
        ', сбоев ' + (counts.failed || 0) + ', агентов живо ' + (counts.agents_alive || 0));
    }).catch(function (error) {
      setText('history-state', 'история не прочитана: ' + error.message, 'bad');
    });
  }

  function renderHistory(items) {
    var body = el('history-table').querySelector('tbody');
    body.innerHTML = '';
    if (!items.length) {
      var empty = document.createElement('tr');
      empty.innerHTML = '<td colspan="5" class="state">задач пока нет</td>';
      body.appendChild(empty);
      return;
    }
    items.forEach(function (item) {
      var row = document.createElement('tr');
      row.innerHTML =
        '<td class="mono">' + escapeHtml(item.task_id) + '</td>' +
        '<td><span class="badge ' + escapeHtml(item.state) + '">' + escapeHtml(item.state) + '</span></td>' +
        '<td>' + escapeHtml(item.agent || '-') + '</td>' +
        '<td>' + escapeHtml(item.created_at || '') + '</td>' +
        '<td>' + escapeHtml(item.prompt || '') + '</td>';
      row.addEventListener('click', function () {
        state.lastId = item.task_id;
        el('status-card').hidden = false;
        api('/api/status/' + encodeURIComponent(item.task_id)).then(renderStatus)
          .catch(function (error) { el('status-hint').textContent = error.message; });
      });
      body.appendChild(row);
    });
  }

  // --- запуск ---------------------------------------------------------------

  document.addEventListener('DOMContentLoaded', function () {
    var savedUrl = localStorage.getItem(STORE.url) || '';
    el('server-url').value = savedUrl || (location.origin.indexOf('http') === 0 ? location.origin : '');
    var active = localStorage.getItem(STORE.active) || '';
    el('api-key').value = active;
    state.key = active;
    renderKeys();
    renderMode();

    el('btn-connect').addEventListener('click', function () { connect(false); });
    el('task-form').addEventListener('submit', submitTask);
    el('task-mode').addEventListener('change', renderMode);
    el('btn-history').addEventListener('click', loadHistory);
    el('btn-answer-md').addEventListener('click', function () { loadAnswer('md'); });
    el('btn-answer-html').addEventListener('click', function () { loadAnswer('html'); });
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden && state.currentId) {
        clearTimeout(state.timer);
        pollOnce();
      }
    });

    if (savedUrl && active) {
      connect(true);
    }
  });
})();

  }
