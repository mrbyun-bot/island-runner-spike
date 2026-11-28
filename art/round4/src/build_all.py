#!/usr/bin/env python3
"""4라운드 전체 산출물 다시 만들기:  python3 art/round4/src/build_all.py
thumbnails/ 실루엣 섬네일, family/ 가족 시트·명도·격자, research/palette.md 대비 계산,
finalists/<종>/ 7장 + 모델 시트, gif/ 속도별, finalists/frame_diff.md, finalists/compare_*.png
"""
import os, sys, math, itertools, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import family, side, sheet
from kit import render, contrast, rel_lum, svg as wrap

R4 = os.path.abspath(os.path.join(HERE, ".."))
FONT = "/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf"
F18 = ImageFont.truetype(FONT, 18); F14 = ImageFont.truetype(FONT, 14); F12 = ImageFont.truetype(FONT, 12)
GREY = (140, 140, 140); WHITE = (230, 230, 230); ORANGE = (255, 159, 10)
SVGD = os.path.join(R4, "src", "svg"); os.makedirs(SVGD, exist_ok=True)

# 팀 평가 결과(의견서 4절과 같음). 순위가 바뀌면 여기만 고친다.
RANK = {"hedgehog": "1위 · 결선", "duckling": "2위 · 결선", "tit": "3위 · 결선", "chipmunk": "4위 · 예비",
        "rabbit": "5위 · 탈락(무난하지만 흔함)", "turtle": "6위 · 탈락(36px에서 초록 덩어리)",
        "quokka": "탈락(곰으로 읽힘)", "otter": "탈락(형태 약함, 먼작귀 해달과 겹칠 위험)"}
FINAL = ["hedgehog", "duckling", "tit"]
FR = side.FRAMES


def on_black(im):
    bg = Image.new("RGB", im.size, (0, 0, 0)); bg.paste(im, (0, 0), im); return bg


# ------------------------------------------------------------ 1. 가족 아이콘과 시트
for e in ("open", "happy", "sleep"):
    sheet.build_icons(e)
sheet.sheet(family.ORDER, os.path.join(R4, "family", "family_sheet.png"),
            "4라운드 캐릭터 가족 8종 · 정면 · 검정 바탕 · 왼쪽 위 36px가 실제 크기 · 주황 글씨가 팀 순위", ranks=RANK)
for k in family.ORDER:  # 초안 파일 정리
    pass
dr_old = os.path.join(R4, "family", "draft_family.png")
if os.path.exists(dr_old):
    os.remove(dr_old)

# 명도 스터디: 같은 시트를 그레이스케일로
g = ImageOps.grayscale(Image.open(os.path.join(R4, "family", "family_sheet.png")))
g.save(os.path.join(R4, "family", "value_study_gray.png"))


# ------------------------------------------------------------ 2. 섬네일: 실루엣 비율 탐색 24장 + 구분도
def silhouette(png):
    a = np.array(Image.open(png).getchannel("A")) > 60
    return a


TH = os.path.join(R4, "thumbnails"); os.makedirs(TH, exist_ok=True)
VAR = {"납작": (1.14, 0.88), "기본": (1.0, 1.0), "길쭉": (0.88, 1.13)}
tiles = []
for k in family.ORDER:
    base = family.SP[k]("open")
    for vn, (vx, vy) in VAR.items():
        a = base.index("<g transform"); b = base.rindex("</svg>")
        t = base[:a] + f'<g transform="translate(54 91) scale({vx} {vy}) translate(-54 -91)">' + base[a:b] + "</g></svg>"
        p36 = os.path.join(TH, f"{k}_{vn}_36.png"); render(t, p36, 36)
        tiles.append((k, vn, p36))
