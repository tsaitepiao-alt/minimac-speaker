"""
MiniMac Speaker — 迷你麥金塔造型藍牙音響 · 參數化機構
build123d 0.13 algebra mode.  單位：mm
執行：.venv/bin/python cad/build_minimac.py
輸出：cad/export/*.step, *.stl, cad/export/dims.json
"""
from math import cos, sin, pi
import json, os
from build123d import (
    Align, Axis, Box, Cylinder, Plane, Pos, Rot, Polyline, make_face, Rectangle,
    extrude, fillet, RectangleRounded, export_step, export_stl, Compound,
)

# ---------------- 主參數 ----------------
W, D, H = 96.0, 118.0, 132.0      # 外觀 寬 / 深 / 高
WALL = 2.4                         # 壁厚
FOOT_H = 8.0                       # 腳高（下射式單體離桌間隙）
FRONT_T = 3.0                      # 面版厚

# 螢幕窗口（面版上）
WIN_W, WIN_H = 60.0, 45.0
WIN_Z0 = 73.0                      # 窗口下緣高度
# 2.8" ST7789 模組（橫放）
SCR_W, SCR_H, SCR_T = 82.5, 50.0, 5.0

# 單體（下射）
DRV_D, DRV_H = 40.0, 22.0
DRV_HOLE = 38.0
DRV_X = 22.0                       # 左右單體中心 x

# 被動輻射器（背板）
PR_W, PR_H = 50.0, 70.0
PR_CX = -4.0                       # 被動輻射器中心 x（避開右側電池座）

C = Align.CENTER
MIN = Align.MIN
Y_FRONT = -D / 2                   # 前緣
Y_BACK = D / 2                     # 後緣

# ---------------- 本體（後殼＋左右＋底＋背） ----------------
body = Box(W, D, H, align=(C, C, MIN))
body = fillet(body.edges().filter_by(Axis.Z), 5.0)
body = fillet(body.edges().group_by(Axis.Z)[-1], 2.0)
body = fillet(body.edges().group_by(Axis.Z)[0], 1.0)

# 腳
for sx in (-1, 1):
    for sy in (-1, 1):
        body += Pos(sx * (W / 2 - 11), sy * (D / 2 - 11), -FOOT_H) * Cylinder(
            6.0, FOOT_H, align=(C, C, MIN)
        )
        body = fillet(
            body.edges().filter_by(lambda e: abs(e.center().Z + FOOT_H) < 1e-6).group_by(Axis.Z)[-1]
            if False else body.edges(),
            0.0,
        ) if False else body

# 前開腔體
cav_y0, cav_y1 = Y_FRONT - 1.0, Y_BACK - WALL
cav = Pos(0, (cav_y0 + cav_y1) / 2, WALL) * Box(
    W - 2 * WALL, cav_y1 - cav_y0, H - WALL, align=(C, C, MIN)
)
body -= cav

# 下射單體孔
for sx in (-1, 1):
    body -= Pos(sx * DRV_X, 0, -1) * Cylinder(DRV_HOLE / 2, WALL + 2, align=(C, C, MIN))

# 背板：被動輻射器窗
pr_cut = Pos(PR_CX, Y_BACK, (WIN_Z0 + WIN_H + 20) / 2) * Rot(90, 0, 0) * Box(
    PR_W, PR_H, WALL + 2, align=(C, C, C)
)
body -= pr_cut
# 背板：USB-C（IP5306 模組）
body -= Pos(28, Y_BACK - WALL / 2, 16) * Box(9.4, WALL + 2, 3.6, align=(C, C, C))
# 背板：電源開關
body -= Pos(-28, Y_BACK - WALL / 2, 16) * Box(13.5, WALL + 2, 7.0, align=(C, C, C))
# 背板：散熱縫
for i, dz in enumerate((112.0, 116.0, 120.0)):
    body -= Pos(0, Y_BACK - WALL / 2, dz) * Box(46, WALL + 2, 2.0, align=(C, C, C))

# 面版面鎖附凸柱（M2 自攻）＋ 螢幕承靠柱
boss_pts = [(-41.6, 8.0), (41.6, 8.0), (-41.6, 124.0), (41.6, 124.0)]
for bx, bz in boss_pts:
    body += Pos(bx, Y_FRONT + WALL, bz) * Rot(-90, 0, 0) * Cylinder(
        4.0, 10.0, align=(C, C, MIN)
    )
    body -= Pos(bx, Y_FRONT + WALL, bz) * Rot(-90, 0, 0) * Cylinder(
        0.85, 14.0, align=(C, C, MIN)
    )
