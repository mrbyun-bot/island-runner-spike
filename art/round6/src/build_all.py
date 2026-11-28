#!/usr/bin/env python3
"""6라운드: 단색 면 + 점 눈, 11종을 한 번에 다시 만든다.

python3 art/round6/src/build_all.py   (저장소 루트 어디서 실행해도 됨)

규칙
- 좌표계 108×108(=36pt@3x). 바닥선 y=90. 아일랜드에서 실제로 보이는 곳은 y 15~93.
- 윤곽선·음영·그라데이션·하이라이트 없음. 몸색·배색·포인트 3색 이하 + 공통 눈 먹색.
- 모두 오른쪽을 보는 옆모습.
- 포즈: run_1..4(달리기 루프), rest_1..2(호흡), still(정지).
"""
import math, os, subprocess, tempfile, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # art/round6
OUT_CH = os.path.join(ROOT, "characters")
OUT_GIF = os.path.join(ROOT, "gif")
OUT_CMP = os.path.join(ROOT, "compare")

INK = "#231C1A"  # 공통 눈 먹색
GROUND = 90
POSES = ["run_1", "run_2", "run_3", "run_4", "rest_1", "rest_2", "still"]

# ---------------------------------------------------------------- 팔레트
PAL = {
    "dog":        {"name": "강아지",   "body": "#FFC47E", "dark": "#E58A4E", "point": "#FF7E93"},
    "rabbit":     {"name": "토끼",     "body": "#F3F0F7", "dark": "#C9C3D6", "point": "#FF94B0"},
    "turtle":     {"name": "거북이",   "body": "#CFEE8E", "dark": "#4FC98A", "point": "#FF8F86"},
    "duck":       {"name": "오리",     "body": "#FFE14F", "dark": "#F2B81E", "point": "#FF9440"},
    "squirrel":   {"name": "다람쥐",   "body": "#FF9F5C", "dark": "#E0743A", "point": "#FFE2BC"},
    "panda":      {"name": "판다",     "body": "#F6F5EF", "dark": "#626B80", "point": "#FF9AA2"},
    "train":      {"name": "기차",     "body": "#74C8FF", "dark": "#3F86D8", "point": "#FF776A"},
    "bike":       {"name": "자전거",   "body": "#FF7867", "dark": "#E6EDF4", "point": "#FFD25A"},
    "skateboard": {"name": "스케이트보드", "body": "#B7E35C", "dark": "#7FB83A", "point": "#FFA548"},
    "balloon":    {"name": "열기구",   "body": "#FF7466", "dark": "#FFD35A", "point": "#FFA040"},
    "rocket":     {"name": "로켓",     "body": "#EEF0F6", "dark": "#FF5E5E", "point": "#FFB52E"},
}
ORDER = list(PAL.keys())

# ---------------------------------------------------------------- SVG 조각
def C(cx, cy, r, f):
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{f}"/>'

def E(cx, cy, rx, ry, f, rot=0):
    t = f' transform="rotate({rot:.2f} {cx:.2f} {cy:.2f})"' if rot else ""
    return f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" fill="{f}"{t}/>'

def R(x, y, w, h, rx, f, rot=0, ox=None, oy=None):
    t = ""
    if rot:
        ox = x + w / 2 if ox is None else ox
        oy = y + h / 2 if oy is None else oy
        t = f' transform="rotate({rot:.2f} {ox:.2f} {oy:.2f})"'
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx:.2f}" fill="{f}"{t}/>'

def L(x1, y1, x2, y2, w, col):
    return (f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" '
            f'stroke-width="{w:.2f}" stroke-linecap="round"/>')

def P(d, f):
    return f'<path d="{d}" fill="{f}"/>'

def ring(cx, cy, r, w, col):
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none" stroke="{col}" stroke-width="{w:.2f}"/>'

def leg(hx, hy, length, ang, w, col):
    """엉덩이(hx,hy)에서 아래로 뻗는 다리. ang: 세로 기준 각도(+는 앞=오른쪽)."""
    a = math.radians(ang)
    return L(hx, hy, hx + length * math.sin(a), hy + length * math.cos(a), w, col)

def G(items, dx=0, dy=0, rot=0, ox=0, oy=0, sx=1, sy=1):
    t = []
    if dx or dy:
        t.append(f"translate({dx:.2f} {dy:.2f})")
    if rot:
        t.append(f"rotate({rot:.2f} {ox:.2f} {oy:.2f})")
    if sx != 1 or sy != 1:
        t.append(f"translate({ox:.2f} {oy:.2f}) scale({sx:.3f} {sy:.3f}) translate({-ox:.2f} {-oy:.2f})")
    tt = f' transform="{" ".join(t)}"' if t else ""
    return f'<g{tt}>' + "".join(items) + "</g>"

