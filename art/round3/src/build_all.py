#!/usr/bin/env python3
"""3라운드 전체 산출물 만들기.
  python3 build_all.py  ->  cat_a..d/ (SVG+PNG), compare/ (비교판), finalist/ (최종 후보), gif/ (속도별)
최종 후보: A(주 후보) -> finalist/cat_*.png, D(대안) -> finalist/alt_d/cat_*.png
"""
import os, subprocess, sys, shutil, tempfile
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cat, fit

R3 = os.path.abspath(os.path.join(HERE, ".."))
FONT = "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"
RUN = ["run_1", "run_2", "run_3", "run_4"]
ALL = RUN + ["rest_1", "rest_2", "still"]
NAMES = {"a": "A 살구 · 선 없음 · 알약 눈", "b": "B 모래 줄무늬 · 점 눈만",
         "c": "C 회청 · 주황 목도리 · 접힌 귀", "d": "D 먹색 · 밝은 테 · 호박색 눈"}
RANK = {"a": "추천 1", "d": "추천 2", "c": "3", "b": "4"}
FINAL = [("a", "finalist"), ("d", "finalist/alt_d")]

def sh(*a):
    subprocess.run(a, check=True, capture_output=True)

def render_dir(d, items):
    """items: [(svg, png, width)]. inkscape 한 번에 여러 장은 이름 지정이 안 돼 한 장씩."""
    for svg, png, w in items:
        sh("inkscape", "--export-type=png", f"--export-width={w}", f"--export-filename={png}", svg)

# 1) 화면 맞춤: 달리기 4장 바깥 상자 기준, 모든 변형·포즈 같은 배율
f, box = fit.fit_set(RUN, style="d")
cat.FIT["run"] = f
print("fit", f, box)

# 2) 변형별 SVG·PNG
for k in "abcd":
    d = os.path.join(R3, f"cat_{k}")
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    items = []
    for p in ALL:
        svg = os.path.join(d, f"cat_{k}_{p}.svg")
        open(svg, "w").write(cat.cat_svg(k, p))
        items += [(svg, os.path.join(d, f"cat_{k}_{p}@3x.png"), 108), (svg, os.path.join(d, f"cat_{k}_{p}_L@3x.png"), 240)]
    render_dir(d, items)

def img(k, p, big=False):
    return Image.open(os.path.join(R3, f"cat_{k}", f"cat_{k}_{p}{'_L' if big else ''}@3x.png")).convert("RGBA")

f1 = ImageFont.truetype(FONT, 17); f2 = ImageFont.truetype(FONT, 13); f3 = ImageFont.truetype(FONT, 12)
GREY = (150, 150, 150)

# 3-1) 비교판: 같은 극단 포즈(뻗은 공중) 36 / 108 / 240
def compare_one(pose, name):
    CW, PAD = 270, 24
    board = Image.new("RGB", (PAD * 2 + CW * 4, 610), (0, 0, 0)); dr = ImageDraw.Draw(board)
    y36, y108, y240 = 96, 186, 346
    dr.text((PAD, y36 - 28), "실제 크기 36px (1배 화면에서 본 최소 크기)", fill=GREY, font=f2)
    dr.text((PAD, y108 - 26), "108px = 아일랜드 칸 36pt @3x, 실기기 화소. 회색 선 사이(y15~93)가 실제로 보이는 띠", fill=GREY, font=f2)
    dr.text((PAD, y240 - 26), "240px (확장·잠금 화면용 _L)", fill=GREY, font=f2)
    for i, k in enumerate("abcd"):
        x0 = PAD + i * CW
        dr.text((x0, 18), NAMES[k], fill=(235, 235, 235), font=f1)
        dr.text((x0, 42), f"팀 순위 {RANK[k]}", fill=(255, 159, 10) if k in "ad" else GREY, font=f3)
        a = img(k, pose).resize((36, 36), Image.LANCZOS)
        board.paste(a, (x0 + 10, y36), a)
        b = img(k, pose); board.paste(b, (x0 + 10, y108), b)
        for yy in (15, 93):
            dr.line([(x0 + 4, y108 + yy), (x0 + 124, y108 + yy)], fill=(70, 70, 70))
        c = img(k, pose, True); board.paste(c, (x0 + 10, y240), c)
    board.save(os.path.join(R3, "compare", name), optimize=True)

