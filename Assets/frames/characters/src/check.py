"""만든 프레임을 확인한다. 사용: python3 check.py
1) identify 로 모든 PNG 크기·투명 확인
2) preview/preview_<char>.png : 검정 바탕, 36px 실제 크기 줄 + 아일랜드에서 보이는 띠 줄 + 108px 1:1 줄 + 240px 줄
3) preview/loop_<char>.gif    : 8fps 달리기 루프(240px·108px·36px 나란히)
4) ImageMagick compare 로 프레임 간 픽셀 차이 표(preview/frame_diff.md)
"""
import os, subprocess, glob
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.dirname(HERE)
PV = os.path.join(D, "preview")
CHARS = ["hamster", "penguin", "rocket"]
FRAMES = ["run_1", "run_2", "run_3", "run_4", "rest_1", "rest_2", "still"]
FONT = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
os.makedirs(PV, exist_ok=True)


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout


# 1) 크기·투명
def check_files():
    rows, bad = [], 0
    for c in CHARS:
        for f in FRAMES:
            for suf, want in (("", 108), ("_L", 240)):
                p = os.path.join(D, f"{c}_{f}{suf}@3x.png")
                out = sh("identify", "-format", "%w %h %[channels] %[fx:minima.a] %[pixel:p{0,0}]", p).split()
                w, h, ch, amin = int(out[0]), int(out[1]), out[2], float(out[3])
                ok = w == want and h == want and ch.endswith("a") and amin == 0.0
                bad += not ok
                rows.append(f"| {os.path.basename(p)} | {w}x{h} | {ch} | {amin:.0f} | {os.path.getsize(p) // 1024}KB | {'통과' if ok else '실패'} |")
    return bad, rows


def on_black(im, size=None):
    if size and im.size[0] != size:
        im = im.resize((size, size), Image.LANCZOS)
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    return bg


# 2) 미리보기
def preview(c):
    font = ImageFont.truetype(FONT, 15)
    small = ImageFont.truetype(FONT, 12)
    pad, gap = 16, 12
    W = pad * 2 + 7 * 240 + 6 * gap
    H = 40 + (36 + 30) + (26 * 3 + 30) + (108 + 30) + (240 + 30) + pad
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    dr = ImageDraw.Draw(img)
    names = {"run_1": "달리기1", "run_2": "달리기2", "run_3": "달리기3", "run_4": "달리기4", "rest_1": "쉼1", "rest_2": "쉼2", "still": "정지"}
    dr.text((pad, 12), f"{c}  ·  검정 바탕, 위에서부터 36px 실제 크기 / 아일랜드 축소 칸 모형(108px 중 y15~93 만 보임, 아이폰 물리 픽셀 1:1) / 108px 1:1(점선 = 보이는 띠 y15~93) / 240px", font=font, fill=(200, 200, 200, 255))
    y = 40
    for row in ("36", "island", "108", "240"):
        for i, f in enumerate(FRAMES):
            x = pad + i * (240 + gap)
            src = Image.open(os.path.join(D, f"{c}_{f}{'_L' if row == '240' else ''}@3x.png")).convert("RGBA")
            if row == "36":
                img.alpha_composite(on_black(src, 36), (x, y))
                dr.text((x + 44, y + 10), names[f], font=small, fill=(150, 150, 150, 255))
            elif row == "island":
                # 36pt 칸 중 보이는 높이 약 26pt → 108px 중 y15~93 만 보인다. 1:1 = 아이폰 물리 픽셀 크기
                crop = on_black(src).crop((0, 15, 108, 93))
                pill = Image.new("RGBA", (150, 78), (0, 0, 0, 255))
                pill.alpha_composite(crop, (0, 0))
                ImageDraw.Draw(pill).rounded_rectangle((0, 0, 149, 77), radius=39, outline=(60, 60, 60, 255), width=1)
                img.alpha_composite(pill, (x, y))
            elif row == "108":
                img.alpha_composite(on_black(src), (x, y))
                for yy in (15, 93):
                    for xx in range(x, x + 108, 6):
                        dr.line((xx, y + yy, xx + 2, y + yy), fill=(255, 159, 10, 255))
            else:
                img.alpha_composite(on_black(src), (x, y))
        y += {"36": 36, "island": 78, "108": 108, "240": 240}[row] + 30
    img.convert("RGB").save(os.path.join(PV, f"preview_{c}.png"), optimize=True)


