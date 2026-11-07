"""印刷稿（絲印／UV 印刷／雷雕）1:1 版面：正面字樣與圖示位置 → hw/print_decals.svg
座標系：展開後的前面板，u 水平（x）、v 沿斜面往上（0 = 底面）。
"""
import math, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 4.0                      # px per mm
W, H, TILT = 82.0, 103.0, 14.47
FACE_L = math.hypot(H, TILT)  # 斜面展開長度 ≈ 104.0
SCR_W, SCR_H, SCR_C = 49.0, 37.0, 60.0
KEY, GAP, KEY_CX, KEY_CV = 10.0, 1.6, -9.0, 21.0
KNOB_D, KNOB_CX, KNOB_CV = 12.0, 19.0, 30.0
MARGIN = 32

Wc = int(W * S + MARGIN * 2 + 560)
Hc = int(FACE_L * S + MARGIN * 2 + 90)

def X(u):  # u(mm, 以中心為 0) → px
    return MARGIN + (u + W / 2) * S

def Y(v):  # v(mm, 由底往上) → px（畫面 y 向下）
    return MARGIN + 70 + (FACE_L - v) * S

s = []
A = s.append
A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wc}" height="{Hc}" viewBox="0 0 {Wc} {Hc}" font-family="Hiragino Sans GB, PingFang TC, sans-serif">')
A(f'<rect width="{Wc}" height="{Hc}" fill="#ffffff"/>')
A(f'<text x="{MARGIN}" y="34" font-size="20" font-weight="700" fill="#111">MT-V3 印刷稿（絲印／UV 印刷／雷雕）— 1:1 版面</text>')
A(f'<text x="{MARGIN}" y="56" font-size="12" fill="#666">單位 mm　前面板展開圖（含 8° 前傾補正，展開長 {FACE_L:.1f}）　* 位置需以實機校核後定稿</text>')

# 面板外框
A(f'<rect x="{X(-W/2):.0f}" y="{Y(FACE_L):.0f}" width="{W*S:.0f}" height="{FACE_L*S:.0f}" rx="{8*S:.0f}" fill="#faf8f3" stroke="#111" stroke-width="1.5"/>')
# 螢幕
A(f'<rect x="{X(-SCR_W/2):.0f}" y="{Y(SCR_C+SCR_H/2):.0f}" width="{SCR_W*S:.0f}" height="{SCR_H*S:.0f}" rx="3" fill="#101820"/>')
A(f'<text x="{X(0):.0f}" y="{Y(SCR_C):.0f}" font-size="13" fill="#7ee787" text-anchor="middle" font-family="monospace">49 × 37 螢幕窗</text>')
# 鍵帽
for i in (-1, 1):
    for j in (-1, 1):
        cx = KEY_CX + i * (KEY + GAP) / 2
        cv = KEY_CV + j * (KEY + GAP) / 2
        A(f'<rect x="{X(cx-KEY/2):.0f}" y="{Y(cv+KEY/2):.0f}" width="{KEY*S:.0f}" height="{KEY*S:.0f}" rx="{0.7*S:.0f}" fill="#e8e5dd" stroke="#333"/>')
# 旋鈕
A(f'<circle cx="{X(KNOB_CX):.0f}" cy="{Y(KNOB_CV):.0f}" r="{KNOB_D/2*S:.0f}" fill="#d93a12"/>')
A(f'<text x="{X(KNOB_CX):.0f}" y="{Y(KNOB_CV)+4:.0f}" font-size="11" fill="#fff" text-anchor="middle">Ø12</text>')

# 字樣：品牌條 + 功能字
# 實拍確認：MINITOO 在螢幕「上方」邊框，鍵盤座再一行小字
A(f'<text x="{X(0):.0f}" y="{Y(SCR_C+SCR_H/2+5.5):.0f}" font-size="{2.8*S*0.42:.0f}" font-weight="700" letter-spacing="2.4" fill="#3a3a3a" text-anchor="middle">M I N I T O O</text>')
A(f'<text x="{X(0):.0f}" y="{Y(37.0):.0f}" font-size="{1.6*S*0.42:.0f}" letter-spacing="1" fill="#555" text-anchor="middle">RETRO PC-STYLE BLUETOOTH SPEAKER</text>')
legend = [
    (-14.8, 12.0, "電源圖示"),
    (-3.2, 27.5, "MODE"),
    (-3.2, 14.2, "▶︎ ‖"),
    (-14.8, 27.5, "＋ / −"),
]
for u, v, txt in legend:
    A(f'<text x="{X(u):.0f}" y="{Y(v):.0f}" font-size="{2.2*S*0.42:.0f}" fill="#555" text-anchor="middle">{txt}</text>')

# 右側說明欄
cx = MARGIN + W * S + 24
rows = [
    ("品牌條", "寬 ≤ 26mm，字高 2.6mm，置中；距離螢幕窗下緣 3.5mm"),
    ("功能字", "字高 2.2mm，深灰 #555；四鍵各一組（電源圖示／MODE／播放鍵／±）"),
    ("製程", "絲印 1 色（深灰）或 UV 印刷；亦可雷雕 0.15 深（不需油墨）"),
    ("公差", "字樣位置 ±0.2mm；與邊緣距離 ≥ 2.5mm"),
    ("實拍1", "MINITOO 在螢幕上方邊框；鍵盤座印 RETRO PC-STYLE …；旋鈕紅色"),
    ("實拍2", "USB-C＋卡片槽在正面底部；−SUBWOOFER− 在頂面；底部 CE/FCC"),
    ("注意", "本稿依照片推定；實機到位後以卡尺校核再定稿"),
]
y = MARGIN + 70
for k, v in rows:
    A(f'<text x="{cx}" y="{y}" font-size="13" font-weight="700" fill="#111">{k}</text>')
    A(f'<text x="{cx}" y="{y+18}" font-size="11" fill="#555">{v}</text>')
    y += 52

# 尺寸線（面板寬與展開高）
A(f'<line x1="{X(-W/2):.0f}" y1="{Y(0)+18:.0f}" x2="{X(W/2):.0f}" y2="{Y(0)+18:.0f}" stroke="#c62828"/>')
A(f'<text x="{X(0):.0f}" y="{Y(0)+14:.0f}" font-size="12" fill="#c62828" text-anchor="middle">82</text>')
A('</svg>')

out = os.path.join(BASE, "hw", "print_decals.svg")
open(out, "w").write("\n".join(s))
print("寫入", out, f"{Wc}x{Hc}")
