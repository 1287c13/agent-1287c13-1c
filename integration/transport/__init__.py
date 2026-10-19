# -*- coding: utf-8 -*-
"""Транспорт внешней интеграции: очередь на сервере, HTTP, WSGI, клиент агента.

Модули пакета:

    store.py      - каталог очереди на сервере (inbox, processing, archive, outbox,
                    failed, agents, events.jsonl) и переходы состояний;
    config.py     - deploy\\config.json: сервер (ключи, базы, лимиты) и агент;
    schema.py     - мини-валидатор JSON Schema по схемам integration\\schemas\\;
    api.py        - логика HTTP-интерфейса (задачи, стадии, ответы, агенты);
    client.py     - HTTP-клиент агента и командной строки;
    http_server.py - локальный сервер на wsgiref (проверка без хостинга);
    wsgi.py        - приложение WSGI для Passenger и подобных серверов.

Точка входа Passenger лежит выше пакета - integration\\passenger_wsgi.py: корень
приложения Passenger - каталог integration\\, а не transport\\.

Смысл разделения: очередь одна и живёт на сервере, а транспорт съёмный. Локальная
проверка (http_server.py) и хостинг (wsgi.py) исполняют один api.py, поэтому
протокол задач от способа запуска не зависит. Агент общается с очередью только по
HTTP (client.py) и не держит второй каталог очереди у себя.
"""

