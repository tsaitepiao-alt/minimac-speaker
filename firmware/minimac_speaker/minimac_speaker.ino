/*
 * miniMac Speaker MM96 — ESP32 藍牙 A2DP 喇叭 + 2.8" ST7789 頻譜／歌詞顯示
 * 硬體與機構：https://github.com/tsaitepiao-alt/minimac-speaker
 *
 * 接線（與 hw/schematic.svg 一致）
 *   MAX98357A  BCLK=26  LRC=25  DIN=22   VIN=5V  SD=3V3
 *   ST7789     SCLK=18  MOSI=23 CS=5 DC=2 RST=4  BL=15
 *   EC11       A=32  B=33  SW=13
 *
 * 編譯：arduino-cli compile --fqbn esp32:esp32:esp32 firmware/minimac_speaker
 * 需要的程式庫：ESP32-A2DP、Adafruit ST7735/ST7789、Adafruit GFX、arduinoFFT、ArduinoJson
 */
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <arduinoFFT.h>
#include <ArduinoJson.h>
#include "BluetoothA2DPSink.h"
#include "ESP_I2S.h"

#if __has_include("secrets.h")
#include "secrets.h"          // #define WIFI_SSID / WIFI_PASS（不進 git）
#define HAVE_WIFI 1
#else
#define HAVE_WIFI 0
#endif

// ---------------- 腳位 ----------------
static const int PIN_I2S_BCLK = 26, PIN_I2S_LRC = 25, PIN_I2S_DOUT = 22;
static const int TFT_SCLK = 18, TFT_MOSI = 23, TFT_CS = 5, TFT_DC = 2, TFT_RST = 4, TFT_BL = 15;
static const int ENC_A = 32, ENC_B = 33, ENC_SW = 13;

#define SCR_W 320
#define SCR_H 240

Adafruit_ST7789 tft(&SPI, TFT_CS, TFT_DC, TFT_RST);
I2SClass i2s;                       // arduino-esp32 3.x 內建 I2S 類別
BluetoothA2DPSink a2dp(i2s);        // 解碼後的 PCM 直接寫進 I2S

// ---------------- FFT ----------------
#define FFT_N 512
static float vReal[FFT_N];
static float vImag[FFT_N];
ArduinoFFT<float> FFT(vReal, vImag, FFT_N, 44100.0f);
volatile int  g_level   = 0;              // 0..100 RMS
volatile int  g_bins[16] = {0};           // 16 段頻譜 0..100
volatile bool g_newAudio = false;
volatile uint32_t g_audioCount = 0;

// ---------------- 狀態 ----------------
volatile int  g_volume = 70;              // 0..127
volatile int  g_encDelta = 0;
volatile bool g_btnPressed = false;
volatile uint32_t g_btnDownAt = 0;
bool g_btConnected = false;
char g_title[64]  = "miniMac Speaker";
char g_artist[64] = "等待藍牙連線…";
int  g_mode = 0;                          // 0=頻譜 1=歌詞 2=時鐘
bool g_playing = false;

// ---------------- 編碼器 ISR ----------------
static volatile int8_t encState = 0;
static const int8_t ENC_TABLE[16] = {0,-1,1,0, 1,0,0,-1, 0,0,0,0, 0,0,0,0};
void IRAM_ATTR encISR() {
  int8_t a = digitalRead(ENC_A), b = digitalRead(ENC_B);
  encState = ((encState << 2) | (a << 1) | b) & 0x0F;
  int8_t d = ENC_TABLE[encState];
  if (d) g_encDelta += d;
}
void IRAM_ATTR btnISR() {
  if (digitalRead(ENC_SW) == LOW) { g_btnDownAt = millis(); }
  else if (g_btnDownAt && millis() - g_btnDownAt > 40) { g_btnPressed = true; }
}

