#!/usr/bin/env python3
"""產生電路接線圖 SVG（全中文標註），輸出 hw/schematic.svg
設計原則：深底、方塊化模組、線色分網路類別、底部寫「為什麼這樣接」。"""
import os

W, H = 1500, 980
BG = "#0f1720"
FG = "#e8eef6"
DIM = "#8fa3b8"

NET = {
    "5V":   ("#ff5252", "5V 電源"),
    "3V3":  ("#ffb74d", "3.3V 電源"),
    "GND":  ("#b0bec5", "接地"),
    "I2S":  ("#64b5f6", "I2S 音訊"),
    "SPI":  ("#81c784", "SPI 顯示"),
    "CTRL": ("#ba68c8", "控制訊號"),
}

def box(x, y, w, h, title, sub="", fill="#1b2735", stroke="#3d5872", tcol=FG):
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>']
    s.append(f'<text x="{x+w/2}" y="{y+26}" text-anchor="middle" fill="{tcol}" font-size="19" font-weight="700">{title}</text>')
    if sub:
        for i, line in enumerate(sub.split("\n")):
            s.append(f'<text x="{x+w/2}" y="{y+48+i*18}" text-anchor="middle" fill="{DIM}" font-size="13">{line}</text>')
    return "\n".join(s)

def pin(x, y, label, side="l", col=FG):
    anchor = "start" if side == "l" else "end"
    dx = 8 if side == "l" else -8
    return f'<text x="{x+dx}" y="{y+5}" text-anchor="{anchor}" fill="{col}" font-size="13">{label}</text>'

def wire(pts, net, dash=None, width=3):
    col, _ = NET[net]
    d = " ".join(f"{p[0]},{p[1]}" for p in pts)
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="{width}"{dash_attr} stroke-linejoin="round" stroke-linecap="round"/>'

