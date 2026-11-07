"""
STL → 擬真渲染（正交投影＋Lambert＋特徵邊線），用 PIL 直接畫。
特徵邊線（折角 >25°）讓倒角、凹槽、分模線、開孔都看得出來。
產出：preview.png（四視圖）、hero.png（3/4 斜視）
"""
import os, math
import numpy as np
import trimesh
from PIL import Image, ImageDraw

EXP = os.path.join(os.path.dirname(__file__), "export")
PARTS = [
    ("body",      (0.78, 0.76, 0.70)),
    ("faceplate", (0.93, 0.91, 0.85)),
    ("knob",      (0.90, 0.42, 0.12)),
    ("pr_clamp",  (0.20, 0.21, 0.24)),
]
CREASE_DEG = 25.0
BG = (13, 17, 23)

def comp_geo():
    """非列印件（螢幕、被動輻射器振膜、單體錐盆）— 讓渲染看起來像成品而不是空殼"""
    out = []
    # 螢幕面板（貼在窗戶後面）
    box = trimesh.creation.box(extents=(62.0, 0.8, 47.0))
    box.apply_translation((0, -51.2, 43.5 + 47 / 2))
    out.append((box, (0.20, 0.26, 0.34)))
    # 被動輻射器振膜（背板窗內）
    pr = trimesh.creation.box(extents=(50.0, 2.0, 70.0))
    pr.apply_translation((-4.0, 54.0, 69.0))
    out.append((pr, (0.16, 0.17, 0.20)))
    # 兩顆單體錐盆（底面往下）
    for sx in (-1, 1):
        c = trimesh.creation.cylinder(radius=19.0, height=3.0, sections=48)
        c.apply_translation((sx * 22.0, 0, 0.5))
        out.append((c, (0.12, 0.12, 0.13)))
    return out

def load():
    tris, cols = [], []
    for name, col in PARTS:
        path = os.path.join(EXP, f"{name}.stl")
        if not os.path.exists(path):
            continue
        m = trimesh.load(path)
        if name != 'knob':
            m = m.subdivide_to_size(max_edge=6.0)   # 細分大三角形，避免畫家演算法排序錯誤
        v = np.asarray(m.vertices, float)
        f = np.asarray(m.faces, int)
        tris.append(v[f])
        cols.append(np.tile(np.array(col), (len(f), 1)))
    for m, col in comp_geo():
        v = np.asarray(m.vertices, float)
        f = np.asarray(m.faces, int)
        tris.append(v[f])
        cols.append(np.tile(np.array(col), (len(f), 1)))
    return np.concatenate(tris), np.concatenate(cols)

def crease_mask(T):
    """每條邊是否為特徵邊（折角 > CREASE_DEG）→ (F,3) bool"""
    flat = T.reshape(-1, 3)
    key = np.round(flat, 3)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1, 3)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
    emap = {}
    for t in range(len(T)):
        for k in range(3):
            a, b = inv[t, k], inv[t, (k + 1) % 3]
            emap.setdefault((min(a, b), max(a, b)), []).append(t)
    out = np.zeros((len(T), 3), bool)
    for t in range(len(T)):
        for k in range(3):
            a, b = inv[t, k], inv[t, (k + 1) % 3]
            fs = emap[(min(a, b), max(a, b))]
            if len(fs) != 2:
                out[t, k] = True
                continue
            d = np.dot(n[fs[0]], n[fs[1]])
            if math.degrees(math.acos(max(-1.0, min(1.0, d)))) > CREASE_DEG:
                out[t, k] = True
    return out

def rotm(yaw, pitch):
    a, b = math.radians(yaw), math.radians(pitch)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    return Rx @ Rz

def project(T, yaw, pitch, W, H, zoom=0.86):
    R = rotm(yaw, pitch)
    V = (T.reshape(-1, 3) @ R.T).reshape(T.shape)
    P = V[:, :, [0, 2]]
    mn, mx = P.reshape(-1, 2).min(0), P.reshape(-1, 2).max(0)
    scale = min(W, H) * zoom / max(mx - mn)
    off = (np.array([W, H]) - (mx - mn) * scale) / 2 - mn * scale
    Q = P * scale + off
    Q[:, :, 1] = H - Q[:, :, 1]
    return V, Q, scale, off

