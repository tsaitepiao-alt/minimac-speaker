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
| 採購清單 | [BOM.md](BOM.md) | 每項都有賣場連結與單價 |
| 韌體 | [`firmware/`](firmware/) | ESP32 A2DP＋頻譜＋歌詞＋旋鈕（已通過編譯：1.22 MB / 38%） |

## 尺寸核對（自動計算，不是目測）

外觀 96×118×132，壁厚 2.4 → 內腔 **91.2 × 113.2 × 129.6**。所有零件包圍盒兩兩比對：

```
2.8吋螢幕模組  82.5 × 5 × 50  貼面板內側       ✓
單體 L/R       Ø40 × 22      下射，籃框貼底板   ✓
ESP32 DevKit   51 × 12 × 28  立放螢幕下        ✓
IP5306 模組    25 × 25 × 8   平放，閃單體      ✓
MAX98357A      22 × 16 × 5   平放              ✓
18650 電池座   21.5 × 20 × 77 立放背右         ✓
被動輻射器     50 × 14 × 70  背板內側          ✓
────────────────────────────────────────────
干涉 0 件 · 超界 0 件
```

數字由 `cad/build_minimac.py` 算出並寫進 `cad/export/dims.json`，網頁直接讀同一份檔案，不是手打的。

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
