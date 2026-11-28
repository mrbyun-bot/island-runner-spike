#!/usr/bin/env python3
"""7라운드: 한 가지 색 실루엣 + 어두운 눈 두 개, 11종을 한 번에 다시 만든다.

python3 art/round7/src/build_all.py   (저장소 어디서 실행해도 됨, 약 1~2분)

규칙
- 좌표계 108×108(=36pt@3x). 아일랜드에서 실제로 보이는 곳은 y 15~93.
- 캐릭터당 몸색 하나. 보조 색 면·윤곽선·음영 없음. 눈만 먹색 + 작은 흰 하이라이트.
- 몸은 도형을 겹친 뒤 흐림→문턱으로 이음새를 녹여 한 덩어리 곡선으로 만든다(shapes.py).
- 달리기 4장: 뻗음 → 모음 → 반대 뻗음 → 모음. 쉼 2장은 눈 감고 세로 4.5% 숨쉬기.
"""
import math, os, sys, json
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from chars import DRAW, POSES, PAL, ORDER   # noqa: E402
from shapes import shrink, EYE              # noqa: E402

ROOT = os.path.dirname(HERE)  # art/round7
OUT_CH = os.path.join(ROOT, "characters")
OUT_GIF = os.path.join(ROOT, "gif")
OUT_CMP = os.path.join(ROOT, "compare")
TMP36 = os.path.join("/tmp", f"r7_36_{os.getuid()}")
MIN_DIFF = 0.18


def job(arg):
    c, pz = arg
    big = DRAW[c](pz)
    col = PAL[c][1]
    os.makedirs(os.path.join(OUT_CH, c), exist_ok=True)
    shrink(big, col, 108).save(os.path.join(OUT_CH, c, f"{c}_{pz}@3x.png"), optimize=True)
    shrink(big, col, 240).save(os.path.join(OUT_CH, c, f"{c}_{pz}_L@3x.png"), optimize=True)
    shrink(big, col, 36).save(os.path.join(TMP36, f"{c}_{pz}.png"))
    return c, pz


def lum(hexc):
    c = [int(hexc[j:j + 2], 16) / 255 for j in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def frame_diff(a, b):
    A = np.asarray(a.convert("RGBA")).astype(int); B = np.asarray(b.convert("RGBA")).astype(int)
    union = (A[..., 3] > 40) | (B[..., 3] > 40)
    ch = (np.abs(A - B).max(axis=2) > 48) & union
    return ch.sum() / max(1, union.sum())


def img(c, pz, size):
    if size == 36:
        return Image.open(os.path.join(TMP36, f"{c}_{pz}.png")).convert("RGBA")
    suf = "_L" if size == 240 else ""
    return Image.open(os.path.join(OUT_CH, c, f"{c}_{pz}{suf}@3x.png")).convert("RGBA")


def main():
    for dd in (OUT_CH, OUT_GIF, OUT_CMP, TMP36):
        os.makedirs(dd, exist_ok=True)
    jobs = [(c, pz) for c in ORDER for pz in POSES]
    with Pool(3) as pool:
        for _ in pool.imap_unordered(job, jobs):
            pass

    rows = ["# 인접 프레임 픽셀 차이 (108px, 7라운드)", "",
            "계산: 두 장 중 하나라도 불투명한 픽셀 가운데 색·투명도가 눈에 띄게(채널 차 48 이상) 바뀐 비율. "
            f"기준 {MIN_DIFF*100:.0f}% 이상.", "",
            "| 캐릭터 | 1→2 | 2→3 | 3→4 | 4→1 | 최소 | 판정 |", "|---|---|---|---|---|---|---|"]
    diffs = {}
    for c in ORDER:
        fr = [img(c, f"run_{j}", 108) for j in range(1, 5)]
        ds = [frame_diff(fr[j], fr[(j + 1) % 4]) for j in range(4)]
        diffs[c] = ds
        rows.append(f"| {PAL[c][0]} ({c}) | " + " | ".join(f"{x*100:.0f}%" for x in ds)
                    + f" | {min(ds)*100:.0f}% | {'통과' if min(ds) >= MIN_DIFF else '미달'} |")
    with open(os.path.join(ROOT, "frame_diff.md"), "w") as f:
        f.write("\n".join(rows) + "\n")

    eyehex = "#%02X%02X%02X" % EYE
    con = {c: {"body_vs_black": round(contrast(PAL[c][1], "#000000"), 1),
               "eye_vs_body": round(contrast(PAL[c][1], eyehex), 1)} for c in ORDER}
    with open(os.path.join(HERE, "contrast.json"), "w") as f:
        json.dump({"eye": eyehex, "contrast": con,
                   "frame_diff": {c: [round(x, 3) for x in v] for c, v in diffs.items()}},
                  f, ensure_ascii=False, indent=1)

    for c in ORDER:
        for size in (108, 240):
            fr = [img(c, f"run_{j}", size) for j in range(1, 5)]
            bg = []
            for im in fr:
                base = Image.new("RGBA", im.size, (0, 0, 0, 255)); base.alpha_composite(im)
                bg.append(base.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=32))
            bg[0].save(os.path.join(OUT_GIF, f"{c}_run_{size}_8fps.gif"), save_all=True,
                       append_images=bg[1:], duration=125, loop=0, disposal=2)

    make_board(diffs, con)
    print("완료:", len(jobs) * 2, "장 저장")
    for c in ORDER:
        print(c, [f"{x*100:.0f}" for x in diffs[c]], con[c])


