"""Build a KDP full-wrap paperback cover PDF for 'The Silence I Come From' (English edition).

Usage: python3 build_cover_en.py <front_clean.jpg> <author_photo> <out.pdf> [pages] [paper]
paper: white (0.002252 in/page) | cream (0.0025 in/page). Trim 5.5 x 8.5 in, 0.125 in bleed.
"""
import sys, pathlib, subprocess
from PIL import Image, ImageFilter

front_src, photo_src, out_pdf = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]).resolve()
pages = int(sys.argv[4]) if len(sys.argv) > 4 else 132
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

FDIR = pathlib.Path(__file__).resolve().parent.parent / 'fonts'
FONTS = FDIR / 'ub-local.css'
bio = 'Joanna Dorobisz grew up in a home where silence was the only protection.<br>Today she helps women reclaim their voice, their feelings and the right to their own lives.'
blurb = [
 'I grew up in a home where words were sharper than a knife and silence was the only shelter. For years I lived in survival mode: I functioned, I smiled, I did what was expected of me — but I didn’t feel.',
 'This book is the story of my journey from frozen to alive. I write about what happens to a child who has to switch off her emotions in order to survive, and about how a grown woman can get them back. Honestly, without embellishment, and with tenderness for every woman who recognises herself in these pages.',
 'I will guide you through ACoA and complex trauma, through the legacy of your ancestors and Family Constellations, to working with your inner child, your body and your frozen emotions. Every chapter ends with exercises and questions to help you walk this path at your own pace.',
 'This is not a guide to “fixing yourself” in a week. It is a way back to who you truly are — to the woman who has the right to feel, to speak and to live life on her own terms.',
]
back_w = TW + BL
html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><link rel="stylesheet" href="file://{FONTS}"><style>@font-face{{font-family:'Dosis';font-weight:500;src:url(file://{FDIR}/cov/Dosis.woff)}} @font-face{{font-family:'Bitter';src:url(file://{FDIR}/cov/Bitter.woff)}}</style>
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
.title {{ position: absolute; top: 1.5in; left: {BL + spine + TW}in; width: {TW}in; text-align: center; font-family: 'Dosis'; font-weight: 500; color: #f6e7ae; font-size: 66pt; line-height: 1.0; letter-spacing: -.01em; text-shadow: 0 1px 6px rgba(0,0,0,.18); }}
.subtitle {{ position: absolute; top: 3.72in; left: {BL + spine + TW}in; width: {TW}in; text-align: center; font-family: 'Bitter'; font-size: 15.5pt; color: #fbf7ee; }}
.spine {{ position: absolute; top: 0; left: {back_w}in; width: {spine}in; height: {H}in; display: flex; align-items: center; justify-content: center; }}
.spine div {{ writing-mode: vertical-rl; white-space: nowrap; font-size: {min(10.5, spine * 72 * 0.55):.1f}pt; letter-spacing: .04em; }}
.spine b {{ font-weight: 500; margin-top: 0.4in; display: inline-block; }}
</style></head><body><div class="cover">
<div class="back">
  <div class="bio"><img src="file://{work / 'photo.jpg'}"><p>{bio}</p></div>
  <div class="blurb">{''.join(f'<p>{p}</p>' for p in blurb)}</div>
  <div class="web">letyoursoulglow.store</div>
</div>
<div class="spine"><div>The Silence I Come From <b>Joanna Dorobisz</b></div></div>
<img class="front" src="file://{work / 'front.jpg'}">
<div class="title">The Silence<br>I Come From</div>
<div class="subtitle">Coming Back to Who You Truly Are</div>
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
