"""用手當比例尺：以手指寬/掌寬為基準，推算機身實際尺寸。
假設（台灣成年男性）：食指近端寬 19mm、掌寬 85mm。
輸出：機身寬度估計（含誤差說明）
"""
import sys
import numpy as np
from PIL import Image

FINGER_MM = 19.0
PALM_MM = 85.0

def load(p):
    return np.array(Image.open(p).convert("RGB")).astype(int)

def masks(a):
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mx, mn = a.max(2), a.min(2)
    skin = (R > 95) & (G > 40) & (B > 20) & (R > G) & (G > B) & (R - G > 15) & (mx - mn > 15)
    cream = (R > 150) & (G > 145) & (B > 125) & (mx - mn < 32)
    return skin, cream

def bbox(m, minpx=500, trim=2.0):
    ys, xs = np.where(m)
    if len(xs) < minpx:
        return None
    cx, cy = np.median(xs), np.median(ys)
    sx, sy = xs.std() + 1e-6, ys.std() + 1e-6
    keep = (np.abs(xs - cx) < trim * sx) & (np.abs(ys - cy) < trim * sy)
    xs, ys = xs[keep], ys[keep]
    return dict(x0=int(xs.min()), x1=int(xs.max()), y0=int(ys.min()), y1=int(ys.max()),
                w=int(xs.max() - xs.min()), h=int(ys.max() - ys.min()), n=len(xs))

def finger_runs(skin, y0, y1, x0, x1):
    """在一帶狀區域內量 skin 的橫向 run 長度，取中位數 → 手指寬（px）"""
    runs = []
    for y in range(y0, y1, max(1, (y1 - y0) // 60)):
        row = skin[y, x0:x1]
        c = 0
        for v in row:
            if v:
                c += 1
            elif c:
                runs.append(c); c = 0
        if c:
            runs.append(c)
    runs = [r for r in runs if r > 6]
    if not runs:
        return None
    runs.sort()
    return int(np.median(runs)), int(np.percentile(runs, 25))

for p in sys.argv[1:]:
    a = load(p)
    h, w, _ = a.shape
    skin, cream = masks(a)
    print("=" * 60)
    print("圖", p.split("/")[-1], f"{w}x{h}", f"skin {skin.mean():.1%} cream {cream.mean():.1%}")
    # 機身：cream，取靠中間的大塊
    yy, xx = np.mgrid[0:h, 0:w]
    central = (np.abs(xx - w / 2) < w * 0.42) & (np.abs(yy - h / 2) < h * 0.42)
    dev = bbox(cream & central, 2000)
    print("  cream 區塊:", dev)
    fr = finger_runs(skin, int(h * 0.25), int(h * 0.85), 0, w)
    print("  skin 橫向 run 中位數:", fr)
    if dev and fr:
        fpx = fr[0]
        print(f"  機身寬 {dev['w']}px ÷ 手指 {fpx}px = {dev['w']/fpx:.2f} 指寬 → ×{FINGER_MM}mm = {dev['w']/fpx*FINGER_MM:.1f}mm")
        print(f"  機身高 {dev['h']}px → {dev['h']/fpx*FINGER_MM:.1f}mm")