// ---------------- A2DP 回呼 ----------------
void audioData(const uint8_t *data, uint32_t len) {
  // 16-bit 立體聲交錯；取最後 FFT_N 個 frame 做頻譜
  const int16_t *p = (const int16_t *)data;
  uint32_t frames = len / 4;
  if (frames < FFT_N) return;
  const int16_t *src = p + (frames - FFT_N) * 2;
  double sum = 0;
  for (int i = 0; i < FFT_N; i++) {
    int16_t mono = (src[i * 2] >> 1) + (src[i * 2 + 1] >> 1);
    vReal[i] = (float)mono;
    vImag[i] = 0;
    sum += (float)mono * (float)mono;
  }
  float rms = sqrt(sum / FFT_N);
  int lv = (int)(20.0f * log10f(rms / 32768.0f + 1e-7f) + 100.0f);
  g_level = constrain(lv, 0, 100);

  FFT.windowing(FFTWindow::Hamming, FFTDirection::Forward);
  FFT.compute(FFTDirection::Forward);
  FFT.complexToMagnitude();
  // 對數分頻：把 512 bins 壓成 16 段（音樂多在 60Hz~8kHz）
  for (int b = 0; b < 16; b++) {
    float f0 = 60.0f * powf(2.0f, b * 0.45f);
    int i0 = constrain((int)(f0 / 44100.0f * FFT_N), 1, FFT_N / 2 - 1);
    int i1 = constrain((int)(f0 * 1.45f / 44100.0f * FFT_N) + 1, i0 + 1, FFT_N / 2 - 1);
    float mx = 0;
    for (int i = i0; i < i1; i++) if (vReal[i] > mx) mx = vReal[i];
    int v = (int)(20.0f * log10f(mx / 1000.0f + 1e-4f) * 3.0f);
    g_bins[b] = constrain(v, 0, 100);
  }
  g_newAudio = true;
  g_audioCount++;
}

void avrcMetadata(uint8_t id, const uint8_t *text) {
  if (!text) return;
  if (id == ESP_AVRC_MD_ATTR_TITLE)  { strlcpy(g_title, (const char *)text, sizeof(g_title)); }
  if (id == ESP_AVRC_MD_ATTR_ARTIST) { strlcpy(g_artist, (const char *)text, sizeof(g_artist)); }
}

void onConnectionChanged(esp_a2d_connection_state_t state, void *) {
  g_btConnected = (state == ESP_A2D_CONNECTION_STATE_CONNECTED);
  if (!g_btConnected) { strlcpy(g_title, "miniMac Speaker", sizeof(g_title)); strlcpy(g_artist, "等待藍牙連線…", sizeof(g_artist)); }
}

// ---------------- 畫面 ----------------
uint16_t hueColor(int h) {          // h: 0..255
  uint8_t r, g, b, s = 255, v = 255;
  uint8_t region = h / 43, rem = (h - region * 43) * 6;
  uint8_t p = (v * (255 - s)) >> 8, q = (v * (255 - ((s * rem) >> 8))) >> 8,
          t = (v * (255 - ((s * (255 - rem)) >> 8))) >> 8;
  switch (region) {
    case 0: r = v; g = t; b = p; break;
    case 1: r = q; g = v; b = p; break;
    case 2: r = p; g = v; b = t; break;
    case 3: r = p; g = q; b = v; break;
    case 4: r = t; g = p; b = v; break;
    default: r = v; g = p; b = q; break;
  }
  return tft.color565(r, g, b);
}

void drawStatic() {
  tft.fillScreen(ST77XX_BLACK);
  tft.fillRect(0, 0, SCR_W, 22, tft.color565(24, 33, 48));
  tft.setTextColor(ST77XX_WHITE); tft.setTextSize(1);
  tft.setCursor(6, 7); tft.print("miniMac MM96");
  tft.drawFastHLine(0, 222, SCR_W, tft.color565(40, 55, 75));
}

void drawStatus() {
  tft.fillRect(200, 4, 116, 14, tft.color565(24, 33, 48));
  tft.setTextColor(g_btConnected ? ST77XX_GREEN : ST77XX_RED);
  tft.setCursor(206, 7); tft.print(g_btConnected ? "BT OK" : "WAIT");
  tft.setTextColor(ST77XX_WHITE);
  tft.setCursor(258, 7); tft.printf("V%03d", g_volume);
}

