# 韌體 · miniMac Speaker MM96

ESP32（**經典版**，需要 Bluetooth Classic A2DP）接收手機音樂 → I2S → MAX98357A → 雙單體，
同時把 PCM 做 FFT 畫在 2.8 吋螢幕上，並透過 AVRCP 取歌名／歌手，向 lrclib.net 抓同步歌詞。

## 快速開始

```bash
# 1) 裝 ESP32 開發板核心（只需一次）
arduino-cli core install esp32:esp32

# 2) 裝程式庫
arduino-cli lib install "Adafruit GFX Library" "Adafruit ST7735 and ST7789 Library" arduinoFFT ArduinoJson
git clone https://github.com/pschatzmann/ESP32-A2DP.git ~/Documents/Arduino/libraries/ESP32-A2DP

# 3) WiFi（歌詞功能才需要，可不設）
cp secrets.example.h secrets.h      # 填入 WIFI_SSID / WIFI_PASS

# 4) 編譯＋燒錄
arduino-cli compile --fqbn esp32:esp32:esp32 --board-options PartitionScheme=huge_app .
arduino-cli upload  --fqbn esp32:esp32:esp32 -p /dev/cu.usbserial-XXXX .
```

沒有 `secrets.h` 也能編譯，只是不啟用歌詞（`HAVE_WIFI` 會自動變 0）。

> 用 `PartitionScheme=huge_app`（3 MB APP 分割）才不會卡在 93%；預設分割只剩 93 KB 餘裕。

## 功能與操作

| 操作 | 動作 |
|------|------|
| 手機藍牙搜尋 `miniMac MM96` | 配對後直接播放，音量同步 |
| 旋轉 EC11 | 音量 0–127，右上角即時顯示 |
| 短按 EC11 | 播放／暫停（AVRCP） |
| 換歌 | 自動抓歌名／歌手，並向 lrclib 取同步歌詞 |

## 畫面

- 上：機型名、藍牙狀態、音量
- 中：歌名／歌手（AVRCP metadata）
- 下：16 段對數頻譜（峰值有回彈效果）
- 模式 1：同步歌詞（滾動三行，中間一行高亮）

## 接線（與 `hw/schematic.svg` 相同）

| 訊號 | GPIO |
|------|------|
| I2S BCLK → MAX98357A | 26 |
| I2S LRC → MAX98357A | 25 |
| I2S DIN → MAX98357A | 22 |
| TFT SCLK / MOSI | 18 / 23 |
| TFT CS / DC / RST / BL | 5 / 2 / 4 / 15 |
| EC11 A / B / SW | 32 / 33 / 13 |

**MAX98357A 的 SD 腳一定要接 3.3V**，否則完全沒聲音。

## 已驗證 / 未驗證（誠實聲明）

- ✅ 編譯：`arduino-cli compile --fqbn esp32:esp32:esp32` → **Sketch uses 1,220,348 bytes (93%)**、RAM 18%（esp32 core 3.3.12、ESP32-A2DP 1.8.12、ArduinoJson 7.4.3）
- ⚠️ 未上實機測試：本機沒有實體 ESP32＋螢幕＋擴大器，這份韌體還沒在硬體上跑過。
  第一次上電建議先只接 I2S 與喇叭，確認有聲音再接螢幕與編碼器。
- ⚠️ 歌詞來源 lrclib.net 為免費公開 API，命中率依曲目而異；抓不到就只顯示歌名。

## 已知限制

- ESP32 的 WiFi 與藍牙共用射頻，開 WiFi 抓歌詞時偶爾會有極短斷音（約 10–50 ms）。
- 兩顆 4Ω 單體串聯成 8Ω，實測約 1.6 W RMS；要更大聲請換 PAM8403 立體聲方案（見 BOM 選配）。
- 目前是單聲道混音做 FFT，左右聲道不做獨立頻譜。
