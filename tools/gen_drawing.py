#!/usr/bin/env python3
"""出 2D 工程圖：三視圖（正／側／俯）＋尺寸標註＋圖框 → hw/drawing.svg（再由 Chrome 轉 PNG）
每個視圖以 3 px/mm 精確排版、互不重疊；直徑以「直徑」中文標示，避免字型缺字。
"""
import base64, io, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cad"))
import render as R

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 3.0
W, D, H, FOOT = 96.0, 118.0, 132.0, 8.0
WIN_W, WIN_H, WIN_Z0 = 62.0, 47.0, 43.5
DRV_X, PR_Z = 22.0, 69.0

def view_png(T, C, cr, yaw, pitch, expect_mm):
    img, _ = R.render(T, C, yaw, pitch, 1600, 1600, bg=(255, 255, 255), crease=cr, zoom=1.0)
    a = np.array(img.convert("L"))
    ys, xs = np.where(a < 250)
    crop = img.crop((int(xs.min()) - 2, int(ys.min()) - 2, int(xs.max()) + 3, int(ys.max()) + 3))
    crop = crop.resize((int(round(expect_mm[0] * S)), int(round(expect_mm[1] * S))), Image.LANCZOS)
    buf = io.BytesIO()
    crop.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode(), crop.size

def main():
    T, C = R.load()
    cr = R.crease_mask(T)
    front, (fw, fh) = view_png(T, C, cr, 0, 0, (W, H + FOOT))
    side, (sw, sh) = view_png(T, C, cr, 90, 0, (D, H + FOOT))
    top, (tw, th) = view_png(T, C, cr, 0, 89.9, (W, D))

    Wc, Hc = 1560, 1120
    fx, fy = 170, 150
    sx, sy = 700, 150
    tx, ty = 1180, 150
    s = []
    A = s.append
    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wc}" height="{Hc}" viewBox="0 0 {Wc} {Hc}" font-family="Hiragino Sans GB, PingFang TC, sans-serif">')
    A(f'<rect width="{Wc}" height="{Hc}" fill="#ffffff"/>')
    A(f'<rect x="20" y="20" width="{Wc-40}" height="{Hc-40}" fill="none" stroke="#111" stroke-width="2"/>')
    A('<text x="48" y="70" font-size="26" font-weight="700" fill="#111">miniMac Speaker MM96 ─ 外觀工程圖</text>')
    A('<text x="48" y="98" font-size="14" fill="#556">單位 mm　比例 3 px/mm　紅字＝標稱尺寸　藍字＝組裝件與製程</text>')

    A(f'<image x="{fx}" y="{fy}" width="{fw}" height="{fh}" href="data:image/png;base64,{front}"/>')
    A(f'<image x="{sx}" y="{sy}" width="{sw}" height="{sh}" href="data:image/png;base64,{side}"/>')
    A(f'<image x="{tx}" y="{ty}" width="{tw}" height="{th}" href="data:image/png;base64,{top}"/>')
    A(f'<text x="{fx}" y="{fy-14}" font-size="16" fill="#111" font-weight="700">正視（前）</text>')
    A(f'<text x="{sx}" y="{sy-14}" font-size="16" fill="#111" font-weight="700">側視（右）</text>')
    A(f'<text x="{tx}" y="{ty-14}" font-size="16" fill="#111" font-weight="700">俯視（上）</text>')

    RED = "#c62828"
    def hdim(x1, x2, y, text):
        A(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{RED}" stroke-width="1"/>')
        for x in (x1, x2):
            A(f'<line x1="{x}" y1="{y-6}" x2="{x}" y2="{y+6}" stroke="{RED}" stroke-width="1"/>')
        A(f'<text x="{(x1+x2)/2}" y="{y-8}" font-size="14" fill="{RED}" text-anchor="middle">{text}</text>')

    def vdim(y1, y2, x, text):
        A(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{RED}" stroke-width="1"/>')
        for y in (y1, y2):
            A(f'<line x1="{x-6}" y1="{y}" x2="{x+6}" y2="{y}" stroke="{RED}" stroke-width="1"/>')
        A(f'<text x="{x+9}" y="{(y1+y2)/2+5}" font-size="14" fill="{RED}">{text}</text>')

    X0, Y0 = fx, fy + fh - FOOT * S
    X1 = X0 + W * S
    YT = Y0 - H * S
    hdim(X0, X1, YT - 46, "96")
    vdim(YT, Y0, X1 + 52, "132")
    vdim(Y0, Y0 + FOOT * S, X1 + 96, "8（腳）")
    wz0, wz1 = Y0 - WIN_Z0 * S, Y0 - (WIN_Z0 + WIN_H) * S
    vdim(wz1, wz0, X0 - 58, "47")
    hdim(X0 + (48 - WIN_W / 2) * S, X0 + (48 + WIN_W / 2) * S, wz1 - 40, "62")
    A(f'<text x="{X0-150}" y="{wz0+4}" font-size="13" fill="{RED}">窗下緣 z={WIN_Z0}</text>')
    A(f'<text x="{X0-150}" y="{wz1-10}" font-size="13" fill="{RED}">窗上緣 z={WIN_Z0+WIN_H}</text>')
    for sgn in (-1, 1):
        cx = X0 + (48 + sgn * DRV_X) * S
        A(f'<line x1="{cx}" y1="{Y0+2}" x2="{cx}" y2="{Y0-FOOT*S-38}" stroke="#1565c0" stroke-width="1" stroke-dasharray="6 4"/>')
    A(f'<text x="{X0-150}" y="{Y0+FOOT*S+56}" font-size="13" fill="#1565c0">下射單體 直徑40 ×2（中心距 44）· 離桌 8mm 出音</text>')

    SY0 = sy + sh - FOOT * S
    hdim(sx, sx + D * S, SY0 + 52, "118")
    vdim(SY0 - H * S, SY0, sx + D * S + 52, "132")
    A(f'<text x="{sx-60}" y="{SY0+FOOT*S+74}" font-size="13" fill="#1565c0">背板：被動輻射器 50×70（中心 z={PR_Z}）· USB-C · 開關 · 散熱縫</text>')

    hdim(tx, tx + W * S, ty + th + 40, "96")
    vdim(ty, ty + th, tx + W * S + 48, "118")

    A('<rect x="48" y="880" width="1464" height="200" fill="none" stroke="#111" stroke-width="1"/>')
    A('<line x1="48" y1="912" x2="1512" y2="912" stroke="#111" stroke-width="1"/>')
    A('<text x="60" y="904" font-size="15" font-weight="700" fill="#111">技術要求</text>')
    notes = [
        "1. 外殼 PETG，壁厚 2.4；面板四角 R6、四周倒角 0.8；面板與機身留 0.15 分模線。",
        "2. 螢幕窗 62×47，內側 2mm CRT 凹槽（邊寬 4），對應 2.8 吋 ST7789（模組 82.5×50×5）。",
        "3. 底板 直徑38 出音孔 ×2，內側 直徑45×1.6 環形承座供單體籃框氣密貼合。",
        "4. 公差：外觀 ±0.3、孔位 ±0.2、配合面 ±0.15（FDM 小批量）；射出量產需加 1 度拔模與模具分模線。",
        "5. 組裝：面板 4×M2×8 自攻鎖入機身凸柱；單體與被動輻射器皆需泡棉氣密。",
    ]
    y = 936
    for n in notes:
        A(f'<text x="60" y="{y}" font-size="14" fill="#334">{n}</text>')
        y += 25
    A('<text x="1120" y="904" font-size="15" font-weight="700" fill="#111">圖框</text>')
    A('<text x="1120" y="936" font-size="13" fill="#334">件號 MM96-HW-01　件名 外殼總成</text>')
    A('<text x="1120" y="960" font-size="13" fill="#334">材質 PETG　製程 FDM（小批量）</text>')
    A('<text x="1120" y="984" font-size="13" fill="#334">比例 3 px/mm　日期 2026-11-07</text>')
    A('<text x="1120" y="1008" font-size="13" fill="#334">設計 William / Hermes</text>')
    A("</svg>")

    out = os.path.join(BASE, "hw", "drawing.svg")
    open(out, "w").write("\n".join(s))
    print("寫入", out)

if __name__ == "__main__":
    main()
