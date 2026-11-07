#!/usr/bin/env python3
"""用 Gemini 影像模型產出產品概念圖（設計定調用）。
用法：python3 tools/gen_concept.py "提示詞" 輸出檔名
"""
import base64, json, os, sys, urllib.request

KEY = None
for line in open(os.path.expanduser("~/.hermes/.env")):
    if line.startswith("GEMINI_API_KEY="):
        KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
if not KEY:
    sys.exit("找不到 GEMINI_API_KEY")

MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
prompt = sys.argv[1]
out = sys.argv[2]

body = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"responseModalities": ["IMAGE"]},
}
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=180) as r:
    data = json.load(r)

saved = 0
for i, cand in enumerate(data.get("candidates", [])):
    for j, part in enumerate(cand.get("content", {}).get("parts", [])):
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            path = out if saved == 0 else out.replace(".png", f"_{saved}.png")
            open(path, "wb").write(base64.b64decode(inline["data"]))
            print("寫入", path, os.path.getsize(path), "bytes")
            saved += 1
        elif part.get("text"):
            print("模型文字：", part["text"][:300])

if not saved:
    print("沒有回傳影像：", json.dumps(data)[:600])