def eye(x, y, closed=False, r=3.0):
    if closed:
        return L(x - 3, y + 0.5, x + 3, y + 0.5, 2.4, INK)
    return C(x, y, r, INK)

def svg(items):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="108" height="108" viewBox="0 0 108 108">'
            + "".join(items) + "</svg>")

# ---------------------------------------------------------------- 포즈 공통
def pose_info(pose):
    """달리기 단계, 몸 흔들림, 쉼 호흡 값."""
    if pose.startswith("run"):
        i = int(pose[-1]) - 1
        return {"mode": "run", "i": i, "bob": [0, -2, 0, -1][i], "breath": 1.0}
    if pose.startswith("rest"):
        i = int(pose[-1]) - 1
        return {"mode": "rest", "i": i, "bob": 0, "breath": [1.0, 1.045][i]}
    return {"mode": "still", "i": 0, "bob": 0, "breath": 1.0}

def quad_angles(i, amp=34):
    """네 다리 각도(앞-가까운, 앞-먼, 뒤-가까운, 뒤-먼). 한 다리씩 90도씩 어긋나 4장이 모두 다르다."""
    ph = math.radians(90 * i)
    return (amp * math.cos(ph), -amp * math.cos(ph), amp * math.sin(ph), -amp * math.sin(ph))

# ---------------------------------------------------------------- 동물
def dog(pose):
    p = PAL["dog"]; s = pose_info(pose); b, d, k = p["body"], p["dark"], p["point"]
    run = s["mode"] == "run"
    if s["mode"] == "rest":
        # 엎드려 숨쉬기: 몸 낮게, 다리 앞으로, 눈 감음
        body = [
            E(48, 78, 27, 12, b),
            L(66, 86, 84, 87, 7, b), L(30, 86, 44, 87, 7, d),
            R(16, 72, 14, 6, 3, b, rot=-20),
        ]
        head = [C(74, 62, 18, b), E(91, 67, 9, 7, b), C(98, 64, 3.2, INK),
                E(64, 59, 6.5, 11, d, rot=25), eye(80, 59, closed=True)]
        return svg([G(body + head, sy=s["breath"], ox=50, oy=GROUND)])
    fa = quad_angles(s["i"]) if run else (4, -4, -4, 4)
    tail = [-28, -12, -28, -12][s["i"]] if run else -20
    ear = [18, 32, 18, 6][s["i"]] if run else 22
    items = [
        leg(64, 74, 14, fa[1], 7.5, d), leg(34, 74, 14, fa[3], 7.5, d),   # 먼 다리(배색)
        E(48, 68, 25, 14, b),
        R(18, 52, 7, 18, 3.5, b, rot=tail, ox=24, oy=64),                  # 꼬리
        leg(68, 74, 14, fa[0], 7.5, b), leg(30, 74, 14, fa[2], 7.5, b),   # 가까운 다리
        C(74, 48, 20, b), E(92, 54, 9.5, 7.5, b),                          # 머리, 주둥이
        C(100, 51, 3.4, INK),                                              # 코
        E(63, 46, 7, 12.5, d, rot=ear),                                    # 처진 귀
        eye(81, 45),
    ]
    if run and s["i"] in (1, 3):
        items.append(E(93, 63, 3, 4, k))                                   # 혀
    return svg([G(items, dy=s["bob"])])

