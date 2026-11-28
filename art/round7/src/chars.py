"""7라운드 11종. 캐릭터당 한 가지 색 실루엣 + 어두운 눈 두 개(작은 흰 하이라이트).

달리기 4장: 뻗음 → 모음(공중) → 반대 뻗음(착지) → 모음(땅).
몸을 위아래로 흔들기보다 몸통을 늘이고 줄이는(스쿼시·스트레치) 쪽으로 움직인다.
"""
import math
from shapes import ell, circ, cap, limb, bez, chain, aff, apt, Part, render

GROUND = 90
POSES = ["run_1", "run_2", "run_3", "run_4", "rest_1", "rest_2", "still"]

PAL = {
    "dog":        ("강아지",       "#FFB15E"),
    "rabbit":     ("토끼",         "#FFB0CC"),
    "turtle":     ("거북이",       "#B2E36A"),
    "duck":       ("오리",         "#FFE35A"),
    "squirrel":   ("다람쥐",       "#DBA67F"),
    "panda":      ("판다",         "#E2E5EA"),
    "train":      ("기차",         "#78DDB8"),
    "bike":       ("자전거",       "#B9B6FF"),
    "skateboard": ("스케이트보드", "#62D4E6"),
    "balloon":    ("열기구",       "#FF8A7A"),
    "rocket":     ("로켓",         "#9CC8FF"),
}
ORDER = list(PAL)


def mode_of(pose):
    if pose.startswith("run"):
        return "run", int(pose[-1]) - 1
    if pose.startswith("rest"):
        return "rest", int(pose[-1]) - 1
    return "still", 0


BREATH = [1.0, 1.045]

# 네발 동물 달리기 표: 늘이기 sx, 줄이기 sy, 기울기(-는 코 위), 높이, 앞다리·뒷다리 각도(+는 앞)
QRUN = [
    dict(sx=1.24, sy=0.80, rot=-8, dy=-3, fa=64, ha=-66, sp=12),   # 뻗음(도약)
    dict(sx=0.82, sy=1.14, rot=0, dy=-7, fa=-34, ha=36, sp=8),     # 모음(공중)
    dict(sx=1.18, sy=0.84, rot=7, dy=0, fa=30, ha=-84, sp=12),     # 반대 뻗음(착지)
    dict(sx=0.88, sy=1.06, rot=-2, dy=2, fa=-10, ha=12, sp=6),     # 모음(땅)
]
QSTILL = dict(sx=1.0, sy=1.0, rot=0, dy=0, fa=4, ha=-4, sp=7)


# ------------------------------------------------------------------ 네발 공통 뼈대
def quad(pose, c):
    mode, i = mode_of(pose)
    brx, bry, LL, lw, bx = c["brx"], c["bry"], c["LL"], c["lw"], c["bx"]
    by0 = GROUND - LL - bry * 0.45
    if mode == "rest":
        rx, ry = brx * 1.06, bry * 0.92
        by = GROUND - ry * 0.98
        rot = 0
    else:
        f = QRUN[i] if mode == "run" else QSTILL
        rx, ry = brx * f["sx"], bry * f["sy"]
        by = by0 + f["dy"] + (bry - ry) * 0.6
        rot = f["rot"]
    a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)

    def R(lx, ly):
        return (bx + lx * ca - ly * sa, by + lx * sa + ly * ca)

    hr = c["hr"]
    hx, hy = R(0.8 * rx + c["hdx"], -0.55 * ry + c["hdy"])
    if mode == "rest":
        hx, hy = R(0.86 * rx + c["hdx"], -0.25 * ry + c["hdy"])
    shoulder, hip = R(0.55 * rx, 0.3 * ry), R(-0.58 * rx, 0.3 * ry)
    polys = [ell(bx, by, rx, ry, rot), circ(hx, hy, hr)]
    if mode == "rest":
        polys += [cap(shoulder[0], GROUND - lw / 2, shoulder[0] + 14, GROUND - lw / 2, lw),
                  ell(hip[0], GROUND - lw * 0.6, lw * 1.3, lw * 0.6)]
    else:
        L = LL + ry * 0.2
        for ang in (f["fa"] + f["sp"], f["fa"] - f["sp"]):
            polys.append(limb(shoulder[0], shoulder[1], L, ang, lw))
        for ang in (f["ha"] - f["sp"], f["ha"] + f["sp"]):
            polys.append(limb(hip[0], hip[1], L, ang, lw))
    ctx = dict(mode=mode, i=i, rx=rx, ry=ry, bx=bx, by=by, rot=rot, R=R, hx=hx, hy=hy, hr=hr)
    polys += c["feat"](ctx)
    parts = [Part(polys, smooth=c.get("smooth", 1.7))]
    eyes = c["eyes"](ctx)
    return finish(c["id"], parts, eyes, mode, i, anchor=(bx, GROUND))


