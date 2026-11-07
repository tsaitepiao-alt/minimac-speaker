"""
MiniMac Speaker MM96-L「MiniBook」— 迷你筆電變體（同電路，只換殼）
  · 掀蓋式：底殼 150×110×28 ＋ 上蓋 150×100×9，合起 37mm
  · 上蓋 4.3 吋 480×272 IPS（模組 105.8×67.2×4.5），窗 97×56
  · 底殼：2×Ø40 下射單體、18650 平躺、ESP32／IP5306／MAX98357A
  · 鍵盤區 4×12 顆凹槽鍵位（裝飾／可雷雕符號）、橘色電源鈕
  · Ø3×130 鋼軸貫穿鉸鏈，開蓋 110 度
單位 mm，build123d 0.13 algebra mode
"""
from math import cos, sin, pi, radians
import json, os
from build123d import (
    Align, Axis, Box, Cylinder, Plane, Pos, Rot, Polyline, make_face, Rectangle,
    RectangleRounded, chamfer, extrude, fillet, export_step, export_stl, Compound,
)

# ---------------- 參數 ----------------
BW, BD, BH = 150.0, 110.0, 28.0      # 底殼 寬 深 高
LW, LD, LT = 150.0, 100.0, 9.0       # 上蓋 寬 深 厚
WALL, PLATE_T, FOOT_H = 2.4, 2.4, 6.0
GAP = 0.15

SCR_W, SCR_H, SCR_T = 105.8, 67.2, 4.5      # 4.3" 480×272 模組
WIN_W, WIN_H = 97.0, 56.0
WIN_ZC = LD / 2                            # 窗在上蓋正中央

DRV_D, DRV_H, DRV_HOLE, DRV_X, DRV_Y = 40.0, 22.0, 38.0, 32.0, -25.0
HINGE_D, HINGE_LEN, OPEN_DEG = 3.2, 130.0, 110.0

C, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX
HY = BD / 2 - 4.0            # 鉸鏈軸心 y（=51）
HZ = BH                      # 鉸鏈軸心 z（底殼頂面）
LID_T_OFF = 2.4              # 上蓋背面到軸心的偏距

# ---------------- 底殼（上開口的槽體，底部另件） ----------------
base = Box(BW, BD, BH, align=(C, C, MIN))
base = fillet(base.edges().filter_by(Axis.Z), 8.0)
base = fillet(base.edges().group_by(Axis.Z)[-1], 2.0)
# 內腔：底部敞開（由底板封閉）
base -= Pos(0, 0, PLATE_T) * Box(BW - 2 * WALL, BD - 2 * WALL, BH - WALL - PLATE_T + 1,
                                 align=(C, C, MIN))
# 鍵盤凹槽 4 排 × 12 鍵
KEY_PITCH, KEY_W = 10.2, 8.6
for r in range(4):
    for c in range(12):
        kx = -5.0 + (c - 5.5) * KEY_PITCH
        ky = -46.0 + r * KEY_PITCH
        base -= Pos(kx, ky, BH - 1.3) * Box(KEY_W, KEY_W, 2.6, align=(C, C, MIN))
# 電源鈕孔（橘色）
base -= Pos(63.0, -46.0, BH - 10) * Cylinder(5.2, 12.0, align=(C, C, MIN))
# 後方 I/O
base -= Pos(-45.0, BD - WALL / 2, 12.0) * Box(9.4, WALL + 2, 3.6, align=(C, C, C))
base -= Pos(40.0, BD - WALL / 2, 12.0) * Box(13.5, WALL + 2, 7.0, align=(C, C, C))
# 底板鎖附凸柱（4 角，M2 自攻）
plate_boss = [(-64.0, -44.0), (64.0, -44.0), (-64.0, 44.0), (64.0, 44.0)]
for bx, by in plate_boss:
    base += Pos(bx, by, 0) * Cylinder(4.0, 10.0, align=(C, C, MIN))
    base -= Pos(bx, by, 0) * Cylinder(0.8, 14.0, align=(C, C, MIN))
# 鉸鏈：底殼後緣半圓槽（讓上蓋的軸筒落進來）＋左右兩支耳
base -= Pos(0, HY, HZ) * Rot(0, 90, 0) * Cylinder(6.3, 24.0, align=(C, C, C))
for sx in (-1, 1):
    base += Pos(sx * 55.0, HY, HZ) * Rot(0, 90, 0) * Cylinder(8.0, 18.0, align=(C, C, C))
    base -= Pos(sx * 55.0, HY, HZ) * Rot(0, 90, 0) * Cylinder(HINGE_D / 2, 24.0, align=(C, C, C))