# 3) 8fps 루프 GIF
def loop_gif(c):
    tmp = []
    for i in range(1, 5):
        L = Image.open(os.path.join(D, f"{c}_run_{i}_L@3x.png")).convert("RGBA")
        S = Image.open(os.path.join(D, f"{c}_run_{i}@3x.png")).convert("RGBA")
        fr = Image.new("RGBA", (240 + 108 + 36 + 48, 256), (0, 0, 0, 255))
        fr.alpha_composite(L, (8, 8))
        fr.alpha_composite(S, (8 + 240 + 16, 8 + 132))
        fr.alpha_composite(S.resize((36, 36), Image.LANCZOS), (8 + 240 + 16 + 108 + 16, 8 + 204))
        p = os.path.join(PV, f"_tmp_{c}_{i}.png")
        fr.convert("RGB").save(p)
        tmp.append(p)
    # GIF 지연은 1/100초 단위라 12.5 를 못 쓴다 → 13/12/13/12 번갈아(4장 50/100초 = 8fps 정확)
    args = ["convert", "-loop", "0"]
    for k, p in enumerate(tmp):
        args += ["-delay", "13" if k % 2 == 0 else "12", p]
    args += ["-layers", "Optimize", os.path.join(PV, f"loop_{c}.gif")]
    subprocess.run(args, check=True)
    for p in tmp:
        os.remove(p)


# 4) 프레임 간 픽셀 차이
def diff(a, b):
    # -fuzz 3%: 안티에일리어싱 미세 차이는 빼고 실제로 달라진 픽셀만 센다. compare 는 결과를 stderr 로 낸다
    r = subprocess.run(["compare", "-metric", "AE", "-fuzz", "3%", a, b, "null:"], capture_output=True, text=True)
    return int(float(r.stderr.split()[0]))


def diff_table():
    pairs = [("run_1", "run_2"), ("run_2", "run_3"), ("run_3", "run_4"), ("run_4", "run_1"),
             ("run_1", "run_3"), ("run_2", "run_4"), ("rest_1", "rest_2"), ("still", "run_1")]
    lines = ["| 캐릭터 | " + " | ".join(f"{a.replace('run_', '달')}↔{b.replace('run_', '달')}" for a, b in pairs) + " |",
             "|---|" + "---|" * len(pairs)]
    for c in CHARS:
        cells = []
        for a, b in pairs:
            n = diff(os.path.join(D, f"{c}_{a}@3x.png"), os.path.join(D, f"{c}_{b}@3x.png"))
            cells.append(f"{n} ({n * 100 / (108 * 108):.1f}%)")
        lines.append(f"| {c} | " + " | ".join(cells) + " |")
    return lines


if __name__ == "__main__":
    bad, rows = check_files()
    print(f"파일 검사: 42장 중 실패 {bad}")
    for c in CHARS:
        preview(c)
        loop_gif(c)
    t = diff_table()
    print("\n".join(t))
    with open(os.path.join(PV, "frame_diff.md"), "w") as f:
        f.write("# 프레임 간 픽셀 차이 (108px, ImageMagick compare -metric AE -fuzz 3%)\n\n"
                "숫자 = 달라진 픽셀 수(108x108=11664 중 비율). 달=달리기, 0 에 가까우면 같은 그림.\n\n" + "\n".join(t) + "\n\n"
                "# 파일 크기·투명 검사 (identify)\n\n| 파일 | 크기 | 채널 | 최소 알파 | 용량 | 판정 |\n|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
