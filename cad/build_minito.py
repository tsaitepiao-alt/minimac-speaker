"""
Minito-class 逆向重建 v3（依您提供的實拍圖比例）
重點：①正面 8 度前傾 ②螢幕佔正面寬 58%、偏上 ③2×2 灰方鍵＋右下橘圓鍵 ④頂部百葉出音孔 ⑤深度 = 0.79 寬
所有尺寸標「假設/量測」來源，未量到的部分明講。
"""
import json, os, math
from build123d import (
    Align, Axis, Box, Cylinder, Plane, Polyline, Pos, Rot, chamfer, extrude,
    fillet, make_face, offset, export_step, export_stl,
)

C, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX

# ---- 主尺寸（假設：以此為基準；比例取自實拍圖目視＋官方 Ditoo 級距）----
W, D, H = 82.0, 61.0, 103.0        # 依「手=比例尺」量測：寬 4.3 指寬 ≈ 82mm
WALL = 2.6
TILT_DEG = 8.0                      # 正面前傾
TILT = H * math.tan(math.radians(TILT_DEG))   # 頂部後縮量 ≈ 16.9

SCR_W, SCR_H = 49.0, 37.0   # 4:3（鍵帽比例尺照片確認），佔寬 60%           # 佔正面寬 58%；4:3 → 對應 2.8" 320x240（有效 57.6×43.2）
SCR_RECESS, SCR_LIP = 3.0, 1.4      # 螢幕內凹深度與邊唇
KEY = 10.0                          # 灰鍵邊長
KEY_GAP = 1.6
KNOB_D = 12.0                       # 橘色圓鍵直徑（佔寬 11.5%）
FOOT_H = 4.0

out = os.path.join(os.path.dirname(__file__), "export")
os.makedirs(out, exist_ok=True)

# ---- 機身：方塊切掉前上角楔形 → 前傾面 ----
body = Box(W, D, H, align=(C, C, MIN))
wedge_pts = [(-D / 2, H), (-D / 2 + TILT, H), (-D / 2, 0)]
wedge_face = make_face(Plane.YZ * Polyline(*wedge_pts, close=True))
wedge = extrude(wedge_face, amount=W / 2, both=True)
body -= wedge

# 外觀圓角
body = fillet(body.edges().filter_by(Axis.Z), 8.0)
body = fillet(body.edges().group_by(Axis.Z)[-1], 2.0)

# ---- 挖殼（壁厚 WALL），背面開口 ----
shell = body - offset(body, -WALL)
shell -= Pos(0, D / 2, 0) * Box(W - 4 * WALL, WALL * 2.2, H - 3 * WALL, align=(C, C, MIN))
shell -= Pos(0, D / 2, 0) * Box(W - 4 * WALL, WALL * 2.2, H - 3 * WALL, align=(C, C, MIN))

# ---- 前傾面上的特徵：螢幕槽＋按鍵 ----
nx, ny, nz = 0.0, -H, TILT
ln = math.sqrt(ny * ny + nz * nz)
front_plane = Plane(origin=(0, -D / 2, 0), z_dir=(nx, ny / ln, nz / ln), x_dir=(1, 0, 0))

def pocket(shape2d, depth):
    """在前傾面上挖 depth 深的凹槽（往機身內）"""
    f = front_plane * shape2d
    return extrude(f, amount=-depth)

# 螢幕槽（含邊唇）
scr_c = 60.0                                  # 從底面沿斜面往上 62mm
scr = front_plane * Pos(0, scr_c, 0) * Box(SCR_W + 2 * SCR_LIP, SCR_H + 2 * SCR_LIP, SCR_RECESS, align=(C, C, C))
shell -= scr
# 螢幕開口（貫穿到內腔）
shell -= front_plane * Pos(0, scr_c, 0) * Box(SCR_W, SCR_H, SCR_RECESS + 6, align=(C, C, C))

# 2×2 灰鍵（左下）＋ 橘圓鍵（右下），都在螢幕下方
key_y = 21.0
for i in (-1, 1):
    for j in (-1, 1):
        cx = -9.0 + i * (KEY + KEY_GAP) / 2
        cy = key_y + j * (KEY + KEY_GAP) / 2
        shell -= front_plane * (Pos(cx, cy, 0) * Box(KEY, KEY, 3.4, align=(C, C, C)))
        shell -= front_plane * (Pos(cx, cy, 0) * Box(KEY + 1.6, KEY + 1.6, 1.2, align=(C, C, C)))
# 橘圓鍵（右下，Ø11）
knob_c = (19.0, 30.0)   # 實拍：橘鈕在控制面板右上
shell -= front_plane * (Pos(knob_c[0], knob_c[1], 0) * Cylinder(KNOB_D / 2 + 0.9, 4.0, align=(C, C, MIN)))
shell -= front_plane * (Pos(knob_c[0], knob_c[1], 0) * Rot(90, 0, 0) * Cylinder(KNOB_D / 2, 3.0))

