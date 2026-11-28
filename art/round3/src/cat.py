#!/usr/bin/env python3
"""3라운드 고양이: 뼈대 좌표(포즈) + 변형 스타일 -> SVG.

좌표계: 108x108 (36pt @3x). 오른쪽을 보고 달린다. 아일랜드에서 보이는 띠는 y 15~93.
같은 포즈 데이터를 네 변형(A~D)이 함께 쓴다. 스타일만 다르다.
"""
import math, os, sys

# ---------------------------------------------------------------- 기하 도구
def lerp(a, b, t): return a + (b - a) * t
def add(p, q): return (p[0] + q[0], p[1] + q[1])
def sub(p, q): return (p[0] - q[0], p[1] - q[1])
def mul(p, k): return (p[0] * k, p[1] * k)
def norm(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)

def smooth_closed(pts, k=1.0):
    """점 목록 -> Catmull-Rom 을 3차 베지어로 바꾼 닫힌 경로."""
    n = len(pts)
    d = f"M{pts[0][0]:.2f},{pts[0][1]:.2f}"
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * k, p1[1] + (p2[1] - p0[1]) / 6 * k)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * k, p2[1] - (p3[1] - p1[1]) / 6 * k)
        d += f" C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}"
    return d + "Z"

def smooth_open(pts):
    d = f"M{pts[0][0]:.2f},{pts[0][1]:.2f}"
    ext = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}"
    return d

def dense(pts, per=8):
    """열린 Catmull-Rom 곡선을 촘촘한 점과 각 점의 구간 위치(0~len-1)로."""
    ext = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for j in range(per):
            t = j / per
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append(((x, y), i - 1 + t))
    out.append((pts[-1], len(pts) - 1))
    return out

def tube(pts, widths, start=0.0):
    """굵기가 변하는 관(다리·꼬리). widths 는 조절점마다의 굵기. start 이후 부분만."""
    dp = [(p, u) for p, u in dense(pts) if u >= start]
    L, R = [], []
    for k, (p, u) in enumerate(dp):
        q0 = dp[max(0, k - 1)][0]; q1 = dp[min(len(dp) - 1, k + 1)][0]
        tg = norm(sub(q1, q0)); nv = (-tg[1], tg[0])
        i = min(int(u), len(widths) - 2); f = u - i
        w = lerp(widths[i], widths[i + 1], f) / 2
        L.append(add(p, mul(nv, w))); R.append(add(p, mul(nv, -w)))
    # 끝은 반원으로 닫는다
    def capr(c, a, b, n=5):
        out = []
        va, vb = sub(a, c), sub(b, c)
        r = math.hypot(*va)
        a0 = math.atan2(va[1], va[0])
        tg = norm(sub(dp[-1][0], dp[-2][0])) if c == dp[-1][0] else norm(sub(dp[0][0], dp[1][0]))
        # a 에서 b 로, tg 쪽으로 볼록하게
        for j in range(1, n):
            ang = math.pi * j / n
            v = add(mul(norm(va), math.cos(ang)), mul(tg, math.sin(ang)))
            out.append(add(c, mul(v, r)))
        return out
    end = dp[-1][0]; beg = dp[0][0]
    pts_ = L + capr(end, L[-1], R[-1]) + R[::-1] + capr(beg, R[0], L[0])
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts_) + "Z"

def quad(a, c, b, t):
    return (lerp(lerp(a[0], c[0], t), lerp(c[0], b[0], t), t),
            lerp(lerp(a[1], c[1], t), lerp(c[1], b[1], t), t))

