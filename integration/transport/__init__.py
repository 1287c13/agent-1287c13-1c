# -*- coding: utf-8 -*-
"""Транспорт внешней интеграции: очередь, валидация по схемам, HTTP и WSGI.

Модули пакета:

    store.py   - каталог queue\\ как очередь (журнал, inbox, processing, archive, outbox);
    schema.py  - мини-валидатор JSON Schema по схемам integration\\schemas\\;
    api.py     - общая логика HTTP-интерфейса (health, task, result, tasks);
    http_server.py    - сервер разработки на http.server (localhost);
    wsgi.py           - приложение WSGI для хостинга (Passenger и подобные);
    passenger_wsgi.py - точка входа Passenger.

Смысл разделения: логика одна (api.py), а транспорт съёмный. Локально гоняют
http_server.py, на сервере - wsgi.py под Passenger; обе стороны читают и пишут одну
и ту же очередь на диске, поэтому переход с локального запуска на серверный ничего
не меняет в протоколе задач.
"""
