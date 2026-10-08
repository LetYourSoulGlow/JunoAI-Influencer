"""Remove the baked-in Polish title/subtitle from the front artwork (sky region) so English text can be set on it."""
import sys, numpy as np
from PIL import Image, ImageFilter
src, dst = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert('RGB')).astype(np.float64)
H, W, _ = im.shape
Y0, Y1 = 280, 1400          # band containing title + subtitle (author line above stays)
band = im[Y0:Y1]
lum = band.mean(axis=2)
smooth = np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.MedianFilter(41))).astype(float)
# box around the title block (glyphs carry a dark halo, so a pixel mask leaves ghosts)
BX0, BX1, BY0, BY1 = 40, 1620, 400 - Y0, 1270 - Y0
mask = np.zeros(lum.shape, bool); mask[BY0:BY1, BX0:BX1] = True
m = Image.fromarray((mask * 255).astype(np.uint8))
# low-order 2D polynomial fit of the sky on non-text pixels
yy, xx = np.mgrid[0:band.shape[0], 0:W]
u, v = xx / W, yy / band.shape[0]
terms = [u**i * v**j for i in range(5) for j in range(5 - i)]
A = np.stack([t[~mask] for t in terms], 1)
Afull = np.stack([t.ravel() for t in terms], 1)
fit = np.zeros_like(band)
rng = np.random.default_rng(1)
for c in range(3):
    coef, *_ = np.linalg.lstsq(A, band[..., c][~mask], rcond=None)
    fit[..., c] = (Afull @ coef).reshape(lum.shape)
resid = (band - fit)[~mask].std()
noise = rng.normal(0, resid * 0.6, lum.shape)
noise = np.asarray(Image.fromarray(((noise + 64)).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(float) - 64
# carry the sky's vertical streak texture across the box from the rows just outside it
hp = lambda r: r - np.asarray(Image.fromarray(r.clip(0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(25))).astype(float)
above = band[BY0 - 60:BY0].mean(0); below = band[BY1:BY1 + 60].mean(0)
streak_a = np.stack([hp(above[:, c][None].repeat(3, 0))[1] for c in range(3)], 1)
streak_b = np.stack([hp(below[:, c][None].repeat(3, 0))[1] for c in range(3)], 1)
t = np.clip((yy - BY0) / (BY1 - BY0), 0, 1)[..., None]
fill = fit + noise[..., None] + (streak_a[None] * (1 - t) + streak_b[None] * t)
alpha = np.asarray(m.filter(ImageFilter.GaussianBlur(22))).astype(float)[..., None] / 255
out = im.copy()
out[Y0:Y1] = band * (1 - alpha) + fill * alpha
Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(dst, quality=96)
print('masked px', mask.sum(), 'resid std', round(resid, 2))