# 캐릭터별 크기 맞춤(배율, 가로 이동): 달리기·쉼 7장을 합친 테두리가 y 16~92, x 4~104 안에 들도록.
FIT = {'dog': (1.31, 9.2, -8.2), 'rabbit': (1.07, 10.2, -5.4), 'turtle': (1.053, 2.6, -3.2), 'duck': (1.134, 2.3, -2.4), 'squirrel': (1.041, 7.3, -5.2), 'panda': (1.188, 10.1, -8.5), 'train': (0.894, 3.6, -1.7), 'bike': (1.041, -0.5, 2.0), 'skateboard': (0.971, -0.5, -4.8), 'balloon': (0.905, 0.0, 1.0), 'rocket': (0.95, 3.3, -7.5)}
EYE_GROW = 1.12   # 36px 에서 눈이 묻히지 않게 조금 키움


def finish(cid, parts, eyes, mode, i, anchor=(54, GROUND)):
    """크기 맞춤 → 쉼이면 눈 감고 세로 숨쉬기."""
    color = PAL[cid][1]
    s_, dx_, dy_ = FIT.get(cid, (1.0, 0.0, 0.0))
    for p in parts:
        p.add = aff(p.add, sx=s_, sy=s_, ox=54, oy=GROUND, dx=dx_, dy=dy_)
        p.cut = aff(p.cut, sx=s_, sy=s_, ox=54, oy=GROUND, dx=dx_, dy=dy_)
        p.smooth *= s_; p.gap *= s_
    eyes = [(54 + (x - 54) * s_ + dx_, GROUND + (y - GROUND) * s_ + dy_, rx * s_ * EYE_GROW, ry * s_ * EYE_GROW, r)
            for (x, y, rx, ry, r) in eyes]
    anchor = (54 + (anchor[0] - 54) * s_ + dx_, GROUND + dy_)
    if mode == "rest":
        s = BREATH[i]
        for p in parts:
            p.add = aff(p.add, sy=s, ox=anchor[0], oy=anchor[1])
            p.cut = aff(p.cut, sy=s, ox=anchor[0], oy=anchor[1])
        closed = []
        for (cx, cy, rx, ry, rot) in eyes:
            cy = anchor[1] + (cy - anchor[1]) * s
            closed.append((cx, cy, max(rx, 2.6) * 1.05))
        return render(color, parts, closed=closed)
    return render(color, parts, eyes=eyes)


def dirpt(x, y, deg, ln):
    a = math.radians(deg)
    return (x + ln * math.cos(a), y + ln * math.sin(a))


# ------------------------------------------------------------------ 강아지: 펄럭이는 처진 귀 + 주둥이
def dog(pose):
    def feat(t):
        hx, hy, hr, i, m = t["hx"], t["hy"], t["hr"], t["i"], t["mode"]
        ea = [208, 158, 218, 172][i] if m == "run" else (128 if m == "still" else 150)
        base = (hx - 0.45 * hr, hy - 0.55 * hr)
        mid = dirpt(*base, ea, 7)
        ear = ell(mid[0], mid[1], 8, 4.6, ea)
        ta = [238, 212, 246, 222][i] if m == "run" else (232 if m == "still" else 200)
        tb = t["R"](-t["rx"] * 0.9, -t["ry"] * 0.35)
        te = dirpt(*tb, ta, 10)
        return [ear, ell(hx + 0.88 * hr, hy + 0.34 * hr, 7.5, 5.4), cap(*tb, *te, 4.6)]

    def eyes(t):
        hx, hy, hr = t["hx"], t["hy"], t["hr"]
        return [(hx + 0.08 * hr, hy - 0.2 * hr, 3.5, 3.5, 0), (hx + 0.58 * hr, hy - 0.22 * hr, 3.5, 3.5, 0)]
    return quad(pose, dict(id="dog", brx=21, bry=12, hr=12.5, LL=15, lw=7.5, bx=44, hdx=2, hdy=-2,
                           feat=feat, eyes=eyes))


