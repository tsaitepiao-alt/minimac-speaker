"""快速出圖：STL → 4 視角灰階渲染 PNG（正交投影＋Lambert 上色，用 PIL 直接畫）"""
import sys, os, math
import numpy as np
import trimesh
from PIL import Image, ImageDraw

EXP = os.path.join(os.path.dirname(__file__), "export")
PARTS = [("body", (0.62, 0.61, 0.58)), ("faceplate", (0.93, 0.92, 0.87)),
         ("knob", (0.88, 0.42, 0.13)), ("pr_clamp", (0.22, 0.22, 0.25))]

VIEWS = [("前視", 0, 8, 0), ("左前 3/4", -38, 18, 0), ("右前 3/4", 38, 18, 0), ("後視", 180, 12, 0)]

def load():
    tris, cols = [], []
    for name, col in PARTS:
        m = trimesh.load(os.path.join(EXP, f"{name}.stl"))
        m = m.subdivide_to_size(max_edge=3.0) if name != "knob" else m
        v = np.asarray(m.vertices, float)
        f = np.asarray(m.faces, int)
        tris.append(v[f])
        cols.append(np.tile(np.array(col), (len(f), 1)))
    return np.concatenate(tris), np.concatenate(cols)

def rot(yaw, pitch):
    a, b = math.radians(yaw), math.radians(pitch)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    return Rx @ Rz

def render(T, C, yaw, pitch, W=760, H=760, bg=(0.09, 0.10, 0.13)):
    R = rot(yaw, pitch)
    V = (T.reshape(-1, 3) @ R.T).reshape(T.shape)
    # 相機看 -Y：投影到 XZ
    P = V[:, :, [0, 2]]
    depth = V[:, :, 1].mean(axis=1)   # 視點在 -Y，Y 越大越遠
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    ln = np.linalg.norm(n, axis=1) + 1e-12
    n = n / ln[:, None]
    Vn = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0])
    Vn /= (np.linalg.norm(Vn, axis=1)[:, None] + 1e-12)
    light = np.array([0.35, -0.85, 0.45]); light /= np.linalg.norm(light)
    sh = np.clip(Vn @ light, 0, 1) * 0.72 + 0.28
    # 背向鏡頭的面（腔體內壁）壓暗，讓開孔看得出來
    sh = np.where(Vn[:, 1] < 0, sh, sh * 0.28)
    cull = (n[:, 1] < 0) | True
    order = np.argsort(-depth)        # 先畫最遠的（Y 大）
    mn, mx = P.reshape(-1, 2).min(0), P.reshape(-1, 2).max(0)
    scale = min(W, H) * 0.86 / max(mx - mn)
    off = (np.array([W, H]) - (mx - mn) * scale) / 2 - mn * scale
    Q = P * scale + off
    Q[:, :, 1] = H - Q[:, :, 1]
    img = Image.new("RGB", (W, H), tuple(int(c * 255) for c in bg))
    d = ImageDraw.Draw(img)
    for i in order:
        col = np.clip(C[i] * sh[i], 0, 1)
        d.polygon([tuple(Q[i, k]) for k in range(3)], fill=tuple(int(c * 255) for c in col))
    return img

if __name__ == "__main__":
    T, C = load()
    imgs = [render(T, C, v[1], v[2]) for v in VIEWS]
    sheet = Image.new("RGB", (760 * 2, 760 * 2), (9, 10, 13))
    for i, im in enumerate(imgs):
        sheet.paste(im, ((i % 2) * 760, (i // 2) * 760))
    out = os.path.join(EXP, "preview.png")
    sheet.save(out)
    print(out, sheet.size)