cols = 6; cw = 150; chh = 120
board = Image.new("RGB", (cols * cw + 40, 90 + ((len(tiles) + cols - 1) // cols) * chh), (255, 255, 255))
dr = ImageDraw.Draw(board)
dr.text((20, 16), "섬네일 24장: 종 8 × 비율 3(납작·기본·길쭉). 검정 실루엣, 실제 36px(왼쪽)과 3배 확대(오른쪽)", fill=(0, 0, 0), font=F14)
dr.text((20, 40), "색·얼굴을 지우고 윤곽만 남겨도 무슨 동물인지 읽히는지 보는 시험", fill=(90, 90, 90), font=F12)
for i, (k, vn, p) in enumerate(tiles):
    r, c = divmod(i, cols); x = 20 + c * cw; y = 70 + r * chh
    m = silhouette(p)
    sil = Image.fromarray(np.where(m, 0, 255).astype("uint8"))
    board.paste(sil, (x, y + 30)); board.paste(sil.resize((108, 108), Image.NEAREST), (x + 40, y))
    dr.text((x, y + 92), f"{family.KO[k].split('(')[0]} {vn}", fill=(0, 0, 0), font=F12)
board.save(os.path.join(TH, "thumbnails_24_silhouette.png"))
for _, _, p in tiles:
    os.remove(p)

# 구분도: 기본 비율 8종 실루엣(36px)끼리 겹침 비율(IoU). 낮을수록 윤곽만으로 구분됨.
sil = {}
for k in family.ORDER:
    sil[k] = silhouette(os.path.join(R4, "family", "icons", f"{k}_front36.png"))
iou_rows = []
for a, b in itertools.combinations(family.ORDER, 2):
    i = (sil[a] & sil[b]).sum(); u = (sil[a] | sil[b]).sum()
    iou_rows.append((i / u, a, b))
iou_rows.sort(reverse=True)

# ------------------------------------------------------------ 3. 팔레트 대비 계산
PAL = {
    "hedgehog": [("가시", "#7E6A5D"), ("얼굴·배", "#F1DEC6"), ("코", "#3A2C27")],
    "duckling": [("몸", "#F2D27E"), ("정수리", "#8C6B4C"), ("부리", "#D98F6E")],
    "tit": [("몸", "#E2B597"), ("정수리", "#C47F5E"), ("꼬리", "#8E6450")],
    "chipmunk": [("몸", "#DCA36B"), ("줄", "#6F4A31"), ("흰 줄", "#F5E4CC")],
    "rabbit": [("몸", "#D5C3AF"), ("귀 끝", "#8B7260"), ("주둥이", "#F2E8DA")],
    "turtle": [("등껍질", "#7FAA7A"), ("머리", "#D3E2A8"), ("테", "#5E8A5C")],
    "quokka": [("몸", "#B39A86"), ("주둥이", "#DCCAB8")],
    "otter": [("몸", "#A57B5C"), ("주둥이", "#EAD7C1")],
}
INK = "#2A211D"
lines = ["# 팔레트 대비 계산 (자동 생성: build_all.py)", "",
         "WCAG 2.x 상대 휘도 공식으로 계산. 글자 기준(4.5:1)은 그림에 그대로 적용되는 규칙이 아니므로 팀 기준을 따로 둠:",
         "- 몸의 주된 면 대 검정 배경 **7:1 이상**(36px에서 몸 덩어리가 바로 떠 보이게)",
         "- 눈(먹색 #2A211D) 대 그 눈이 놓인 면 **7:1 이상**(점 눈이 2~3화소로 줄어도 남게)",
         "- 표식색 대 몸색 **1.5:1 이상**(무늬가 같은 덩어리로 뭉개지지 않게). 어두운 표식이 검정과 닿는 경우는 아래 표에 따로 적음",
         "", "공식 출처: https://www.w3.org/TR/WCAG21/#dfn-relative-luminance , https://www.w3.org/TR/WCAG21/#dfn-contrast-ratio", "",
         "| 종 | 색 | 값 | 대 검정 | 대 첫 색(몸) | 눈(먹색) 대 이 색 |", "|---|---|---|---|---|---|"]
for k, cols_ in PAL.items():
    base = cols_[0][1] if k != "hedgehog" else cols_[1][1]
    for nm, hx in cols_:
        lines.append(f"| {family.KO[k]} | {nm} | `{hx}` | {contrast(hx, '#000000'):.1f}:1 | {contrast(hx, base):.2f}:1 | {contrast(INK, hx):.1f}:1 |")
lines += ["", "## 36px 실루엣 겹침(IoU, 높을수록 윤곽이 비슷함) 상위 6쌍", "", "| 쌍 | IoU |", "|---|---|"]
for v, a, b in iou_rows[:6]:
    lines.append(f"| {family.KO[a]} – {family.KO[b]} | {v:.2f} |")
lines += ["", "하위 3쌍(가장 잘 구분됨): " + ", ".join(f"{family.KO[a]}–{family.KO[b]} {v:.2f}" for v, a, b in iou_rows[-3:])]
open(os.path.join(R4, "research", "palette.md"), "w").write("\n".join(lines) + "\n")

# ------------------------------------------------------------ 4. 구성 격자(비율표) 그림
grid = Image.new("RGB", (40 + 300 * 4, 400), (0, 0, 0)); dg = ImageDraw.Draw(grid)
dg.text((20, 14), "구성 격자: 108 칸 기준. 회색 띠 = 아일랜드에서 보이는 y15~93, 주황 선 = 눈 높이, 파랑 선 = 몸 꼭대기·바닥", fill=WHITE, font=F14)
GEO = {"hedgehog": (90 - 40 * 1.14, 0.48), "duckling": (None, 0.5), "tit": (None, 0.5), "chipmunk": (None, 0.5)}
for i, k in enumerate(["hedgehog", "duckling", "tit", "chipmunk"]):
    im = Image.open(os.path.join(R4, "family", "icons", f"{k}_front_L@3x.png")).convert("RGBA")
    x0, y0 = 30 + i * 300, 60
    s = 240 / 108
    dg.rectangle([x0, y0 + 15 * s, x0 + 240, y0 + 93 * s], fill=(28, 28, 28))
    grid.paste(im, (x0, y0), im)
    a = np.array(im.getchannel("A")) > 60
    ys = np.where(a.any(1))[0]; top, bot = ys.min(), ys.max()
    # 눈: 먹색 화소의 세로 중심
    rgb = np.array(im.convert("RGB")).astype(int)
    ink = (abs(rgb - np.array([0x2A, 0x21, 0x1D])).sum(2) < 30) & a
    ey = np.where(ink.any(1))[0].mean() if ink.any() else 0
    for yy, col in ((top, (80, 140, 255)), (bot, (80, 140, 255)), (ey, ORANGE)):
        dg.line([(x0, y0 + yy), (x0 + 240, y0 + yy)], fill=col, width=1)
    ratio = (ey - top) / (bot - top)
    dg.text((x0, y0 + 250), f"{family.KO[k]}", fill=WHITE, font=F14)
    dg.text((x0, y0 + 272), f"눈 높이 = 위에서 {ratio*100:.0f}% (귀·가시 포함)", fill=GREY, font=F12)
    dg.text((x0, y0 + 290), f"덩어리 높이 {(bot-top)/s:.0f} / 108", fill=GREY, font=F12)
grid.save(os.path.join(R4, "family", "construction_grid.png"))

# ------------------------------------------------------------ 5. 결선 캐릭터: 프레임·모델 시트
FIN = os.path.join(R4, "finalists")
diff_md = ["# 인접 프레임 화소 차이 (자동 생성)", "",
           "검정 위에 합성한 108px 프레임끼리, 채널 차이가 3%(8/255)를 넘는 화소 수. 괄호는 전체 11,664 화소 중 비율.",
           "4→1 이 다른 이음과 비슷한 크기면 루프가 튀지 않음. 너무 작으면(2% 미만) 같은 장처럼 보임.", "",
           "| 종 | 1→2 | 2→3 | 3→4 | 4→1 | 쉼1↔쉼2 | 정지↔달1 |", "|---|---|---|---|---|---|---|"]
ident = []
for k in FINAL:
    fit = side.fit_char(k)
    d = os.path.join(FIN, k); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for fr in FR:
        t = side.side_svg(k, fr)
        open(os.path.join(SVGD, f"{k}_{fr}.svg"), "w").write(t)
        render(t, os.path.join(d, f"{k}_{fr}@3x.png"), 108)
        render(t, os.path.join(d, f"{k}_{fr}_L@3x.png"), 240)
        render(t, os.path.join(d, f"_{k}_{fr}_36.png"), 36)
    arr = {fr: np.array(on_black(Image.open(os.path.join(d, f"{k}_{fr}@3x.png")).convert("RGBA"))).astype(int) for fr in FR}
    def df(a, b):
        n = int((abs(arr[a] - arr[b]).max(2) > 8).sum()); return f"{n} ({n/11664*100:.1f}%)"
    diff_md.append(f"| {family.KO[k]} | {df('run_1','run_2')} | {df('run_2','run_3')} | {df('run_3','run_4')} | {df('run_4','run_1')} | {df('rest_1','rest_2')} | {df('still','run_1')} |")
    # 핵심 띠 확인
    for fr in FR:
        a = np.array(Image.open(os.path.join(d, f"{k}_{fr}@3x.png")).getchannel("A")) > 24
        ys = np.where(a.any(1))[0]; xs = np.where(a.any(0))[0]
        ident.append((k, fr, ys.min(), ys.max(), xs.min(), xs.max()))

    # 모델 시트: 정면 · 옆면 · 표정 3종 · 36px
    ms = Image.new("RGB", (1100, 640), (0, 0, 0)); dm = ImageDraw.Draw(ms)
    dm.text((24, 18), f"{family.KO[k]} 모델 시트 · 정면 / 옆면(정지) / 표정 3종 / 실제 36px", fill=WHITE, font=F18)
    front = Image.open(os.path.join(R4, "family", "icons", f"{k}_front_L@3x.png")).convert("RGBA")
    sideL = Image.open(os.path.join(d, f"{k}_still_L@3x.png")).convert("RGBA")
    ms.paste(front, (24, 60), front); ms.paste(sideL, (300, 60), sideL)
    dm.text((24, 310), "정면", fill=GREY, font=F14); dm.text((300, 310), "옆면(달리기 방향 오른쪽)", fill=GREY, font=F14)
    for j, (e, nm) in enumerate((("open", "기본"), ("happy", "기쁨"), ("sleep", "쉼·잠"))):
        sfx = "" if e == "open" else f"_{e}"
        im = Image.open(os.path.join(R4, "family", "icons", f"{k}_front{sfx}@3x.png")).convert("RGBA")
        ms.paste(im, (600 + j * 160, 80), im); dm.text((600 + j * 160, 200), nm, fill=GREY, font=F14)
    for j, fr in enumerate(FR):
        im = Image.open(os.path.join(d, f"_{k}_{fr}_36.png")).convert("RGBA")
        ms.paste(im, (600 + j * 64, 300), im)
    dm.text((600, 346), "36px: 달1 달2 달3 달4 쉼1 쉼2 정지", fill=GREY, font=F12)
    for j, fr in enumerate(FR):
        im = Image.open(os.path.join(d, f"{k}_{fr}@3x.png")).convert("RGBA")
        x = 24 + j * 150; y = 400
        dm.rectangle([x, y + 15, x + 108, y + 93], outline=(45, 45, 45))
        ms.paste(im, (x, y), im); dm.text((x, y + 116), fr, fill=GREY, font=F12)
    dm.text((24, 600), "108px 칸의 회색 사각형 = 아일랜드에서 보이는 띠(y15~93)", fill=GREY, font=F12)
    ms.save(os.path.join(d, "model_sheet.png"))
open(os.path.join(FIN, "frame_diff.md"), "w").write("\n".join(diff_md) + "\n")
with open(os.path.join(FIN, "bbox.md"), "w") as fo:
    fo.write("# 프레임 바깥 상자(108px, 알파>24)\n\n| 종 | 장 | y 위 | y 아래 | x 왼 | x 오른 |\n|---|---|---|---|---|---|\n")
    for r in ident:
        fo.write("| " + " | ".join(str(v) for v in r) + " |\n")

# ------------------------------------------------------------ 6. 비교판(사용자가 볼 것)
cb = Image.new("RGB", (40 + 140 * 7 + 200, 80 + 230 * len(FINAL)), (0, 0, 0)); dc = ImageDraw.Draw(cb)
dc.text((20, 16), "결선 3종 달리기·쉼·정지 7장 · 108px(실기기 화소) · 회색 테두리 = 아일랜드에서 보이는 띠", fill=WHITE, font=F14)
dc.text((20, 40), "오른쪽 끝: 실제 크기 36px로 달리기 4장", fill=GREY, font=F12)
for r, k in enumerate(FINAL):
    y = 80 + r * 230
    dc.text((20, y), f"{family.KO[k]}  ({RANK[k]})", fill=ORANGE, font=F14)
    for j, fr in enumerate(FR):
        im = Image.open(os.path.join(FIN, k, f"{k}_{fr}@3x.png")).convert("RGBA")
        x = 20 + j * 140
        dc.rectangle([x, y + 30 + 15, x + 108, y + 30 + 93], outline=(45, 45, 45))
        cb.paste(im, (x, y + 30), im)
        dc.text((x, y + 150), ["달리기1", "달리기2", "달리기3", "달리기4", "쉼1", "쉼2", "정지"][j], fill=GREY, font=F12)
    for j in range(4):
        im = Image.open(os.path.join(FIN, k, f"_{k}_run_{j+1}_36.png")).convert("RGBA")
        cb.paste(im, (20 + 7 * 140 + j * 44, y + 66), im)
cb.save(os.path.join(FIN, "compare_finalists_7frames.png"))

# 가족+결선 한눈에(사용자용 첫 장): 정면 8종 36px 줄 + 결선 달리기 1장
ov = Image.new("RGB", (1100, 330), (0, 0, 0)); do = ImageDraw.Draw(ov)
do.text((20, 14), "실제 크기 36px 한 줄(아일랜드에 들어갈 크기). 위: 정면 8종 / 아래: 결선 3종 달리기 4장", fill=WHITE, font=F14)
for i, k in enumerate(family.ORDER):
    im = Image.open(os.path.join(R4, "family", "icons", f"{k}_front36.png")).convert("RGBA")
    ov.paste(im, (20 + i * 70, 60), im)
    do.text((20 + i * 70, 100), family.KO[k].split("(")[0][:5], fill=GREY, font=F12)
for r, k in enumerate(FINAL):
    for j in range(4):
        im = Image.open(os.path.join(FIN, k, f"_{k}_run_{j+1}_36.png")).convert("RGBA")
        ov.paste(im, (20 + j * 50 + r * 260, 160), im)
    do.text((20 + r * 260, 205), family.KO[k].split("(")[0], fill=GREY, font=F12)
# 아일랜드 모형(알약) 안에 넣어 보기
for r, k in enumerate(FINAL):
    x = 20 + r * 260; y = 240
    do.rounded_rectangle([x, y, x + 210, y + 37], radius=18, fill=(0, 0, 0), outline=(40, 40, 40))
    im = Image.open(os.path.join(FIN, k, f"_{k}_run_1_36.png")).convert("RGBA").crop((0, 5, 36, 31))
    ov.paste(im, (x + 12, y + 6), im)
    do.text((x + 160, y + 10), "42%", fill=ORANGE, font=F14)
do.text((20, 300), "맨 아래: 아일랜드 모형(36pt 칸, 위아래 잘린 26pt 띠). 서버 모형이라 실기기와 다를 수 있음", fill=GREY, font=F12)
ov.save(os.path.join(R4, "family", "actual_size_36px.png"))

# ------------------------------------------------------------ 7. GIF (240 + 108 + 36 한 화면)
GIF = os.path.join(R4, "gif"); os.makedirs(GIF, exist_ok=True)


def gif_frame(k, fr):
    c = Image.new("RGB", (420, 260), (0, 0, 0)); dd = ImageDraw.Draw(c)
    L = Image.open(os.path.join(FIN, k, f"{k}_{fr}_L@3x.png")).convert("RGBA"); c.paste(L, (10, 10), L)
    m = Image.open(os.path.join(FIN, k, f"{k}_{fr}@3x.png")).convert("RGBA")
    dd.line([(290, 20 + 15), (398, 20 + 15)], fill=(40, 40, 40)); dd.line([(290, 20 + 93), (398, 20 + 93)], fill=(40, 40, 40))
    c.paste(m, (290, 20), m)
    s = Image.open(os.path.join(FIN, k, f"_{k}_{fr}_36.png")).convert("RGBA"); c.paste(s, (326, 170), s)
    return c


for k in FINAL:
    run = [gif_frame(k, f"run_{i}") for i in range(1, 5)]
    for nm, ms_ in (("fast_0.5s_8fps", 125), ("normal_1.0s", 250), ("slow_2.0s", 500)):
        run[0].save(os.path.join(GIF, f"{k}_run_{nm}.gif"), save_all=True, append_images=run[1:], duration=ms_, loop=0)
    rest = [gif_frame(k, "rest_1"), gif_frame(k, "rest_2")]
    rest[0].save(os.path.join(GIF, f"{k}_rest_breath.gif"), save_all=True, append_images=rest[1:], duration=700, loop=0)
    flow = [gif_frame(k, "still")] * 6 + run * 6 + rest * 3
    dur = [125] * 6 + [125] * 24 + [700] * 6
    flow[0].save(os.path.join(GIF, f"{k}_flow_8fps.gif"), save_all=True, append_images=flow[1:], duration=dur, loop=0)

# 36px 임시 파일은 결선 폴더에 남기지 않음(앱 파일 규칙은 108·240 두 크기)
for k in FINAL:
    for fr in FR:
        p = os.path.join(FIN, k, f"_{k}_{fr}_36.png")
        if os.path.exists(p):
            os.remove(p)
print("fit", side.FIT)
print("IoU top", [(round(v, 2), a, b) for v, a, b in iou_rows[:4]])