# ------------------------------------------------------------------ 토끼: 긴 귀 두 개 + 동그란 꼬리
def rabbit(pose):
    def feat(t):
        hx, hy, hr, i, m = t["hx"], t["hy"], t["hr"], t["i"], t["mode"]
        sw = [-20, 6, -26, 0][i] if m == "run" else (0 if m == "still" else -48)
        out = []
        for (bx_, by_, a0, ln) in ((hx - 0.3 * hr, hy - 0.6 * hr, -112, 20), (hx + 0.12 * hr, hy - 0.72 * hr, -96, 19)):
            e = dirpt(bx_, by_, a0 + sw, ln)
            out.append(cap(bx_, by_, *e, 6.4))
        tb = t["R"](-t["rx"] * 1.0, -t["ry"] * 0.15)
        out.append(circ(*tb, 5.2))
        return out

    def eyes(t):
        hx, hy, hr = t["hx"], t["hy"], t["hr"]
        return [(hx + 0.12 * hr, hy - 0.02 * hr, 3.1, 3.4, 0), (hx + 0.66 * hr, hy + 0.0 * hr, 3.1, 3.4, 0)]
    return quad(pose, dict(id="rabbit", brx=18, bry=12.5, hr=12, LL=12, lw=7, bx=44, hdx=1, hdy=-1,
                           feat=feat, eyes=eyes))


# ------------------------------------------------------------------ 다람쥐: 몸보다 큰 꼬리
def squirrel(pose):
    def feat(t):
        hx, hy, hr, i, m = t["hx"], t["hy"], t["hr"], t["i"], t["mode"]
        tb = t["R"](-t["rx"] * 0.85, -t["ry"] * 0.2)
        rel = [(-5, -3), (-11, -11), (-13, -22), (-9, -32), (-1, -37), (6, -35)]
        rad = [5, 6.5, 8, 8.5, 8, 6]
        tr = [-22, 8, -14, 14][i] if m == "run" else (0 if m == "still" else 22)
        ts = [1.0, 0.9, 1.0, 0.92][i] if m == "run" else (1.0 if m == "still" else 0.85)
        pts = [apt((tb[0] + x * ts, tb[1] + y * ts), rot=tr, ox=tb[0], oy=tb[1]) for x, y in rel]
        ear = ell(hx - 0.25 * hr, hy - 0.95 * hr, 3.4, 5.6, -12)
        return chain(pts, [r * ts for r in rad]) + [ear]

    def eyes(t):
        hx, hy, hr = t["hx"], t["hy"], t["hr"]
        return [(hx + 0.22 * hr, hy - 0.05 * hr, 3.4, 3.4, 0), (hx + 0.7 * hr, hy - 0.02 * hr, 3.0, 3.0, 0)]
    return quad(pose, dict(id="squirrel", brx=15, bry=11, hr=11, LL=11, lw=6.2, bx=56, hdx=1, hdy=-2,
                           feat=feat, eyes=eyes))


# ------------------------------------------------------------------ 판다: 둥근 귀 + 처진 큰 눈(눈 무늬를 눈으로)
def panda(pose):
    def feat(t):
        hx, hy, hr = t["hx"], t["hy"], t["hr"]
        return [circ(hx - 0.62 * hr, hy - 0.78 * hr, 5.6), circ(hx + 0.34 * hr, hy - 0.92 * hr, 5.6),
                circ(*t["R"](-t["rx"] * 0.98, -t["ry"] * 0.2), 4)]

    def eyes(t):
        hx, hy, hr = t["hx"], t["hy"], t["hr"]
        return [(hx - 0.1 * hr, hy + 0.06 * hr, 3.9, 5.6, 28), (hx + 0.5 * hr, hy + 0.06 * hr, 3.9, 5.6, -28)]
    return quad(pose, dict(id="panda", brx=23, bry=15, hr=15, LL=11, lw=10, bx=44, hdx=0, hdy=-1,
                           feat=feat, eyes=eyes))


# ------------------------------------------------------------------ 거북이: 둥근 등딱지 + 앞으로 뺀 목
TRUN = [dict(sx=1.14, sy=0.86, dy=-1, fa=46, neck=7), dict(sx=0.88, sy=1.12, dy=-4, fa=-30, neck=-2),
        dict(sx=1.1, sy=0.9, dy=0, fa=-46, neck=5), dict(sx=0.92, sy=1.05, dy=1, fa=22, neck=0)]


