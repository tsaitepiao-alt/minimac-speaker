"""v3（Minito-class）2D 工程圖：正視／側視（看前傾）／俯視 ＋尺寸標註 → hw/drawing_v3.svg
比例 3 px/mm，第三角法；尺寸全部取自 build_minito.py 的參數。
"""
import base64, io, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cad"))
import render as R

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 3.0
W, D, H, TILT = 82.0, 61.0, 103.0, 14.47
SCR_W, SCR_H, SCR_C = 49.0, 37.0, 60.0
KEY, KNOB_D = 10.0, 12.0

PARTS = [("front_shell", (0.93, 0.90, 0.82)), ("back_cover", (0.88, 0.85, 0.77)),
         ("orange_key", (0.60, 0.60, 0.62)), ("keycaps", (0.55, 0.56, 0.58))]

def load_all():
    tris, cols = [], []
    for name, col in PARTS:
        m = R.trimesh.load(os.path.join(BASE, "cad", "export", f"minito_{name}.stl"))
        m = m.subdivide_to_size(max_edge=5.0)
        v = np.asarray(m.vertices, float); f = np.asarray(m.faces, int)
        tris.append(v[f]); cols.append(np.tile(np.array(col), (len(f), 1)))
    return np.concatenate(tris), np.concatenate(cols)

def view_png(T, C, cr, yaw, pitch, expect_mm):
    img, _ = R.render(T, C, yaw, pitch, 1400, 1400, bg=(255, 255, 255), crease=cr, zoom=1.0)
    a = np.array(img.convert("L"))
    ys, xs = np.where(a < 250)
    crop = img.crop((int(xs.min()) - 2, int(ys.min()) - 2, int(xs.max()) + 3, int(ys.max()) + 3))
    crop = crop.resize((int(round(expect_mm[0] * S)), int(round(expect_mm[1] * S))), Image.LANCZOS)
    buf = io.BytesIO(); crop.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode(), crop.size

