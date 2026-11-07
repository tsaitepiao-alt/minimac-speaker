"""
MiniMac Speaker MM96 — 參數化機構 v2（工業級外觀比例）
把「方盒子」改成真正的一體成型電腦造型：
  · 螢幕窗 62×47 放上緣，額頭 41.5 / 下巴 43.5（Mac 128K 的門面比例）
  · 窗戶內側 2mm CRT 凹槽（邊寬 4mm）
  · 面板四角 R6、四周 0.8mm 倒角；面板與機身留 0.15mm 分模線
  · 下巴：軟碟槽 46×5、Ø18 橘色旋鈕、Ø3 電源燈
  · 兩側散熱縫×3、背部被動輻射器／USB-C／開關／散熱縫
  · 底板單體承座（Ø45×1.6 環形凹台）確保氣密貼合
build123d 0.13 algebra mode，單位 mm
"""
from math import cos, sin, pi
import json, os
from build123d import (
    Align, Axis, Box, Cylinder, Plane, Pos, Rot, Polyline, make_face, Rectangle,
    RectangleRounded, chamfer, extrude, fillet, export_step, export_stl, Compound,
)

# ---------------- 主參數 ----------------
W, D, H = 96.0, 118.0, 132.0
WALL = 2.4
FOOT_H = 8.0
FRONT_T = 3.0
PART_GAP = 0.15

WIN_W, WIN_H, WIN_Z0 = 62.0, 47.0, 43.5
SCR_W, SCR_H, SCR_T = 82.5, 50.0, 5.0
BEZEL_REC, BEZEL_LIP = 2.0, 4.0

DRV_D, DRV_H, DRV_HOLE, DRV_X = 40.0, 22.0, 38.0, 22.0
PR_W, PR_H, PR_CX = 50.0, 70.0, -4.0
PR_Z = 69.0

C, MIN = Align.CENTER, Align.MIN
Y_FRONT, Y_BACK = -D / 2, D / 2
FP_Y = Y_FRONT - FRONT_T - PART_GAP        # 面板外表面 y
FPC = FP_Y - FRONT_T / 2                   # 面板厚度中心 y

# ---------------- 機身 ----------------
body = Box(W, D, H, align=(C, C, MIN))
body = fillet(body.edges().filter_by(Axis.Z), 6.0)
body = fillet(body.edges().group_by(Axis.Z)[-1], 2.5)
body = fillet(body.edges().group_by(Axis.Z)[0], 1.0)

# 四顆橡膠腳
for sx in (-1, 1):
    for sy in (-1, 1):
        body += Pos(sx * (W / 2 - 12), sy * (D / 2 - 12), -FOOT_H) * Cylinder(6.0, FOOT_H, align=(C, C, MIN))

# 內腔
cav_y0, cav_y1 = Y_FRONT - 1.0, Y_BACK - WALL
body -= Pos(0, (cav_y0 + cav_y1) / 2, WALL) * Box(
    W - 2 * WALL, cav_y1 - cav_y0, H - 2 * WALL, align=(C, C, MIN))

# 下射單體：貫穿孔 + 內側環形承座
for sx in (-1, 1):
    body -= Pos(sx * DRV_X, 0, -1) * Cylinder(DRV_HOLE / 2, WALL + 2, align=(C, C, MIN))
    body -= Pos(sx * DRV_X, 0, WALL) * Cylinder(DRV_D / 2 + 2.5, 1.6, align=(C, C, MIN))
    body -= Pos(sx * DRV_X, 0, WALL) * Cylinder(DRV_HOLE / 2, 3.0, align=(C, C, MIN))

# 背部開孔
body -= Pos(PR_CX, Y_BACK, PR_Z) * Rot(90, 0, 0) * Box(PR_W, PR_H, WALL + 2, align=(C, C, C))
body -= Pos(28, Y_BACK - WALL / 2, 16) * Box(9.4, WALL + 2, 3.6, align=(C, C, C))
body -= Pos(-28, Y_BACK - WALL / 2, 16) * Box(13.5, WALL + 2, 7.0, align=(C, C, C))
for dz in (112.0, 116.0, 120.0):
    body -= Pos(0, Y_BACK - WALL / 2, dz) * Box(46, WALL + 2, 2.0, align=(C, C, C))

# 兩側散熱縫
for sx in (-1, 1):
    for dz in (104.0, 110.0, 116.0):
        body -= Pos(sx * (W / 2 - WALL / 2), 34.0, dz) * Box(WALL + 2, 26.0, 3.0, align=(C, C, C))