def turtle(pose):
    mode, i = mode_of(pose)
    bx, yb = 44, 79
    f = TRUN[i] if mode == "run" else dict(sx=1, sy=1, dy=0, fa=4, neck=2 if mode == "still" else -4)
    sx, sy = f["sx"], f["sy"]
    if mode == "rest":
        sx, sy, yb = 1.04, 0.96, 85
    yb += f["dy"]
    shell = ell(bx, yb, 27 * sx, 26 * sy)
    cutb = [[(-50, yb + 3), (160, yb + 3), (160, 200), (-50, 200)]]
    legs = []
    if mode != "rest":
        L = GROUND - yb + 1
        for (lx, ang) in ((bx + 15 * sx, f["fa"]), (bx + 7 * sx, -f["fa"]), (bx - 9 * sx, -f["fa"]), (bx - 18 * sx, f["fa"])):
            legs.append(limb(lx, yb - 2, L, ang * 0.7, 9.5))
    nk = f["neck"]
    hx, hy = bx + 27 * sx + 6 + nk, yb - 10 - (2 if mode == "run" and i in (0, 2) else 0)
    if mode == "rest":
        hx, hy = bx + 26 * sx + 3, yb - 5
    head = [circ(hx, hy, 10.5), cap(bx + 16 * sx, yb - 4, hx - 3, hy + 1, 10)]
    tail = [cap(bx - 26 * sx, yb - 1, bx - 33 * sx, yb + 3, 5)]
    parts = [Part([shell], cut=cutb, smooth=1.8),
             Part(legs + head + tail + [ell(bx, yb + 1, 26 * sx, 4)], smooth=1.6)]
    eyes = [(hx - 0.5, hy - 2.2, 3.0, 3.2, 0), (hx + 5.4, hy - 2.4, 3.0, 3.2, 0)]
    return finish("turtle", parts, eyes, mode, i, anchor=(bx, GROUND))


# ------------------------------------------------------------------ 오리: 납작한 부리 + 위로 솟은 꼬리, 두 발
DRUN = [dict(sx=1.16, sy=0.86, rot=-8, dy=-3, la=48, lb=-40, ll=13),
        dict(sx=0.86, sy=1.12, rot=0, dy=-7, la=10, lb=-6, ll=8),
        dict(sx=1.12, sy=0.88, rot=8, dy=0, la=-42, lb=46, ll=13),
        dict(sx=0.92, sy=1.06, rot=-2, dy=2, la=-4, lb=8, ll=10)]


def duck(pose):
    mode, i = mode_of(pose)
    f = DRUN[i] if mode == "run" else dict(sx=1, sy=1, rot=0, dy=0, la=6, lb=-6, ll=12)
    bx = 46
    rx, ry = 19 * f["sx"], 14 * f["sy"]
    by = GROUND - 12 - ry * 0.75 + f["dy"]
    rot = f["rot"]
    if mode == "rest":
        rx, ry, by, rot = 21, 13, GROUND - 12.5, 0
    a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)

    def R(lx, ly):
        return (bx + lx * ca - ly * sa, by + lx * sa + ly * ca)
    hx, hy = R(rx * 0.72, -ry - 6)
    if mode == "rest":
        hx, hy = R(rx * 0.7, -ry - 1)
    hr = 11.5
    tail = [R(-rx * 0.7, -ry * 0.5), R(-rx * 1.32, -ry * 1.25), R(-rx * 0.6, ry * 0.3)]
    polys = [ell(bx, by, rx, ry, rot), circ(hx, hy, hr), tail,
             ell(hx + hr * 0.98, hy + hr * 0.28, 8.5, 3.8, -4)]
    if mode != "rest":
        for (lx, ang) in ((3, f["la"]), (-5, f["lb"])):
            hpt = R(lx, ry * 0.75)
            a2 = math.radians(ang); L = f["ll"]
            fx, fy = hpt[0] + L * math.sin(a2), hpt[1] + L * math.cos(a2)
            polys += [cap(*hpt, fx, fy, 4.4), ell(fx + 3, fy, 5.6, 2.6, ang * 0.3)]
    parts = [Part(polys, smooth=1.5)]
    eyes = [(hx + 0.02 * hr, hy - 0.2 * hr, 3.3, 3.3, 0), (hx + 0.5 * hr, hy - 0.24 * hr, 3.3, 3.3, 0)]
    return finish("duck", parts, eyes, mode, i, anchor=(bx, GROUND))