def main():
    T, C = load_all()
    cr = R.crease_mask(T)
    front, (fw, fh) = view_png(T, C, cr, 0, 0, (W, H))
    side, (sw, sh) = view_png(T, C, cr, 90, 0, (D, H))
    top, (tw, th) = view_png(T, C, cr, 0, 89.9, (W, D))

    Wc, Hc = 1560, 1100
    fx, fy, sx, sy, tx, ty = 150, 200, 620, 200, 1000, 200
    A = [].append
    s = []
    A = s.append
    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wc}" height="{Hc}" viewBox="0 0 {Wc} {Hc}" font-family="Hiragino Sans GB, PingFang TC, sans-serif">')
    A(f'<rect width="{Wc}" height="{Hc}" fill="#fff"/>')
    A(f'<rect x="20" y="20" width="{Wc-40}" height="{Hc-40}" fill="none" stroke="#111" stroke-width="2"/>')
    A('<text x="48" y="70" font-size="26" font-weight="700" fill="#111">Minito-class 逆向重建 v3 ─ 外觀工程圖</text>')
    A('<text x="48" y="98" font-size="14" fill="#556">單位 mm　比例 3 px/mm　尺寸來源：手指(4.0–4.5 指寬)＋鍵帽(4–5u) 雙比例尺推定，非實機量測</text>')
    A(f'<image x="{fx}" y="{fy}" width="{fw}" height="{fh}" href="data:image/png;base64,{front}"/>')
    A(f'<image x="{sx}" y="{sy}" width="{sw}" height="{sh}" href="data:image/png;base64,{side}"/>')
    A(f'<image x="{tx}" y="{ty}" width="{tw}" height="{th}" href="data:image/png;base64,{top}"/>')
    A(f'<text x="{fx}" y="{fy-14}" font-size="16" font-weight="700" fill="#111">正視</text>')
    A(f'<text x="{sx}" y="{sy-14}" font-size="16" font-weight="700" fill="#111">側視（前傾 8°）</text>')
    A(f'<text x="{tx}" y="{ty-14}" font-size="16" font-weight="700" fill="#111">俯視</text>')

    RED = "#c62828"
    def hd(x1, x2, y, t):
        A(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{RED}"/>')
        for x in (x1, x2):
            A(f'<line x1="{x}" y1="{y-6}" x2="{x}" y2="{y+6}" stroke="{RED}"/>')
        A(f'<text x="{(x1+x2)/2}" y="{y-8}" font-size="14" fill="{RED}" text-anchor="middle">{t}</text>')

    def vd(y1, y2, x, t):
        A(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{RED}"/>')
        for y in (y1, y2):
            A(f'<line x1="{x-6}" y1="{y}" x2="{x+6}" y2="{y}" stroke="{RED}"/>')
        A(f'<text x="{x+9}" y="{(y1+y2)/2+5}" font-size="14" fill="{RED}">{t}</text>')

    X0, Y0 = fx, fy + fh          # 機身左下角
    X1, YT = X0 + W * S, Y0 - H * S
    hd(X0, X1, Y0 + 62, "82")
    vd(YT, Y0, X1 + 46, "103")
    # 螢幕：中心 z=60，49×37
    scr_bot = Y0 - (SCR_C - SCR_H / 2) * S
    scr_top = Y0 - (SCR_C + SCR_H / 2) * S
    vd(scr_top, scr_bot, X0 - 52, "37")
    hd(X0 + (W / 2 - SCR_W / 2) * S, X0 + (W / 2 + SCR_W / 2) * S, scr_top - 30, "49")
    A(f'<text x="{X0-146}" y="{Y0-(SCR_C)*S:.0f}" font-size="13" fill="{RED}">螢幕中心 z={SCR_C:.0f}</text>')
    # 鍵與旋鈕
    A(f'<text x="{X0-146}" y="{Y0-14}" font-size="13" fill="#1565c0">10×10 鍵 ×4（2×2）、橘旋鈕直徑12（中心 z=30）</text>')

    SY0 = sy + sh
    hd(sx, sx + D * S, SY0 + 44, "61")
    vd(SY0 - H * S, SY0, sx + D * S + 44, "103")
    A(f'<text x="{sx}" y="{SY0+72}" font-size="13" fill="#1565c0">頂部後縮 {TILT:.1f}（= 8° 前傾）</text>')

    hd(tx, tx + W * S, ty + th + 40, "82")
    vd(ty, ty + th, tx + W * S + 44, "61")

    A('<rect x="48" y="880" width="1464" height="190" fill="none" stroke="#111"/>')
    A('<text x="62" y="906" font-size="15" font-weight="700" fill="#111">技術要求</text>')
    notes = [
        "1. 外殼 PETG（列印）／ABS（射出）；壁厚 2.6；四角 R8；前傾 8°。",
        "2. 螢幕窗 49×37（4:3），對應 2.8 吋 320×240；內凹 3mm、邊唇 1.4。",
        "3. 控制區：2×2 鍵帽 10×10（行程 0.8，倒角 0.7）＋ 橘色旋鈕 直徑12（12 條滾花）。",
        "4. 頂部出音柵孔 9 條 × 2.6（節距 6.5）；背面 USB-C 9.4×3.6、開關 13.5×7、散熱 3 條。",
        "5. 公差：外觀 ±0.3、孔位 ±0.2、配合 ±0.15；射出需 1° 拔模與分模線。",
        "6. 本圖尺寸由照片雙比例尺推定，實機到位後需重新校核並升版（v3 → v4）。",
    ]
    y = 934
    for n in notes:
        A(f'<text x="62" y="{y}" font-size="14" fill="#334">{n}</text>'); y += 24
    A('<text x="1120" y="906" font-size="15" font-weight="700" fill="#111">圖框</text>')
    A('<text x="1120" y="936" font-size="13" fill="#334">件號 MT-V3-01　件名 外殼總成</text>')
    A('<text x="1120" y="960" font-size="13" fill="#334">件數 4（前殼／背蓋／鍵帽／旋鈕）</text>')
    A('<text x="1120" y="984" font-size="13" fill="#334">比例 3 px/mm　日期 2026-11-08</text>')
    A("</svg>")
    out = os.path.join(BASE, "hw", "drawing_v3.svg")
    open(out, "w").write("\n".join(s))
    print("寫入", out)

if __name__ == "__main__":
    main()
