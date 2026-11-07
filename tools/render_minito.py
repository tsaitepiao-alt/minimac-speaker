"""Minito-style v3 渲染（含螢幕示意與橘色圓鍵）"""
import math, os, sys
import numpy as np, trimesh
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cad"))
import render as R

EXP = os.path.join(os.path.dirname(__file__), "..", "cad", "export")
W, D, H, TILT = 82.0, 61.0, 103.0, 14.47
SCR_W, SCR_H, SCR_C = 49.0, 37.0, 60.0
L = math.hypot(H, TILT)

def load(name, col, sub=4.0):
    m = trimesh.load(os.path.join(EXP, f"minito_{name}.stl"))
    return m.subdivide_to_size(max_edge=sub), col

def screen_quad():
    f = SCR_C / L
    y = -D / 2 + TILT * f
    z = H * f
    q = trimesh.creation.box(extents=(SCR_W - 1.0, 0.8, SCR_H - 1.0))
    q.apply_transform(trimesh.transformations.rotation_matrix(math.radians(-8.0), [1, 0, 0]))
    q.apply_translation((0, y - 1.2, z))
    return q.subdivide_to_size(max_edge=6.0), (0.10, 0.16, 0.26)

if __name__ == "__main__":
    parts = [load("front_shell", (0.93, 0.90, 0.82)), load("back_cover", (0.88, 0.85, 0.77)),
             load("orange_key", (0.92, 0.45, 0.13)), load("keycaps", (0.55, 0.56, 0.58)),
             screen_quad()]
    tris, cols = [], []
    for m, c in parts:
        v = np.asarray(m.vertices, float); f = np.asarray(m.faces, int)
        tris.append(v[f]); cols.append(np.tile(np.array(c), (len(f), 1)))
    T, C = np.concatenate(tris), np.concatenate(cols)
    cr = R.crease_mask(T)
    R.render(T, C, -30, 16, 1000, 1000, crease=cr, zoom=0.80)[0].save(os.path.join(EXP, "minito_hero.png"))
    R.render(T, C, 0, 3, 900, 900, crease=cr, zoom=0.86)[0].save(os.path.join(EXP, "minito_front.png"))
    # 與參考圖並排
    ref = Image.open(sys.argv[1]).convert("RGB")
    ref.thumbnail((700, 700))
    hero = Image.open(os.path.join(EXP, "minito_hero.png"))
    sheet = Image.new("RGB", (ref.width + hero.width + 30, max(ref.height, hero.height) + 20), (255, 255, 255))
    sheet.paste(ref, (10, 10)); sheet.paste(hero, (ref.width + 20, 10))
    sheet.save(os.path.join(EXP, "minito_compare.png"))
    print("ok", sheet.size)