# 螢幕下托（左右各一，高 6，深 6）
for sx in (-1, 1):
    body += Pos(sx * 30, Y_FRONT + WALL + 3.0, WIN_Z0 - 3.0) * Box(
        8.0, 6.0, 3.0, align=(C, C, MIN)
    )

# ---------------- 面版 ----------------
fp = Pos(0, Y_FRONT - FRONT_T, 0) * Box(W, FRONT_T, H, align=(C, MIN, MIN))
fp = fillet(fp.edges().filter_by(Axis.Y), 5.0)

def y_cut(shape):
    return fp - shape

# 面版開孔：一律做成 3.5mm 前後對稱的切刀，確保貫穿 3mm 面版
FPC = Y_FRONT - FRONT_T + FRONT_T / 2      # 面版厚度中心線 y

def cut_rect(w, h, zc, xc=0.0, r=0.0):
    sk = Plane.XZ * Pos(xc, zc) * (RectangleRounded(w, h, r) if r > 0 else Rectangle(w, h))
    return Pos(0, FPC, 0) * extrude(sk, amount=4.0, both=True)   # ±4mm 一定貫穿

def cut_hole(d, zc, xc=0.0):
    return Pos(xc, FPC, zc) * Rot(90, 0, 0) * Cylinder(d / 2, 10.0)   # 10mm 長，前後貫穿

# 螢幕窗
fp -= cut_rect(WIN_W, WIN_H, WIN_Z0 + WIN_H / 2, r=2.5)
# 旋鈕孔（Ø7.2 穿 EC11 軸）
fp -= cut_hole(7.6, 32.0, 30.0)
# 軟碟槽（裝飾＋散熱）
fp -= cut_rect(44.0, 5.0, 62.0, -8.0, r=1.8)
# 電源指示燈
fp -= cut_hole(3.0, 40.0, -30.0)
# 鎖附孔
for bx, bz in boss_pts:
    fp -= cut_hole(2.4, bz, bx)

# ---------------- 旋鈕（EC11） ----------------
pts = []
N = 24
for i in range(N * 2):
    r = 9.0 if i % 2 == 0 else 8.3
    t = 2 * pi * i / (N * 2)
    pts.append((r * cos(t), r * sin(t)))
knob = extrude(make_face(Polyline(*pts, close=True)), 9.0)
KNOB_POS = (30.0, Y_FRONT - FRONT_T, 32.0)
knob = Pos(*KNOB_POS) * Rot(90, 0, 0) * knob
knob -= Cylinder(3.1, 12.0, align=(C, C, MIN))
knob -= Pos(0, -9.0, 3.0) * Box(6.0, 4.0, 10.0, align=(C, C, MIN))  # D 軸平面

# ---------------- 被動輻射器壓框 ----------------
clamp = Pos(PR_CX, 0, 0) * Box(PR_W + 14, PR_H + 14, 4.0, align=(C, C, MIN))
clamp -= Pos(PR_CX, 0, -1) * Box(PR_W + 2, PR_H + 2, 6.0, align=(C, C, MIN))
for sx in (-1, 1):
    for sy in (-1, 1):
        clamp -= Pos(PR_CX + sx * (PR_W / 2 + 4), sy * (PR_H / 2 + 4), -1) * Cylinder(
            1.1, 8.0, align=(C, C, MIN)
        )

# ---------------- 尺寸核對（AABB） ----------------
def aabb(name, x0, x1, y0, y1, z0, z1, note=""):
    return dict(name=name, bbox=[round(v, 1) for v in (x0, x1, y0, y1, z0, z1)], note=note)

