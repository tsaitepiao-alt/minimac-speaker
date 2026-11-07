"""從實拍參考圖量測正面比例（螢幕/機身/橘鈕），輸出比例報告。
用途：逆向工程時的「比例依據」，不是絕對尺寸。
"""
import sys
import numpy as np
from PIL import Image

p = sys.argv[1]
im = Image.open(p).convert("RGB")
a = np.array(im)
print("image", im.size)
R, G, B = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
mx, mn = a.max(2).astype(int), a.min(2).astype(int)
sat = mx - mn
beige = (R > 140) & (G > 130) & (B > 105) & (sat < 45)
dark = mx < 95
orange = (R > 150) & (G > 60) & (G < 160) & (B < 110) & (R - B > 70)

def bbox(m, minpx=200):
    ys, xs = np.where(m)
    if len(xs) < minpx:
        return None
    cx, cy = np.median(xs), np.median(ys)
    sx, sy = xs.std() + 1e-6, ys.std() + 1e-6
    keep = (np.abs(xs - cx) < 2.2 * sx) & (np.abs(ys - cy) < 2.2 * sy)
    xs, ys = xs[keep], ys[keep]
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()), len(xs)

bb = bbox(beige)
sb = bbox(dark, 300)
ob = bbox(orange, 80)
print("beige(機身)", bb)
print("dark(螢幕)", sb)
print("orange(橘鈕)", ob)
if bb and sb:
    bw, bh = bb[1] - bb[0], bb[3] - bb[2]
    sw, sh = sb[1] - sb[0], sb[3] - sb[2]
    print(f"\n機身 bbox {bw}x{bh}px")
    print(f"螢幕 {sw}x{sh}px → 寬佔 {sw/bw:.1%}、高佔 {sh/bh:.1%}、長寬比 {sw/sh:.2f}")
    print(f"螢幕上緣距頂 {(sb[2]-bb[2])/bh:.1%}、左右置中偏移 {((sb[0]+sb[1])/2-(bb[0]+bb[1])/2)/bw:+.1%}")
if bb and ob:
    ow = max(ob[1] - ob[0], ob[3] - ob[2])
    bw = bb[1] - bb[0]
    print(f"橘鈕直徑 {ow}px → 佔機身寬 {ow/bw:.1%}")
    print(f"橘鈕中心 距右邊 {(bb[1]-ob[1])/bw:.1%}、距下邊 {(bb[3]-ob[3])/max(bb[3]-bb[2],1):.1%}")