VERDICT_FILE = os.path.join(HERE, "verdict.json")


def font(sz, bold=False):
    fdir = "/usr/share/fonts/truetype/nanum/"
    for n in (["NanumGothicBold.ttf"] if bold else ["NanumGothic.ttf"]):
        if os.path.exists(fdir + n):
            return ImageFont.truetype(fdir + n, sz)
    return ImageFont.load_default()


def tile(im, size):
    t = Image.new("RGBA", (size, size), (0, 0, 0, 255)); t.alpha_composite(im)
    return t.convert("RGB")


def make_board(diffs, con):
    verdict = json.load(open(VERDICT_FILE)) if os.path.exists(VERDICT_FILE) else {}
    FB, FS, FT = font(26, True), font(18), font(14)
    colw, rowh, pad, cols = 760, 300, 30, 2
    nrows = math.ceil(len(ORDER) / cols)
    W = cols * colw + pad * 2
    H = 150 + nrows * rowh + 40
    board = Image.new("RGB", (W, H), (0, 0, 0))
    dr = ImageDraw.Draw(board)
    dr.text((pad, 24), "7라운드: 한 가지 색 실루엣 + 눈 두 개, 11종", fill=(240, 240, 240), font=font(34, True))
    dr.text((pad, 72), "각 칸 왼쪽 위: 실제 36px 달리기 4장 · 정지 · 쉼 / 아래: 36px 를 3배 확대(뻗음·모음) / 가운데 108px / 오른쪽 240px.  "
            "회색 띠 = 아일랜드에서 잘리는 위아래", fill=(170, 170, 170), font=FS)
    dr.text((pad, 100), "판정: ○ 36px 에서 바로 읽힘  △ 읽히지만 약함  × 36px 에서 그 동물·물건으로 안 읽힘",
            fill=(170, 170, 170), font=FS)
    for n, c in enumerate(ORDER):
        cx = pad + (n % cols) * colw; cy = 140 + (n // cols) * rowh
        v = verdict.get(c, {"mark": "?", "note": ""})
        dr.text((cx, cy), f"{v['mark']} {PAL[c][0]}", fill=(240, 240, 240), font=FB)
        dr.text((cx + 200, cy + 6), v["note"], fill=(200, 200, 200), font=FS)
        x = cx; y = cy + 44
        for pz in ["run_1", "run_2", "run_3", "run_4", "still", "rest_1"]:
            board.paste(tile(img(c, pz, 36), 36), (x, y))
            dr.rectangle([x, y, x + 35, y + 4], fill=(40, 40, 40))
            dr.rectangle([x, y + 31, x + 35, y + 35], fill=(40, 40, 40))
            x += 44
        dr.text((cx, y + 42), "36px 실제 크기", fill=(130, 130, 130), font=FT)
        x = cx; y2 = cy + 110
        for pz in ["run_1", "run_2"]:
            board.paste(tile(img(c, pz, 36).resize((108, 108), Image.NEAREST), 108), (x, y2)); x += 116
        dr.text((cx, y2 + 112), "36px 를 3배 확대(뻗음·모음)", fill=(130, 130, 130), font=FT)
        x = cx + 250
        board.paste(tile(img(c, "run_1", 108), 108), (x, cy + 110))
        dr.rectangle([x, cy + 110, x + 107, cy + 124], outline=(50, 50, 50))
        dr.rectangle([x, cy + 203, x + 107, cy + 217], outline=(50, 50, 50))
        x += 124
        board.paste(tile(img(c, "run_1", 240), 240), (x, cy + 36))
        dr.line([x, cy + 36 + 33, x + 239, cy + 36 + 33], fill=(50, 50, 50))
        dr.line([x, cy + 36 + 207, x + 239, cy + 36 + 207], fill=(50, 50, 50))
        dr.rectangle([cx + 250, cy + 236, cx + 280, cy + 256], fill=PAL[c][1])
        dr.text((cx + 290, cy + 238), PAL[c][1], fill=(170, 170, 170), font=FT)
        dr.text((cx + 250, cy + 262), f"검정 대비 {con[c]['body_vs_black']}:1 · 눈/몸 {con[c]['eye_vs_body']}:1 · "
                f"프레임차 최소 {min(diffs[c])*100:.0f}%", fill=(130, 130, 130), font=FT)
    board.save(os.path.join(OUT_CMP, "family_11.png"), optimize=True)

    strip = Image.new("RGB", (len(ORDER) * 44 + 20, 46), (0, 0, 0))
    for n, c in enumerate(ORDER):
        strip.paste(tile(img(c, "run_1", 36), 36).crop((0, 5, 36, 31)), (10 + n * 44, 10))
    strip.save(os.path.join(OUT_CMP, "island_strip_actual.png"))
    strip.resize((strip.width * 3, strip.height * 3), Image.NEAREST).save(
        os.path.join(OUT_CMP, "island_strip_x3.png"))


if __name__ == "__main__":
    main()