base = base.clean()

# ---------------- 底板（Ø38 出音孔 ×2、腳、螺孔） ----------------
plate = Box(BW, BD, PLATE_T, align=(C, C, MIN))
plate = fillet(plate.edges().filter_by(Axis.Z), 8.0)
for sx in (-1, 1):
    plate -= Pos(sx * DRV_X, DRV_Y, -1) * Cylinder(DRV_HOLE / 2, PLATE_T + 2, align=(C, C, MIN))
for bx, by in plate_boss:
    plate -= Pos(bx, by, -1) * Cylinder(1.2, 6.0, align=(C, C, MIN))
for sx in (-1, 1):
    for sy in (-1, 1):
        plate += Pos(sx * (BW / 2 - 12), sy * (BD / 2 - 12), -FOOT_H) * Cylinder(6.0, FOOT_H, align=(C, C, MIN))
plate = plate.clean()

# ---------------- 上蓋（螢幕窗＋鉸鏈耳） ----------------
lid = Box(LW, LD, LT, align=(C, C, MIN))
lid = fillet(lid.edges().filter_by(Axis.Z), 8.0)
lid = chamfer(lid.edges().group_by(Axis.Z)[-1], 0.8)
# 螢幕模組座：從上蓋 +z 面挖 5.5 深（-z 面才是打開後朝向使用者的顯示面）
lid -= Pos(0, 0, LT - (SCR_T + 1.0)) * Box(SCR_W + 6, SCR_H + 6, SCR_T + 1.0,
                                          align=(C, C, MIN))
# 螢幕窗（貫穿厚度 z，面朝 +z＝打開後面向使用者）
lid -= Pos(0, 0, LT / 2) * Box(WIN_W, WIN_H, LT + 4, align=(C, C, C))
# 鉸鏈耳（中間一支，與底殼兩支交錯）
lid += Pos(0, HY - LD / 2 + 2.0, 0) * Cylinder(6.0, 18.0, align=(C, C, C)) if False else lid
lid += Pos(0, LD / 2, 0) * Rot(0, 90, 0) * Cylinder(6.0, 14.0, align=(C, C, C))
lid -= Pos(0, LD / 2, 0) * Rot(0, 90, 0) * Cylinder(HINGE_D / 2, 20.0, align=(C, C, C))
lid = lid.clean()

# ---------------- 電源鈕 ----------------
btn = Cylinder(5.0, 10.0, align=(C, C, MIN)) - Cylinder(2.6, 6.0, align=(C, C, MIN))
btn = (Pos(63.0, -46.0, BH - 3.0) * btn).clean()

# ---------------- 尺寸／干涉核對（合蓋狀態） ----------------
def aabb(name, x0, x1, y0, y1, z0, z1, note=""):
    return dict(name=name, bbox=[round(v, 1) for v in (x0, x1, y0, y1, z0, z1)], note=note)

inner = dict(x=(-BW / 2 + WALL, BW / 2 - WALL), y=(-BD / 2 + WALL, BD / 2 - WALL),
             z=(PLATE_T, BH - WALL))
parts = [
    aabb("單體L", -DRV_X - DRV_D / 2, -DRV_X + DRV_D / 2, DRV_Y - DRV_D / 2, DRV_Y + DRV_D / 2, PLATE_T, PLATE_T + DRV_H, "下射"),
    aabb("單體R", DRV_X - DRV_D / 2, DRV_X + DRV_D / 2, DRV_Y - DRV_D / 2, DRV_Y + DRV_D / 2, PLATE_T, PLATE_T + DRV_H, "下射"),
    aabb("ESP32 DevKit", -60, -9, -4, 24, PLATE_T, PLATE_T + 12, "平放左後"),
    aabb("IP5306 模組", 0, 25, -2, 23, PLATE_T, PLATE_T + 8, "平放中央"),
    aabb("MAX98357A", 30, 52, -2, 14, PLATE_T, PLATE_T + 5, "平放右中"),
    aabb("18650 電池座", -38, 39, 26.8, 43.2, PLATE_T, PLATE_T + 18.5, "平躺後方"),
    aabb("4.3吋螢幕模組", -SCR_W / 2, SCR_W / 2, -SCR_H / 2, SCR_H / 2, 0.0, SCR_T, "嵌上蓋內側（上蓋局部座標）"),
]