# 面板鎖附凸柱（壓進側壁 1.4mm，避免相切造成非封閉網格）
boss_pts = [(-43.0, 9.0), (43.0, 9.0), (-43.0, 123.0), (43.0, 123.0)]
for bx, bz in boss_pts:
    body += Pos(bx, Y_FRONT + WALL, bz) * Rot(-90, 0, 0) * Cylinder(4.0, 11.0, align=(C, C, MIN))
    body -= Pos(bx, Y_FRONT + WALL, bz) * Rot(-90, 0, 0) * Cylinder(0.8, 15.0, align=(C, C, MIN))
body = body.clean()

# ---------------- 面板 ----------------
fp = Pos(0, FP_Y, 0) * Box(W, FRONT_T, H, align=(C, MIN, MIN))
fp = fillet(fp.edges().filter_by(Axis.Y), 6.0)
fp = chamfer(fp.edges().group_by(Axis.Z)[-1], 0.8)
fp = chamfer(fp.edges().group_by(Axis.Z)[0], 0.4)

def cut_rect(w, h, zc, xc=0.0, r=0.0, depth=None, yc=None):
    d = depth if depth else FRONT_T / 2 + 1.5
    sk = Plane.XZ * Pos(xc, zc) * (RectangleRounded(w, h, r) if r > 0 else Rectangle(w, h))
    return Pos(0, yc if yc is not None else FPC, 0) * extrude(sk, amount=d, both=True)

def cut_hole(dia, zc, xc=0.0, depth=None, yc=None):
    return Pos(xc, yc if yc is not None else FPC, zc) * Rot(90, 0, 0) * Cylinder(
        dia / 2, depth if depth else FRONT_T + 3.0)

# 螢幕窗（貫穿）
fp -= cut_rect(WIN_W, WIN_H, WIN_Z0 + WIN_H / 2, r=2.5)
# CRT 凹槽：面板內側再挖 2mm 深
fp -= cut_rect(WIN_W + 2 * BEZEL_LIP, WIN_H + 2 * BEZEL_LIP, WIN_Z0 + WIN_H / 2, r=4.0,
               depth=BEZEL_REC + 1.0, yc=FP_Y + FRONT_T - BEZEL_REC / 2)
# 旋鈕孔 / 軟碟槽 / 電源燈
fp -= cut_hole(7.6, 16.0, 32.0)
fp -= cut_rect(46.0, 5.0, 31.0, -12.0, r=1.8)
fp -= cut_hole(3.0, 12.0, -36.0)
for bx, bz in boss_pts:
    fp -= cut_hole(2.4, bz, bx)
# 螢幕固定柱（背面，位於窗外側不擋畫面）
for sx in (-1, 1):
    fp += Pos(sx * 36.0, FP_Y + FRONT_T - 0.5, WIN_Z0 + 1.0) * Rot(-90, 0, 0) * Cylinder(
        2.5, 6.0, align=(C, C, MIN))
    fp -= Pos(sx * 36.0, FP_Y + FRONT_T - 0.5, WIN_Z0 + 1.0) * Rot(-90, 0, 0) * Cylinder(
        0.8, 10.0, align=(C, C, MIN))
fp = fp.clean()

# ---------------- 旋鈕 ----------------
pts = []
for i in range(48):
    r = 9.0 if i % 2 == 0 else 8.3
    t = 2 * pi * i / 48
    pts.append((r * cos(t), r * sin(t)))
knob = extrude(make_face(Polyline(*pts, close=True)), 9.0)
knob -= Cylinder(3.1, 14.0, align=(C, C, MIN))
knob -= Pos(0, -9.0, 3.0) * Box(6.0, 4.0, 12.0, align=(C, C, MIN))
knob = (Pos(32.0, FP_Y, 16.0) * Rot(90, 0, 0) * knob).clean()

# ---------------- 被動輻射器壓框 ----------------
clamp_local = Box(PR_W + 14, PR_H + 14, 4.0, align=(C, C, MIN))
clamp_local -= Pos(0, 0, -1) * Box(PR_W + 2, PR_H + 2, 6.0, align=(C, C, MIN))
for sx in (-1, 1):
    for sy in (-1, 1):
        clamp_local -= Pos(sx * (PR_W / 2 + 4), sy * (PR_H / 2 + 4), -1) * Cylinder(1.1, 8.0, align=(C, C, MIN))
clamp = (Pos(PR_CX, Y_BACK - WALL, PR_Z) * Rot(90, 0, 0) * clamp_local).clean()

# ---------------- 尺寸／干涉核對 ----------------
def aabb(name, x0, x1, y0, y1, z0, z1, note=""):
    return dict(name=name, bbox=[round(v, 1) for v in (x0, x1, y0, y1, z0, z1)], note=note)