def rabbit(pose):
    p = PAL["rabbit"]; s = pose_info(pose); b, d, k = p["body"], p["dark"], p["point"]
    if s["mode"] == "rest":
        items = [E(48, 76, 25, 14, b), C(24, 72, 6, b), E(70, 82, 10, 5, b),
                 C(70, 62, 16, b),
                 E(52, 50, 5.5, 16, d, rot=-70), E(56, 46, 5.5, 16, b, rot=-62),
                 eye(76, 60, closed=True), C(85, 65, 2.4, k)]
        return svg([G(items, sy=s["breath"], ox=50, oy=GROUND)])
    run = s["mode"] == "run"
    i = s["i"]
    # 뛰기: 1 뻗기 → 2 모으기 → 3 뒷발 차기 → 4 착지
    hind = [58, -10, 40, 0][i] if run else -6      # 뒷발 각도(+ 뒤로 차기) → 아래서 부호 반대로
    front = [-38, 22, 0, -18][i] if run else 4
    earr = [-52, -38, -48, -34][i] if run else -32
    items = [
        leg(62, 76, 11, -front * 0.6 + 12, 6.5, d),                       # 먼 앞발
        E(30, 82, 10, 5.5, d, rot=hind * 0.5),                             # 먼 뒷발
        E(46, 70, 23, 15, b), C(23, 64, 6.5, b),                           # 몸, 꼬리
        E(34, 83, 11, 6, b, rot=hind * 0.6),                               # 가까운 뒷발
        leg(64, 76, 12, front, 6.5, b),
        C(68, 55, 16.5, b),
        E(54, 34, 5.5, 17, d, rot=earr - 8),                               # 먼 귀
        E(60, 32, 6, 17, b, rot=earr),                                     # 가까운 귀
        E(60, 32, 2.6, 11, k, rot=earr),                                   # 귀 안
        eye(75, 52), C(84, 57, 2.4, k),
    ]
    return svg([G(items, dy=s["bob"])])

def turtle(pose):
    p = PAL["turtle"]; s = pose_info(pose); b, d, k = p["body"], p["dark"], p["point"]
    run = s["mode"] == "run"
    shell = P("M 16 80 C 16 50 34 44 50 44 C 66 44 84 50 84 80 Z", d)
    rim = R(13, 76, 74, 7, 3.5, b)
    if s["mode"] == "rest":
        # 머리 반쯤 넣고 숨쉬기
        items = [R(10, 82, 10, 6, 3, b), R(70, 82, 12, 6, 3, b), shell, rim,
                 C(88, 74, 11, b), eye(91, 72, closed=True), C(94, 78, 2.4, k)]
        return svg([G(items, sy=s["breath"], ox=50, oy=GROUND)])
    fa = quad_angles(s["i"], amp=30) if run else (0, 0, 0, 0)
    neck = [0, -2, 0, 2][s["i"]] if run else 0
    items = [
        leg(70, 80, 9, fa[1], 10, b), leg(30, 80, 9, fa[3], 10, b),
        P("M 16 74 L 6 80 L 16 82 Z", b),                                  # 꼬리
        shell, rim,
        leg(64, 81, 9, fa[0], 10, b), leg(24, 81, 9, fa[2], 10, b),
        L(78, 74, 90, 64 + neck, 13, b), C(92, 62 + neck, 13, b),           # 목, 머리
        eye(96, 58 + neck), C(99, 66 + neck, 2.6, k),
    ]
    return svg([G(items, dy=s["bob"] * 0.5)])

def duck(pose):
    p = PAL["duck"]; s = pose_info(pose); b, d, k = p["body"], p["dark"], p["point"]
    run = s["mode"] == "run"
    if s["mode"] == "rest":
        items = [E(50, 76, 28, 14, b), P("M 22 72 L 12 62 L 26 68 Z", b), E(48, 74, 14, 7, d),
                 C(72, 56, 15, b), E(89, 60, 9, 4.8, k), eye(75, 53, closed=True)]
        return svg([G(items, sy=s["breath"], ox=50, oy=GROUND)])
    i = s["i"]
    la = [30, 0, -30, 0][i] if run else 3
    lb = [-30, 0, 30, 0][i] if run else -3
    lift_a = [0, 4, 0, 0][i] if run else 0
    lift_b = [0, 0, 0, 4][i] if run else 0
    wing = [-6, -30, -6, -30][i] if run else 0
    def footleg(hx, ang, lift, col):
        a = math.radians(ang); ln = 13 - lift
        fx, fy = hx + ln * math.sin(a), 78 + ln * math.cos(a)
        return L(hx, 78, fx, fy, 4, col) + E(fx + 3, fy, 5, 2.6, col)
    items = [
        footleg(52, lb, lift_b, k),
        E(48, 68, 26, 15, b), P("M 26 62 L 12 50 L 30 58 Z", b),           # 몸, 꼬리
        footleg(46, la, lift_a, k),
        L(62, 60, 68, 46, 14, b), C(70, 40, 15, b),                        # 목, 머리
        E(88, 44, 9.5, 5, k),                                              # 부리
        eye(74, 37),
        E(44, 64, 14, 7.5, d, rot=wing),                                   # 날개
    ]
    return svg([G(items, dy=s["bob"])])

