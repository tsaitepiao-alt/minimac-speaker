#!/usr/bin/env python3
"""BOM 產生器：唯一價格來源，改這裡再跑一次就會重算 BOM.md 的總價與售價。"""
import os

# (分類, 品名, 規格/型號, 數量, 單價TWD, 採購處, 連結, 備註)
ITEMS = [
    ("電子", "ESP32 開發板", "ESP32-WROOM-32 DevKitC V4 / 30pin（需經典藍牙 A2DP）", 1, 180,
     "傑森創工 / 台灣物聯 / 蝦皮", "https://shopee.tw/search?keyword=ESP32%20DevKit%20WROOM-32",
     "⚠️ 不可用 ESP32-S3／C3／C6：它們沒有 Bluetooth Classic，無法當 A2DP 喇叭"),
    ("電子", "I2S 數位擴大模組", "MAX98357A（3.2W @ 4Ω, 5V）", 1, 110,
     "淘寶／立創", "https://www.lcsc.com/product-detail/C910544.html",
     "晶片原廠頁；模組在淘寶搜「MAX98357A 模块」約 ¥6"),
    ("電子", "彩色螢幕模組", "2.8 吋 ST7789 240×320 SPI（含 PCB 排針）", 1, 260,
     "傑森創工", "https://www.jmaker.com.tw/products/2-8-spi-lcd",
     "橫放使用（320×240）；同款台灣物聯也有"),
    ("電子", "電源管理模組", "IP5306 行動電源模組 5V/2.4A（USB-C 充電＋4 段電量）", 1, 120,
     "淘寶／立創", "https://www.lcsc.com/product-detail/C181692.html",
     "晶片頁；模組淘寶搜「IP5306 移动电源模块 5V 2.4A」"),
    ("電子", "鋰電池", "18650 3.7V 3000mAh（有保護板）", 1, 150, "台灣電子材料行／蝦皮",
     "https://shopee.tw/search?keyword=18650%203000mAh%20%E4%BF%9D%E8%AD%B7%E6%9D%BF", "禁止無保護板裸電芯"),
    ("電子", "電池座", "18650 單節焊接式電池座", 1, 25, "今華／蝦皮",
     "https://shopee.tw/search?keyword=18650%20%E9%9B%BB%E6%B1%A0%E5%BA%A7", ""),
    ("電子", "旋轉編碼器", "EC11 帶按鍵 15mm 半軸（音量／選曲）", 1, 45, "今華電子",
     "https://www.icshop.com.tw/en/products/368011000377", "店家頁會擋爬蟲，瀏覽器可正常開"),
    ("電子", "電源開關", "SS-12D00 撥桿開關（或 8mm 船型開關）", 1, 25, "今華／蝦皮",
     "https://shopee.tw/search?keyword=SS-12D00%20%E9%96%8B%E9%97%9C", ""),
    ("電聲", "全音域單體", "40mm 4Ω 3W 泡棉邊（兩顆串聯成 8Ω）", 2, 70, "蝦皮／淘寶",
     "https://shopee.tw/search?keyword=40mm%204%E6%AD%90%203W%20%E5%96%87%E5%8F%AD",
     "兩顆串聯＝8Ω，可直接接 MAX98357A，不需第二顆擴大器"),
    ("電聲", "被動輻射器", "50×70mm 橢圓被動輻射器（低音補強）", 1, 90, "淘寶",
     "https://s.taobao.com/search?q=%E8%A2%AB%E5%8A%A8%E8%BE%90%E5%B0%84%E5%99%A8+50x70", ""),
    ("機構", "自攻螺絲", "M2×8 十字（面板鎖附）", 8, 3, "今華／五金行",
     "https://shopee.tw/search?keyword=M2x8%20%E8%87%AA%E6%94%BB%E8%9E%BA%E7%B5%B2", "鎖進列印件凸柱，不需螺母"),
    ("機構", "螺絲＋熱熔螺母", "M3×6 ＋ M3 熱熔銅螺母（被動輻射器壓框）", 4, 6, "五金行",
     "https://shopee.tw/search?keyword=M3%20%E7%86%B1%E7%86%94%E9%8A%85%E7%B4%8B%E6%AF%8D", ""),
    ("機構", "喇叭網布", "Ø100 金屬或布質網片（下射出音孔）", 2, 30, "蝦皮／音響材料",
     "https://shopee.tw/search?keyword=%E5%96%87%E5%8F%AD%E7%B6%B2%E5%B8%83", ""),
    ("機構", "泡棉密封條", "2mm 厚 × 10mm 寬 單面膠（氣密用）", 1, 30, "五金行",
     "https://shopee.tw/search?keyword=%E6%B3%A1%E6%A3%89%E5%AF%86%E5%B0%81%E6%A2%9D%202mm", "沒做氣密，被動輻射器等於沒用"),
    ("線材", "矽導線", "26AWG 紅／黑／白 各 1m", 1, 60, "今華／蝦皮",
     "https://shopee.tw/search?keyword=26AWG%20%E7%9F%BD%E5%B0%8E%E7%B7%9A", ""),
    ("線材", "端子組", "JST-XH 2P/3P/4P 公母頭＋壓線鉗", 1, 60, "蝦皮／淘寶",
     "https://shopee.tw/search?keyword=JST-XH%20%E7%AB%AF%E5%AD%90%E7%B5%84", "模組化＝日後好換零件"),
    ("列印", "PETG 線材", "外殼約 200g（含失敗備料）", 1, 120, "3D 列印材料行",
     "https://shopee.tw/search?keyword=PETG%201.75mm%20%E7%B7%9A%E6%9D%90", "PETG 比 PLA 耐熱、不會被音響震到變形"),
    ("包裝", "包裝盒＋說明卡", "牛皮紙盒 120×150×90 ＋ A6 卡", 1, 80, "印刷廠／蝦皮",
     "https://shopee.tw/search?keyword=%E7%89%9B%E7%9A%AE%E7%B4%99%E7%9B%92%20%E5%AE%9A%E5%88%B6", ""),
]

