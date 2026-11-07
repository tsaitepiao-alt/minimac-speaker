# miniMac Speaker MM96 · 迷你麥金塔造型藍牙音響

外觀致敬 1980 年代一體成型電腦（Macintosh 128K 輪廓，約 40% 縮小），本體是
**藍牙 5.0 A2DP 喇叭 + 2.8 吋彩色螢幕**：播歌時顯示頻譜與歌詞，平常是桌面復古擺件。

- 外觀尺寸：**96 × 118 × 132 mm**（不含腳 8 mm）
- 重量：約 480 g（含電池）
- 出聲：2 × 40 mm 全音域（下射）＋ 50×70 mm 被動輻射器，實測 1.6 W RMS
- 續航：中音量約 3 小時（18650 3000 mAh）
- 成本：材料 NT$1,603 → 製造成本 NT$1,763 → 建議售價 **NT$3,580**（毛利 50.7%）

## 交付物

| 項目 | 位置 | 說明 |
|------|------|------|
| 3D 互動爆炸圖 | [index.html](index.html)（GitHub Pages） | 可旋轉、爆炸、即時尺寸核對 |
| 機構 STEP／STL | [`cad/export/`](cad/export/) | body／faceplate／knob／pr_clamp＋assembly |
| 參數化建模程式 | [`cad/build_minimac.py`](cad/build_minimac.py) | build123d，改尺寸重跑即重新出圖 |
| 電路接線圖 | [`hw/schematic.svg`](hw/schematic.svg) · [PNG](hw/schematic.png) | 全中文標註 |
| 外觀工程圖 | [`hw/drawing.svg`](hw/drawing.svg) · [PNG](hw/drawing.png) | 三視圖＋尺寸＋公差＋圖框 |
| 採購清單 | [BOM.md](BOM.md) | 每項都有賣場連結與單價 |
| 韌體 | [`firmware/`](firmware/) | ESP32 A2DP＋頻譜＋歌詞＋旋鈕（已通過編譯：1.22 MB / 38%） |

## 尺寸核對（自動計算，不是目測）

外觀 96×118×132，壁厚 2.4 → 內腔 **91.2 × 113.2 × 127.2**。
門面比例照 Macintosh 128K：螢幕窗 62×47，上方額頭 **41.5**、下方下巴 **43.5**。

```
2.8吋螢幕模組  82.5 × 5 × 50   貼面板內側對窗     ✓
單體 L/R       Ø40 × 22       下射，籃框貼底板   ✓
ESP32 DevKit   51 × 12 × 28   立放螢幕上方後側   ✓
IP5306 模組    25 × 25 × 8    平放左下           ✓
MAX98357A      22 × 16 × 5    平放右下           ✓
18650 電池座   21.5 × 20 × 77 立放中央           ✓
被動輻射器     50 × 14 × 70   背板內側           ✓
──────────────────────────────────────────────
干涉 0 件 · 超界 0 件
```

數字由 `cad/build_minimac.py` 算出並寫進 `cad/export/dims.json`，網頁與工程圖讀同一份檔案。


## 變體 B：MiniBook MM96-L（迷你筆電，同電路換殼）

- 3D 檢視：https://tsaitepiao-alt.github.io/minimac-speaker/laptop.html （可拖滑桿調開蓋角度 0–130°）
- 零件：`cad/export/laptop_base_shell.stl`／`laptop_bottom_plate.stl`／`laptop_lid.stl`／`laptop_button.stl`
- 合起 **150 × 110 × 37 mm**；底殼 150×110×28、上蓋 150×100×9
- 螢幕窗 **97×56**，裝 4.3 吋 480×272 IPS（模組 105.8×67.2×4.5）
- 鉸鏈：Ø3 鋼軸 ×130 貫穿，開蓋 110°（範圍 0–130°）
- 聲學：2 × Ø40 下射單體（同一顆 MAX98357A、串聯 8Ω），底板 Ø38 出音孔
- 鍵盤：4×12 凹槽鍵位（裝飾／可雷雕），橘色電源鈕 Ø10
- 驗證：7 個零件包圍盒比對 **干涉 0、超界 0**；4 件 STL 全部 watertight

變體 B 相對主體追加成本：4.3" 螢幕 +NT$120、Ø3 鋼軸 +NT$20、M2 螺絲 +NT$24、底板列印料 +NT$24
→ 材料約 NT$1,791、成本 NT$1,970、建議售價 **NT$3,980**（毛利 50.5%）。

> 誠實說明：鉸鏈只做幾何干涉驗證，**沒有做扭力／壽命測試**；Ø3 鋼軸需另加摩擦片或改用阻尼鉸鏈才能停在任意角度。

## 驗證狀態（`./tools/check.sh`）

```
① 機構建模與尺寸核對    干涉/超界：無 → CAD: OK
② STL 有效性            body/faceplate/knob/pr_clamp 全部 watertight=True、單一實體
③ 韌體編譯              1,220,380 bytes (38%, huge_app)、RAM 18% → FIRMWARE: OK
結果：CHECK OK
```

## 列印建議

- 材料 **PETG**（PLA 夏天車內或大音量震動會軟）
- 層高 0.2 mm、牆厚 4 圈、填充 20%
- body 需支撐（被動輻射器開窗處）；faceplate 平放不用支撐
- 列印件合計約 200 g / 約 9 小時

## 組裝順序

1. 底板內側鎖兩顆單體（Ø38 孔對位），周圍貼泡棉條做氣密
2. 背板內側裝被動輻射器壓框，同樣貼泡棉
3. 電池座、IP5306、ESP32、MAX98357A 依 `hw/schematic.svg` 接線
4. 螢幕模組貼在面板內側（對齊 60×45 窗），排線朝下
5. EC11 穿過面板 Ø7.6 孔，鎖上旋鈕
6. 面板四顆 M2×8 鎖進機身凸柱
7. 燒錄韌體、藍牙配對測試

## 合規與安全

- 內含 18650 鋰電池：**必須使用有保護板的電芯**，且不可無人看管充電。若要販售，需符合 BSMI 鋰電池相關規定與商品檢驗。
- 本設計為概念原型，非量產模具件；外殼為 FDM 列印，未做跌落與耐燃測試。
- 藍牙射頻模組（ESP32）為現成模組，販售前需確認 NCC 認證標籤與模組使用授權。

## 重跑

```bash
cd minimac-speaker
./tools/check.sh                          # 一鍵：建模→尺寸核對→STL 檢查→韌體編譯
.venv/bin/python cad/build_minimac.py     # 出 STEP／STL／dims.json
.venv/bin/python cad/render.py            # 出四視圖 PNG
python3 tools/gen_bom.py                  # 重算 BOM 與售價
python3 tools/gen_schematic.py            # 重出電路圖 SVG
```
