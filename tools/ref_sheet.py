"""把使用者提供的多張參考圖拼成一張對照表（標 A/B/C/D），確認每張是哪個角度/版本。"""
import os
from PIL import Image, ImageDraw, ImageFont

SRC = "/Users/william/.hermes/profiles/home/cache/documents/native-inputs"
files = [
    ("A  商品頁（正面）", "1d440a4dcee1110dc44f46d97c18c393975c3763be5344f4c5ee2915b3c09ca8/img_502788c1f4f3.jpg"),
    ("B  桌面情境（貼紙＋歌詞同步）", "1b8c2f973f47b48469d7fcace230166fd8b865a7716d80b953426dee6e08563e/img_9f9c96c9f900.jpg"),
    ("C  手持高角度（方螢幕＋2x2鍵）", "dc048254966fa10119d393f6b441b83adb52276f2ebe8ba414013923eb785c12/img_ba0dc4e0b11e.jpg"),
    ("D  手持正面（膠囊螢幕＋底座）", "785622a5a591ac6a48c69563372a253ce599ac605ea534dc433ab00ab1caa247/img_5e252c6b53e3.jpg"),
]
H = 620
tiles = []
for label, rel in files:
    p = os.path.join(SRC, rel)
    im = Image.open(p).convert("RGB")
    im = im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
    tiles.append((label, im))

font = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 22, index=0)
pad = 12
Wtot = sum(t.width for _, t in tiles) + pad * (len(tiles) + 1)
canvas = Image.new("RGB", (Wtot, H + 56), (255, 255, 255))
d = ImageDraw.Draw(canvas)
x = pad
for label, im in tiles:
    canvas.paste(im, (x, 44))
    d.text((x + 2, 12), label, fill=(20, 24, 30), font=font)
    x += im.width + pad

out = os.path.expanduser("~/products/minimac-speaker/cad/export/ref_sheet.png")
canvas.save(out)
print(out, canvas.size)