# ---- 頂部百葉出音孔（3 條）----
for k in range(-4, 5):
    shell -= Pos(0, k * 6.5, H - 1.0) * Box(W - 28, 2.6, 3.0, align=(C, C, MIN))

# ---- 背面 I/O 與散熱 ----
shell -= Pos(-22.0, D / 2 - WALL, 14.0) * Box(9.4, WALL + 3, 3.6, align=(C, C, C))
shell -= Pos(20.0, D / 2 - WALL, 14.0) * Box(13.5, WALL + 3, 7.0, align=(C, C, C))
for k in (-1, 0, 1):
    shell -= Pos(0, D / 2 - WALL, 84.0 + k * 7.0) * Box(40.0, WALL + 3, 2.2, align=(C, C, C))

# ---- 腳墊 ----
for sx in (-1, 1):
    for sy in (-1, 1):
        shell -= Pos(sx * (W / 2 - 14), sy * (D / 2 - 14), 0) * Cylinder(5.2, 2.0, align=(C, C, MIN))

shell = shell.clean()

# ---- 後蓋（獨立件，印後鎖上）----
back = Box(W - 1.0, WALL, H - 1.0, align=(C, C, MIN))
back = fillet(back.edges().filter_by(Axis.Z), 1.2)
for k in (-1, 0, 1):
    back -= Pos(0, 0, 74.0 + k * 6.0) * Box(28.0, WALL + 3, 1.6, align=(C, C, MIN))
back = (Pos(0, D / 2 - WALL / 2, 0) * back).clean()

# ---- 四顆灰鍵帽（獨立件，鍵盤實體）----
caps = []
for i in (-1, 1):
    for j in (-1, 1):
        cx = -9.0 + i * (KEY + KEY_GAP) / 2
        cy = key_y + j * (KEY + KEY_GAP) / 2
        cap = Box(KEY - 0.9, KEY - 0.9, 2.4, align=(C, C, MIN))
        cap = chamfer(cap.edges().group_by(Axis.Z)[-1], 0.7)
        caps.append(front_plane * Pos(cx, cy, -1.9) * Rot(90, 0, 0) * cap)
keycaps = caps[0]
for c in caps[1:]:
    keycaps += c
keycaps = keycaps.clean()

# ---- 橘色圓鍵（獨立件）----
knob = Cylinder(KNOB_D / 2 - 0.15, 7.0, align=(C, C, MIN))
knob -= Cylinder(KNOB_D / 2 - 2.2, 2.0, align=(C, C, MIN))
# 側面滾花（12 條）— 實拍上橘鈕有細紋，這是質感關鍵
for i in range(12):
    ang = math.radians(i * 30)
    r = KNOB_D / 2 - 0.55
    knob -= Pos(r * math.cos(ang), r * math.sin(ang), 1.2) * Rot(0, 0, math.degrees(ang)) * Box(1.1, 0.9, 5.6, align=(C, C, MIN))
knob = (front_plane * Pos(knob_c[0], knob_c[1], -2.0) * Rot(-90, 0, 0) * knob).clean()

dims = dict(
    variant="minito-v3",
    outer=dict(W=W, D=D, H=H), depth_ratio=round(D / W, 2),
    wall=WALL, tilt_deg=TILT_DEG, tilt_mm=round(TILT, 1),
    screen=dict(w=SCR_W, h=SCR_H, center_from_bottom=scr_c,
                width_ratio=round(SCR_W / W, 2), recess=SCR_RECESS, lip=SCR_LIP,
                panel="2.8吋 320x240（有效 57.6×43.2）"),
    keys=dict(size=KEY, gap=KEY_GAP, layout="2x2 左下", knob_d=KNOB_D),
    feet=FOOT_H, parts=["front_shell", "back_cover", "orange_key", "keycaps"],
    measured_from="實拍圖目視比例（front 角度）",
    assumed="深度、壁厚、按鍵行程、內部結構",
)
json.dump(dims, open(os.path.join(out, "minito_dims.json"), "w"), ensure_ascii=False, indent=1)

for name, s in dict(front_shell=shell, back_cover=back, orange_key=knob, keycaps=keycaps).items():
    export_step(s, os.path.join(out, f"minito_{name}.step"))
    export_stl(s, os.path.join(out, f"minito_{name}.stl"), tolerance=0.12)
    print(f"{name:12s} vol={s.volume/1000:8.2f} cm3  bbox={[round(v,1) for v in s.bounding_box().size]}")
print("外觀", W, "×", D, "×", H, "｜前傾", TILT_DEG, "度｜螢幕窗", SCR_W, "×", SCR_H, f"({SCR_W/W:.0%} 寬)")
