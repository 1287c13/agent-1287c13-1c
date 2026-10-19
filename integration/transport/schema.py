import json
import re

TYPES = {
    'object': dict,
    'array': list,
    'string': str,
    'boolean': bool,
    'integer': int,
    'number': (int, float),
    'null': type(None),
}


def read_schema(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_errors(errors):
    return '; '.join(errors)


def validate(instance, schema, where=''):
    errors = []
    if not isinstance(schema, dict):
        return errors

    expected = schema.get('type')
    if expected is not None:
        names = expected if isinstance(expected, list) else [expected]
        if isinstance(instance, bool) and 'boolean' not in names:
            errors.append('%s: ожидается %s, пришло boolean' % (where or 'значение', '/'.join(names)))
            return errors
        if not any(isinstance(instance, TYPES[n]) for n in names if n in TYPES):
            errors.append('%s: ожидается %s, пришло %s' % (where or 'значение', '/'.join(names), type(instance).__name__))
            return errors

    if isinstance(instance, str):
        pattern = schema.get('pattern')
        if pattern and not re.match(pattern, instance):
            errors.append('%s: "%s" не соответствует образцу %s' % (where or 'значение', instance, pattern))
        if 'minLength' in schema and len(instance) < schema['minLength']:
            errors.append('%s: короче %d символов' % (where or 'значение', schema['minLength']))
        if 'maxLength' in schema and len(instance) > schema['maxLength']:
            errors.append('%s: длиннее %d символов' % (where or 'значение', schema['maxLength']))

    if 'enum' in schema and instance not in schema['enum']:
        errors.append('%s: "%s" не из перечня %s' % (where or 'значение', instance, ', '.join(map(str, schema['enum']))))

    if isinstance(instance, int) and not isinstance(instance, bool):
        if 'minimum' in schema and instance < schema['minimum']:
            errors.append('%s: меньше %s' % (where or 'значение', schema['minimum']))

    if isinstance(instance, dict):
        for name in schema.get('required', []):
            if name not in instance:
                errors.append('не заполнено обязательное поле "%s"' % name)
        props = schema.get('properties', {})
        for name, value in instance.items():
            child = props.get(name)
            if child is None:
                if schema.get('additionalProperties') is False:
                    errors.append('поле "%s" схемой не разрешено' % name)
                continue
            prefix = '%s.%s' % (where, name) if where else name
            errors.extend(validate(value, child, prefix))
    elif isinstance(instance, list):
        item_schema = schema.get('items')
        if isinstance(item_schema, dict):
            for index, value in enumerate(instance):
                errors.extend(validate(value, item_schema, '%s[%d]' % (where or 'элемент', index)))
    return errors