def squirrel(pose):
    p = PAL["squirrel"]; s = pose_info(pose); b, d, k = p["body"], p["dark"], p["point"]
    run = s["mode"] == "run"
    def tail(rot):
        return G([P("M 40 82 C 14 84 6 60 14 40 C 20 24 40 20 44 34 C 46 44 34 42 32 50 "
                    "C 30 60 40 70 46 74 Z", b)], rot=rot, ox=42, oy=80)
    if s["mode"] == "rest":
        items = [tail(-4), E(56, 76, 18, 13, b), E(62, 78, 8, 9, k),
                 C(70, 58, 14, b), P("M 62 48 L 62 36 L 70 45 Z", b),
                 eye(76, 56, closed=True), C(84, 61, 2.2, INK)]
        return svg([G(items, sy=s["breath"], ox=56, oy=GROUND)])
    i = s["i"]
    fa = quad_angles(i, amp=36) if run else (5, -5, -5, 5)
    tr = [-6, 6, -6, 2][i] if run else 0
    items = [
        leg(64, 78, 11, fa[1], 6.5, d), leg(48, 78, 11, fa[3], 6.5, d),
        tail(tr),
        E(56, 72, 17, 12, b), E(63, 74, 7, 8, k),                         # 몸, 배
        leg(66, 79, 11, fa[0], 6.5, b), leg(46, 79, 11, fa[2], 6.5, b),
        C(72, 54, 14.5, b), P("M 64 44 L 63 30 L 73 41 Z", b),           # 머리, 뾰족 귀
        eye(78, 51), C(86, 57, 2.3, INK),
    ]
    return svg([G(items, dy=s["bob"])])

def panda(pose):
    p = PAL["panda"]; s = pose_info(pose); b, d, k = p["body"], p["dark"], p["point"]
    run = s["mode"] == "run"
    if s["mode"] == "rest":
        # 앉아서 숨쉬기
        items = [E(48, 72, 24, 18, b), E(36, 86, 10, 6, d), E(64, 86, 10, 6, d),
                 C(70, 50, 18, b), C(60, 34, 6, d), C(78, 33, 6, d),
                 E(77, 50, 5, 6.5, d, rot=20), C(87, 56, 2.6, d),
                 L(64, 66, 70, 76, 9, d)]
        return svg([G(items, sy=s["breath"], ox=50, oy=GROUND)])
    i = s["i"]
    fa = quad_angles(i, amp=28) if run else (3, -3, -3, 3)
    sway = [-3, 0, 3, 0][i] if run else 0                                  # 뒤뚱 기울기
    items = [
        leg(64, 74, 12, fa[1], 10, d), leg(34, 74, 12, fa[3], 10, d),
        E(48, 66, 27, 17, b), C(22, 60, 4.5, b),
        leg(68, 75, 12, fa[0], 10, d), leg(30, 75, 12, fa[2], 10, d),
        C(74, 46, 19, b), C(64, 30, 6.5, d), C(81, 29, 6.5, d),            # 머리, 귀
        E(82, 46, 5, 6.5, d, rot=20), C(83, 45, 1.9, b),                   # 눈 무늬, 눈
        C(92, 52, 2.8, d),                                                 # 코
    ]
    return svg([G(items, dy=s["bob"], rot=sway, ox=50, oy=GROUND)])

# ---------------------------------------------------------------- 사물
def train(pose):
    p = PAL["train"]; s = pose_info(pose); b, d, k = p["body"], p["dark"], p["point"]
    run = s["mode"] == "run"
    ang = [0, 90, 180, 270][s["i"]] if run else 0
    wheels = [(28, 80, 10), (56, 81, 9), (80, 81, 9)]
    items = []
    # 연기(몸색 동그라미): 달릴 때 크기와 위치가 바뀜
    if run:
        puffs = [[(84, 32, 6), (72, 25, 4)], [(82, 30, 7.5), (68, 24, 5)],
                 [(84, 31, 6.5), (70, 23, 6)], [(83, 33, 5), (66, 26, 4.5)]][s["i"]]
    elif s["mode"] == "rest":
        puffs = [[(84, 34, 4)], [(84, 32, 5.5)]][s["i"]]
    else:
        puffs = []
    for (x, y, r) in puffs:
        items.append(C(x, y, r, b))
    items += [
        R(78, 40, 10, 14, 3, d),                                           # 굴뚝
        R(42, 50, 54, 28, 12, b),                                          # 보일러
        R(12, 34, 36, 44, 6, d), R(9, 31, 42, 7, 3.5, d),                  # 기관실, 지붕
        R(18, 42, 14, 12, 3, b),                                           # 창
        R(8, 74, 92, 6, 3, d),                                             # 차대
    ]
    for (x, y, r) in wheels:
        items.append(C(x, y, r, k))
        a = math.radians(ang)
        items.append(C(x + 0.55 * r * math.cos(a), y + 0.55 * r * math.sin(a), 2.6, d))
    a = math.radians(ang)
    rx1, ry1 = 28 + 5.5 * math.cos(a), 80 + 5.5 * math.sin(a)
    rx2, ry2 = 80 + 5 * math.cos(a), 81 + 5 * math.sin(a)
    if run or True:
        items.append(L(rx1, ry1, rx2, ry2, 3.2, d))                         # 연결봉
    items.append(eye(72, 60))
    return svg([G(items, dy=s["bob"] * 0.5)])

