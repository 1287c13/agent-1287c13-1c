import html
import re

PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<style>
  body { margin: 0; padding: 32px 16px; background: #f4f6fb; color: #101828;
         font: 15px/1.6 "Segoe UI", system-ui, sans-serif; }
  main { max-width: 860px; margin: 0 auto; background: #fff; border: 1px solid #e4e7ec;
         border-radius: 14px; padding: 28px 32px; }
  h1, h2, h3, h4 { color: #101828; line-height: 1.25; margin: 28px 0 12px; }
  h1 { font-size: 24px; margin-top: 0; }
  h2 { font-size: 19px; }
  h3 { font-size: 16px; }
  p { margin: 10px 0; }
  a { color: #4f46e5; }
  code { background: #f2f4f7; border-radius: 6px; padding: 2px 6px;
         font-family: Consolas, monospace; font-size: 13px; }
  pre { background: #f2f4f7; border: 1px solid #e4e7ec; border-radius: 10px;
        padding: 14px 16px; overflow-x: auto; }
  pre code { background: none; padding: 0; }
  blockquote { margin: 12px 0; padding: 4px 16px; border-left: 3px solid #d0d5dd; color: #667085; }
  table { border-collapse: collapse; width: 100%%; margin: 14px 0; }
  th, td { border: 1px solid #e4e7ec; padding: 8px 10px; text-align: left; vertical-align: top; }
  th { background: #f9fafb; font-weight: 600; }
  ul, ol { margin: 10px 0; padding-left: 24px; }
  li { margin: 4px 0; }
  hr { border: 0; border-top: 1px solid #e4e7ec; margin: 22px 0; }
  .source { color: #667085; font-size: 13px; margin: 0 0 18px; }
</style>
</head>
<body>
<main>
%(body)s
</main>
</body>
</html>
"""

HEADING = re.compile(r'^(#{1,6})\s+(.*)$')
BULLET = re.compile(r'^\s*[-*+]\s+(.*)$')
NUMBER = re.compile(r'^\s*\d+[.)]\s+(.*)$')
RULE = re.compile(r'^\s*(-{3,}|\*{3,}|_{3,})\s*$')
TABLE_ROW = re.compile(r'^\s*\|.*\|\s*$')
TABLE_SEP = re.compile(r'^\s*\|(\s*:?-{2,}:?\s*\|)+\s*$')


def inline(text):
    out = html.escape(text, quote=False)
    out = re.sub(r'`([^`]+)`', r'<code>\1</code>', out)
    out = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', out)
    out = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', out)
    return re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2">\1</a>', out)


def table_cells(line):
    return [cell.strip() for cell in line.strip().strip('|').split('|')]


def render_table(lines, start):
    head = table_cells(lines[start])
    index = start + 2
    body = []
    while index < len(lines) and TABLE_ROW.match(lines[index]):
        body.append(table_cells(lines[index]))
        index += 1
    out = ['<table>', '<thead><tr>']
    out += ['<th>%s</th>' % inline(cell) for cell in head]
    out.append('</tr></thead>')
    if body:
        out.append('<tbody>')
        for row in body:
            out.append('<tr>' + ''.join('<td>%s</td>' % inline(cell) for cell in row) + '</tr>')
        out.append('</tbody>')
    out.append('</table>')
    return '\n'.join(out), index


def render_list(lines, start, ordered):
    pattern = NUMBER if ordered else BULLET
    items = []
    index = start
    while index < len(lines):
        match = pattern.match(lines[index])
        if not match:
            break
        items.append(match.group(1).strip())
        index += 1
    tag = 'ol' if ordered else 'ul'
    body = ''.join('<li>%s</li>' % inline(item) for item in items)
    return '<%s>%s</%s>' % (tag, body, tag), index


def render_body(markdown):
    lines = (markdown or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    out = []
    paragraph = []
    index = 0

    def flush():
        if paragraph:
            out.append('<p>%s</p>' % '<br>'.join(inline(line) for line in paragraph))
            del paragraph[:]

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith('```'):
            flush()
            code = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith('```'):
                code.append(lines[index])
                index += 1
            index += 1
            out.append('<pre><code>%s</code></pre>' % html.escape('\n'.join(code)))
            continue
        heading = HEADING.match(stripped)
        if heading:
            flush()
            level = min(6, len(heading.group(1)) + 1)
            out.append('<h%d>%s</h%d>' % (level, inline(heading.group(2)), level))
            index += 1
            continue
        if RULE.match(stripped):
            flush()
            out.append('<hr>')
            index += 1
            continue
        if TABLE_ROW.match(line) and index + 1 < len(lines) and TABLE_SEP.match(lines[index + 1]):
            flush()
            block, index = render_table(lines, index)
            out.append(block)
            continue
        if BULLET.match(line) or NUMBER.match(line):
            flush()
            block, index = render_list(lines, index, bool(NUMBER.match(line)))
            out.append(block)
            continue
        if stripped.startswith('>'):
            flush()
            quote = []
            while index < len(lines) and lines[index].strip().startswith('>'):
                quote.append(lines[index].strip()[1:].strip())
                index += 1
            out.append('<blockquote>%s</blockquote>' % inline(' '.join(quote)))
            continue
        if not stripped:
            flush()
            index += 1
            continue
        paragraph.append(stripped)
        index += 1
    flush()
    return '\n'.join(out)


def render(markdown, title='Ответ задачи', source=''):
    body = render_body(markdown)
    if source:
        body = '<p class="source">%s</p>\n%s' % (html.escape(source), body)
    return PAGE % {'title': html.escape(title), 'body': body}


def answer_file_name(task_id, kind='html'):
    return 'answer_%s.%s' % (task_id or 'task', kind)
