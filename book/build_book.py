"""Build a KDP-ready print PDF of 'Cisza, z której pochodzę' from the Ridero docx.

Usage: python3 build_book.py <input.docx> <out_dir> [trim]
trim: a5 (5.83x8.27in, default) | 6x9 | 5.5x8.5
"""
import sys, re, html, json, subprocess, pathlib
import docx
import pyphen
HYPH = pyphen.Pyphen(lang='pl_PL', left=3, right=3)

def shy(t):
    # soft hyphens so justified Polish text doesn't open wide gaps
    return re.sub(r'\w{7,}', lambda m: HYPH.inserted(m.group(0), hyphen='\u00ad'), t)

TRIMS = {"a5": ("5.83in", "8.27in"), "6x9": ("6in", "9in"), "5.5x8.5": ("5.5in", "8.5in")}
src, out = sys.argv[1], pathlib.Path(sys.argv[2])
trim = sys.argv[3] if len(sys.argv) > 3 else "a5"
W, H = TRIMS[trim]
out.mkdir(parents=True, exist_ok=True)
FONTCSS = pathlib.Path(__file__).resolve().parent / 'fonts' / 'eb-local.css'

paras = [p.text.strip() for p in docx.Document(src).paragraphs]
END = re.compile(r'[.!?…:”"»),;—-]$')

def esc(t): return html.escape(t, quote=False)

blocks, chapters, ul = [], [], []
def flush():
    global ul
    if ul:
        blocks.append('<ul>' + ''.join(f'<li>{esc(x)}</li>' for x in ul) + '</ul>')
        ul = []

for i, t in enumerate(paras):
    if i == 0 or not t:  # title handled on title page
        if not t: flush()
        continue
    if t.startswith('•'):
        ul.append(t.lstrip('•').strip()); continue
    flush()
    m = re.match(r'^Rozdział\s+(\d+):\s*(.+)$', t)
    if m or t.startswith('Zakończenie:') or t == 'Epilog':
        if m: label, title = f'Rozdział {m.group(1)}', m.group(2)
        elif t == 'Epilog': label, title = '', 'Epilog'
        else: label, title = 'Zakończenie', t.split(':', 1)[1].strip()
        cid = f'ch{len(chapters)+1}'
        chapters.append((cid, label, title))
        blocks.append(f'<section class="chapter" id="{cid}"><div class="ch-label">{esc(label)}</div><h1>{esc(title)}</h1></section>')
        continue
    if t.startswith('Ćwiczenia i\xa0pytania refleksyjne') or t.startswith('Ćwiczenia i pytania refleksyjne'):
        blocks.append(f'<h2 class="ex">{esc(t)}</h2>'); continue
    if i >= len(paras) - 4 and t in ('Joanna Dorobisz',):
        blocks.append(f'<p class="sign">{esc(t)}</p>'); continue
    if re.match(r'^\d+\.\s', t) and len(t) < 100:
        blocks.append(f'<h3>{esc(t)}</h3>'); continue
    if len(t) < 75 and not END.search(t):
        blocks.append(f'<h2>{esc(t)}</h2>'); continue
    blocks.append(f'<p>{shy(esc(t))}</p>')
flush()

def toc_html(pages):
    rows = []
    for cid, label, title in chapters:
        pg = pages.get(cid, '')
        lab = f'<span class="tl">{esc(label)}</span>' if label else ''
        rows.append(f'<li>{lab}<span class="tt">{esc(title)}</span><span class="pg">{pg}</span></li>')
    return '<ol class="toc">' + ''.join(rows) + '</ol>'