# 3-2) 비교판: 변형별 달리기 4장 (108px + 36px)
def compare_cycle(name):
    PAD, CW = 24, 116
    W = PAD * 2 + 300 + CW * 4 + 40 + 44 * 4
    board = Image.new("RGB", (W, 60 + 4 * 140), (0, 0, 0)); dr = ImageDraw.Draw(board)
    dr.text((PAD, 16), "달리기 4장: 1 뻗은 공중 → 2 앞발 착지 → 3 모은 공중 → 4 뒷발 디딤 → 1   (오른쪽 작은 줄 = 36px)", fill=GREY, font=f2)
    for r, k in enumerate("adcb"):
        y = 60 + r * 140
        dr.text((PAD, y + 40), NAMES[k], fill=(235, 235, 235), font=f2)
        dr.text((PAD, y + 62), f"팀 순위 {RANK[k]}", fill=(255, 159, 10) if k in "ad" else GREY, font=f3)
        for i, p in enumerate(RUN):
            im = img(k, p); x = PAD + 300 + i * CW
            board.paste(im, (x, y), im)
            for yy in (15, 93):
                dr.line([(x, y + yy), (x + 108, y + yy)], fill=(45, 45, 45))
            s = im.resize((36, 36), Image.LANCZOS)
            board.paste(s, (PAD + 300 + 4 * CW + 40 + i * 44, y + 36), s)
    board.save(os.path.join(R3, "compare", name), optimize=True)

compare_one("run_1", "compare_4variants_run_1.png")
compare_cycle("compare_4variants_runcycle.png")

# 4) 최종 후보 파일 (char = cat)
for k, sub in FINAL:
    d = os.path.join(R3, sub); os.makedirs(d, exist_ok=True)
    for p in ALL:
        shutil.copy(os.path.join(R3, f"cat_{k}", f"cat_{k}_{p}@3x.png"), os.path.join(d, f"cat_{p}@3x.png"))
        shutil.copy(os.path.join(R3, f"cat_{k}", f"cat_{k}_{p}_L@3x.png"), os.path.join(d, f"cat_{p}_L@3x.png"))
    # 최종 후보 한 장 보기
    sheet = Image.new("RGB", (24 * 2 + 7 * 250, 24 + 20 + 250 + 30 + 120 + 20), (0, 0, 0)); dr = ImageDraw.Draw(sheet)
    dr.text((24, 12), f"{NAMES[k]} — 달리기 4 · 쉼 2 · 정지 1 (위 240px, 아래 108px)", fill=(235, 235, 235), font=f2)
    for i, p in enumerate(ALL):
        L = img(k, p, True); sheet.paste(L, (24 + i * 250, 40), L)
        S = img(k, p); sheet.paste(S, (24 + i * 250 + 66, 40 + 250 + 20), S)
        dr.text((24 + i * 250 + 100, 40 + 250 + 4), p, fill=GREY, font=f3)
    sheet.save(os.path.join(d, "sheet.png"), optimize=True)

# 5) GIF: 한 바퀴 0.5초(8fps) / 1.0초 / 2.0초, 쉼 루프. 240 + 108(띠 표시) + 36 를 한 화면에
def gif_frame(k, p):
    fr = Image.new("RGB", (420, 260), (0, 0, 0)); dr = ImageDraw.Draw(fr)
    L = img(k, p, True); fr.paste(L, (8, 10), L)
    S = img(k, p); fr.paste(S, (290, 30), S)
    for yy in (15, 93):
        dr.line([(286, 30 + yy), (402, 30 + yy)], fill=(60, 60, 60))
    T = S.resize((36, 36), Image.LANCZOS); fr.paste(T, (326, 170), T)
    return fr

def make_gif(k, poses, delay_ticks, name):
    with tempfile.TemporaryDirectory() as t:
        files = []
        for i, p in enumerate(poses):
            fn = os.path.join(t, f"{i}.png"); gif_frame(k, p).save(fn); files.append(fn)
        sh("convert", "-delay", delay_ticks, "-loop", "0", *files, "-layers", "Optimize", os.path.join(R3, "gif", name))

os.makedirs(os.path.join(R3, "gif"), exist_ok=True)
for k, _ in FINAL:
    make_gif(k, RUN, "1x8", f"cat_{k}_run_fast_0.5s_8fps.gif")
    make_gif(k, RUN, "1x4", f"cat_{k}_run_normal_1.0s.gif")
    make_gif(k, RUN, "1x2", f"cat_{k}_run_slow_2.0s.gif")
    make_gif(k, ["rest_1", "rest_2"], "9x10", f"cat_{k}_rest_breath.gif")
    # 정지 -> 출발 -> 빠른 달리기 -> 쉼 흐름
    make_gif(k, ["still"] * 4 + RUN * 4 + ["rest_1", "rest_2"] * 3, "1x8", f"cat_{k}_flow_8fps.gif")
print("done")
