# -*- coding: utf-8 -*-
"""Точка входа Passenger: приложение берётся из transport\\wsgi.py.

Passenger ищет в каталоге приложения файл passenger_wsgi.py и вызывает из него
объект `application`. Класть всю логику сюда не нужно: она живёт в transport\\wsgi.py,
иначе у хостинга и у локальной проверки были бы разные реализации.

Перед запуском Passenger задаёт каталог приложения; каталогом приложения выбран
integration\\, поэтому корень харнесса - на уровень выше.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_INTEGRATION = os.path.dirname(_HERE)
if _INTEGRATION not in sys.path:
    sys.path.insert(0, _INTEGRATION)

os.environ.setdefault('INTEGRATION_ROOT', os.path.dirname(_INTEGRATION))

from transport.wsgi import application  # noqa: E402,F401
