"""비교판 만들기 (검정 바탕).
- A 렌더(480px)를 240·108 로 줄이고(Lanczos + 약한 선명화) 각 폴더에 PNG 로 둔다.
- hamster_compare.png : 지금(임시) / A / B / C 햄스터를 36px 실제, 108px(@3x), 240px, 아일랜드 모형으로 비교
- family_A/B/C.png, family_all.png : 햄스터·펭귄·로켓을 같은 조건으로
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OLD = os.path.abspath(os.path.join(R, "..", "..", "Assets", "frames", "hamster_still@3x.png"))
FONT = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
FONT_B = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
if not os.path.exists(FONT_B):
    FONT_B = FONT
DIRS = [("A_3d", "A 3D 장난감"), ("B_sticker", "B 윤곽선 스티커"), ("C_flat", "C 면 분할")]
CHARS = [("hamster", "햄스터"), ("penguin", "펭귄"), ("rocket", "로켓")]
BG = (0, 0, 0, 255)
INK = (200, 200, 200, 255)
DIM = (120, 120, 120, 255)
ORANGE = (255, 159, 10, 255)


def f(sz, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, sz)


def down(img, size):
    out = img.resize((size, size), Image.LANCZOS)
    return out.filter(ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=1)) if size <= 120 else out


# 1) A 렌더를 규격 크기로
for n, _ in CHARS:
    src = os.path.join(R, "A_3d", "src", "render", f"{n}_480.png")
    if os.path.exists(src):
        im = Image.open(src).convert("RGBA")
        down(im, 240).save(os.path.join(R, "A_3d", f"{n}_240.png"), optimize=True)
        down(im, 108).save(os.path.join(R, "A_3d", f"{n}_108.png"), optimize=True)


def load(d, n, sz):
    return Image.open(os.path.join(R, d, f"{n}_{sz}.png")).convert("RGBA")


def to36(im108):
    return im108.resize((36, 36), Image.LANCZOS)


def band(draw, x, y, s):
    """축소 칸에서 실제로 보이는 높이(약 26/36) 안내선"""
    top = y + round(s * 15 / 108)
    bot = y + round(s * 93 / 108)
    for xx in range(x, x + s, 6):
        draw.line([(xx, top), (min(xx + 3, x + s), top)], fill=(70, 70, 70, 255))
        draw.line([(xx, bot), (min(xx + 3, x + s), bot)], fill=(70, 70, 70, 255))


def island(im108, scale):
    """축소 아일랜드 모형: 왼쪽 칸 그림(위아래 잘림) + 오른쪽 주황 숫자. scale=1 이면 pt 그대로, 3 이면 @3x"""
    h = 37 * scale
    w = 200 * scale
    pill = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(pill)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(0, 0, 0, 255), outline=(38, 38, 40, 255), width=max(1, scale // 2))
    s = 36 * scale
    ch = im108.resize((s, s), Image.LANCZOS) if s != 108 else im108
    vis_top, vis_bot = round(s * 15 / 108), round(s * 93 / 108)
    crop = ch.crop((0, vis_top, s, vis_bot))
    pill.alpha_composite(crop, (int(7 * scale), (h - crop.height) // 2))
    d.text((w - 14 * scale, h // 2), "42%", font=f(15 * scale, True), fill=ORANGE, anchor="rm")
    return pill


def hamster_board():
    cols = [("지금(임시 그림)", Image.open(OLD).convert("RGBA"), None)]
    for d, label in DIRS:
        cols.append((label, load(d, "hamster", 108), load(d, "hamster", 240)))
    colw, pad, lab = 300, 40, 230
    W = lab + colw * len(cols) + pad
    rows_h = [70, 70, 150, 270, 90, 150]
    H = sum(rows_h) + pad * 2 + 40
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((pad, 24), "햄스터 시안 비교 — 검정 바탕, 같은 형태를 세 가지 방식으로", font=f(24, True), fill=(235, 235, 235, 255))
    y = 24 + 50
    for i, (name, _, _) in enumerate(cols):
        d.text((lab + i * colw + colw // 2, y + 30), name, font=f(20, True), fill=INK if i else DIM, anchor="mm")
    y += rows_h[0]
    row_labels = ["36pt 실제 크기(1배)", "36pt @3x = 108px\n아이폰이 실제로 그리는 픽셀\n점선 = 축소 칸에서 보이는 높이", "80pt @3x = 240px\n확장·잠금 화면", "축소 아일랜드 모형(1배)", "축소 아일랜드 모형(@3x)"]
    for r, rl in enumerate(row_labels):
        h = rows_h[r + 1]
        d.multiline_text((pad, y + h // 2), rl, font=f(15), fill=DIM, anchor="lm", spacing=6)
        for i, (_, im108, im240) in enumerate(cols):
            cx = lab + i * colw + colw // 2
            if r == 0:
                t = to36(im108); img.alpha_composite(t, (cx - 18, y + h // 2 - 18))
            elif r == 1:
                img.alpha_composite(im108, (cx - 54, y + h // 2 - 54)); band(d, cx - 54, y + h // 2 - 54, 108)
            elif r == 2:
                if im240 is None:
                    big = im108.resize((240, 240), Image.LANCZOS)
                    img.alpha_composite(big, (cx - 120, y + h // 2 - 120))
                    d.text((cx, y + h - 6), "(108px 를 늘린 것)", font=f(12), fill=DIM, anchor="mb")
                else:
                    img.alpha_composite(im240, (cx - 120, y + h // 2 - 120))
            elif r == 3:
                p = island(im108, 1); img.alpha_composite(p, (cx - p.width // 2, y + h // 2 - p.height // 2))
            else:
                p = island(im108, 3).resize((200 * 3 * 270 // 600, 37 * 3 * 270 // 600), Image.LANCZOS)
                p = island(im108, 3)
                p = p.crop((0, 0, 140 * 3 // 2 + 60, p.height))  # 왼쪽 칸 쪽만
                img.alpha_composite(p, (cx - p.width // 2, y + h // 2 - p.height // 2))
        y += h
    d.text((pad, H - 30), "모형의 아일랜드 테두리(짙은 회색)는 안내용이며 실제 기기에서는 보이지 않습니다. 그림은 모두 자체 제작.", font=f(13), fill=DIM)
    img.convert("RGB").save(os.path.join(R, "compare", "hamster_compare.png"), optimize=True)


def family_rows(d_name, label, img, draw, x0, y0):
    draw.text((x0, y0), label, font=f(20, True), fill=INK)
    y = y0 + 40
    # 실제 크기 줄
    draw.text((x0, y + 18), "36px 실제", font=f(13), fill=DIM, anchor="lm")
    for i, (n, _) in enumerate(CHARS):
        img.alpha_composite(to36(load(d_name, n, 108)), (x0 + 110 + i * 60, y))
    y += 56
    draw.text((x0, y + 54), "3배(108px)", font=f(13), fill=DIM, anchor="lm")
    for i, (n, nm) in enumerate(CHARS):
        cx = x0 + 110 + i * 140
        img.alpha_composite(load(d_name, n, 108), (cx, y))
        band(draw, cx, y, 108)
        draw.text((cx + 54, y + 118), nm, font=f(13), fill=DIM, anchor="mt")
    return y + 140


def family_boards():
    for d_name, label in DIRS:
        W, H = 600, 280
        img = Image.new("RGBA", (W, H), BG)
        dr = ImageDraw.Draw(img)
        family_rows(d_name, label + " — 가족 맛보기", img, dr, 30, 24)
        img.convert("RGB").save(os.path.join(R, "compare", f"family_{d_name.split('_')[0]}.png"), optimize=True)
    W, H = 600, 30 + 250 * 3 + 30
    img = Image.new("RGBA", (W, H), BG)
    dr = ImageDraw.Draw(img)
    y = 24
    for d_name, label in DIRS:
        y = family_rows(d_name, label, img, dr, 30, y) + 20
    img.convert("RGB").save(os.path.join(R, "compare", "family_all.png"), optimize=True)


def zoom_board():
    """같은 그림을 쳇바퀴만 키우고 햄스터를 1.2배로 바꾼 구도(추가 제안)"""
    cols = [("B 지금 구도", "B_sticker", "hamster"), ("B 확대 구도", "B_sticker", "hamster_zoom"),
            ("C 지금 구도", "C_flat", "hamster"), ("C 확대 구도", "C_flat", "hamster_zoom")]
    colw, pad, lab = 290, 40, 200
    W = lab + colw * 4 + pad
    rows_h = [60, 60, 150, 150, 270]
    H = sum(rows_h) + 100
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((pad, 24), "추가 제안: 쳇바퀴를 칸 끝까지 키우고 햄스터를 1.2배로", font=f(24, True), fill=(235, 235, 235, 255))
    y = 74
    for i, (nm, _, _) in enumerate(cols):
        d.text((lab + i * colw + colw // 2, y + 28), nm, font=f(19, True), fill=INK, anchor="mm")
    y += rows_h[0]
    labels = ["36px 실제", "108px(@3x)\n점선 = 보이는 높이", "축소 아일랜드 모형(@3x)", "240px(80pt@3x)"]
    for r, rl in enumerate(labels):
        h = rows_h[r + 1]
        d.multiline_text((pad, y + h // 2), rl, font=f(15), fill=DIM, anchor="lm", spacing=6)
        for i, (_, dn, fn) in enumerate(cols):
            cx = lab + i * colw + colw // 2
            im108 = Image.open(os.path.join(R, dn, f"{fn}_108.png")).convert("RGBA")
            if r == 0:
                img.alpha_composite(to36(im108), (cx - 18, y + h // 2 - 18))
            elif r == 1:
                img.alpha_composite(im108, (cx - 54, y + h // 2 - 54)); band(d, cx - 54, y + h // 2 - 54, 108)
            elif r == 2:
                p = island(im108, 3); p = p.crop((0, 0, 270, p.height))
                img.alpha_composite(p, (cx - p.width // 2, y + h // 2 - p.height // 2))
            else:
                im240 = Image.open(os.path.join(R, dn, f"{fn}_240.png")).convert("RGBA")
                img.alpha_composite(im240, (cx - 120, y + h // 2 - 120))
        y += h
    img.convert("RGB").save(os.path.join(R, "compare", "hamster_zoom_proposal.png"), optimize=True)


hamster_board()
family_boards()
zoom_board()
print("ok")
