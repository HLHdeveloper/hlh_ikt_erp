#!/usr/bin/env python3
"""Convierte los manuales markdown a HTML autocontenido (sin dependencias) y los
deja en static/manualak/ del módulo hernani, para servirlos en el navegador.

Uso:  python3 manualak/build_html.py
Reejecutar cada vez que se editen los .md.
"""
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(
    HERE, '..', 'addons19', 'openeducat_erp', 'openeducat_hernani',
    'static', 'manualak')

MANUALS = [
    ('MANUAL_SIS_HASIBERRIENTZAT.md', 'sis_hasiberrientzat.html'),
    ('MANUAL_SIS_LABURPENA.md', 'sis_laburpena.html'),
]

CSS = """
:root{--g:#198754;--g2:#146c43;--bg:#f6faf7}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
 line-height:1.6;color:#222;max-width:880px;margin:0 auto;padding:2rem 1.2rem;
 background:#fff}
h1{color:var(--g2);border-bottom:3px solid var(--g);padding-bottom:.3rem}
h2{color:var(--g2);margin-top:2rem;border-bottom:1px solid #cde7d6;padding-bottom:.2rem}
h3{color:var(--g)}
a{color:var(--g2)}
code{background:#eef5f0;padding:.1rem .35rem;border-radius:.25rem;font-size:.92em}
blockquote{margin:1rem 0;padding:.6rem 1rem;background:var(--bg);
 border-left:4px solid var(--g);border-radius:.25rem;color:#33493d}
table{border-collapse:collapse;width:100%;margin:1rem 0}
th,td{border:1px solid #cfe3d6;padding:.4rem .6rem;text-align:left;vertical-align:top}
th{background:#e8f6ec;color:var(--g2)}
hr{border:none;border-top:1px solid #d7e6dc;margin:2rem 0}
ul,ol{padding-left:1.4rem}
li{margin:.25rem 0}
"""


def inline(text):
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def parse_list(lines, i, ordered):
    pat = re.compile(r'^\s*\d+\.\s+') if ordered else re.compile(r'^\s*[-*]\s+')
    bullet = re.compile(r'^\s*([-*]|\d+\.)\s+')
    items = []
    n = len(lines)
    while i < n and pat.match(lines[i]):
        text = pat.sub('', lines[i])
        i += 1
        while (i < n and lines[i].strip() and not bullet.match(lines[i])
               and lines[i][:1] in (' ', '\t')):
            text += ' ' + lines[i].strip()
            i += 1
        items.append(text)
    return i, items


def convert(md):
    lines = md.split('\n')
    out, i, n = [], 0, len(md.split('\n'))
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if re.match(r'^---+$', s):
            out.append('<hr/>'); i += 1; continue
        m = re.match(r'^(#{1,6})\s+(.*)$', s)
        if m:
            lv = len(m.group(1))
            out.append('<h%d>%s</h%d>' % (lv, inline(m.group(2)), lv)); i += 1; continue
        if s.startswith('>'):
            buf = []
            while i < n and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip()[1:].strip()); i += 1
            out.append('<blockquote>%s</blockquote>' % inline(' '.join(buf))); continue
        if s.startswith('|'):
            tbl = []
            while i < n and lines[i].strip().startswith('|'):
                tbl.append(lines[i].strip()); i += 1
            cells = lambda r: [c.strip() for c in r.strip().strip('|').split('|')]
            header = cells(tbl[0])
            body = tbl[2:] if len(tbl) > 1 and re.match(r'^\|?[\s:\-|]+\|?$', tbl[1]) else tbl[1:]
            th = ''.join('<th>%s</th>' % inline(c) for c in header)
            rows = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in cells(r)) for r in body)
            out.append('<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (th, rows)); continue
        if re.match(r'^[-*]\s+', s):
            i, items = parse_list(lines, i, False)
            out.append('<ul>%s</ul>' % ''.join('<li>%s</li>' % inline(it) for it in items)); continue
        if re.match(r'^\d+\.\s+', s):
            i, items = parse_list(lines, i, True)
            out.append('<ol>%s</ol>' % ''.join('<li>%s</li>' % inline(it) for it in items)); continue
        buf = []
        while i < n and lines[i].strip() and not re.match(r'^(#|>|\||[-*]\s|\d+\.\s|---)', lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        out.append('<p>%s</p>' % inline(' '.join(buf)))
    return '\n'.join(out)


def build():
    os.makedirs(OUT, exist_ok=True)
    for src, dst in MANUALS:
        with open(os.path.join(HERE, src), encoding='utf-8') as f:
            md = f.read()
        title = md.split('\n', 1)[0].lstrip('# ').strip()
        body = convert(md)
        page = ('<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>%s</title><style>%s</style></head><body>%s</body></html>'
                % (html.escape(title), CSS, body))
        with open(os.path.join(OUT, dst), 'w', encoding='utf-8') as f:
            f.write(page)
        print('->', os.path.normpath(os.path.join(OUT, dst)))


if __name__ == '__main__':
    build()