def bike(pose):
    p = PAL["bike"]; s = pose_info(pose); b, w, k = p["body"], p["dark"], p["point"]
    run = s["mode"] == "run"
    ang = [0, 45, 90, 135][s["i"]] if run else 20
    rw, fw = (27, 70), (81, 70)
    bb = (52, 72)
    items = []
    for (cx, cy) in (rw, fw):
        items.append(ring(cx, cy, 15.5, 5.5, w))
        for da in (0, 90):
            a = math.radians(ang + da)
            items.append(L(cx - 13 * math.cos(a), cy - 13 * math.sin(a),
                           cx + 13 * math.cos(a), cy + 13 * math.sin(a), 2.2, w))
        items.append(C(cx, cy, 3, w))
    # 크랭크(뒤쪽 페달)
    ca = math.radians(ang * 2 + 180)
    items.append(L(bb[0], bb[1], bb[0] + 9 * math.cos(ca), bb[1] + 9 * math.sin(ca), 3.5, k))
    items += [
        L(rw[0], rw[1], bb[0], bb[1], 5, b), L(rw[0], rw[1], 46, 46, 5, b),   # 체인스테이, 시트스테이
        L(bb[0], bb[1], 46, 46, 5, b), L(46, 46, 74, 46, 5, b),               # 시트튜브, 탑튜브
        L(bb[0], bb[1], 74, 46, 5, b), L(72, 38, fw[0], fw[1], 5, b),         # 다운튜브, 포크
        R(36, 37, 18, 6, 3, k),                                               # 안장
        L(72, 38, 66, 32, 4.5, b), L(66, 32, 76, 30, 4.5, b),                 # 핸들
        C(bb[0], bb[1], 4.5, b),
    ]
    ca2 = math.radians(ang * 2)
    px, py = bb[0] + 9 * math.cos(ca2), bb[1] + 9 * math.sin(ca2)
    items += [L(bb[0], bb[1], px, py, 3.5, k), R(px - 4.5, py - 2, 9, 4, 2, k)]
    bob = s["bob"] * 0.5
    if s["mode"] == "rest":
        bob = [0, -0.8][s["i"]]
    return svg([G(items, dy=bob)])

def skateboard(pose):
    p = PAL["skateboard"]; s = pose_info(pose); b, d, k = p["body"], p["dark"], p["point"]
    run = s["mode"] == "run"
    i = s["i"]
    tilt = [0, -9, 0, 5][i] if run else 0
    lift = [0, -3, -1, 0][i] if run else 0
    deck = P("M 8 56 C 8 68 16 74 26 74 L 82 74 C 92 74 100 68 100 56 "
             "C 96 62 90 64 82 64 L 26 64 C 18 64 12 62 8 56 Z", b)
    wa = [0, 90, 180, 270][i] if run else 0
    parts = [deck, eye(62, 69, r=2.6), eye(72, 69, r=2.6), R(24, 73, 14, 5, 2, d), R(70, 73, 14, 5, 2, d)]
    for x in (31, 77):
        parts.append(C(x, 82, 8, k))
        a = math.radians(wa)
        parts.append(C(x + 3 * math.cos(a), 82 + 3 * math.sin(a), 1.8, d))
    items = [G(parts, dy=lift, rot=tilt, ox=77, oy=82)]
    if run:
        lines = [[(0, 44, 14), (4, 52, 8)], [(2, 42, 10), (0, 50, 14)],
                 [(0, 46, 12), (6, 54, 6)], [(4, 40, 6), (0, 48, 10)]][i]
        for (x, y, ln) in lines:
            items.append(L(x, y + lift, x + ln * 0.5, y + lift, 3, d))
    if s["mode"] == "rest":
        items = [G(parts, dy=[0, -0.8][s["i"]])]
    return svg(items)