# ------------------------------------------------------------------ 기차: 굴뚝 + 바퀴 셋 + 연기
TRAIN = [dict(sx=1.08, sy=0.88, ws=1.12, dy=0), dict(sx=0.94, sy=1.08, ws=0.92, dy=-3),
         dict(sx=1.06, sy=0.9, ws=1.08, dy=0, lean=3), dict(sx=0.96, sy=1.04, ws=0.96, dy=1)]


def train(pose):
    mode, i = mode_of(pose)
    f = TRAIN[i] if mode == "run" else dict(sx=1, sy=1, ws=1, dy=0)
    body = [bez([(14, 78), ((14, 78), (14, 34), (14, 34)), ((14, 30), (40, 30), (40, 34)),
                 ((40, 34), (40, 46), (44, 46)), ((60, 46), (86, 46), (88, 54)),
                 ((92, 64), (94, 78), (90, 78)), ((60, 78), (30, 78), (14, 78))]),
            cap(78, 52, 79, 40, 10), ell(79, 37, 7.5, 3.5),           # 굴뚝
            cap(10, 31, 44, 31, 6)]                                    # 지붕
    body = aff(body, sx=f["sx"], sy=f["sy"], ox=54, oy=80, rot=f.get("lean", 0), rox=54, roy=80, dy=f["dy"])
    wheels = []
    for wx in (28, 56, 80):
        wx2 = 54 + (wx - 54) * f["sx"]
        wheels.append(ell(wx2, 84 - 8 * (1 / f["ws"] - 1), 8.2 * f["ws"], 8.2 / f["ws"]))
    puffs = []
    top = apt((79, 33), sx=f["sx"], sy=f["sy"], ox=54, oy=80, dy=f["dy"])
    if mode == "run":
        sets = [[(2, -6, 5.5), (-9, -13, 4.5), (-22, -16, 3.4)], [(1, -8, 6.5), (-12, -12, 5.5), (-25, -14, 4)],
                [(3, -5, 4.5), (-7, -14, 6.5), (-20, -18, 4.5)], [(0, -7, 6), (-14, -13, 4), (-26, -16, 5)]][i]
    elif mode == "rest":
        sets = [[(2, -6, 3.5)], [(2, -7, 4.5)]][i]
    else:
        sets = [(2, -6, 4)]
    for (dx, dy, r) in sets:
        puffs.append(circ(top[0] + dx, max(14, top[1] + dy), r))
    parts = [Part(body, smooth=2.6), Part(wheels, smooth=0, gap=2.4), Part(puffs, smooth=0.8, gap=1.5)]
    e1 = apt((66, 60), sx=f["sx"], sy=f["sy"], ox=54, oy=80, dy=f["dy"])
    e2 = apt((79, 60), sx=f["sx"], sy=f["sy"], ox=54, oy=80, dy=f["dy"])
    eyes = [(e1[0], e1[1], 3.6, 3.6, 0), (e2[0], e2[1], 3.6, 3.6, 0)]
    return finish("train", parts, eyes, mode, i, anchor=(54, GROUND))


# ------------------------------------------------------------------ 자전거: 바퀴 두 개(고리) + 통통한 삼각 몸
BIKE = [dict(sx=1.1, sy=0.9, rot=0, dy=0, wsx=1.08), dict(sx=0.92, sy=1.08, rot=0, dy=-5, wsx=0.95),
        dict(sx=1.04, sy=0.96, rot=-12, dy=-1, wsx=1.0), dict(sx=0.96, sy=1.02, rot=0, dy=1, wsx=1.1)]


