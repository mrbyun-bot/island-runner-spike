#!/usr/bin/env python3
"""가족 시트: 검정 바탕, 36px 실제 줄 + 108px + 240px. 사용: python3 sheet.py [표정]"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import family
from kit import render

R4 = os.path.abspath(os.path.join(HERE, ".."))
FONT = "/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf"
GREY = (140, 140, 140)


def build_icons(expr="open", outdir=None):
    outdir = outdir or os.path.join(R4, "family", "icons")
    os.makedirs(outdir, exist_ok=True)
    for k in family.ORDER:
        t = family.SP[k](expr)
        sfx = "" if expr == "open" else f"_{expr}"
        open(os.path.join(R4, "src", "svg", f"{k}_front{sfx}.svg"), "w").write(t)
        for w, tag in ((36, "36"), (108, "@3x"), (240, "_L@3x")):
            render(t, os.path.join(outdir, f"{k}_front{sfx}{tag}.png"), w)


def sheet(order, out, title, labels=None, ranks=None, expr="open"):
    f1 = ImageFont.truetype(FONT, 18); f2 = ImageFont.truetype(FONT, 13)
    CW, PAD = 258, 24
    W = PAD * 2 + CW * len(order) if len(order) <= 4 else PAD * 2 + CW * 4
    rows = (len(order) + 3) // 4
    RH = 470
    img = Image.new("RGB", (W, 64 + RH * rows), (0, 0, 0)); dr = ImageDraw.Draw(img)
    dr.text((PAD, 20), title, fill=(220, 220, 220), font=f1)
    d = os.path.join(R4, "family", "icons")
    sfx = "" if expr == "open" else f"_{expr}"
    for i, k in enumerate(order):
        r, c = divmod(i, 4)
        x0 = PAD + c * CW; y0 = 64 + r * RH
        lab = (labels or family.KO)[k]
        dr.text((x0, y0 + 4), lab, fill=(230, 230, 230), font=f1)
        if ranks:
            dr.text((x0, y0 + 28), ranks[k], fill=(255, 159, 10) if "탈락" not in ranks[k] else GREY, font=f2)
        i36 = Image.open(os.path.join(d, f"{k}_front{sfx}36.png")).convert("RGBA")
        i108 = Image.open(os.path.join(d, f"{k}_front{sfx}@3x.png")).convert("RGBA")
        i240 = Image.open(os.path.join(d, f"{k}_front{sfx}_L@3x.png")).convert("RGBA")
        # 36px 실제 크기: 아일랜드 칸처럼 위아래 잘린 띠(36 중 y5~31)
        img.paste(i36, (x0, y0 + 60), i36)
        dr.text((x0 + 44, y0 + 70), "36px 실제", fill=GREY, font=f2)
        img.paste(i108, (x0 + 120, y0 + 50), i108)
        dr.line([(x0 + 120, y0 + 50 + 15), (x0 + 228, y0 + 50 + 15)], fill=(50, 50, 50))
        dr.line([(x0 + 120, y0 + 50 + 93), (x0 + 228, y0 + 50 + 93)], fill=(50, 50, 50))
        img.paste(i240, (x0, y0 + 180), i240)
    img.save(out)


if __name__ == "__main__":
    os.makedirs(os.path.join(R4, "src", "svg"), exist_ok=True)
    for e in ("open", "happy", "sleep"):
        build_icons(e)
    sheet(family.ORDER, os.path.join(R4, "family", "draft_family.png"), "4라운드 가족 후보 8종 (정면, 검정 바탕)")