def balloon(pose):
    p = PAL["balloon"]; s = pose_info(pose); b, y, k = p["body"], p["dark"], p["point"]
    run = s["mode"] == "run"
    i = s["i"]
    sw = [-12, 0, 12, 0][i] if run else 0                 # 바구니 흔들림
    tilt = [3, 0, -3, 0][i] if run else 0
    rise = [0, -1, -2, -1][i] if run else 0
    if s["mode"] == "rest":
        rise = [0, 1.5][s["i"]]
    env = [P("M 54 16 C 30 16 26 40 34 52 C 40 61 48 66 50 70 L 58 70 C 60 66 68 61 74 52 "
             "C 82 40 78 16 54 16 Z", b),
           P("M 54 16 C 46 16 44 40 47 52 C 49 60 51 66 52 70 L 56 70 C 57 66 59 60 61 52 "
             "C 64 40 62 16 54 16 Z", y),
           eye(42, 40), eye(66, 40)]
    basket = [L(50, 70, 46, 78, 2, y), L(58, 70, 62, 78, 2, y), R(44, 77, 20, 12, 3, y)]
    flame = []
    if run:
        fh = [6, 9, 6, 9][i]
        flame = [E(54, 72 - fh / 2 + 1, 2.6, fh / 2, k)]
    items = [G(env + flame, rot=tilt, ox=54, oy=42),
             G(basket, rot=sw, ox=54, oy=70)]
    return svg([G(items, dy=rise + 3)])

def rocket(pose):
    p = PAL["rocket"]; s = pose_info(pose); w, r_, k = p["body"], p["dark"], p["point"]
    run = s["mode"] == "run"
    i = s["i"]
    body = [
        P("M 26 46 L 30 34 L 44 46 Z", r_), P("M 26 66 L 30 78 L 44 66 Z", r_),   # 날개
        P("M 26 46 L 74 46 C 86 46 96 52 100 56 C 96 60 86 66 74 66 L 26 66 Z", w),
        C(64, 56, 6.5, r_), eye(64, 56, r=2.6),
    ]
    if run:
        fl = [(22, 26, 8), (16, 30, 7), (24, 22, 8), (12, 34, 6.5)][i]
        flame = [P(f"M 26 47 L {fl[1]-fl[0]+26-fl[1]+2:.1f} 56 L 26 65 Z", k)]
        tip = 26 - fl[1]
        flame = [P(f"M 26 47 C {26-fl[1]*0.5:.1f} 48 {tip:.1f} 52 {tip:.1f} 56 "
                   f"C {tip:.1f} 60 {26-fl[1]*0.5:.1f} 64 26 65 Z", k),
                 P(f"M 26 51 C {26-fl[1]*0.3:.1f} 52 {26-fl[1]*0.6:.1f} 54 {26-fl[1]*0.6:.1f} 56 "
                   f"C {26-fl[1]*0.6:.1f} 58 {26-fl[1]*0.3:.1f} 60 26 61 Z", r_)]
    elif s["mode"] == "rest":
        ln = [7, 10][s["i"]]
        flame = [P(f"M 26 50 C 22 51 {26-ln} 54 {26-ln} 56 C {26-ln} 58 22 61 26 62 Z", k)]
    else:
        flame = []
    return svg([G(flame + body, dy=s["bob"] * 0.5)])

DRAW = {"dog": dog, "rabbit": rabbit, "turtle": turtle, "duck": duck, "squirrel": squirrel,
        "panda": panda, "train": train, "bike": bike, "skateboard": skateboard,
        "balloon": balloon, "rocket": rocket}

# ---------------------------------------------------------------- 렌더
def render_many(jobs):
    tmp = tempfile.mkdtemp(prefix="r6svg_")
    cmds = []
    for n, (s, out, w) in enumerate(jobs):
        pth = os.path.join(tmp, f"{n}.svg")
        with open(pth, "w") as f:
            f.write(s)
        cmds.append(f"file-open:{pth}; export-filename:{out}; export-width:{w}; "
                    f"export-height:{w}; export-background-opacity:0; export-do; file-close")
    subprocess.run(["inkscape", "--shell"], input=("\n".join(cmds) + "\nquit\n").encode(),
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1800)
    miss = [o for _, o, _ in jobs if not os.path.exists(o)]
    if miss:
        raise RuntimeError(f"렌더 실패 {len(miss)}개: {miss[:3]}")

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