def render(T, C, yaw, pitch, W=900, H=900, bg=BG, crease=None, zoom=0.86):
    V, Q, scale, off = project(T, yaw, pitch, W, H, zoom)
    depth = V[:, :, 1].mean(axis=1)
    order = np.argsort(-depth)
    Vn = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0])
    Vn /= (np.linalg.norm(Vn, axis=1)[:, None] + 1e-12)
    light = np.array([0.35, -0.82, 0.45]); light /= np.linalg.norm(light)
    sh = np.clip(Vn @ light, 0, 1) * 0.78 + 0.22
    facing = Vn[:, 1] < 0
    sh = np.where(facing, sh, sh * 0.30)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    for i in order:
        col = tuple(int(min(255, c * 255)) for c in np.clip(C[i] * sh[i], 0, 1))
        tri = [tuple(Q[i, k]) for k in range(3)]
        d.polygon(tri, fill=col)
        if crease is not None and facing[i]:
            ec = tuple(int(min(255, c * 255)) for c in np.clip(C[i] * 0.40, 0, 1))
            for k in range(3):
                if crease[i, k]:
                    d.line([tri[k], tri[(k + 1) % 3]], fill=ec, width=1)
    return img, (V, Q, scale, off)

def screen_overlay():
    im = Image.new("RGB", (320, 240), (8, 14, 26))
    d = ImageDraw.Draw(im)
    for i in range(14):
        d.rectangle([0, 200 - i * 14, 320, 201 - i * 14], fill=(16, 26, 42))
    d.text((14, 12), "miniMac", fill=(126, 231, 135))
    d.text((14, 30), "BLUETOOTH  A2DP", fill=(140, 163, 184))
    d.text((14, 178), "NOW PLAYING", fill=(255, 183, 77))
    d.text((14, 198), "close my eyes...", fill=(232, 238, 246))
    for i in range(16):
        h = 10 + abs(math.sin(i * 0.7)) * 44
        col = (74, 222, 128) if i % 3 else (255, 183, 77)
        d.rectangle([12 + i * 18, 168 - h, 12 + i * 18 + 12, 168], fill=col)
    return im

def paste_screen(img, T, W=900, H=900, w0=62.0, h0=47.0, z0=43.5):
    """正視圖：把螢幕內容貼進窗口（正交投影＝軸對齊矩形）"""
    _, _, scale, off = project(T, 0, 0, W, H)
    px0 = -w0 / 2 * scale + off[0]; px1 = w0 / 2 * scale + off[0]
    py1 = H - (z0 * scale + off[1]); py0 = H - ((z0 + h0) * scale + off[1])
    rect = (int(px0), int(py0), int(px1), int(py1))
    scr = screen_overlay().resize((rect[2] - rect[0], rect[3] - rect[1]), Image.LANCZOS)
    img.paste(scr, rect[:2])
    return img

if __name__ == "__main__":
    T, C = load()
    cr = crease_mask(T)
    views = [("front", 0, 0), ("left", -38, 14), ("right", 38, 14), ("back", 180, 10)]
    imgs = []
    for name, yaw, pitch in views:
        im, _ = render(T, C, yaw, pitch, 900, 900, crease=cr)
        if name == "front":
            im = paste_screen(im, T)
        imgs.append(im)
    sheet = Image.new("RGB", (1800, 1800), BG)
    for i, im in enumerate(imgs):
        sheet.paste(im, ((i % 2) * 900, (i // 2) * 900))
    sheet.save(os.path.join(EXP, "preview.png"))
    hero, _ = render(T, C, -35, 18, 1200, 1200, crease=cr, zoom=0.82)
    hero.save(os.path.join(EXP, "hero.png"))
    print("ok")