CSS = f"""
@page {{ size: {W} {H}; margin: 0.75in 0.6in 0.85in 0.75in;
  @bottom-center {{ content: counter(page); font-family: 'EB Garamond', serif; font-size: 9.5pt; color: #444; }} }}
@page :left {{ margin-left: 0.6in; margin-right: 0.75in; }}
@page :right {{ margin-left: 0.75in; margin-right: 0.6in; }}
@page front {{ @bottom-center {{ content: none; }} }}
@page opener {{ @bottom-center {{ content: none; }} }}
html {{ font-family: 'EB Garamond', serif; font-size: 11.5pt; line-height: 1.42; color: #111; }}
body {{ margin: 0; }}
.front {{ page: front; break-after: page; }}
.title-page {{ text-align: center; padding-top: 1.6in; }}
.title-page .author {{ font-size: 13pt; letter-spacing: .25em; text-transform: uppercase; }}
.title-page h1 {{ font-size: 28pt; font-weight: 500; line-height: 1.15; margin: .9in 0 .25in; }}
.title-page .sub {{ font-size: 14pt; font-style: italic; }}
.copy {{ display: flex; flex-direction: column; justify-content: flex-end; height: 6.4in; font-size: 9.5pt; line-height: 1.5; }}
.copy p {{ text-indent: 0; margin: 0 0 .6em; }}
.blank {{ page: front; break-after: page; height: 1px; }}
.toc-page h1 {{ font-size: 17pt; font-weight: 500; text-align: center; margin: 0 0 .25in; }}
ol.toc {{ list-style: none; padding: 0; margin: 0; font-size: 9.6pt; line-height: 1.25; }}
ol.toc li {{ display: grid; grid-template-columns: 1fr auto; column-gap: 12px; margin-bottom: 5px; break-inside: avoid; }}
ol.toc .tl {{ grid-column: 1 / 3; font-size: 7.5pt; letter-spacing: .15em; text-transform: uppercase; color: #555; }}
ol.toc .tt {{ grid-column: 1; }}
ol.toc .pg {{ grid-column: 2; text-align: right; }}
.chapter {{ break-before: page; padding-top: 1in; margin-bottom: .45in; text-align: center; }}
.ch-label {{ font-size: 10pt; letter-spacing: .25em; text-transform: uppercase; color: #555; margin-bottom: 14px; }}
.chapter h1 {{ font-size: 19pt; font-weight: 500; line-height: 1.25; margin: 0 .2in; }}
.chapter::after {{ content: ''; display: block; width: 40px; height: 1px; background: #888; margin: 22px auto 0; }}
p {{ margin: 0; text-indent: 1.2em; text-align: justify; hyphens: auto; orphans: 2; widows: 2; }}
.chapter + p, h2 + p, h3 + p, ul + p {{ text-indent: 0; }}
h2 {{ font-size: 13pt; font-weight: 600; margin: 1.3em 0 .5em; line-height: 1.25; break-after: avoid; }}
h2.ex {{ font-size: 12pt; font-weight: 500; text-align: center; letter-spacing: .12em; text-transform: uppercase; margin: 2em 0 1em; padding: .5em 0; border-top: .5pt solid #777; border-bottom: .5pt solid #777; }}
h3 {{ font-size: 11.5pt; font-weight: 600; font-style: italic; margin: 1.1em 0 .35em; break-after: avoid; line-height: 1.3; }}
ul {{ margin: .4em 0 .6em; padding-left: 1.3em; }}
li {{ margin-bottom: .2em; text-align: left; }}
.sign {{ text-indent: 0; text-align: right; font-style: italic; margin-top: .6em; }}
"""

def build(pages):
    body = f"""
<div class="front title-page"><div class="author">Joanna Dorobisz</div><h1>Cisza,<br>z której pochodzę</h1><div class="sub">Mapa powrotu do siebie</div></div>
<div class="front copy"><p>Copyright © Joanna Dorobisz</p><p>ISBN: 9798161014752</p><p>Wszelkie prawa zastrzeżone. Żadna część tej książki nie może być powielana ani rozpowszechniana bez pisemnej zgody autorki, z wyjątkiem krótkich cytatów w recenzjach.</p><p>Książka nie zastępuje terapii ani pomocy specjalistycznej. Jeśli doświadczasz przemocy lub kryzysu, skontaktuj się ze specjalistą lub telefonem zaufania.</p><p>Let Your Soul Glow · letyoursoulglow.store</p></div>
<div class="front toc-page"><h1>Spis treści</h1>{toc_html(pages)}</div>
<div class="blank"></div>
{''.join(blocks)}
"""
    return f"""<!doctype html><html lang="pl"><head><meta charset="utf-8">
<link href="file://{FONTCSS}" rel="stylesheet">
<style>{CSS}</style></head><body>{body}</body></html>"""

def render(htmlstr, pdf):
    (out / 'book.html').write_text(htmlstr)
    js = f"""const {{ chromium }} = require('playwright');
(async()=>{{const b=await chromium.launch({{executablePath:'/opt/pw-browsers/chromium'}});const p=await b.newPage();
await p.goto('file://{(out/'book.html').resolve()}');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(1500);
await p.pdf({{path:'{pdf}',preferCSSPageSize:true,printBackground:true}});await b.close();}})();"""
    (out / 'render.js').write_text(js)
    npm_root = subprocess.check_output(['npm', 'root', '-g'], text=True).strip()
    subprocess.run(['node', str(out / 'render.js')], check=True, env={'NODE_PATH': npm_root, 'PATH': '/usr/bin:/usr/local/bin:/bin'})

def find_pages(pdf):
    n = int(re.search(r'Pages:\s+(\d+)', subprocess.check_output(['pdfinfo', pdf], text=True)).group(1))
    texts = [subprocess.check_output(['pdftotext', '-f', str(k), '-l', str(k), '-layout', pdf, '-'], text=True) for k in range(1, n + 1)]
    norm = lambda s: re.sub(r'\s+', ' ', s.replace('\xa0', ' ')).strip()
    pages = {}
    keys = [norm(t)[:28] for _, _, t in chapters]
    # front matter = every page up to the last one listing several chapter titles (the contents)
    start = 1 + max([k for k in range(1, n + 1) if sum(key in norm(texts[k - 1]) for key in keys) >= 3] or [0])
    for cid, label, title in chapters:
        key = norm(title)[:28]
        for k in range(start, n + 1):
            if key in norm(texts[k - 1]) and (not label or norm(label).upper() in norm(texts[k - 1]).upper()):
                pages[cid] = k; break
    return pages, n

pdf1 = str(out / 'pass1.pdf')
render(build({}), pdf1)
pages, n = find_pages(pdf1)
final = str(out / f'Cisza_z_ktorej_pochodze_KDP_{trim}.pdf')
render(build(pages), final)
pages2, n2 = find_pages(final)
print(json.dumps({'pages_total': n2, 'pages': pages2, 'toc_matches_pass2': pages == pages2, 'chapters': len(chapters), 'found': len(pages)}, ensure_ascii=False))