def main():
    for dd in (OUT_CH, OUT_GIF, OUT_CMP):
        os.makedirs(dd, exist_ok=True)
    tmp36 = tempfile.mkdtemp(prefix="r6_36_")
    jobs = []
    for c in ORDER:
        os.makedirs(os.path.join(OUT_CH, c), exist_ok=True)
        for pz in POSES:
            s = DRAW[c](pz)
            jobs.append((s, os.path.join(OUT_CH, c, f"{c}_{pz}@3x.png"), 108))
            jobs.append((s, os.path.join(OUT_CH, c, f"{c}_{pz}_L@3x.png"), 240))
            jobs.append((s, os.path.join(tmp36, f"{c}_{pz}.png"), 36))
    render_many(jobs)

    def img(c, pz, size):
        if size == 36:
            return Image.open(os.path.join(tmp36, f"{c}_{pz}.png")).convert("RGBA")
        suf = "_L" if size == 240 else ""
        return Image.open(os.path.join(OUT_CH, c, f"{c}_{pz}{suf}@3x.png")).convert("RGBA")

    # 프레임 차이표
    rows = ["# 인접 프레임 픽셀 차이 (108px, 6라운드)", "",
            "계산: 두 장 중 하나라도 불투명한 픽셀 가운데 색·투명도가 눈에 띄게(채널 차 48 이상) 바뀐 비율. 기준 15% 이상.", "",
            "| 캐릭터 | 1→2 | 2→3 | 3→4 | 4→1 | 최소 | 판정 |", "|---|---|---|---|---|---|---|"]
    diffs = {}
    for c in ORDER:
        fr = [img(c, f"run_{j}", 108) for j in range(1, 5)]
        ds = [frame_diff(fr[j], fr[(j + 1) % 4]) for j in range(4)]
        diffs[c] = ds
        rows.append(f"| {PAL[c]['name']} ({c}) | " + " | ".join(f"{x*100:.0f}%" for x in ds)
                    + f" | {min(ds)*100:.0f}% | {'통과' if min(ds) >= 0.15 else '미달'} |")
    with open(os.path.join(ROOT, "frame_diff.md"), "w") as f:
        f.write("\n".join(rows) + "\n")

    # 대비표
    con = {c: {k: round(contrast(PAL[c][k], "#000000"), 1) for k in ("body", "dark", "point")} for c in ORDER}
    with open(os.path.join(HERE, "contrast.json"), "w") as f:
        json.dump({"contrast_vs_black": con, "frame_diff": {c: [round(x, 3) for x in v] for c, v in diffs.items()}},
                  f, ensure_ascii=False, indent=1)

    # GIF (8fps = 125ms)
    for c in ORDER:
        for size in (108, 240):
            fr = [img(c, f"run_{j}", size) for j in range(1, 5)]
            bg = []
            for im in fr:
                base = Image.new("RGBA", im.size, (0, 0, 0, 255)); base.alpha_composite(im)
                bg.append(base.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=64))
            bg[0].save(os.path.join(OUT_GIF, f"{c}_run_{size}_8fps.gif"), save_all=True,
                       append_images=bg[1:], duration=125, loop=0, disposal=2)

    # 비교판
    make_board(img, diffs, con)
    print("완료:", len(jobs), "장 렌더")
    for c in ORDER:
        print(c, [f"{x*100:.0f}" for x in diffs[c]], con[c])

VERDICT_FILE = os.path.join(HERE, "verdict.json")