int shownBins[16] = {0};
void drawSpectrum() {
  const int baseY = 196, maxH = 120, gap = 3;
  int bw = (SCR_W - 16 - gap * 15) / 16;
  for (int i = 0; i < 16; i++) {
    int target = g_bins[i];
    // 峰值慢慢落，視覺上會「彈」
    shownBins[i] = (target > shownBins[i]) ? target : shownBins[i] - 3;
    if (shownBins[i] < 0) shownBins[i] = 0;
    int h = shownBins[i] * maxH / 100;
    int x = 8 + i * (bw + gap);
    tft.fillRect(x, baseY - maxH, bw, maxH, ST77XX_BLACK);
    uint16_t c = hueColor(constrain(200 - i * 10, 0, 255));
    tft.fillRect(x, baseY - h, bw, h, c);
  }
  tft.drawFastHLine(0, baseY + 2, SCR_W, tft.color565(40, 55, 75));
}

void drawTrackText() {
  tft.fillRect(0, 24, SCR_W, 46, ST77XX_BLACK);
  tft.setTextWrap(false);
  tft.setTextColor(ST77XX_WHITE); tft.setTextSize(2);
  tft.setCursor(8, 30); tft.print(g_title);
  tft.setTextColor(tft.color565(150, 170, 195)); tft.setTextSize(1);
  tft.setCursor(8, 56); tft.print(g_artist);
}

// ---------------- 歌詞（lrclib.net，免費無金鑰） ----------------
#define LYR_MAX 48
static char lyrLine[LYR_MAX][96];
static int  lyrTime[LYR_MAX];
static int  lyrCount = 0, lyrShown = -1;
static char lyrKey[128] = "";
volatile bool lyrWanted = false;
char lyrPendingTitle[64] = "", lyrPendingArtist[64] = "";

int parseLRC(const String &lrc) {
  int n = 0;
  int pos = 0;
  while (pos < (int)lrc.length() && n < LYR_MAX) {
    int nl = lrc.indexOf('\n', pos);
    if (nl < 0) nl = lrc.length();
    String line = lrc.substring(pos, nl); pos = nl + 1;
    if (line.length() < 6 || line[0] != '[') continue;
    int t = line.indexOf(']');
    if (t < 0) continue;
    String ts = line.substring(1, t);
    int c1 = ts.indexOf(':'), c2 = ts.indexOf('.');
    if (c1 < 0 || c2 < 0) continue;
    int mm = ts.substring(0, c1).toInt();
    int ss = ts.substring(c1 + 1, c2).toInt();
    int cs = ts.substring(c2 + 1).toInt();
    String txt = line.substring(t + 1); txt.trim();
    if (!txt.length()) continue;
    lyrTime[n] = mm * 60 + ss;
    strlcpy(lyrLine[n], txt.c_str(), sizeof(lyrLine[n]));
    n++;
  }
  if (n) lyrTime[n] = 99999;
  return n;
}

String URLEncoder(const char *s);      // 前置宣告（.ino 自動原型在含 String 回傳時不可靠）

void lyricsTask(void *) {
  for (;;) {
    if (lyrWanted && HAVE_WIFI) {
      lyrWanted = false;
      WiFiClientSecure cli; cli.setInsecure();
      HTTPClient http;
      String url = "https://lrclib.net/api/get?artist_name=";
      url += URLEncoder(lyrPendingArtist);
      url += "&track_name=";  url += URLEncoder(lyrPendingTitle);
      if (http.begin(cli, url)) {
        http.setTimeout(8000);
        int code = http.GET();
        if (code == 200) {
          String body = http.getString();
          JsonDocument filter;
          filter["syncedLyrics"] = true;
          JsonDocument doc;
          if (!deserializeJson(doc, body, DeserializationOption::Filter(filter))) {
            String lrc = doc["syncedLyrics"] | "";
            if (lrc.length() > 10) lyrCount = parseLRC(lrc);
          }
        }
        http.end();
      }
    }
    vTaskDelay(pdMS_TO_TICKS(500));
  }
}