def torso_pts(hip, sho, bend, ru=(10, 11), rd=(10, 12.5), waist=3.0, n=10):
    d = sub(sho, hip)
    up = norm((d[1], -d[0]))
    mid = mul(add(hip, sho), 0.5)
    ctl = add(mid, mul(up, bend * 2))
    upper, lower = [], []
    for i in range(n + 1):
        t = i / n
        p = quad(hip, ctl, sho, t)
        tg = norm(sub(quad(hip, ctl, sho, min(1, t + .01)), quad(hip, ctl, sho, max(0, t - .01))))
        nu = (tg[1], -tg[0])
        r_u = lerp(ru[0], ru[1], t) - 0.8 * math.sin(math.pi * t)
        r_d = lerp(rd[0], rd[1], t) - waist * math.sin(math.pi * t)
        upper.append(add(p, mul(nu, r_u)))
        lower.append(add(p, mul(nu, -r_d)))
    def cap(center, tg, r_u, r_d, forward):
        nu = (tg[1], -tg[0])
        out = []
        for j in range(1, 6):
            a = math.pi * j / 6
            s = 1 if forward else -1
            # 위 법선에서 시작해 앞(또는 뒤)으로 돌아 아래 법선까지
            r = lerp(r_u, r_d, j / 6)
            v = add(mul(nu, math.cos(a)), mul(tg, s * math.sin(a)))
            out.append(add(center, mul(v, r)))
        return out
    tg1 = norm(sub(sho, ctl)); tg0 = norm(sub(ctl, hip))
    pts = upper + cap(sho, tg1, ru[1], rd[1], True) + lower[::-1] + cap(hip, tg0, ru[0], rd[0], False)[::-1]
    return pts

# ---------------------------------------------------------------- 포즈
# 각 다리는 [뿌리, 관절..., 발] 좌표. 뿌리는 어깨/엉덩이 근처.
# 4장 갤럽: 1 뻗은 공중 / 2 앞발 착지(모으기 시작) / 3 모은 공중 / 4 뒷발 디딤(뻗기 시작)
POSES = {
 "run_1": dict(hip=(31, 53), sho=(68, 51), bend=-1.5, head=(83, 40), tilt=-4, ear=-14, scarf=(-17, -1),
     fn=[(69, 56), (81, 61), (92, 64), (99, 63)], ff=[(66, 57), (77, 64), (87, 69), (93, 69)],
     hn=[(32, 56), (22, 63), (12, 66), (5, 63)], hf=[(35, 58), (25, 66), (16, 70), (10, 70)],
     tail=[(25, 49), (15, 46), (8, 41), (4, 34)]),
 "run_2": dict(hip=(35, 52), sho=(68, 54), bend=3, head=(82, 43), tilt=4, ear=-6, scarf=(-15, 3),
     fn=[(69, 59), (71, 70), (70, 80), (73, 86)], ff=[(66, 60), (62, 70), (57, 79), (55, 85)],
     hn=[(35, 55), (42, 64), (48, 70), (55, 71)], hf=[(38, 57), (43, 67), (47, 74), (53, 76)],
     tail=[(27, 49), (17, 49), (10, 45), (6, 39)]),
 "run_3": dict(hip=(38, 51), sho=(67, 52), bend=7, head=(81, 42), tilt=2, ear=-2, scarf=(-13, -7),
     fn=[(67, 57), (66, 65), (60, 69), (55, 67)], ff=[(64, 58), (62, 66), (56, 70), (51, 69)],
     hn=[(40, 55), (50, 59), (58, 65), (66, 71)], hf=[(42, 57), (51, 62), (58, 69), (63, 75)],
     tail=[(31, 46), (24, 39), (22, 30), (17, 24)]),
 "run_4": dict(hip=(34, 54), sho=(69, 50), bend=1.5, head=(84, 38), tilt=-7, ear=-10, scarf=(-17, -4),
     fn=[(70, 55), (79, 58), (89, 59), (96, 56)], ff=[(67, 56), (76, 61), (85, 64), (91, 63)],
     hn=[(34, 57), (30, 67), (26, 77), (22, 86)], hf=[(37, 59), (35, 69), (33, 78), (31, 86)],
     tail=[(26, 50), (16, 47), (10, 40), (7, 32)]),
}