def bike(pose):
    mode, i = mode_of(pose)
    f = BIKE[i] if mode == "run" else dict(sx=1, sy=1, rot=0, dy=0, wsx=1.0)
    rw, fw = (27, 73), (82, 73)
    frame = [bez([(30, 70), ((38, 52), (44, 42), (50, 40)), ((60, 38), (68, 38), (74, 40)),
                  ((76, 50), (66, 72), (56, 74)), ((46, 76), (32, 74), (30, 70))]),
             cap(fw[0], fw[1], 74, 38, 5), cap(rw[0], rw[1], 50, 46, 5),
             cap(70, 30, 76, 40, 5), cap(66, 29, 80, 29, 5),                # 핸들
             ell(46, 37, 9, 3.6, -6)]                                       # 안장
    kw = dict(sx=f["sx"], sy=f["sy"], ox=54, oy=88, rot=f["rot"], rox=rw[0], roy=rw[1], dy=f["dy"])
    frame = aff(frame, **kw)
    wheels, holes = [], []
    for (cx, cy) in (rw, fw):
        c2 = apt((cx, cy), **kw)
        if (cx, cy) == rw:
            c2 = (c2[0], min(c2[1], 74) + f["dy"] * 0.0)
        wheels.append(ell(c2[0], c2[1], 15 * f["wsx"], 15 / f["wsx"]))
        holes.append(ell(c2[0], c2[1], 9.6 * f["wsx"], 9.6 / f["wsx"]))
        holes  # 바퀴는 고리
    hubs = [circ(*apt(p, **kw), 3.2) for p in (rw, fw)]
    parts = [Part(wheels, cut=holes, smooth=0), Part(hubs, smooth=0),
             Part(frame, smooth=1.3, gap=2.0)]
    e1, e2 = apt((55, 52), **kw), apt((65, 51), **kw)
    eyes = [(e1[0], e1[1], 3.4, 3.4, 0), (e2[0], e2[1], 3.4, 3.4, 0)]
    return finish("bike", parts, eyes, mode, i, anchor=(54, GROUND))


# ------------------------------------------------------------------ 스케이트보드: 통통한 판(양 끝이 살짝 들림) + 바퀴 둘
SKATE = [dict(sx=1.1, sy=0.84, rot=0, dy=0), dict(sx=0.96, sy=1.04, rot=-17, dy=-7),
         dict(sx=0.9, sy=1.16, rot=0, dy=-11), dict(sx=1.1, sy=0.8, rot=5, dy=1)]


def skateboard(pose):
    mode, i = mode_of(pose)
    f = SKATE[i] if mode == "run" else dict(sx=1, sy=1, rot=0, dy=0)
    deck = [bez([(10, 58), ((14, 62), (20, 63), (30, 63)), ((46, 63), (62, 63), (78, 63)),
                 ((88, 63), (94, 62), (98, 58)), ((102, 62), (100, 77), (86, 77)),
                 ((66, 77), (42, 77), (22, 77)), ((8, 77), (6, 62), (10, 58))])]
    kw = dict(sx=f["sx"], sy=f["sy"], ox=54, oy=77, rot=f["rot"], rox=30, roy=84, dy=f["dy"])
    deck = aff(deck, **kw)
    wheels = [circ(*apt(p, **kw), 7.0) for p in ((28, 84), (80, 84))]
    parts = [Part(deck, smooth=1.6), Part(wheels, smooth=0, gap=2.2)]
    e1, e2 = apt((60, 70), **kw), apt((72, 70), **kw)
    eyes = [(e1[0], e1[1], 3.6, 3.8, 0), (e2[0], e2[1], 3.6, 3.8, 0)]
    return finish("skateboard", parts, eyes, mode, i, anchor=(54, GROUND))


# ------------------------------------------------------------------ 열기구: 물방울 풍선 + 흔들리는 바구니
BAL = [dict(sx=0.9, sy=1.1, sw=-14, dy=-2), dict(sx=1.1, sy=0.9, sw=0, dy=1),
       dict(sx=0.92, sy=1.08, sw=14, dy=-3), dict(sx=1.12, sy=0.88, sw=0, dy=2)]


