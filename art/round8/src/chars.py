"""8라운드 10종(7라운드를 더 귀엽게: 큰 머리, 안쪽 아래 큰 눈, 짧은 몸). 캐릭터당 한 가지 색 실루엣 + 어두운 눈 두 개(작은 흰 하이라이트).

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
    dict(sx=1.14, sy=0.87, rot=-7, dy=-3, fa=58, ha=-60, sp=12),   # 뻗음(도약)
    dict(sx=0.86, sy=1.12, rot=0, dy=-7, fa=-32, ha=34, sp=8),     # 모음(공중)
    dict(sx=1.10, sy=0.89, rot=6, dy=0, fa=30, ha=-76, sp=12),     # 반대 뻗음(착지)
    dict(sx=0.90, sy=1.06, rot=-2, dy=2, fa=-10, ha=12, sp=6),     # 모음(땅)
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
import json as _json, os as _os
_FITF = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "fit.json")
FIT = {k: tuple(v) for k, v in _json.load(open(_FITF)).items()} if _os.path.exists(_FITF) else {}
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


# ------------------------------------------------------------------ 공통: 얼굴 눈 두 개(머리 안쪽·조금 아래, 간격 넓게)
def face_eyes(hx, hy, hr, r=3.7, fwd=0.12, gap=0.86, low=0.14, ry=None):
    """머리 원(hx,hy,hr) 안에 앞을 보는 눈 두 개. fwd: 얼굴 중심을 앞으로 민 정도, gap: 눈 간격(hr 배수)."""
    cx = hx + fwd * hr
    ry = r if ry is None else ry
    return [(cx - gap * hr / 2, hy + low * hr, r, ry, 0), (cx + gap * hr / 2, hy + low * hr * 0.9, r, ry, 0)]


# ------------------------------------------------------------------ 강아지: 큰 둥근 머리 + 처진 귀 + 짧은 주둥이
def dog(pose):
    def feat(t):
        hx, hy, hr, i, m = t["hx"], t["hy"], t["hr"], t["i"], t["mode"]
        ea = [176, 162, 182, 166][i] if m == "run" else (166 if m == "still" else 172)
        base = (hx - 0.34 * hr, hy - 0.86 * hr)
        mid = dirpt(*base, ea, 9)
        ear = ell(mid[0], mid[1], 9.6, 5.0, ea)
        ta = [236, 212, 244, 222][i] if m == "run" else (232 if m == "still" else 200)
        tb = t["R"](-t["rx"] * 0.9, -t["ry"] * 0.35)
        te = dirpt(*tb, ta, 8)
        return [ear, ell(hx + 0.9 * hr, hy + 0.4 * hr, 6.6, 5.0), cap(*tb, *te, 4.6)]

    def eyes(t):
        return face_eyes(t["hx"], t["hy"], t["hr"], r=3.7, fwd=0.14, gap=0.84, low=0.12)
    return quad(pose, dict(id="dog", brx=15, bry=11, hr=15, LL=10, lw=7.5, bx=46, hdx=3, hdy=-6,
                           feat=feat, eyes=eyes))


# ------------------------------------------------------------------ 토끼: 큰 머리 + 둥근 긴 귀 두 개 + 동그란 꼬리
def rabbit(pose):
    def feat(t):
        hx, hy, hr, i, m = t["hx"], t["hy"], t["hr"], t["i"], t["mode"]
        sw = [-18, 6, -24, 0][i] if m == "run" else (0 if m == "still" else -46)
        out = []
        for (bx_, by_, a0, ln) in ((hx - 0.34 * hr, hy - 0.62 * hr, -110, 16), (hx + 0.16 * hr, hy - 0.74 * hr, -94, 15)):
            e = dirpt(bx_, by_, a0 + sw, ln)
            out.append(cap(bx_, by_, *e, 7.4))
        tb = t["R"](-t["rx"] * 1.0, -t["ry"] * 0.15)
        out.append(circ(*tb, 4.6))
        return out

    def eyes(t):
        return face_eyes(t["hx"], t["hy"], t["hr"], r=3.5, ry=3.9, fwd=0.1, gap=0.88, low=0.16)
    return quad(pose, dict(id="rabbit", brx=14, bry=11, hr=14.5, LL=8.5, lw=7, bx=46, hdx=2, hdy=-5,
                           feat=feat, eyes=eyes))


# ------------------------------------------------------------------ 다람쥐: 큰 머리 + 몸만 한 말린 꼬리(7라운드보다 작게)
def squirrel(pose):
    def feat(t):
        hx, hy, hr, i, m = t["hx"], t["hy"], t["hr"], t["i"], t["mode"]
        tb = t["R"](-t["rx"] * 0.85, -t["ry"] * 0.2)
        rel = [(-4, -2), (-9, -9), (-10, -18), (-7, -25), (-1, -29), (4, -27)]
        rad = [4.4, 5.4, 6.4, 6.6, 6.0, 4.6]
        tr = [-20, -4, -12, 0][i] if m == "run" else (0 if m == "still" else 22)
        ts = [1.0, 0.92, 1.0, 0.94][i] if m == "run" else (1.0 if m == "still" else 0.86)
        pts = [apt((tb[0] + x * ts, tb[1] + y * ts), rot=tr, ox=tb[0], oy=tb[1]) for x, y in rel]
        ear = ell(hx - 0.22 * hr, hy - 0.92 * hr, 3.8, 4.8, -10)
        snout = ell(hx + 0.88 * hr, hy + 0.3 * hr, 3.8, 3.4)
        return chain(pts, [r * ts for r in rad]) + [ear, snout]

    def eyes(t):
        return face_eyes(t["hx"], t["hy"], t["hr"], r=3.5, fwd=0.12, gap=0.86, low=0.14)
    return quad(pose, dict(id="squirrel", brx=13, bry=10, hr=14, LL=8.5, lw=6.4, bx=56, hdx=2, hdy=-5,
                           feat=feat, eyes=eyes))


# ------------------------------------------------------------------ 거북이: 작은 둥근 등딱지 + 큰 머리, 짧은 목
TRUN = [dict(sx=1.12, sy=0.88, dy=-1, fa=46, neck=4), dict(sx=0.88, sy=1.12, dy=-4, fa=-30, neck=-2),
        dict(sx=1.08, sy=0.91, dy=0, fa=-46, neck=3), dict(sx=0.92, sy=1.05, dy=1, fa=22, neck=0)]


def turtle(pose):
    mode, i = mode_of(pose)
    bx, yb = 42, 80
    f = TRUN[i] if mode == "run" else dict(sx=1, sy=1, dy=0, fa=4, neck=1 if mode == "still" else -3)
    sx, sy = f["sx"], f["sy"]
    if mode == "rest":
        sx, sy, yb = 1.04, 0.96, 85
    yb += f["dy"]
    shell = ell(bx, yb, 21 * sx, 21 * sy)
    cutb = [[(-50, yb + 3), (160, yb + 3), (160, 200), (-50, 200)]]
    legs = []
    if mode != "rest":
        L = GROUND - yb + 1
        for (lx, ang) in ((bx + 12 * sx, f["fa"]), (bx + 5 * sx, -f["fa"]), (bx - 7 * sx, -f["fa"]), (bx - 14 * sx, f["fa"])):
            legs.append(limb(lx, yb - 2, L, ang * 0.7, 9))
    nk = f["neck"]
    hr = 13.5
    hx, hy = bx + 21 * sx + 8 + nk, yb - 13 - (2 if mode == "run" and i in (0, 2) else 0)
    if mode == "rest":
        hx, hy = bx + 21 * sx + 6, yb - 9
    head = [circ(hx, hy, hr), cap(bx + 12 * sx, yb - 3, hx - 4, hy + 3, 10)]
    tail = [cap(bx - 20 * sx, yb - 1, bx - 26 * sx, yb + 2, 4.6)]
    parts = [Part([shell], cut=cutb, smooth=1.8),
             Part(legs + head + tail + [ell(bx, yb + 1, 20 * sx, 4)], smooth=1.6)]
    eyes = face_eyes(hx, hy, hr, r=3.5, fwd=0.08, gap=0.86, low=0.12)
    return finish("turtle", parts, eyes, mode, i, anchor=(bx, GROUND))


# ------------------------------------------------------------------ 오리: 큰 머리 + 짧은 부리 + 작은 몸, 솟은 꼬리
DRUN = [dict(sx=1.12, sy=0.88, rot=-7, dy=-3, la=48, lb=-40, ll=10),
        dict(sx=0.88, sy=1.1, rot=0, dy=-7, la=10, lb=-6, ll=6),
        dict(sx=1.08, sy=0.9, rot=7, dy=0, la=-42, lb=46, ll=10),
        dict(sx=0.92, sy=1.06, rot=-2, dy=2, la=-4, lb=8, ll=8)]


def duck(pose):
    mode, i = mode_of(pose)
    f = DRUN[i] if mode == "run" else dict(sx=1, sy=1, rot=0, dy=0, la=6, lb=-6, ll=9)
    bx = 44
    rx, ry = 16 * f["sx"], 12 * f["sy"]
    by = GROUND - 9 - ry * 0.8 + f["dy"]
    rot = f["rot"]
    if mode == "rest":
        rx, ry, by, rot = 18, 11.5, GROUND - 11, 0
    a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)

    def R(lx, ly):
        return (bx + lx * ca - ly * sa, by + lx * sa + ly * ca)
    hr = 14.5
    hx, hy = R(rx * 0.62, -ry - 7)
    if mode == "rest":
        hx, hy = R(rx * 0.6, -ry - 3)
    tail = [R(-rx * 0.7, -ry * 0.5), R(-rx * 1.25, -ry * 1.05), R(-rx * 0.6, ry * 0.3)]
    polys = [ell(bx, by, rx, ry, rot), circ(hx, hy, hr), tail,
             ell(hx + hr * 0.98, hy + hr * 0.34, 6.4, 3.6, -4)]
    if mode != "rest":
        for (lx, ang) in ((3, f["la"]), (-5, f["lb"])):
            hpt = R(lx, ry * 0.75)
            a2 = math.radians(ang); L = f["ll"]
            fx, fy = hpt[0] + L * math.sin(a2), hpt[1] + L * math.cos(a2)
            polys += [cap(*hpt, fx, fy, 4.6), ell(fx + 2.5, fy, 5.0, 2.6, ang * 0.3)]
    parts = [Part(polys, smooth=1.5)]
    eyes = face_eyes(hx, hy, hr, r=3.6, fwd=0.06, gap=0.84, low=0.08)
    return finish("duck", parts, eyes, mode, i, anchor=(bx, GROUND))


# ------------------------------------------------------------------ 기차: 짧고 통통한 기관차 + 큰 앞 얼굴 + 바퀴 둘 + 연기
TRAIN = [dict(sx=1.08, sy=0.9, ws=1.12, dy=0), dict(sx=0.94, sy=1.08, ws=0.92, dy=-3),
         dict(sx=1.06, sy=0.92, ws=1.08, dy=0, lean=3), dict(sx=0.96, sy=1.04, ws=0.96, dy=1)]


def train(pose):
    mode, i = mode_of(pose)
    f = TRAIN[i] if mode == "run" else dict(sx=1, sy=1, ws=1, dy=0)
    body = [bez([(20, 78), ((20, 78), (20, 38), (20, 38)), ((20, 32), (42, 32), (42, 38)),
                 ((42, 38), (42, 46), (46, 46)), ((62, 44), (88, 44), (90, 56)),
                 ((93, 66), (94, 78), (88, 78)), ((60, 78), (36, 78), (20, 78))]),
            cap(78, 50, 78, 38, 10), ell(78, 35, 7.5, 3.6),           # 굴뚝
            cap(16, 33, 46, 33, 6)]                                    # 지붕
    body = aff(body, sx=f["sx"], sy=f["sy"], ox=56, oy=80, rot=f.get("lean", 0), rox=56, roy=80, dy=f["dy"])
    wheels = []
    for wx in (34, 76):
        wx2 = 56 + (wx - 56) * f["sx"]
        wheels.append(ell(wx2, 83 - 8 * (1 / f["ws"] - 1), 9.5 * f["ws"], 9.5 / f["ws"]))
    puffs = []
    top = apt((78, 31), sx=f["sx"], sy=f["sy"], ox=56, oy=80, dy=f["dy"])
    if mode == "run":
        sets = [[(2, -6, 5.5), (-9, -12, 4.5), (-21, -14, 3.4)], [(1, -8, 6.5), (-12, -11, 5.5), (-24, -12, 4)],
                [(3, -5, 4.5), (-7, -13, 6.5), (-20, -16, 4.5)], [(0, -7, 6), (-14, -12, 4), (-25, -14, 5)]][i]
    elif mode == "rest":
        sets = [[(2, -6, 3.5)], [(2, -7, 4.5)]][i]
    else:
        sets = [(2, -6, 4)]
    for (dx, dy, r) in sets:
        puffs.append(circ(top[0] + dx, max(14, top[1] + dy), r))
    parts = [Part(body, smooth=3.2), Part(wheels, smooth=0, gap=2.4), Part(puffs, smooth=0.8, gap=1.5)]
    e1 = apt((62, 61), sx=f["sx"], sy=f["sy"], ox=56, oy=80, dy=f["dy"])
    e2 = apt((78, 61), sx=f["sx"], sy=f["sy"], ox=56, oy=80, dy=f["dy"])
    eyes = [(e1[0], e1[1], 4.1, 4.1, 0), (e2[0], e2[1], 4.1, 4.1, 0)]
    return finish("train", parts, eyes, mode, i, anchor=(56, GROUND))


# ------------------------------------------------------------------ 자전거: 큰 바퀴 둘(사이 틈) + 가는 뼈대 + 작은 둥근 몸통
BIKE = [dict(sx=1.06, sy=0.92, rot=0, dy=0, wsx=1.07), dict(sx=0.94, sy=1.08, rot=0, dy=-5, wsx=0.95),
        dict(sx=1.03, sy=0.96, rot=-11, dy=-1, wsx=1.0), dict(sx=0.97, sy=1.03, rot=0, dy=1, wsx=1.09)]


def bike(pose):
    mode, i = mode_of(pose)
    f = BIKE[i] if mode == "run" else dict(sx=1, sy=1, rot=0, dy=0, wsx=1.0)
    rw, fw = (24, 72), (86, 72)
    WR, HOLE = 17, 11.2
    frame = [cap(rw[0], rw[1], 46, 54, 5.2),                                  # 뒤 지지대
             cap(fw[0], fw[1], 75, 36, 5.2),                                  # 앞 포크
             cap(60, 50, 76, 44, 5),                                          # 몸통-포크
             cap(70, 31, 82, 31, 5), cap(73, 31, 75.5, 38, 5),                # 핸들
             ell(53, 50, 14.5, 12)]                                           # 몸통(눈 자리)
    kw = dict(sx=f["sx"], sy=f["sy"], ox=55, oy=88, rot=f["rot"], rox=rw[0], roy=rw[1], dy=f["dy"])
    frame = aff(frame, **kw)
    wheels, holes = [], []
    for (cx, cy) in (rw, fw):
        c2 = apt((cx, cy), **kw)
        if (cx, cy) == rw:
            c2 = (c2[0], min(c2[1], 73))
        wheels.append(ell(c2[0], c2[1], WR * f["wsx"], WR / f["wsx"]))
        holes.append(ell(c2[0], c2[1], HOLE * f["wsx"], HOLE / f["wsx"]))
    hubs = [circ(*apt(p, **kw), 3.4) for p in (rw, fw)]
    parts = [Part(wheels, cut=holes, smooth=0), Part(hubs, smooth=0),
             Part(frame, smooth=1.2, gap=2.0)]
    e1, e2 = apt((47, 51), **kw), apt((60, 51), **kw)
    eyes = [(e1[0], e1[1], 3.8, 3.8, 0), (e2[0], e2[1], 3.8, 3.8, 0)]
    return finish("bike", parts, eyes, mode, i, anchor=(55, GROUND))


# ------------------------------------------------------------------ 스케이트보드: 두툼한 판(양 끝 들림) + 큰 바퀴 둘, 판 위 큰 눈
SKATE = [dict(sx=1.08, sy=0.88, rot=0, dy=0), dict(sx=0.96, sy=1.04, rot=-16, dy=-7),
         dict(sx=0.92, sy=1.12, rot=0, dy=-11), dict(sx=1.08, sy=0.86, rot=5, dy=1)]


def skateboard(pose):
    mode, i = mode_of(pose)
    f = SKATE[i] if mode == "run" else dict(sx=1, sy=1, rot=0, dy=0)
    deck = [bez([(18, 50), ((22, 56), (28, 58), (36, 58)), ((48, 58), (60, 58), (72, 58)),
                 ((80, 58), (86, 56), (90, 50)), ((97, 56), (96, 78), (82, 78)),
                 ((66, 78), (42, 78), (26, 78)), ((12, 78), (11, 56), (18, 50))])]
    kw = dict(sx=f["sx"], sy=f["sy"], ox=54, oy=78, rot=f["rot"], rox=32, roy=86, dy=f["dy"])
    deck = aff(deck, **kw)
    wheels = [circ(*apt(p, **kw), 8.0) for p in ((32, 86), (76, 86))]
    parts = [Part(deck, smooth=1.8), Part(wheels, smooth=0, gap=2.2)]
    e1, e2 = apt((46, 68), **kw), apt((62, 68), **kw)
    eyes = [(e1[0], e1[1], 4.2, 4.4, 0), (e2[0], e2[1], 4.2, 4.4, 0)]
    return finish("skateboard", parts, eyes, mode, i, anchor=(54, GROUND))


# ------------------------------------------------------------------ 열기구: 둥근 풍선 + 벌어진 줄 둘 + 큰 바구니
BAL = [dict(sx=0.92, sy=1.08, sw=-10, dy=-2), dict(sx=1.08, sy=0.92, sw=0, dy=1),
       dict(sx=0.94, sy=1.06, sw=10, dy=-3), dict(sx=1.1, sy=0.9, sw=0, dy=2)]


def balloon(pose):
    mode, i = mode_of(pose)
    f = BAL[i] if mode == "run" else dict(sx=1, sy=1, sw=0, dy=0)
    env = [bez([(54, 12), ((76, 12), (86, 26), (84, 40)), ((82, 52), (68, 58), (62, 62)),
                ((58, 64), (50, 64), (46, 62)), ((40, 58), (26, 52), (24, 40)),
                ((22, 26), (32, 12), (54, 12))])]
    env = aff(env, sx=f["sx"], sy=f["sy"], ox=54, oy=62, dy=f["dy"])
    neck = apt((54, 62), dy=f["dy"])
    ropes = [cap(neck[0] - 7, neck[1] - 1, neck[0] - 10, neck[1] + 14, 3.2),
             cap(neck[0] + 7, neck[1] - 1, neck[0] + 10, neck[1] + 14, 3.2)]
    bas = bez([(40, 75), ((48, 74), (60, 74), (68, 75)), ((68, 82), (66, 90), (62, 90)),
               ((56, 90), (52, 90), (46, 90)), ((42, 90), (40, 82), (40, 75))])
    bas = aff([bas], dy=f["dy"])[0]
    bas = aff(ropes + [bas, cap(39, 75, 69, 75, 4.4)], rot=f["sw"], ox=neck[0], oy=neck[1])
    parts = [Part(env, smooth=1.0), Part(bas, smooth=0.5, gap=1.8)]
    e1 = apt((45, 38), sx=f["sx"], sy=f["sy"], ox=54, oy=62, dy=f["dy"])
    e2 = apt((63, 38), sx=f["sx"], sy=f["sy"], ox=54, oy=62, dy=f["dy"])
    eyes = [(e1[0], e1[1], 4.4, 4.6, 0), (e2[0], e2[1], 4.4, 4.6, 0)]
    return finish("balloon", parts, eyes, mode, i, anchor=(54, GROUND))


# ------------------------------------------------------------------ 로켓: 짧고 통통한 몸 + 날개 셋 + 불꽃 방울
ROCK = [dict(sx=1.0, sy=1.1, dy=0), dict(sx=1.08, sy=0.9, dy=2), dict(sx=0.98, sy=1.08, dy=-2), dict(sx=1.06, sy=0.92, dy=1)]
ROCK_TILT = 42


def rocket(pose):
    mode, i = mode_of(pose)
    f = ROCK[i] if mode == "run" else dict(sx=1, sy=1, dy=0)
    body = [bez([(54, 20), ((64, 24), (72, 36), (72, 50)), ((72, 60), (69, 68), (65, 73)),
                 ((60, 76), (48, 76), (43, 73)), ((39, 68), (36, 60), (36, 50)),
                 ((36, 36), (44, 24), (54, 20))]),
            bez([(39, 58), ((31, 62), (28, 72), (29, 81)), ((34, 79), (38, 76), (44, 72))]),
            bez([(69, 58), ((77, 62), (80, 72), (79, 81)), ((74, 79), (70, 76), (64, 72))]),
            cap(54, 66, 54, 81, 6)]
    kw = dict(sx=f["sx"], sy=f["sy"], ox=54, oy=56, rot=ROCK_TILT, rox=54, roy=56, dy=f["dy"])
    body = aff(body, **kw)
    if mode == "run":
        fl = [[(0, 9, 6), (1, 19, 4.6), (-1, 27, 3.2)], [(0, 8, 5), (0, 16, 3.6)],
              [(0, 9, 6.4), (-1, 20, 5), (1, 29, 3.4)], [(0, 8, 5.4), (1, 17, 4.2), (0, 25, 2.6)]][i]
    elif mode == "rest":
        fl = [[(0, 8, 3.2)], [(0, 8, 4)]][i]
    else:
        fl = [(0, 8, 4)]
    base = (54, 76 * f["sy"] + 56 * (1 - f["sy"]))
    flame = aff([circ(base[0] + dx, base[1] + dy, r) for (dx, dy, r) in fl],
                rot=ROCK_TILT, ox=54, oy=56, rox=54, roy=56, dy=f["dy"])
    parts = [Part(body, smooth=1.3), Part(flame, smooth=0, gap=1.8)]
    c = apt((54, 48), **kw)
    eyes = [(c[0] - 7.2, c[1] + 0.5, 3.9, 3.9, 0), (c[0] + 7.2, c[1] - 0.5, 3.9, 3.9, 0)]
    return finish("rocket", parts, eyes, mode, i, anchor=(54, GROUND))


DRAW = dict(dog=dog, rabbit=rabbit, turtle=turtle, duck=duck, squirrel=squirrel,
            train=train, bike=bike, skateboard=skateboard, balloon=balloon, rocket=rocket)
