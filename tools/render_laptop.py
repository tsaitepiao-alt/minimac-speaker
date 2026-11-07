"""MiniBook（筆電變體）組立渲染：上蓋開 110 度，含螢幕示意"""
import os, sys, math
import numpy as np, trimesh
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cad"))
import render as R

EXP = os.path.join(os.path.dirname(__file__), "..", "cad", "export")
BW, BD, BH, LD, LT = 150.0, 110.0, 28.0, 100.0, 9.0
HY, HZ, OPEN = 51.0, 28.0, 110.0
WIN_W, WIN_H, WIN_ZC = 97.0, 56.0, 50.0

def rotx(deg, y0, z0):
    a = math.radians(deg)
    M = np.array([[1, 0, 0, 0],
                  [0, math.cos(a), -math.sin(a), 0],
                  [0, math.sin(a), math.cos(a), 0],
                  [0, 0, 0, 1]])
    T1 = np.eye(4); T1[1, 3], T1[2, 3] = -y0, -z0
    T2 = np.eye(4); T2[1, 3], T2[2, 3] = y0, z0
    return T2 @ M @ T1

def load_part(name, col, transform=None):
    m = trimesh.load(os.path.join(EXP, f"laptop_{name}.stl"))
    m = m.subdivide_to_size(max_edge=5.0)
    if transform is not None:
        m.apply_transform(transform)
    return m, col

def build():
    tris, cols = [], []
    parts = [
        load_part("base_shell", (0.80, 0.78, 0.72)),
        load_part("button", (0.90, 0.42, 0.12)),
    ]
    T_close = np.eye(4); T_close[1, 3] = HY - LD / 2; T_close[2, 3] = BH
    T_open = rotx(-OPEN, HY, HZ) @ T_close
    parts.append(load_part("lid", (0.93, 0.91, 0.85), T_open))
    # 螢幕示意（上蓋窗後方）
    scr = trimesh.creation.box(extents=(WIN_W - 1, WIN_H - 1, 1.5))
    scr.apply_translation((0, 0, 3.0))
    scr = scr.subdivide_to_size(max_edge=8.0)
    scr.apply_transform(T_open)
    parts.append((scr, (0.34, 0.44, 0.56)))
    for m, col in parts:
        v = np.asarray(m.vertices, float); f = np.asarray(m.faces, int)
        tris.append(v[f]); cols.append(np.tile(np.array(col), (len(f), 1)))
    return np.concatenate(tris), np.concatenate(cols)

if __name__ == "__main__":
    T, C = build()
    cr = R.crease_mask(T)
    R.render(T, C, -32, 22, 1200, 1200, crease=cr, zoom=0.80)[0].save(os.path.join(EXP, "laptop_hero.png"))
    R.render(T, C, 0, 6, 900, 900, crease=cr, zoom=0.86)[0].save(os.path.join(EXP, "laptop_front.png"))
    print("ok")