def balloon(pose):
    mode, i = mode_of(pose)
    f = BAL[i] if mode == "run" else dict(sx=1, sy=1, sw=0, dy=0)
    env = [bez([(54, 14), ((76, 14), (84, 32), (78, 46)), ((73, 57), (62, 63), (59, 68)),
                ((57, 70), (51, 70), (49, 68)), ((46, 63), (35, 57), (30, 46)),
                ((24, 32), (32, 14), (54, 14))])]
    env = aff(env, sx=f["sx"], sy=f["sy"], ox=54, oy=68, dy=f["dy"])
    neck = apt((54, 68), dy=f["dy"])
    bas = [cap(neck[0] - 4, neck[1], neck[0] - 6, neck[1] + 9, 2.4), cap(neck[0] + 4, neck[1], neck[0] + 6, neck[1] + 9, 2.4),
           bez([(44, 77), ((50, 76), (58, 76), (64, 77)), ((64, 82), (63, 88), (60, 88)),
                ((56, 88), (52, 88), (48, 88)), ((45, 88), (44, 82), (44, 77))])]
    bas = [p if k < 2 else aff([p], dy=f["dy"])[0] for k, p in enumerate(bas)]
    bas = aff(bas, rot=f["sw"], ox=neck[0], oy=neck[1])
    parts = [Part(env, smooth=1.0), Part(bas, smooth=0.6, gap=1.8)]
    e1 = apt((44, 40), sx=f["sx"], sy=f["sy"], ox=54, oy=68, dy=f["dy"])
    e2 = apt((60, 40), sx=f["sx"], sy=f["sy"], ox=54, oy=68, dy=f["dy"])
    eyes = [(e1[0], e1[1], 4.0, 4.2, 0), (e2[0], e2[1], 4.0, 4.2, 0)]
    return finish("balloon", parts, eyes, mode, i, anchor=(54, GROUND))


# ------------------------------------------------------------------ 로켓: 비스듬히 위로, 뾰족 코 + 아래로 벌어진 날개 셋 + 불꽃 방울
ROCK = [dict(sx=1.0, sy=1.14, dy=0), dict(sx=1.1, sy=0.88, dy=2), dict(sx=0.98, sy=1.1, dy=-2), dict(sx=1.08, sy=0.9, dy=1)]
ROCK_TILT = 42


def rocket(pose):
    mode, i = mode_of(pose)
    f = ROCK[i] if mode == "run" else dict(sx=1, sy=1, dy=0)
    # 똑바로 선 로켓(코가 위)을 그린 뒤 오른쪽으로 기울인다. 중심 (54, 52)
    body = [bez([(54, 14), ((62, 20), (68, 32), (68, 48)), ((68, 58), (66, 68), (63, 74)),
                 ((58, 76), (50, 76), (45, 74)), ((42, 68), (40, 58), (40, 48)),
                 ((40, 32), (46, 20), (54, 14))]),
            bez([(42, 58), ((34, 62), (30, 72), (31, 82)), ((36, 80), (40, 76), (46, 72))]),   # 왼 날개
            bez([(66, 58), ((74, 62), (78, 72), (77, 82)), ((72, 80), (68, 76), (62, 72))]),   # 오른 날개
            cap(54, 66, 54, 82, 6)]                                                            # 가운데 날개
    kw = dict(sx=f["sx"], sy=f["sy"], ox=54, oy=56, rot=ROCK_TILT, rox=54, roy=56, dy=f["dy"])
    body = aff(body, **kw)
    if mode == "run":
        fl = [[(0, 10, 6), (1, 21, 4.6), (-1, 30, 3.2)], [(0, 9, 5), (0, 17, 3.6)],
              [(0, 10, 6.4), (-1, 22, 5), (1, 32, 3.4)], [(0, 9, 5.4), (1, 19, 4.2), (0, 27, 2.6)]][i]
    elif mode == "rest":
        fl = [[(0, 9, 3.2)], [(0, 9, 4)]][i]
    else:
        fl = [(0, 9, 4)]
    base = (54, 76 * f["sy"] + 56 * (1 - f["sy"]))
    flame = aff([circ(base[0] + dx, base[1] + dy, r) for (dx, dy, r) in fl],
                rot=ROCK_TILT, ox=54, oy=56, rox=54, roy=56, dy=f["dy"])
    parts = [Part(body, smooth=1.3), Part(flame, smooth=0, gap=1.8)]
    # 눈은 몸통 위쪽, 얼굴이 앞(보는 사람)을 향하게 똑바로
    e1, e2 = apt((48, 42), **kw), apt((60, 42), **kw)
    eyes = [(e1[0], e1[1], 3.6, 3.6, 0), (e2[0], e2[1], 3.6, 3.6, 0)]
    return finish("rocket", parts, eyes, mode, i, anchor=(54, GROUND))


DRAW = dict(dog=dog, rabbit=rabbit, turtle=turtle, duck=duck, squirrel=squirrel, panda=panda,
            train=train, bike=bike, skateboard=skateboard, balloon=balloon, rocket=rocket)