def make_board(img, diffs, con):
    verdict = {}
    if os.path.exists(VERDICT_FILE):
        verdict = json.load(open(VERDICT_FILE))
    fdir = "/usr/share/fonts/truetype/nanum/"
    def font(sz, bold=False):
        for n in (["NanumGothicBold.ttf", "NanumSquareRoundB.ttf"] if bold else ["NanumGothic.ttf", "NanumSquareRoundR.ttf"]):
            if os.path.exists(fdir + n):
                return ImageFont.truetype(fdir + n, sz)
        return ImageFont.load_default()
    F, FB, FS = font(22), font(26, True), font(18)
    colw = 760; rowh = 300; pad = 30
    cols = 2
    nrows = math.ceil(len(ORDER) / cols)
    W = cols * colw + pad * 2
    H = 150 + nrows * rowh + 40
    board = Image.new("RGB", (W, H), (0, 0, 0))
    dr = ImageDraw.Draw(board)
    dr.text((pad, 24), "6라운드: 단색 면 + 점 눈, 11종", fill=(240, 240, 240), font=font(34, True))
    dr.text((pad, 72), "각 칸 왼쪽 위: 실제 36px 달리기 4장 · 정지 · 쉼 / 가운데 108px / 오른쪽 240px.  "
            "회색 띠 = 아일랜드에서 잘리는 위아래(약 15px@3x)", fill=(170, 170, 170), font=FS)
    dr.text((pad, 100), "판정: ○ 36px 에서 바로 읽힘  △ 읽히지만 약함  × 36px 에서 안 읽힘",
            fill=(170, 170, 170), font=FS)
    for n, c in enumerate(ORDER):
        cx = pad + (n % cols) * colw; cy = 140 + (n // cols) * rowh
        v = verdict.get(c, {"mark": "?", "note": ""})
        dr.text((cx, cy), f"{v['mark']} {PAL[c]['name']}", fill=(240, 240, 240), font=FB)
        dr.text((cx + 190, cy + 6), v["note"], fill=(200, 200, 200), font=FS)
        # 36px 줄: 아일랜드 칸처럼 위아래를 잘라 보여 줌(36×26 보이는 부분)
        x = cx; y = cy + 44
        for pz in ["run_1", "run_2", "run_3", "run_4", "still", "rest_1"]:
            im = img(c, pz, 36)
            tile = Image.new("RGBA", (36, 36), (0, 0, 0, 255)); tile.alpha_composite(im)
            board.paste(tile.convert("RGB"), (x, y))
            dr.rectangle([x, y, x + 35, y + 4], fill=(40, 40, 40))
            dr.rectangle([x, y + 31, x + 35, y + 35], fill=(40, 40, 40))
            x += 44
        dr.text((cx, y + 42), "36px 실제 크기", fill=(130, 130, 130), font=font(14))
        # 36px 를 정수배(3배) 확대한 것: 픽셀이 어떻게 뭉치는지
        x = cx; y2 = cy + 110
        for pz in ["run_1", "run_3"]:
            im = img(c, pz, 36).resize((108, 108), Image.NEAREST)
            tile = Image.new("RGBA", (108, 108), (0, 0, 0, 255)); tile.alpha_composite(im)
            board.paste(tile.convert("RGB"), (x, y2)); x += 116
        dr.text((cx, y2 + 112), "36px 를 3배 확대(픽셀 확인)", fill=(130, 130, 130), font=font(14))
        # 108, 240
        x = cx + 250
        im = img(c, "run_1", 108)
        t = Image.new("RGBA", (108, 108), (0, 0, 0, 255)); t.alpha_composite(im)
        board.paste(t.convert("RGB"), (x, cy + 110))
        dr.rectangle([x, cy + 110, x + 107, cy + 124], outline=(50, 50, 50))
        dr.rectangle([x, cy + 203, x + 107, cy + 217], outline=(50, 50, 50))
        x += 124
        im = img(c, "run_1", 240)
        t = Image.new("RGBA", (240, 240), (0, 0, 0, 255)); t.alpha_composite(im)
        board.paste(t.convert("RGB"), (x, cy + 36))
        dr.line([x, cy + 36 + 33, x + 239, cy + 36 + 33], fill=(50, 50, 50))
        dr.line([x, cy + 36 + 207, x + 239, cy + 36 + 207], fill=(50, 50, 50))
        sw = [PAL[c]["body"], PAL[c]["dark"], PAL[c]["point"]]
        for j, hc in enumerate(sw):
            dr.rectangle([cx + 250 + j * 40, cy + 236, cx + 280 + j * 40, cy + 256], fill=hc)
        dr.text((cx + 250, cy + 262), f"대비 {con[c]['body']} / {con[c]['dark']} / {con[c]['point']} : 1  "
                f"프레임차 최소 {min(diffs[c])*100:.0f}%", fill=(130, 130, 130), font=font(14))
    board.save(os.path.join(OUT_CMP, "family_11.png"), optimize=True)

    # 아일랜드 줄 미리보기: 실제 크기 한 줄(36px 칸 11개, 위아래 잘림) + 같은 줄 3배
    strip = Image.new("RGB", (len(ORDER) * 44 + 20, 46), (0, 0, 0))
    for n, c in enumerate(ORDER):
        im = img(c, "run_1", 36); t = Image.new("RGBA", (36, 36), (0, 0, 0, 255)); t.alpha_composite(im)
        strip.paste(t.convert("RGB").crop((0, 5, 36, 31)), (10 + n * 44, 10))
    strip.save(os.path.join(OUT_CMP, "island_strip_actual.png"))
    strip.resize((strip.width * 3, strip.height * 3), Image.NEAREST).save(
        os.path.join(OUT_CMP, "island_strip_x3.png"))

if __name__ == "__main__":
    main()
