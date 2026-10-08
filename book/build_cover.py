"""Build a KDP full-wrap paperback cover PDF for 'Cisza, z której pochodzę'.

Usage: python3 build_cover.py <front.jpg> <author_photo> <out.pdf> [pages] [paper]
paper: white (0.002252 in/page) | cream (0.0025 in/page). Trim 5.5 x 8.5 in, 0.125 in bleed.
"""
import sys, pathlib, subprocess
from PIL import Image, ImageFilter

front_src, photo_src, out_pdf = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]).resolve()
pages = int(sys.argv[4]) if len(sys.argv) > 4 else 128
paper = sys.argv[5] if len(sys.argv) > 5 else 'white'
DPI, TW, TH, BL = 300, 5.5, 8.5, 0.125
spine = pages * (0.002252 if paper == 'white' else 0.0025)
W, H = 2 * TW + spine + 2 * BL, TH + 2 * BL
work = out_pdf.parent / 'cover_work'; work.mkdir(parents=True, exist_ok=True)

# front panel incl. right/top/bottom bleed, cropped from the centre of the artwork
fw, fh = round((TW + BL) * DPI), round(H * DPI)
im = Image.open(front_src).convert('RGB')
scale = max(fw / im.width, fh / im.height)
im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
left = (im.width - fw) // 2
im = im.crop((left, (im.height - fh) // 2, left + fw, (im.height - fh) // 2 + fh))
im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
im.save(work / 'front.jpg', quality=95, dpi=(DPI, DPI))
print(f'front artwork effective resolution: {round(DPI / scale)} dpi before upscaling')
Image.open(photo_src).convert('RGB').save(work / 'photo.jpg', quality=95)

FONTS = pathlib.Path(__file__).resolve().parent / 'fonts' / 'ub-local.css'
bio = 'Joanna Dorobisz dorastała w domu, w którym milczenie było jedyną ochroną. Dziś pomaga kobietom odzyskać głos, czucie i prawo do własnego życia.'
blurb = [
 'Dorastałam w domu, w którym słowa były ostrzejsze niż nóż, a milczenie było jedynym schronieniem. Przez lata żyłam w trybie przetrwania: funkcjonowałam, uśmiechałam się, wykonywałam obowiązki, ale nie czułam.',
 'Ta książka to zapis mojej drogi od zamrożenia do życia. Piszę w niej o tym, co dzieje się z dzieckiem, które musi wyłączyć emocje, żeby przetrwać, i o tym, jak dorosła kobieta może je odzyskać. Uczciwie, bez upiększeń i z czułością dla każdej, która rozpozna w tych stronach siebie.',
 'W książce przeprowadzę Cię przez temat DDA i złożonej traumy, przez dziedzictwo przodków i ustawienia systemowe, aż po pracę z wewnętrznym dzieckiem, ciałem i zamrożonymi emocjami. Każdy rozdział kończy się ćwiczeniami i pytaniami, które pomogą Ci przejść tę drogę we własnym tempie.',
 'To nie jest poradnik o tym, jak „naprawić się” w tydzień. To mapa powrotu do siebie, do kobiety, która ma prawo czuć, mówić i żyć po swojemu.',
]
back_w = TW + BL
html = f"""<!doctype html><html lang="pl"><head><meta charset="utf-8"><link rel="stylesheet" href="file://{FONTS}">
<style>
@page {{ size: {W}in {H}in; margin: 0; }}
html, body {{ margin: 0; }}
.cover {{ position: relative; width: {W}in; height: {H}in; background: #0b0b0b; overflow: hidden; font-family: 'Ubuntu', sans-serif; color: #f2efe9; }}
.front {{ position: absolute; top: 0; right: 0; width: {TW + BL}in; height: {H}in; }}
.back {{ position: absolute; top: 0; left: 0; width: {back_w}in; height: {H}in; }}
.bio {{ position: absolute; left: {BL + 0.55}in; right: 0.5in; top: {BL + 0.6}in; display: flex; gap: 0.18in; align-items: flex-start; }}
.bio img {{ width: 1.05in; height: 1.05in; object-fit: cover; flex-shrink: 0; }}
.bio p {{ margin: 0; font-size: 11.5pt; line-height: 1.38; font-weight: 500; }}
.blurb {{ position: absolute; left: {BL + 0.55}in; right: 0.5in; top: {BL + 2.05}in; font-size: 9.6pt; line-height: 1.45; }}
.blurb p {{ margin: 0 0 0.11in; }}
.blurb p:last-child {{ font-style: italic; color: #e9d9a8; }}
.web {{ position: absolute; left: {BL + 0.55}in; top: {H - BL - 0.6}in; font-size: 8.5pt; letter-spacing: .08em; color: #bdb6a8; }}
.spine {{ position: absolute; top: 0; left: {back_w}in; width: {spine}in; height: {H}in; display: flex; align-items: center; justify-content: center; }}
.spine div {{ writing-mode: vertical-rl; white-space: nowrap; font-size: {min(10.5, spine * 72 * 0.55):.1f}pt; letter-spacing: .04em; }}
.spine b {{ font-weight: 500; margin-top: 0.4in; display: inline-block; }}
</style></head><body><div class="cover">
<div class="back">
  <div class="bio"><img src="file://{work / 'photo.jpg'}"><p>{bio}</p></div>
  <div class="blurb">{''.join(f'<p>{p}</p>' for p in blurb)}</div>
  <div class="web">letyoursoulglow.store</div>
</div>
<div class="spine"><div>Cisza, z której pochodzę <b>Joanna Dorobisz</b></div></div>
<img class="front" src="file://{work / 'front.jpg'}">
</div></body></html>"""
(work / 'cover.html').write_text(html)
js = f"""const {{ chromium }} = require('playwright');
(async()=>{{const b=await chromium.launch({{executablePath:'/opt/pw-browsers/chromium'}});const p=await b.newPage();
await p.goto('file://{work / 'cover.html'}');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(1200);
await p.pdf({{path:'{out_pdf}',preferCSSPageSize:true,printBackground:true}});await b.close();}})();"""
(work / 'render.js').write_text(js)
npm_root = subprocess.check_output(['npm', 'root', '-g'], text=True).strip()
subprocess.run(['node', str(work / 'render.js')], check=True, env={'NODE_PATH': npm_root, 'PATH': '/usr/bin:/usr/local/bin:/bin'})
print(f'cover {W:.4f} x {H:.4f} in, spine {spine:.4f} in ({spine*25.4:.1f} mm), {pages} pages, {paper} paper')