UPGRADES = [
    ("立體聲（2×3W）", "PCM5102A I2S DAC ＋ PAM8403 2×3W 擴大板", 210,
     "需要兩顆單體分別發聲；代價是多了類比雜訊與上電爆音要處理"),
    ("觸控螢幕", "2.8 吋 ST7789 電容觸控版", 120, "取代旋鈕，直接點畫面切換模式"),
    ("雙倍電量", "第二顆 18650 ＋ 並聯電池座", 175, "中音量續航 3h → 6h，重量 +45g"),
    ("真皮革／木紋貼皮", "PVC 貼皮 300×200", 120, "外殼列印後貼皮，質感直接升級"),
]

MARGIN = 0.50      # 目標毛利
OVERHEAD = 1.10    # BOM → 成本（耗損、運費、備品）

def twd(n):
    return f"NT${n:,.0f}"

def main():
    lines = []
    A = lines.append
    bom = sum(q * p for _, _, _, q, p, *_ in ITEMS)
    cost = bom * OVERHEAD
    price = cost / (1 - MARGIN)
    import math
    price_round = int(math.ceil(price / 100.0) * 100 - 20)   # 無條件進位到百元再減 20（尾數 .980）

    A("# BOM 採購清單 · miniMac Speaker MM96\n")
    A("> 這份清單由 `tools/gen_bom.py` 產生，價格改那裡、重跑就重算。單價為 2026-11 台灣零售／淘寶常見價，")
    A("> 實際下單請以賣場當下標價為準。\n")
    A(f"- 直接材料（BOM）合計：**{twd(bom)}**")
    A(f"- 含耗損／運費（BOM × {OVERHEAD}）＝ **成本 {twd(cost)}**")
    A(f"- 建議售價（毛利 {int(MARGIN*100)}%）： **{twd(price_round)}**（實算毛利 {100*(1-cost/price_round):.1f}%）\n")
    A("## 一、必要零件\n")
    A("| # | 分類 | 品名 | 規格／型號 | 數量 | 單價 | 小計 | 採購處 | 連結 |")
    A("|---|------|------|------------|------|------|------|--------|------|")
    for i, (cat, name, spec, qty, unit, shop, url, note) in enumerate(ITEMS, 1):
        A(f"| {i} | {cat} | {name} | {spec} | {qty} | {twd(unit)} | {twd(qty*unit)} | {shop} | [開賣場]({url}) |")
    A("")
    A("## 二、選配升級\n")
    A("| 項目 | 內容 | 加價 | 說明 |")
    A("|------|------|------|------|")
    for name, what, add, why in UPGRADES:
        A(f"| {name} | {what} | {twd(add)} | {why} |")
    A("")
    A("## 三、關鍵採購提醒\n")
    A("1. **ESP32 一定要挑「經典 ESP32-WROOM-32」**：ESP32-S3／C3／C6 沒有 Bluetooth Classic（A2DP），")
    A("   只能做 BLE，接不上手機的藍牙音樂。這一項買錯整台不能用。")
    A("2. **同一家買齊省運費**：傑森創工同時有 ESP32、2.8 吋螢幕、MAX98357A、IP5306；")
    A("   單體與被動輻射器走蝦皮／淘寶會便宜 40%，但要多等 7–14 天。")
    A("3. **單體兩顆串聯成 8Ω**：4Ω＋4Ω 串聯＝8Ω，MAX98357A 在 5V 下給 1.6W，")
    A("   不用第二顆擴大器就有立體雙出音孔；並聯成 2Ω 會超過晶片建議負載，不要這樣接。")
    A("4. **電池一定要有保護板**：18650 裸電芯沒有過放保護，IP5306 模組有，但電芯本身出事不會救你。")
    A("5. **氣密決定低音**：被動輻射器要把箱體分前後腔，泡棉條沒貼好，低頻會直接漏光。")
    A("")
    A("## 四、成本結構\n")
    A("| 項目 | 金額 | 佔比 |")
    A("|------|------|------|")
    cat_tot = {}
    for cat, _, _, q, p, *_ in ITEMS:
        cat_tot[cat] = cat_tot.get(cat, 0) + q * p
    for cat, v in sorted(cat_tot.items(), key=lambda x: -x[1]):
        A(f"| {cat} | {twd(v)} | {100*v/bom:.0f}% |")
    A(f"| **材料合計** | **{twd(bom)}** | 100% |")
    A(f"| 耗損／運費 10% | {twd(bom*0.10)} | |")
    A(f"| **製造成本** | **{twd(cost)}** | |")
    A(f"| 售價 {twd(price_round)} 的毛利 | {twd(price_round-cost)} | {100*(1-cost/price_round):.1f}% |")

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BOM.md")
    open(out, "w").write("\n".join(lines) + "\n")
    print(f"BOM 合計 {twd(bom)} / 成本 {twd(cost)} / 售價 {twd(price_round)} / 毛利 {100*(1-cost/price_round):.1f}%")
    print("寫入", out)

if __name__ == "__main__":
    main()