inner = dict(x=(-W / 2 + WALL, W / 2 - WALL), y=(Y_FRONT, Y_BACK - WALL), z=(WALL, H - WALL))
parts = [
    aabb("2.8吋螢幕模組", -SCR_W / 2, SCR_W / 2, Y_FRONT + WALL, Y_FRONT + WALL + SCR_T,
         WIN_Z0 - 1.5, WIN_Z0 - 1.5 + SCR_H, "貼面板內側對窗"),
    aabb("單體L", -DRV_X - DRV_D / 2, -DRV_X + DRV_D / 2, -DRV_D / 2, DRV_D / 2, WALL, WALL + DRV_H, "下射"),
    aabb("單體R", DRV_X - DRV_D / 2, DRV_X + DRV_D / 2, -DRV_D / 2, DRV_D / 2, WALL, WALL + DRV_H, "下射"),
    aabb("ESP32 DevKit", -25, 26, -48, -36, 95.0, 123.0, "立放螢幕上方後側"),
    aabb("IP5306 模組", -42, -17, -10, 15, 26.4, 34.4, "平放左下"),
    aabb("MAX98357A", 22, 44, 30, 46, 26.4, 31.4, "平放右下"),
    aabb("18650 電池座", -8.0, 13.5, 18, 38.5, 26.4, 103.4, "立放中央"),
    aabb("被動輻射器", PR_CX - PR_W / 2, PR_CX + PR_W / 2, Y_BACK - WALL - 14, Y_BACK - WALL,
         PR_Z - PR_H / 2, PR_Z + PR_H / 2, "背板內側"),
]

def overlap(a, b):
    ax0, ax1, ay0, ay1, az0, az1 = a["bbox"]
    bx0, bx1, by0, by1, bz0, bz1 = b["bbox"]
    return all([min(ax1, bx1) - max(ax0, bx0) > 0.5,
                min(ay1, by1) - max(ay0, by0) > 0.5,
                min(az1, bz1) - max(az0, bz0) > 0.5])

fails = []
for p in parts:
    x0, x1, y0, y1, z0, z1 = p["bbox"]
    bad = []
    if x0 < inner["x"][0] - 0.1 or x1 > inner["x"][1] + 0.1: bad.append("X超出")
    if y0 < inner["y"][0] - 0.1 or y1 > inner["y"][1] + 0.1: bad.append("Y超出")
    if z0 < inner["z"][0] - 0.1 or z1 > inner["z"][1] + 0.1: bad.append("Z超出")
    p["in_bounds"], p["issues"] = not bad, bad
    if bad: fails.append(p["name"] + ":" + ",".join(bad))
for i in range(len(parts)):
    for j in range(i + 1, len(parts)):
        if overlap(parts[i], parts[j]):
            fails.append(f"{parts[i]['name']} × {parts[j]['name']} 干涉")

dims = dict(
    outer=dict(W=W, D=D, H=H), wall=WALL, foot_h=FOOT_H, front_t=FRONT_T, part_gap=PART_GAP,
    inner=dict(W=round(W - 2 * WALL, 1), D=round(D - 2 * WALL, 1), H=round(H - 2 * WALL, 1)),
    screen=dict(window=[WIN_W, WIN_H], module=[SCR_W, SCR_H, SCR_T], z0=WIN_Z0, recess=BEZEL_REC),
    forehead=round(H - (WIN_Z0 + WIN_H), 1), chin=WIN_Z0,
    driver=dict(d=DRV_D, h=DRV_H, x=DRV_X), pr=dict(w=PR_W, h=PR_H),
    parts=parts, conflicts=fails,
)

out = os.path.join(os.path.dirname(__file__), "export")
os.makedirs(out, exist_ok=True)
solids = dict(body=body, faceplate=fp, knob=knob, pr_clamp=clamp)
for name, s in solids.items():
    export_step(s, os.path.join(out, f"{name}.step"))
    export_stl(s, os.path.join(out, f"{name}.stl"), tolerance=0.12)
export_step(Compound(children=[body, fp, knob, clamp]), os.path.join(out, "assembly.step"))
json.dump(dims, open(os.path.join(out, "dims.json"), "w"), ensure_ascii=False, indent=1)

print("外觀 W×D×H =", W, D, H)
print("螢幕窗", WIN_W, "×", WIN_H, "｜額頭", dims["forehead"], "｜下巴", dims["chin"])
print("內腔 =", dims["inner"])
for p in parts:
    print(f"  {p['name']:14s} {p['bbox']} {'OK' if p['in_bounds'] else p['issues']}")
print("干涉/超界：", "無" if not fails else fails)
for n, s in solids.items():
    print(n, "vol cm3 =", round(s.volume / 1000, 2))