inner = dict(x=(-W / 2 + WALL, W / 2 - WALL), y=(Y_FRONT, Y_BACK - WALL), z=(WALL, H - WALL))
parts = [
    aabb("2.8吋螢幕模組", -SCR_W / 2, SCR_W / 2, Y_FRONT + WALL, Y_FRONT + WALL + SCR_T,
         WIN_Z0 - 2.5, WIN_Z0 - 2.5 + SCR_H, "貼面版內側，置中對窗"),
    aabb("單體L", -DRV_X - DRV_D / 2, -DRV_X + DRV_D / 2, -DRV_D / 2, DRV_D / 2, WALL, WALL + DRV_H, "下射，籃框貼底板內側"),
    aabb("單體R", DRV_X - DRV_D / 2, DRV_X + DRV_D / 2, -DRV_D / 2, DRV_D / 2, WALL, WALL + DRV_H, "下射，籃框貼底板內側"),
    aabb("ESP32 DevKit", -25, 26, Y_FRONT + WALL + SCR_T + 2, Y_FRONT + WALL + SCR_T + 14,
         WIN_Z0 - 12, WIN_Z0 - 12 + 28, "立放於螢幕下"),
    aabb("IP5306 模組", 10, 35, -5, 20, WALL + DRV_H + 2, WALL + DRV_H + 10, "平放，閃單體"),
    aabb("MAX98357A x2", -45, -22, 14, 30, WALL + DRV_H + 2, WALL + DRV_H + 7, "平放"),
    aabb("18650 電池座", 24.0, 45.5, 30, 50.5, WALL + DRV_H + 2, WALL + DRV_H + 2 + 77, "立放背右"),
    aabb("被動輻射器", PR_CX - PR_W / 2, PR_CX + PR_W / 2, Y_BACK - WALL - 14, Y_BACK - WALL,
         (WIN_Z0 + WIN_H + 20) / 2 - PR_H / 2, (WIN_Z0 + WIN_H + 20) / 2 + PR_H / 2, "背板內側"),
]

def overlap(a, b):
    ax0, ax1, ay0, ay1, az0, az1 = a["bbox"]
    bx0, bx1, by0, by1, bz0, bz1 = b["bbox"]
    return all([
        min(ax1, bx1) - max(ax0, bx0) > 0.5,
        min(ay1, by1) - max(ay0, by0) > 0.5,
        min(az1, bz1) - max(az0, bz0) > 0.5,
    ])

fails = []
for p in parts:
    x0, x1, y0, y1, z0, z1 = p["bbox"]
    out = []
    if x0 < inner["x"][0] - 0.1 or x1 > inner["x"][1] + 0.1: out.append("X超出")
    if y0 < inner["y"][0] - 0.1 or y1 > inner["y"][1] + 0.1: out.append("Y超出")
    if z0 < inner["z"][0] - 0.1 or z1 > inner["z"][1] + 0.1: out.append("Z超出")
    p["in_bounds"] = not out
    p["issues"] = out
    if out:
        fails.append(p["name"] + ":" + ",".join(out))

pairs = []
for i in range(len(parts)):
    for j in range(i + 1, len(parts)):
        if overlap(parts[i], parts[j]):
            fails.append(f"{parts[i]['name']} × {parts[j]['name']} 干涉")
            pairs.append([parts[i]["name"], parts[j]["name"]])

dims = dict(
    outer=dict(W=W, D=D, H=H),
    wall=WALL, foot_h=FOOT_H, front_t=FRONT_T,
    inner=dict(
        W=round(W - 2 * WALL, 1), D=round(D - 2 * WALL, 1), H=round(H - WALL, 1)
    ),
    screen=dict(window=[WIN_W, WIN_H], module=[SCR_W, SCR_H, SCR_T], z0=WIN_Z0),
    driver=dict(d=DRV_D, h=DRV_H, x=DRV_X),
    pr=dict(w=PR_W, h=PR_H),
    parts=parts, conflicts=fails,
)

# ---------------- 匯出 ----------------
out = os.path.join(os.path.dirname(__file__), "export")
os.makedirs(out, exist_ok=True)
solids = dict(body=body, faceplate=fp, knob=knob, pr_clamp=clamp)
for name, s in solids.items():
    export_step(s, os.path.join(out, f"{name}.step"))
    export_stl(s, os.path.join(out, f"{name}.stl"), tolerance=0.15)
export_step(Compound(children=[body, fp, knob, Pos(PR_CX, 0, 0) * clamp]),
            os.path.join(out, "assembly.step"))
with open(os.path.join(out, "dims.json"), "w") as f:
    json.dump(dims, f, ensure_ascii=False, indent=1)

print("外觀 W×D×H =", W, D, H)
print("內腔  =", dims["inner"])
for p in parts:
    print(f"  {p['name']:14s} bbox={p['bbox']} {'OK' if p['in_bounds'] else p['issues']}")
print("干涉/超界：", fails if fails else "無")
for name, s in solids.items():
    print(name, "volume cm3 =", round(s.volume / 1000, 2))