# 몸통을 짧게: 엉덩이·뒷다리·꼬리를 5px 앞으로 (머리 대 몸 비율을 귀엽게)
for _p in POSES.values():
    _p["hip"] = (_p["hip"][0] + 5, _p["hip"][1])
    for _k in ("hn", "hf", "tail"):
        _p[_k] = [(x + 5, y) for x, y in _p[_k]]

# 쉼(엎드려 숨쉬기 2장)·정지(앉기). 달리기와 같은 배율로 그린다(크기가 튀지 않게).
POSES["rest_1"] = dict(hip=(40, 73), sho=(66, 72), bend=2.5, head=(80, 60), tilt=6, ear=-4, eyes_closed=True,
    torso=dict(ru=(11, 11.5), rd=(9, 9.5)), scarf=(-13, 6),
    fn=[(66, 76), (74, 80), (83, 82), (88, 82)], ff=[(63, 77), (70, 81), (78, 83), (83, 83)],
    hn=[(40, 76), (48, 80), (55, 83), (60, 83)], hf=None,
    tail=[(31, 76), (25, 82), (32, 85), (46, 85)])
POSES["rest_2"] = dict(POSES["rest_1"], head=(80, 61.2), tilt=8, ear=-7, bend=3.5, scarf=(-13, 7),
    torso=dict(ru=(12.2, 12.6), rd=(9.4, 9.8)),
    tail=[(31, 76), (25, 82), (32, 85.5), (47, 84)])
POSES["still"] = dict(hip=(46, 75), sho=(60, 59), bend=-1, head=(69, 45), tilt=-2, ear=0, scarf=(-12, 8),
    torso=dict(ru=(12.5, 10), rd=(12.5, 11)), haunch=(13.5, 11),
    fn=[(61, 63), (63, 72), (63, 80), (65, 86)], ff=[(57, 64), (58, 73), (58, 80), (59, 86)],
    hn=[(45, 78), (51, 83), (56, 86), (60, 87)], hf=None,
    tail=[(36, 82), (36, 89), (52, 90), (64, 85)], tail_front=True)

# 정지 자세는 띠(y93) 안에 들도록 2px 위로
_st = POSES["still"]
for _k in ("hip", "sho", "head"):
    _st[_k] = (_st[_k][0], _st[_k][1] - 2)
for _k in ("fn", "ff", "hn", "tail"):
    _st[_k] = [(x, y - 2) for x, y in _st[_k]]

# 화면 맞춤: 같은 세트(달리기 4장)는 같은 배율. build 스크립트가 재서 넣는다.
FIT = {}

# ---------------------------------------------------------------- 변형 스타일
STYLES = {
 # A: 선 없음, 살구 단면, 크림 배·주둥이·꼬리 끝, 알약 눈 + 하이라이트 1, 둥근 끝 귀
 "a": dict(body="#F4AE68", far="#B9783C", belly="#FFE6C4", tip="#FFE6C4", rim=None,
           eye="pill", eyec="#2B1D16", nose="#E8787A", blush="#F07F6A", ear="round", earin="#E8907A",
           head_s=1.1, marks=None),
 # B: 선 없음, 모래색 + 등 줄무늬·꼬리 고리, 점 눈만(가장 단순한 얼굴), 길고 뾰족한 귀
 "b": dict(body="#E6D6B8", far="#A8977A", belly=None, tip="#6E5640", rim=None,
           eye="dot", eyec="#2A221C", nose=None, blush=None, ear="tall", earin=None,
           head_s=1.02, marks="stripes", markc="#8A6C50"),
 # C: 선 없음, 연회청 + 흰 배, 주황 목도리(흩날림 오버랩), 둥근 점 눈 + 하이라이트, 끝 접힌 귀
 "c": dict(body="#B4BFCD", far="#7C8798", belly="#F1F3F6", tip="#F1F3F6", rim=None,
           eye="round", eyec="#1F232B", nose="#E58A8F", blush=None, ear="fold", earin="#E8A2A6",
           head_s=1.1, marks="scarf", markc="#FF9F0A"),
 # D: 선 있음(밝은 테), 먹색 몸, 큰 호박색 눈 + 세로 동공, 뾰족 귀, 분홍 코
 "d": dict(body="#2A2A31", far="#1C1C21", belly=None, tip=None, rim="#F3E7D3", rimw=1.7,
           eye="amber", eyec="#FFC53D", nose="#F29AA0", blush=None, ear="point", earin="#5A4650",
           head_s=1.1, marks=None),
}

