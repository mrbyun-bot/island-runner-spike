"""작업 중 확인용: 지정한 캐릭터를 240·108·36px 로 검정 바탕에 놓고 한 장으로 본다.
python3 preview.py dog [rabbit ...] → /tmp 이 아니라 스크래치 폴더에 저장(인자 2번째: 출력 경로)."""
import sys, os
from PIL import Image
from kit import Canvas, render_many
import chars

out = os.environ.get("PREV", "preview.png")
names = sys.argv[1:] or list(chars.CHARS)
tmp = os.path.join(os.path.dirname(out) or ".", "_prev")
os.makedirs(tmp, exist_ok=True)
jobs = []
for n in names:
    for size, lod in ((240, "full"), (108, "full"), (36, "small")):
        cv = Canvas(size, lod); chars.CHARS[n](cv)
        jobs.append((cv.svg(), f"{tmp}/{n}_{size}.png", size))
render_many(jobs)
W = 400
sheet = Image.new("RGB", (W * len(names), 260), "black")
for i, n in enumerate(names):
    for size, x, y in ((240, 0, 10), (108, 250, 10), (36, 250, 140)):
        im = Image.open(f"{tmp}/{n}_{size}.png")
        sheet.paste(im, (i * W + x, y), im)
    big36 = Image.open(f"{tmp}/{n}_36.png").resize((108, 108), Image.NEAREST)
    sheet.paste(big36, (i * W + 290, 140), big36)
sheet.save(out)
print(out)