def label(x, y, text, col=FG, size=12, anchor="middle", weight="400"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{col}" font-size="{size}" font-weight="{weight}">{text}</text>'

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="PingFang TC, Noto Sans TC, sans-serif">']
svg.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
svg.append(label(40, 52, "miniMac Speaker MM96 ─ 電路接線圖", FG, 30, "start", "700"))
svg.append(label(40, 82, "ESP32 經典藍牙（A2DP）接收 → I2S 數位音訊 → 3W 擴大 → 雙單體＋被動輻射器", DIM, 15, "start"))

# ---- 電源鏈 ----
svg.append(label(40, 130, "① 電源鏈", NET["5V"][0], 16, "start", "700"))
svg.append(box(40, 150, 190, 96, "18650 鋰電池", "3.7V 3000mAh\n含保護板", "#241d1d", "#7a4b4b"))
svg.append(box(290, 150, 210, 130, "IP5306 模組", "USB-C 充電 5V/2A\n升壓輸出 5V 2.4A\n4 段 LED 電量",
               "#241d1d", "#7a4b4b"))
svg.append(wire([(230, 198), (290, 198)], "5V"))
svg.append(label(260, 190, "B+ B−", NET["5V"][0]))

svg.append(box(560, 150, 300, 300, "ESP32 DevKitC", "經典 ESP32-WROOM-32\n5V 進 → 板載 LDO 3.3V"))
# 左側電源腳
svg.append(pin(560, 236, "5V / VIN", "l", NET["5V"][0]))
svg.append(pin(560, 262, "GND", "l", NET["GND"][0]))
svg.append(pin(560, 288, "3V3", "l", NET["3V3"][0]))
svg.append(wire([(500, 196), (530, 196), (530, 236), (560, 236)], "5V"))
svg.append(wire([(500, 250), (530, 250), (530, 262), (560, 262)], "GND"))
svg.append(wire([(520, 288), (560, 288)], "3V3"))

# 開關
svg.append(box(40, 300, 190, 70, "電源開關", "SS-12D00", "#241d1d", "#7a4b4b"))
svg.append(wire([(135, 246), (135, 300)], "5V"))
svg.append(label(150, 285, "串在 5V 主線", NET["5V"][0], 12, "start"))

# ---- 音訊鏈 ----
svg.append(label(900, 130, "② 音訊鏈（I2S 數位）", NET["I2S"][0], 16, "start", "700"))
svg.append(box(900, 150, 250, 200, "MAX98357A", "I2S DAC＋D 類擴大\n5V / 4Ω→3.2W\nSD 腳接 3.3V＝開啟"))
for i, (n, net) in enumerate([("BCLK ← GPIO26", "I2S"), ("LRC  ← GPIO25", "I2S"), ("DIN  ← GPIO22", "I2S")]):
    svg.append(pin(900, 250 + i * 22, n, "l", NET[net][0]))
svg.append(wire([(860, 256), (880, 256), (880, 250), (900, 250)], "I2S"))
svg.append(wire([(860, 272), (890, 272), (890, 272), (900, 272)], "I2S"))
svg.append(wire([(860, 288), (900, 288)], "I2S"))
svg.append(wire([(860, 236), (870, 236), (870, 380), (1150, 380), (1150, 210)], "5V", width=2.5))

svg.append(box(1210, 150, 250, 120, "單體 左", "40mm 4Ω 3W", "#1a2420", "#3f6b52"))
svg.append(box(1210, 300, 250, 120, "單體 右", "40mm 4Ω 3W\n兩顆串聯＝8Ω", "#1a2420", "#3f6b52"))
svg.append(wire([(1150, 210), (1180, 210), (1180, 190), (1210, 190)], "I2S"))
svg.append(wire([(1210, 250), (1190, 250), (1190, 360), (1210, 360)], "I2S"))
svg.append(label(1200, 300, "串聯", NET["I2S"][0], 13, "end"))
svg.append(wire([(1460, 360), (1480, 360), (1480, 210), (1150, 210)], "I2S", width=2))
svg.append(label(1240, 440, "被動輻射器 50×70mm 裝在背板（不是電子件）", DIM, 13, "start"))

# ---- 顯示與控制 ----
svg.append(label(40, 470, "③ 顯示與控制", NET["SPI"][0], 16, "start", "700"))
svg.append(box(40, 490, 270, 240, "2.8 吋 ST7789", "240×320 SPI IPS\n橫放 = 320×240"))
for i, n in enumerate(["SCLK ← GPIO18", "MOSI ← GPIO23", "CS   ← GPIO5", "DC   ← GPIO2", "RST  ← GPIO4", "BL   ← GPIO15"]):
    svg.append(label(330, 546 + i * 26, n, NET["SPI"][0], 13, "start"))

# SPI 六線匯流排：一條粗線代表 6 條，終點標腳位
svg.append(wire([(310, 600), (470, 600), (470, 470), (700, 470), (700, 452)], "SPI", width=7))
svg.append(label(478, 590, "SPI 六線匯流排", NET["SPI"][0], 13, "start"))

svg.append(box(900, 490, 250, 150, "EC11 旋轉編碼器", "A → GPIO32\nB → GPIO33\nSW → GPIO13", "#241f2b", "#6b4b8a"))
svg.append(wire([(900, 565), (830, 565), (830, 470), (760, 470), (760, 452)], "CTRL", width=5))
svg.append(label(838, 555, "3 條控制線", NET["CTRL"][0], 13, "start"))
svg.append(box(1210, 490, 250, 150, "操作對應", "轉 = 音量\n按一下 = 播放／暫停\n長按 = 換顯示模式", "#1b2735", "#3d5872"))

# ---- 電源流向註記 ----
svg.append(wire([(560, 236), (520, 236)], "5V", dash="6,5", width=2))

# ---- 圖例 ----
ly = 690
svg.append(f'<rect x="40" y="{ly-30}" width="1420" height="270" rx="10" fill="#141d28" stroke="#2c3f52"/>')
svg.append(label(60, ly, "訊號類別", FG, 15, "start", "700"))
for i, (k, (c, name)) in enumerate(NET.items()):
    x = 60 + (i % 3) * 300
    y = ly + 32 + (i // 3) * 28
    svg.append(f'<line x1="{x}" y1="{y-5}" x2="{x+40}" y2="{y-5}" stroke="{c}" stroke-width="4"/>')
    svg.append(label(x + 50, y, f"{name}（{k}）", FG, 13, "start"))

notes = [
    "為什麼這樣接：①手機用藍牙經典協定（A2DP）推音樂，ESP32 解碼後用 I2S 數位訊號丟給 MAX98357A，少了類比走線就不會有電流聲。",
    "② MAX98357A 的 SD 腳一定要接 3.3V 才會工作，沒接會完全沒聲音（這是新手最常卡住的地方）。",
    "③ 兩顆 4Ω 單體串聯成 8Ω，一顆擴大器就能推兩顆；並聯成 2Ω 聲音更大但超過晶片負載，會燒。",
    "④ IP5306 可以邊充邊放；電池掉到 3.4V 以下自動斷電保護電芯。",
    "⑤ 5V 只給 ESP32 的 5V 腳（板載 LDO 轉 3.3V）與 MAX98357A 的 VIN；螢幕與編碼器一律吃 3.3V。",
]
for i, n in enumerate(notes):
    svg.append(label(60, ly + 96 + i * 26, n, DIM, 13, "start"))

svg.append("</svg>")

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hw")
os.makedirs(out, exist_ok=True)
path = os.path.join(out, "schematic.svg")
open(path, "w").write("\n".join(svg))
print("寫入", path)