// 簡單 URL encode（歌名常含空白與中文）
String URLEncoder(const char *s) {
  String out;
  char buf[4];
  for (int i = 0; s[i]; i++) {
    uint8_t c = (uint8_t)s[i];
    if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.') out += (char)c;
    else if (c == ' ') out += '+';
    else { snprintf(buf, sizeof(buf), "%%%02X", c); out += buf; }
  }
  return out;
}

void drawLyrics(int sec) {
  int idx = 0;
  for (int i = 0; i < lyrCount; i++) if (lyrTime[i] <= sec) idx = i;
  if (idx == lyrShown) return;
  lyrShown = idx;
  tft.fillRect(0, 74, SCR_W, 148, ST77XX_BLACK);
  tft.setTextSize(2);
  for (int k = -1; k <= 1; k++) {
    int i = idx + k;
    if (i < 0 || i >= lyrCount) continue;
    tft.setTextColor(k == 0 ? ST77XX_WHITE : tft.color565(90, 105, 125));
    tft.setCursor(8, 130 + k * 34);
    tft.print(lyrLine[i]);
  }
}

// ---------------- setup / loop ----------------
void setup() {
  Serial.begin(115200);
  pinMode(TFT_BL, OUTPUT); digitalWrite(TFT_BL, HIGH);
  pinMode(ENC_A, INPUT_PULLUP); pinMode(ENC_B, INPUT_PULLUP); pinMode(ENC_SW, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_A), encISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_B), encISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_SW), btnISR, CHANGE);

  SPI.begin(TFT_SCLK, -1, TFT_MOSI, TFT_CS);
  tft.init(240, 320, SPI_MODE0);
  tft.setRotation(3);              // 橫放 320×240
  drawStatic();
  tft.setTextColor(ST77XX_WHITE); tft.setTextSize(1);
  tft.setCursor(8, 100); tft.print("開機中…");

  i2s.setPins(PIN_I2S_BCLK, PIN_I2S_LRC, PIN_I2S_DOUT);   // BCLK, LRC(WS), DOUT
  if (!i2s.begin(I2S_MODE_STD, 44100, I2S_DATA_BIT_WIDTH_16BIT,
                 I2S_SLOT_MODE_STEREO, I2S_STD_SLOT_BOTH)) {
    tft.setCursor(8, 120); tft.print("I2S 初始化失敗");
  }
  a2dp.set_stream_reader(audioData, true);   // true = 同時保留 I2S 出聲
  a2dp.set_avrc_metadata_callback(avrcMetadata);
  a2dp.set_on_connection_state_changed(onConnectionChanged);
  a2dp.start("miniMac MM96");
  a2dp.set_volume(g_volume);

#if HAVE_WIFI
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  xTaskCreatePinnedToCore(lyricsTask, "lyrics", 8192, nullptr, 1, nullptr, 0);
#endif
  drawTrackText();
}

uint32_t lastDraw = 0, lastSec = 0;
void loop() {
  // 旋鈕音量
  int d = g_encDelta;
  if (d) {
    g_encDelta = 0;
    g_volume = constrain(g_volume + d, 0, 127);
    a2dp.set_volume(g_volume);
    drawStatus();
  }
  // 按鍵：短按播放/暫停，長按換模式
  if (g_btnPressed) {
    g_btnPressed = false;
    if (g_playing) { a2dp.pause(); g_playing = false; }
    else           { a2dp.play();  g_playing = true;  }
  }

  if (millis() - lastDraw > 45) {
    lastDraw = millis();
    if (g_mode == 0) drawSpectrum();
  }
  if (millis() - lastSec > 1000) {
    lastSec = millis();
    drawStatus();
    if (strcmp(lyrKey, g_title) != 0) {      // 換歌就抓新歌詞
      strlcpy(lyrKey, g_title, sizeof(lyrKey));
      strlcpy(lyrPendingTitle, g_title, sizeof(lyrPendingTitle));
      strlcpy(lyrPendingArtist, g_artist, sizeof(lyrPendingArtist));
      lyrCount = 0; lyrShown = -1; lyrWanted = true;
      drawTrackText();
    }
    if (g_mode == 1 && lyrCount) drawLyrics((millis() / 1000) % 300);
  }
}