def overlap(a, b):
    ax0, ax1, ay0, ay1, az0, az1 = a["bbox"]
    bx0, bx1, by0, by1, bz0, bz1 = b["bbox"]
    return all([min(ax1, bx1) - max(ax0, bx0) > 0.5,
                min(ay1, by1) - max(ay0, by0) > 0.5,
                min(az1, bz1) - max(az0, bz0) > 0.5])

fails = []
for p in parts[:6]:      # 螢幕在上蓋，不與底殼零件比對
    x0, x1, y0, y1, z0, z1 = p["bbox"]
    bad = []
    if x0 < inner["x"][0] - 0.1 or x1 > inner["x"][1] + 0.1: bad.append("X超出")
    if y0 < inner["y"][0] - 0.1 or y1 > inner["y"][1] + 0.1: bad.append("Y超出")
    if z0 < inner["z"][0] - 0.1 or z1 > inner["z"][1] + 0.1: bad.append("Z超出")
    p["in_bounds"], p["issues"] = not bad, bad
    if bad: fails.append(p["name"] + ":" + ",".join(bad))
for i in range(6):
    for j in range(i + 1, 6):
        if overlap(parts[i], parts[j]):
            fails.append(f"{parts[i]['name']} × {parts[j]['name']} 干涉")
parts[-1]["in_bounds"], parts[-1]["issues"] = True, []

closed_h = BH + LT
dims = dict(
    variant="laptop",
    outer=dict(W=BW, D=BD, H=BH), lid=dict(W=LW, D=LD, T=LT),
    closed=dict(W=BW, D=BD, H=closed_h),
    wall=WALL, plate_t=PLATE_T, foot_h=FOOT_H,
    inner=dict(W=round(BW - 2 * WALL, 1), D=round(BD - 2 * WALL, 1), H=round(BH - WALL - PLATE_T, 1)),
    screen=dict(window=[WIN_W, WIN_H], module=[SCR_W, SCR_H, SCR_T], type="4.3吋 480x272 IPS"),
    driver=dict(d=DRV_D, h=DRV_H, x=DRV_X, y=DRV_Y),
    hinge=dict(axis_pin=3.0, len=HINGE_LEN, open_deg=OPEN_DEG),
    parts=parts, conflicts=fails,
)

# ---------------- 匯出 ----------------
out = os.path.join(os.path.dirname(__file__), "export")
os.makedirs(out, exist_ok=True)
solids = dict(lid=lid, base_shell=base, bottom_plate=plate, button=btn)
for name, s in solids.items():
    export_step(s, os.path.join(out, f"laptop_{name}.step"))
    export_stl(s, os.path.join(out, f"laptop_{name}.stl"), tolerance=0.12)

# 組立（上蓋開 110 度，繞鉸鏈軸旋轉）
def lid_open(shape):
    return Pos(0, HY, HZ) * Rot(-OPEN_DEG, 0, 0) * Pos(0, -HY, -(HZ - 0)) * shape

# 上蓋原始位置：底面貼在底殼頂面（z = BH），背面朝 -y
lid_placed = Pos(0, HY - LD / 2, BH) * lid_placed if False else lid
asm_lid = Pos(0, 0, 0) * lid
# 先把上蓋移到合蓋位置：上蓋 z=0..LT 需放到 z=BH..BH+LT，且 y 對齊底殼（上蓋深 100、底殼 110）
closed_lid = Pos(0, HY - LD / 2, BH) * lid   # 上蓋後緣對齊鉸鏈軸
open_lid = Pos(0, HY, HZ) * Rot(-OPEN_DEG, 0, 0) * Pos(0, -HY, -HZ) * closed_lid
assembly = Compound(children=[base, plate, open_lid, btn])
export_step(assembly, os.path.join(out, "laptop_assembly.step"))
export_stl(assembly, os.path.join(out, "laptop_assembly.stl"), tolerance=0.12)
json.dump(dims, open(os.path.join(out, "laptop_dims.json"), "w"), ensure_ascii=False, indent=1)

print("合起  W×D×H =", BW, BD, closed_h, "｜開蓋角度", OPEN_DEG)
print("底殼內腔 =", dims["inner"])
for p in parts:
    print(f"  {p['name']:14s} {p['bbox']} {'OK' if p['in_bounds'] else p['issues']}")
print("干涉/超界：", "無" if not fails else fails)
for n, s in solids.items():
    print(n, "vol cm3 =", round(s.volume / 1000, 2))