def leg_path(pts):
    return smooth_open(pts)

def ear_poly(kind, base_c, s, rot):
    """귀: 머리 위 기준점에서 그린다. 오른쪽이 앞."""
    if kind == "tall":
        pts = [(-5.5, 2), (-1.5, -11.5), (5, 2)]
    elif kind == "round":
        pts = [(-6, 2), (-4.5, -6), (-1.2, -9.5), (2.2, -6.5), (6, 2)]
    elif kind == "fold":
        pts = [(-6, 2), (-3.5, -7), (-0.5, -9.0), (3.5, -6.5), (2.5, -4.5), (6, 2)]
    else:  # point
        pts = [(-6, 2), (-2.5, -10), (5.5, 2)]
    a = math.radians(rot)
    out = []
    for x, y in pts:
        x, y = x * s, y * s
        out.append((base_c[0] + x * math.cos(a) - y * math.sin(a),
                    base_c[1] + x * math.sin(a) + y * math.cos(a)))
    return out

def poly_d(pts):
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z"

def cat_svg(style_key, pose_key, size=108):
    st = STYLES[style_key]
    P = POSES[pose_key] if isinstance(pose_key, str) else pose_key
    rim = st.get("rim"); rw = st.get("rimw", 0)
    hs = st["head_s"]
    body, far = st["body"], st["far"]
    hx, hy = P["head"]
    rx, ry = 15.0 * hs, 13.0 * hs
    tilt = P.get("tilt", 0)
    far_layer, near_layer = [], []   # (종류, 데이터, 색, 굵기)

    # 다리 굵기(뿌리 -> 발목). 뒷다리는 허벅지가 굵고 발목이 가늘다: 날렵함의 핵심
    WF = [7.4, 5.4, 4.0, 3.8]
    WH = [9.5, 6.4, 3.9, 3.7]
    def paw(pts, col, layer, s=1.0):
        a, b = pts[-2], pts[-1]
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        tg = norm(sub(b, a))
        c = add(b, mul(tg, 0.8))
        layer.append(("ellipse_r", (c[0], c[1], 3.3 * s, 2.5 * s, ang), col, 0))
    for key, W in (("hf", WH), ("ff", WF)):
        if P.get(key):
            far_layer.append(("fill", tube(P[key], W), far, 0)); paw(P[key], far, far_layer)
    # 먼 쪽 귀 (머리 뒤)
    ear_base_far = (hx + 2.5 * hs, hy - ry * 0.78)
    far_layer.append(("fill", poly_d(ear_poly(st["ear"], ear_base_far, hs * 0.95, P.get("ear", 0) + 8)), far, 0))

    # 꼬리
    tail = P["tail"]
    WT = [6.6, 5.6, 4.8, 4.4]
    near_layer.append(("fill", tube(tail, WT), body, 0))
    if st.get("tip"):
        near_layer.append(("fill", tube(tail, WT, start=2.25), st["tip"], 0))
    # 몸통 + 엉덩이 살
    tp = torso_pts(P["hip"], P["sho"], P["bend"], **P.get("torso", {}))
    near_layer.append(("fill", smooth_closed(tp), body, 0))
    # 가까운 다리 (엉덩이 살은 허벅지 방향으로 기운 타원)
    if P.get("hn"):
        k = P["hn"][1]; h0 = P["hn"][0]
        ang = math.degrees(math.atan2(k[1] - h0[1], k[0] - h0[0]))
        near_layer.append(("ellipse_r", (h0[0] + 0.5 * (k[0] - h0[0]) * 0.35, h0[1] - 1 + 0.5 * (k[1] - h0[1]) * 0.35, *P.get("haunch", (11.5, 9.5)), ang), body, 0))
        near_layer.append(("fill", tube(P["hn"], WH), body, 0)); paw(P["hn"], body, near_layer)
    front_layer = []   # 선 있는 변형: 가까운 앞다리를 따로 테를 둘러 몸 위로
    if P.get("fn"):
        tgt = front_layer if rim else near_layer
        tgt.append(("fill", tube(P["fn"], WF), body, 0)); paw(P["fn"], body, tgt)
    # 목: 어깨와 머리를 잇는 살
    neck = [add(P["sho"], (-3, -9)), add((hx, hy), (-9 * hs, -4)), add((hx, hy), (-4 * hs, 9 * hs)), add(P["sho"], (4, 6))]
    near_layer.append(("fill", smooth_closed(neck), body, 0))
    if P.get("tail_front"):
        near_layer.append(("fill", tube(tail, [6.0, 5.4, 4.8, 4.4]), body, 0))
        if st.get("tip"):
            near_layer.append(("fill", tube(tail, [6.0, 5.4, 4.8, 4.4], start=2.25), st["tip"], 0))
    # 가까운 쪽 귀
    ear_base = (hx - 4.5 * hs, hy - ry * 0.80)
    near_layer.append(("fill", poly_d(ear_poly(st["ear"], ear_base, hs, P.get("ear", 0))), body, 0))
    # 머리
    near_layer.append(("head", (hx, hy, rx, ry, tilt), body, 0))

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 108 108">']
    fit = FIT.get(P.get("set", "run"), (1, 0, 0))
    out.append(f'<g id="fit" transform="translate({fit[1]:.2f} {fit[2]:.2f}) scale({fit[0]:.4f})">')

    def emit(items, with_rim):
        g = []
        if with_rim and rim:
            g.append(f'<g id="rim" fill="{rim}" stroke="{rim}" stroke-width="{2*rw:.2f}" stroke-linejoin="round" stroke-linecap="round">')
            for kind, data, col, w in items:
                if kind == "stroke":
                    g.append(f'<path d="{data}" fill="none" stroke-width="{w+2*rw:.2f}"/>')
                elif kind == "fill":
                    g.append(f'<path d="{data}"/>')
                elif kind == "ellipse":
                    cx, cy, ex, ey = data
                    g.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{ex}" ry="{ey}"/>')
                elif kind == "ellipse_r":
                    cx, cy, ex, ey, an = data
                    g.append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{ex}" ry="{ey}" transform="rotate({an:.1f} {cx:.2f} {cy:.2f})"/>')
                elif kind == "head":
                    cx, cy, ex, ey, tl = data
                    g.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{ex}" ry="{ey}" transform="rotate({tl} {cx} {cy})"/>')
            g.append('</g>')
        for kind, data, col, w in items:
            if kind == "stroke":
                g.append(f'<path d="{data}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
            elif kind == "fill":
                g.append(f'<path d="{data}" fill="{col}" stroke="{col}" stroke-width="0.6" stroke-linejoin="round"/>')
            elif kind == "ellipse":
                cx, cy, ex, ey = data
                g.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{ex}" ry="{ey}" fill="{col}"/>')
            elif kind == "ellipse_r":
                cx, cy, ex, ey, an = data
                g.append(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{ex}" ry="{ey}" fill="{col}" transform="rotate({an:.1f} {cx:.2f} {cy:.2f})"/>')
            elif kind == "head":
                cx, cy, ex, ey, tl = data
                g.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{ex}" ry="{ey}" fill="{col}" transform="rotate({tl} {cx} {cy})"/>')
            elif kind == "tip":
                # 꼬리 끝 마지막 30% 만 다른 색
                pts = data
                a = quad(pts[1], pts[2], pts[3], 0.35)
                g.append(f'<path d="{smooth_open([a, pts[3]])}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>')
        return g

    out.append('<g id="far">'); out += emit(far_layer, True); out.append('</g>')
    out.append('<g id="near">'); out += emit(near_layer, True)
    if front_layer:
        out.append('<g id="front">'); out += emit(front_layer, True); out.append('</g>')

    # ---- 무늬·배·얼굴 (머리 좌표계 안에서)
    clip_id = f"bodyclip_{style_key}"
    if st.get("belly"):
        # 가슴털: 어깨 앞 아래에 한 덩어리 (몸통·목 윤곽 안으로 자른다)
        out.append(f'<clipPath id="{clip_id}"><path d="{smooth_closed(tp)}"/><path d="{smooth_closed(neck)}"/></clipPath>')
        s_ = P["sho"]
        out.append(f'<ellipse cx="{s_[0]+7:.1f}" cy="{s_[1]+6:.1f}" rx="8.5" ry="8" fill="{st["belly"]}" clip-path="url(#{clip_id})"/>')
    if st.get("marks") == "stripes":
        out.append(f'<clipPath id="{clip_id}"><path d="{smooth_closed(tp)}"/></clipPath>')
        h, s_ = P["hip"], P["sho"]
        for t in (0.22, 0.44, 0.66):
            p = quad(h, add(mul(add(h, s_), .5), mul(norm((s_[1]-h[1], -(s_[0]-h[0]))), P["bend"]*2)), s_, t)
            ang = math.degrees(math.atan2(s_[1]-h[1], s_[0]-h[0]))
            out.append(f'<rect x="{p[0]-1.6:.1f}" y="{p[1]-14:.1f}" width="3.2" height="9" rx="1.6" fill="{st["markc"]}" clip-path="url(#{clip_id})" transform="rotate({ang:.1f} {p[0]:.1f} {p[1]:.1f})"/>')
        # 이마 줄 하나
        out.append(f'<rect x="{hx-2.5:.1f}" y="{hy-ry-1:.1f}" width="2.6" height="6" rx="1.3" fill="{st["markc"]}" transform="rotate({tilt} {hx} {hy})"/>')
        # 꼬리 고리 2개
        for t in (0.35, 0.62):
            p = quad(tail[1], tail[2], tail[3], t)
            out.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="2.9" fill="{st["markc"]}"/>')
    if st.get("marks") == "scarf":
        s_ = P["sho"]
        # 목 둘레 위치: 머리 아래 뒤쪽
        a = add((hx, hy), (-10 * hs, 2)); b = add((hx, hy), (-1 * hs, 11 * hs))
        out.append(f'<path d="M{a[0]:.1f},{a[1]:.1f} Q{a[0]+1:.1f},{b[1]:.1f} {b[0]:.1f},{b[1]:.1f}" fill="none" stroke="{st["markc"]}" stroke-width="4.6" stroke-linecap="round"/>')
        # 흩날리는 두 끝: 매듭에서 뒤로. 포즈마다 각도가 늦게 따라옴(오버랩)
        fl = P.get("scarf", (-15, -2))
        k0 = add(a, (1, 2))
        e1 = add(k0, fl); e2 = add(k0, (fl[0] * 0.75, fl[1] + 5))
        out.append(f'<path d="{tube([k0, add(k0,(fl[0]*0.5, fl[1]*0.5-2)), e1], [3.6, 3.2, 2.0])}" fill="{st["markc"]}"/>')
        out.append(f'<path d="{tube([k0, add(k0,(fl[0]*0.4, fl[1]*0.4+3)), e2], [3.2, 2.8, 1.8])}" fill="#D98200"/>')

    # 얼굴: 머리 기울기를 따라 돈다
    out.append(f'<g id="face" transform="rotate({tilt} {hx} {hy})">')
    if st.get("earin"):
        eb = ear_poly(st["ear"], ear_base, hs * 0.55, P.get("ear", 0))
        eb = [add(p, (0.4, 1.6 * hs)) for p in eb]
        out.append(f'<path d="{poly_d(eb)}" fill="{st["earin"]}" stroke="{st["earin"]}" stroke-width="0.6" stroke-linejoin="round"/>')
    # 주둥이(앞쪽 아래)
    mzx, mzy = hx + rx * 0.72, hy + ry * 0.32
    if st.get("belly"):
        out.append(f'<ellipse cx="{mzx:.1f}" cy="{mzy:.1f}" rx="{5.6*hs:.1f}" ry="{4.2*hs:.1f}" fill="{st["belly"]}"/>')
    ex, ey = hx + rx * 0.38, hy - ry * 0.08
    closed = P.get("eyes_closed", False)
    if closed:
        col = st["eyec"] if st["eye"] != "amber" else rim
        out.append(f'<path d="M{ex-2.6:.1f},{ey:.1f} Q{ex:.1f},{ey+2.4:.1f} {ex+2.6:.1f},{ey:.1f}" fill="none" stroke="{col}" stroke-width="1.5" stroke-linecap="round"/>')
    elif st["eye"] == "pill":
        out.append(f'<ellipse cx="{ex:.1f}" cy="{ey:.1f}" rx="{2.6*hs:.2f}" ry="{3.6*hs:.2f}" fill="{st["eyec"]}"/>')
        out.append(f'<circle cx="{ex+0.6:.1f}" cy="{ey-1.2:.1f}" r="1.15" fill="#FFFFFF"/>')
    elif st["eye"] == "dot":
        out.append(f'<circle cx="{ex:.1f}" cy="{ey+0.4:.1f}" r="{2.3*hs:.2f}" fill="{st["eyec"]}"/>')
    elif st["eye"] == "round":
        out.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="3.2" fill="{st["eyec"]}"/>')
        out.append(f'<circle cx="{ex+0.9:.1f}" cy="{ey-0.9:.1f}" r="0.9" fill="#FFFFFF"/>')
    elif st["eye"] == "amber":
        out.append(f'<ellipse cx="{ex:.1f}" cy="{ey:.1f}" rx="3.5" ry="3.9" fill="{st["eyec"]}"/>')
        out.append(f'<ellipse cx="{ex+0.6:.1f}" cy="{ey:.1f}" rx="0.95" ry="2.6" fill="#141417"/>')
    if st.get("nose"):
        nx, ny = hx + rx * 0.98, hy + ry * 0.10
        out.append(f'<path d="M{nx-1.6:.1f},{ny-1.0:.1f} L{nx+0.8:.1f},{ny-1.0:.1f} L{nx-0.3:.1f},{ny+0.8:.1f}Z" fill="{st["nose"]}" stroke="{st["nose"]}" stroke-width="0.8" stroke-linejoin="round"/>')
    if st.get("blush") and not closed:
        out.append(f'<ellipse cx="{ex+0.5:.1f}" cy="{ey+4.6:.1f}" rx="2.3" ry="1.3" fill="{st["blush"]}" opacity="0.85"/>')
    elif st.get("blush"):
        out.append(f'<ellipse cx="{ex+0.5:.1f}" cy="{ey+4.0:.1f}" rx="2.3" ry="1.3" fill="{st["blush"]}" opacity="0.85"/>')
    out.append('</g>')
    out.append('</g></g></svg>')
    return "\n".join(out)

if __name__ == "__main__":
    outdir = sys.argv[1]
    keys = sys.argv[2].split(",") if len(sys.argv) > 2 else list(STYLES)
    poses = sys.argv[3].split(",") if len(sys.argv) > 3 else list(POSES)
    os.makedirs(outdir, exist_ok=True)
    for k in keys:
        for p in poses:
            with open(os.path.join(outdir, f"cat_{k}_{p}.svg"), "w") as f:
                f.write(cat_svg(k, p))
