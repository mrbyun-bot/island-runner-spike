"""5라운드 산출물 만들기. python3 build.py [compare|finalists|all]
- compare/: 8종 비교판(검정 바탕, 실제 36px 줄 + 108 + 240), 그레이스케일·실루엣 시험
- finalists/<char>/: 달리기 4 + 쉼 2 + 정지 1, 108px(@3x)·240px(_L@3x), 투명 배경
- gif/: 8fps GIF, finalists/frame_diff.md: 인접 프레임 픽셀 차이
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import Canvas, render_many
import chars, poses

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TMP = os.path.join(ROOT, "src", "_tmp")
os.makedirs(TMP, exist_ok=True)
FONT = "/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf"
FONT_R = "/usr/share/fonts/truetype/nanum/NanumSquareRoundR.ttf"
if not os.path.exists(FONT_R):
    FONT_R = FONT

NAMES = {"dog": "강아지", "rabbit": "토끼", "squirrel": "다람쥐", "turtle": "거북이",
         "rocket": "로켓", "plane": "종이비행기", "balloon": "열기구", "train": "기차"}
ORDER = ["dog", "rabbit", "squirrel", "turtle", "rocket", "plane", "balloon", "train"]
EVAL = json.load(open(os.path.join(ROOT, "src", "eval.json"))) if os.path.exists(
    os.path.join(ROOT, "src", "eval.json")) else {}


def font(sz, bold=True):
    return ImageFont.truetype(FONT if bold else FONT_R, sz)


def fit_box(name, pose_list):
    """여러 포즈 전체를 담는 정사각 viewBox 하나(장마다 크기가 튀지 않게)."""
    big = (-80, -80, 400, 400)
    jobs = []
    for i, pz in enumerate(pose_list):
        cv = Canvas(400); chars.CHARS[name](cv, pz)
        jobs.append((cv.svg(vb=big), f"{TMP}/fit_{name}_{i}.png", 400))
    render_many(jobs)
    x0 = y0 = 1e9; x1 = y1 = -1e9
    for _, f, _ in jobs:
        a = np.array(Image.open(f))[:, :, 3]
        ys, xs = np.nonzero(a > 8)
        x0, x1 = min(x0, xs.min()), max(x1, xs.max())
        y0, y1 = min(y0, ys.min()), max(y1, ys.max())
    sc = big[2] / 400
    bx0, bx1, by0, by1 = big[0] + x0 * sc, big[0] + x1 * sc, big[1] + y0 * sc, big[1] + y1 * sc
    side = max(bx1 - bx0, by1 - by0) * 1.08
    cx = (bx0 + bx1) / 2
    bottom = by1 + side * 0.04
    return (cx - side / 2, bottom - side, side, side)


def render_set(name, pose_list, sizes, vb, prefix):
    jobs = []
    for key, pz in pose_list:
        for sz in sizes:
            cv = Canvas(sz, "small" if sz <= 48 else "full"); chars.CHARS[name](cv, pz)
            jobs.append((cv.svg(vb=vb), f"{prefix}_{key}_{sz}.png", sz))
    render_many(jobs)


# ---------------------------------------------------------------- 비교판
def compare():
    out = os.path.join(ROOT, "compare"); os.makedirs(out, exist_ok=True)
    boxes = {}
    for n in ORDER:
        boxes[n] = fit_box(n, [poses.still(n)])
        render_set(n, [("still", poses.still(n))], (240, 108, 36), boxes[n], f"{TMP}/cmp_{n}")
    W, H = 2040, 1250
    im = Image.new("RGB", (W, H), "black"); d = ImageDraw.Draw(im)
    d.text((40, 30), "5라운드 스타일 확정 시안 · 동물 4 + 사물 4 · 검정 바탕", font=font(30), fill="#FFFFFF")
    d.text((40, 74), "가변 폭 색선 · 셀 음영 1단 · 왼쪽 위 빛 · 3/4 시점(오른쪽 보기) · 맨 위 줄이 실제 36px",
           font=font(20, False), fill="#9A9A9A")
    # 실제 크기 줄: 아일랜드 모양 알약 안에
    d.text((40, 128), "실제 크기 36px (아일랜드 축소 상태에 들어가는 크기)", font=font(20), fill="#FF9F0A")
    x = 40
    for n in ORDER:
        d.rounded_rectangle((x, 160, x + 200, 212), radius=26, fill="#000000", outline="#2A2A2A", width=2)
        s = Image.open(f"{TMP}/cmp_{n}_still_36.png"); im.paste(s, (x + 150, 168), s)
        d.text((x + 18, 175), NAMES[n], font=font(18, False), fill="#BBBBBB")
        x += 245
    for row, group in enumerate([ORDER[:4], ORDER[4:]]):
        y0 = 260 + row * 490
        d.text((40, y0), "동물" if row == 0 else "사물(탈것)", font=font(24), fill="#FFFFFF")
        for i, n in enumerate(group):
            x0 = 40 + i * 500
            ev = EVAL.get(n, {})
            tag = ev.get("tag", "")
            col = {"결선": "#FF9F0A", "통과": "#7FD6A0", "보류": "#C9C9C9", "탈락": "#FF6B6B"}.get(tag, "#C9C9C9")
            d.text((x0, y0 + 44), NAMES[n], font=font(26), fill="#FFFFFF")
            if tag:
                d.text((x0 + 10 + d.textlength(NAMES[n], font=font(26)), y0 + 48), tag, font=font(20), fill=col)
            big = Image.open(f"{TMP}/cmp_{n}_still_240.png"); im.paste(big, (x0, y0 + 90), big)
            mid = Image.open(f"{TMP}/cmp_{n}_still_108.png"); im.paste(mid, (x0 + 260, y0 + 90), mid)
            sm = Image.open(f"{TMP}/cmp_{n}_still_36.png"); im.paste(sm, (x0 + 260, y0 + 214), sm)
            z = sm.resize((108, 108), Image.NEAREST); im.paste(z, (x0 + 320, y0 + 214), z)
            d.text((x0 + 260, y0 + 330), "108 · 36 · 36 확대", font=font(14, False), fill="#777777")
            line = ev.get("line", "")
            for j, t in enumerate(wrap(line, 22)):
                d.text((x0, y0 + 345 + j * 24), t, font=font(17, False), fill="#BDBDBD")
    im.save(os.path.join(out, "compare_8_styles.png"), optimize=True)
    # 그레이스케일(명도) + 실루엣
    g = Image.new("RGB", (2040, 420), "black"); dg = ImageDraw.Draw(g)
    dg.text((40, 24), "명도 시험(그레이스케일 108px) · 아래: 검은 실루엣 36px (윤곽만으로 무엇인지 읽히는가)",
            font=font(22), fill="#FFFFFF")
    for i, n in enumerate(ORDER):
        x0 = 40 + i * 245
        m = Image.open(f"{TMP}/cmp_{n}_still_108.png")
        gray = Image.merge("RGBA", (*[m.convert("L")] * 3, m.split()[3]))
        g.paste(gray, (x0, 80), gray)
        s = Image.open(f"{TMP}/cmp_{n}_still_36.png")
        sil = Image.new("RGBA", s.size, (235, 235, 235, 255)); sil.putalpha(s.split()[3])
        sil2 = sil.resize((72, 72), Image.NEAREST)
        g.paste(sil, (x0, 230), sil); g.paste(sil2, (x0 + 50, 230), sil2)
        dg.text((x0, 330), NAMES[n], font=font(18, False), fill="#BBBBBB")
    g.save(os.path.join(out, "value_silhouette_test.png"), optimize=True)
    json.dump({n: boxes[n] for n in ORDER}, open(os.path.join(ROOT, "src", "viewboxes.json"), "w"), indent=1)
    print("compare done")


def wrap(t, n):
    out, cur = [], ""
    for w in t.split(" "):
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------- 결선
def finalists(names):
    for n in names:
        fd = os.path.join(ROOT, "finalists", n); os.makedirs(fd, exist_ok=True)
        seq = poses.sequence(n)  # [(key, pose)]
        vb = fit_box(n, [pz for _, pz in seq])
        render_set(n, seq, (108, 240, 36), vb, f"{TMP}/fin_{n}")
        for key, _ in seq:
            Image.open(f"{TMP}/fin_{n}_{key}_108.png").save(f"{fd}/{n}_{key}@3x.png", optimize=True)
            Image.open(f"{TMP}/fin_{n}_{key}_240.png").save(f"{fd}/{n}_{key}_L@3x.png", optimize=True)
        sheet(n, seq, fd)
        gifs(n)
    diff_table(names)


def sheet(n, seq, fd):
    im = Image.new("RGB", (1960, 640), "black"); d = ImageDraw.Draw(im)
    d.text((30, 20), f"{NAMES[n]} · 달리기 4장 + 쉼 2장 + 정지 1장 · 위 240px, 아래 108px와 실제 36px",
           font=font(24), fill="#FFFFFF")
    lab = {"run_1": "달리기1", "run_2": "달리기2", "run_3": "달리기3", "run_4": "달리기4", "rest_1": "쉼1",
           "rest_2": "쉼2", "still": "정지"}
    for i, (key, _) in enumerate(seq):
        x = 30 + i * 275
        L = Image.open(f"{TMP}/fin_{n}_{key}_240.png"); im.paste(L, (x, 70), L)
        d.rectangle((x, 70, x + 239, 309), outline="#222222")
        M = Image.open(f"{TMP}/fin_{n}_{key}_108.png"); im.paste(M, (x, 360), M)
        S = Image.open(f"{TMP}/fin_{n}_{key}_36.png"); im.paste(S, (x + 140, 400), S)
        d.text((x, 520), lab[key], font=font(20, False), fill="#BBBBBB")
    im.save(os.path.join(fd, f"{n}_sheet.png"), optimize=True)


def gifs(n):
    gd = os.path.join(ROOT, "gif"); os.makedirs(gd, exist_ok=True)
    def frames(keys, sz):
        out = []
        for k in keys:
            f = Image.open(f"{TMP}/fin_{n}_{k}_{sz}.png")
            bg = Image.new("RGBA", f.size, (0, 0, 0, 255)); bg.alpha_composite(f)
            out.append(bg.convert("RGB"))
        return out
    run = ["run_1", "run_2", "run_3", "run_4"]
    for sz in (240, 108):
        fr = frames(run, sz)
        fr[0].save(f"{gd}/{n}_run_{sz}_8fps.gif", save_all=True, append_images=fr[1:], duration=125, loop=0)
    flow = ["still"] * 4 + run * 4 + ["rest_1", "rest_1", "rest_2", "rest_2"] * 3
    fr = frames(flow, 240)
    fr[0].save(f"{gd}/{n}_flow_240_8fps.gif", save_all=True, append_images=fr[1:], duration=125, loop=0)


def diff_table(names):
    rows = ["# 인접 프레임 픽셀 차이 (108px, RGBA 어느 채널이든 8% 넘게 다른 화소 비율)", "",
            "| 캐릭터 | 1→2 | 2→3 | 3→4 | 4→1 | 1→3 | 쉼1↔쉼2 | 정지↔달리기1 |", "|---|---|---|---|---|---|---|---|"]
    for n in names:
        def A(k):
            return np.array(Image.open(f"{TMP}/fin_{n}_{k}_108.png").convert("RGBA")).astype(int)
        def df(a, b):
            return 100 * np.mean(np.abs(A(a) - A(b)).max(2) > 20)
        pairs = [("run_1", "run_2"), ("run_2", "run_3"), ("run_3", "run_4"), ("run_4", "run_1"), ("run_1", "run_3"),
                 ("rest_1", "rest_2"), ("still", "run_1")]
        rows.append(f"| {NAMES[n]} | " + " | ".join(f"{df(a, b):.1f}%" for a, b in pairs) + " |")
    rows += ["", "판정 기준: 달리기 인접 4쌍이 모두 8% 이상이면 \"서로 다른 포즈\". 1→3 이 0% 에 가까우면 3번 장이 1번 장의 복사본이라는 뜻이라 실패."]
    open(os.path.join(ROOT, "finalists", "frame_diff.md"), "w").write("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("compare", "all"):
        compare()
    if what in ("finalists", "all"):
        finalists(sys.argv[2:] or poses.FINALISTS)


def process_strip(n="turtle"):
    """같은 캐릭터를 공정 단계별로: ① 구성 형태(러프) ② 가변 폭 색선 ③ 평면색 ④ 셀 음영·하이라이트(완성)."""
    vb = fit_box(n, [poses.still(n)])
    jobs = []
    for m in ("rough", "line", "flat", "final"):
        cv = Canvas(300); cv.mode = m; chars.CHARS[n](cv, poses.still(n))
        jobs.append((cv.svg(vb=vb), f"{TMP}/proc_{n}_{m}.png", 300))
    render_many(jobs)
    im = Image.new("RGB", (1300, 420), "black"); d = ImageDraw.Draw(im)
    d.text((30, 20), f"공정 단계 · {NAMES[n]}", font=font(24), fill="#FFFFFF")
    labs = ["① 구성 형태(조절점 곡선)", "② 가변 폭 색선", "③ 평면색", "④ 셀 음영 1단 + 하이라이트"]
    for i, m in enumerate(("rough", "line", "flat", "final")):
        f = Image.open(f"{TMP}/proc_{n}_{m}.png")
        if m == "line":
            bg = Image.new("RGBA", f.size, (0, 0, 0, 255)); bg.alpha_composite(f); f = bg
        im.paste(f, (20 + i * 320, 70), f.convert("RGBA"))
        d.text((24 + i * 320, 380), labs[i], font=font(18, False), fill="#BBBBBB")
    out = os.path.join(ROOT, "research"); os.makedirs(out, exist_ok=True)
    im.save(os.path.join(out, f"process_{n}.png"), optimize=True)
