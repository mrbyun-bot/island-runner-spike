"""무료 3종(햄스터·펭귄·로켓) 실제 사용 프레임을 B 윤곽선 스티커 방식으로 만든다.

사용: python3 make_frames.py            → src/svg/*.svg 를 쓰고 Inkscape 로 ../*.png 를 뽑는다
출력: {char}_run_1..4@3x.png, {char}_rest_1..2@3x.png, {char}_still@3x.png        (108x108)
      {char}_run_1..4_L@3x.png, {char}_rest_1..2_L@3x.png, {char}_still_L@3x.png (240x240)
한 장이 완성된 통그림이다(쳇바퀴·불꽃 등 고정 요소도 장마다 들어감).

2라운드 달리기 설계(2026-11-28)
- 아일랜드는 초당 8장이 한계라 4장 = 0.5초. 부드러움은 장 수가 아니라 포즈 설계로 낸다.
- 4장 = 한 걸음의 접지 → 내려감 → 지나감 → 올라감. 다음 걸음은 반대 다리가 같은 일을 하므로,
  안쪽·바깥 다리를 같은 모양·색으로 그리면 4장 루프가 끊김 없이 이어진다(8단계 보폭을 4장 간격으로 두 다리가 나눠 씀).
- 몸통 위아래는 1px 안쪽으로 줄이고, 발·꼬리·귀·목도리·머리깃·불꽃이 서로 다른 박자(위상차)로 움직여 달림을 만든다.
- 겹침 동작: lag() — 앞 장의 몸 움직임을 한 장 늦게 따라간다(4장 루프라 i-1 은 돌아감).
"""
import os, sys, subprocess, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from chars import P, LINE, BORDER, CHARS, flame_path, HAM_HIP_H, HAM_HIP_F, HAM_GROUND

OUT = os.path.dirname(HERE)            # Assets/frames/characters
SVG_DIR = os.path.join(HERE, "svg")


# ---------- 기본 도형 ----------
def shape_el(shape, attrs, transform=""):
    t = f' transform="{transform}"' if transform else ""
    k = shape[0]
    if k == "circle":
        return f'<circle cx="{shape[1]}" cy="{shape[2]}" r="{shape[3]}" {attrs}{t}/>'
    if k == "ellipse":
        return f'<ellipse cx="{shape[1]}" cy="{shape[2]}" rx="{shape[3]}" ry="{shape[4]}" {attrs}{t}/>'
    return f'<path d="{shape[1]}" {attrs}{t}/>'


def is_empty(shape):
    return shape[0] == "ellipse" and shape[3] < 0.1


def rot(a, cx, cy):
    return f"rotate({a:.2f} {cx} {cy})" if a else ""


def mv(dx, dy):
    return f"translate({dx:.2f} {dy:.2f})" if (dx or dy) else ""


def squash(px, py, sx=1, sy=1, dy=0, r=0, k=1.0):
    """기준점 (px,py)(발바닥)를 중심으로 기울기 r, 가로 sx·세로 sy, 위아래 dy. k 는 전체 배율."""
    return f"translate({px} {py + dy:.2f}) rotate({r:.2f}) scale({k * sx:.3f} {k * sy:.3f}) translate({-px} {-py})"


def join(*ts):
    return " ".join(t for t in ts if t)


def capsule(x1, y1, x2, y2, r):
    """두 점을 잇는 둥근 막대(다리)."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L * r, dx / L * r
    return ("path", f"M{x1 + nx:.2f} {y1 + ny:.2f} L{x2 + nx:.2f} {y2 + ny:.2f} A{r} {r} 0 0 0 {x2 - nx:.2f} {y2 - ny:.2f} "
                    f"L{x1 - nx:.2f} {y1 - ny:.2f} A{r} {r} 0 0 0 {x1 + nx:.2f} {y1 + ny:.2f} Z")


def lag(seq, i, k):
    """겹침 동작: 앞 장에서 이번 장으로 몸이 움직인 양의 k 배만큼 반대로 뒤처진다."""
    return k * (seq[i - 1] - seq[i])


# ---------- 쳇바퀴 ----------
def wheel(sz, angle):
    """확대 구도 쳇바퀴: 중심 (54,52), 반지름 43, 테 민트 #7BE0C3, 살 3갈래 + 살 끝 리벳 3개."""
    cx, cy, r, w = 54, 52, 43, 4.5
    ow = 2.6 if sz == 108 else 2.0
    sp = [(cx + 40.5 * math.cos(math.radians(angle + 120 * k)), cy + 40.5 * math.sin(math.radians(angle + 120 * k))) for k in range(3)]
    o = ['<g id="wheel">',
         f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{BORDER}" stroke-width="{w + 2 * ow + 3}"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINE}" stroke-width="{w + 2 * ow}"/>']
    for x, y in sp:
        o.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" stroke="{LINE}" stroke-width="{3 + 2 * ow * .7:.2f}" stroke-linecap="round"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{P["ring"]}" stroke-width="{w}"/>')
    for x, y in sp:
        o.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" stroke="{P["spoke"]}" stroke-width="3" stroke-linecap="round"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="4.6" fill="{P["hub"]}" stroke="{LINE}" stroke-width="{ow * .8:.2f}"/>')
    for x, y in sp:
        o.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.6" fill="{P["hub"]}" stroke="{LINE}" stroke-width="{ow * .7:.2f}"/>')
    o.append("</g>")
    return "\n".join(o)


# ---------- 얼굴: 캐릭터마다 다른 공식 ----------
def eye_open(style, x, y, r, side):
    """side: -1 왼눈, +1 오른눈(눈꼬리 방향)."""
    E = P["eye"]
    if style == "droop":
        # 햄스터: 가로로 조금 넓은 타원을 바깥쪽이 처지게 기울임 + 코 쪽 위에 큰 하이라이트 1개
        a = 14 * side
        return (f'<ellipse cx="{x}" cy="{y}" rx="{r * 1.04:.2f}" ry="{r * .94:.2f}" fill="{E}" transform="rotate({a} {x} {y})"/>'
                f'<circle cx="{x - side * r * .34:.2f}" cy="{y - r * .36:.2f}" r="{r * .42:.2f}" fill="#fff"/>')
    if style == "ring":
        # 펭귄: 흰 눈테 + 조금 아래·안쪽을 보는 동공, 하이라이트 없음
        return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{P["pen_ring"]}" stroke="{LINE}" stroke-width="0.9"/>'
                f'<circle cx="{x - side * r * .16:.2f}" cy="{y + r * .14:.2f}" r="{r * .6:.2f}" fill="{E}"/>')
    # round2 로켓: 정원 + 하이라이트 2개(큰 것 오른쪽 위, 작은 것 왼쪽 아래)
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{E}"/>'
            f'<circle cx="{x + r * .32:.2f}" cy="{y - r * .36:.2f}" r="{r * .34:.2f}" fill="#fff"/>'
            f'<circle cx="{x - r * .38:.2f}" cy="{y + r * .36:.2f}" r="{r * .15:.2f}" fill="#fff" opacity=".9"/>')


def eye_closed(style, x, y, r, sz):
    w = 1.9 if sz == 108 else 1.5
    E = P["eye"]
    if style == "ring":
        # 펭귄: 눈테는 남기고 가운데 눈꺼풀 선
        return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{P["pen_ring"]}" stroke="{LINE}" stroke-width="0.9"/>'
                f'<path d="M{x - r * .62:.2f} {y + .2:.2f} Q{x:.2f} {y + r * .55:.2f} {x + r * .62:.2f} {y + .2:.2f}" fill="none" stroke="{E}" stroke-width="{w * .85:.2f}" stroke-linecap="round"/>')
    k = 1.0 if style == "droop" else 0.8
    return (f'<path d="M{x - r * .95 * k:.2f} {y - .2:.2f} Q{x:.2f} {y + r * .95 * k:.2f} {x + r * .95 * k:.2f} {y - .2:.2f}" fill="none" '
            f'stroke="{E}" stroke-width="{w}" stroke-linecap="round"/>')


def face(fd, sz, closed=False):
    o = []
    for (x, y, rx, ry) in fd["blush"]:
        o.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{P["blush"]}" opacity=".95"/>')
    for k, (x, y, r) in enumerate(fd["eyes"]):
        side = -1 if k == 0 else 1
        o.append(eye_closed(fd["eye_style"], x, y, r, sz) if closed else eye_open(fd["eye_style"], x, y, r, side))
    if "nose" in fd:
        x, y, rx, ry = fd["nose"]
        o.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{P["nose"]}"/>')
    if "beak" in fd:
        o.append(f'<path d="{fd["beak"]}" fill="{P["beak"]}" stroke="{LINE}" stroke-width="1.1" stroke-linejoin="round"/>')
    if "mouth" in fd:
        o.append(f'<path d="{fd["mouth"]}" fill="none" stroke="{P["eye"]}" stroke-width="{1.15 if sz == 108 else 0.95}" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>')
    return "\n".join(o)


def gloss(hl, sz, gt):
    """광택: 캐릭터마다 모양이 다르다."""
    w = 2.2 if sz == 108 else 1.8
    if hl[0] == "arc":
        return f'<path d="{hl[1]}" fill="none" stroke="#fff" stroke-width="{w}" stroke-linecap="round" opacity=".85"{gt}/>'
    if hl[0] == "spot":
        _, x, y, rx, ry, a = hl
        return f'<g{gt}><ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="#fff" opacity=".55" transform="rotate({a} {x} {y})"/></g>'
    _, d, (dx, dy) = hl
    return (f'<g{gt}><path d="{d}" fill="none" stroke="#fff" stroke-width="{w}" stroke-linecap="round" opacity=".9"/>'
            f'<circle cx="{dx}" cy="{dy}" r="{w * .55:.2f}" fill="#fff" opacity=".9"/></g>')


# ---------- 한 장 그리기 ----------
def char_svg(name, sz, pose):
    """pose: G(전체 변환), t{그룹 또는 부위 id: 변환}, shape{부위 id: 바꾼 모양}, closed(눈 감음), angle(쳇바퀴), K(선 굵기 보정 배율)"""
    parts, fd = CHARS[name]
    t = pose.get("t", {})
    shp = pose.get("shape", {})
    K = pose.get("K", 1.0)

    def tf(pid, grp):
        return join(t.get(grp, ""), t.get(pid, ""))

    body = []
    if name == "hamster":
        body.append(wheel(sz, pose.get("angle", -30)))
    body.append(f'<g id="{name}" transform="{pose.get("G", "")}">' if pose.get("G") else f'<g id="{name}">')
    ow = (2.6 if sz == 108 else 2.0) / K     # 바깥 윤곽 반폭
    iw = (1.5 if sz == 108 else 1.1) / K     # 안쪽 선
    items = [(pid, shp.get(pid, s), col, role, grp) for pid, s, col, role, grp in parts]
    items = [it for it in items if not is_empty(it[1])]
    sil = [(pid, s, grp) for pid, s, _, role, grp in items if "sil" in role]
    body.append('<g id="border">' + "".join(shape_el(s, f'fill="{BORDER}" stroke="{BORDER}" stroke-width="{2 * ow + 3:.2f}" stroke-linejoin="round"', tf(pid, g)) for pid, s, g in sil) + "</g>")
    body.append('<g id="outline">' + "".join(shape_el(s, f'fill="{LINE}" stroke="{LINE}" stroke-width="{2 * ow:.2f}" stroke-linejoin="round"', tf(pid, g)) for pid, s, g in sil) + "</g>")
    for pid, s, col, role, grp in items:
        st = f' stroke="{LINE}" stroke-width="{iw:.2f}" stroke-linejoin="round"' if "line" in role else ""
        body.append(f'<g id="{pid}">' + shape_el(s, f'fill="{P[col]}"{st}', tf(pid, grp)) + "</g>")
    g = t.get(fd["grp"], "")
    gt = f' transform="{g}"' if g else ""
    body.append(gloss(fd["hl"], sz, gt))
    body.append(f'<g id="face"{gt}>{face(fd, sz, pose.get("closed", False))}</g>')
    body.append("</g>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" width="{sz}" height="{sz}">\n'
            + "\n".join(body) + "\n</svg>\n")


# ---------- 포즈: 햄스터 ----------
# 한 발의 보폭 8단계 (앞뒤 dx, 위아래 dy, 발 기울기) — 뿌리(엉덩이·어깨) 바로 아래가 0
#  0 접지(앞으로 뻗어 닿음) 1 체중 실림 2 몸 밑을 지나 뒤로 3 박차기(발끝으로)
#  4 들어 올림 5 몸 밑으로 접어 넘김 6 앞으로 휘두름 7 뻗어 내리기 직전
STRIDE = [(4.4, 0.0, -10), (1.8, 0.0, 0), (-1.0, 0.0, 6), (-4.0, -0.5, 26),
          (-3.8, -2.9, 18), (-0.8, -3.9, 0), (2.4, -3.4, -12), (4.6, -1.5, -16)]
RAISE = -3.0   # 달리기·정지: 몸·머리를 3 더 띄워 다리가 보이게. 쉼은 내려서 엎드림


def ham_leg(hip, phase, amp, body_dy, scale=1.0):
    """뿌리에서 발까지 다리 막대 + 발. phase 는 STRIDE 번호(0~7)."""
    fx, fy, fa = STRIDE[phase % 8]
    hx, hy = hip[0], hip[1] + body_dy
    x, y = hip[0] + fx * amp * scale, HAM_GROUND + fy * scale
    leg = capsule(hx, hy, x, y - 1.2, 2.5)
    foot = ("path", ellipse_path(x + 0.8, y, 3.5, 2.3, fa))
    return leg, foot


def ellipse_path(cx, cy, rx, ry, a):
    """기울인 타원(발): rotate 대신 경로로 만들어 그룹 변환과 섞이지 않게 한다."""
    pts = []
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    for k in range(16):
        th = 2 * math.pi * k / 16
        ex, ey = rx * math.cos(th), ry * math.sin(th)
        pts.append((cx + ex * ca - ey * sa, cy + ex * sa + ey * ca))
    return "M" + " L".join(f"{px:.2f} {py:.2f}" for px, py in pts) + " Z"


def ham_legs(ph_h, ph_f, body_dy, amp_h=1.35, amp_f=1.1, scale=1.0, head_dy=0.0):
    """뒷다리 두 개(ph_h=(가까운, 먼)), 앞다리 두 개. 반환: shape dict."""
    s = {}
    for k, ph in enumerate(ph_h):
        leg, foot = ham_leg(HAM_HIP_H, ph, amp_h, body_dy, scale)
        s[f"leg_h{k + 1}"], s[f"foot_h{k + 1}"] = leg, foot
    for k, ph in enumerate(ph_f):
        leg, foot = ham_leg(HAM_HIP_F, ph, amp_f, body_dy + head_dy, scale)
        s[f"leg_f{k + 1}"], s[f"foot_f{k + 1}"] = leg, foot
    return s


def hamster_poses():
    poses = {}
    # 몸: 1 접지(보통) → 2 내려감(가장 낮음, 살짝 눌림) → 3 지나감(보통) → 4 올라감(가장 높음, 살짝 늘어남)
    dy = [0.0, 0.8, 0.0, -0.8]
    sxy = [(1.01, 0.99), (1.025, 0.975), (1.0, 1.0), (0.985, 1.015)]
    tilt = [0.0, 0.8, 0.0, -0.8]                   # 내려갈 때 코가 조금 숙고, 올라갈 때 조금 듦
    angle = [-30, 0, 30, 60]                       # 쳇바퀴: 시계 방향 30도씩, 다음 장(90)은 -30 과 같은 모양
    for i in range(4):
        hd = lag(dy, i, 0.7)                       # 머리는 몸보다 한 장 늦게
        ea = lag(dy, i, 5.0)                       # 귀는 더 늦고 크게(바깥으로 젖힘)
        ta = 12 * math.sin(math.radians(90 * (i - 1)))   # 꼬리는 몸보다 한 장 늦은 박자로 위아래
        sx, sy = sxy[i]
        legs = ham_legs((i, i + 4), (i + 2, i + 6), dy[i] + RAISE, head_dy=hd)   # 앞다리는 뒷다리보다 2단계 앞선 박자
        poses[f"run_{i + 1}"] = dict(
            angle=angle[i], K=1.2,
            G=squash(60, 89, 1, 1, dy=1.9, r=tilt[i], k=1.2),
            shape=legs,
            t=dict(body=join(mv(0, dy[i] + RAISE), squash(46, 84, sx, sy)), head=join(mv(0, dy[i] + hd + RAISE), squash(63, 81, sx, sy)),
                   tail=join(mv(0, dy[i] + RAISE), rot(ta, 26, 70)),
                   ear_l=rot(-ea, 50, 51), ear_l_in=rot(-ea, 50, 51),
                   ear_r=rot(ea, 73.5, 49), ear_r_in=rot(ea, 73.5, 49)))
    # 정지: 네 발로 서서 출발 준비(바퀴 멈춤, 눈 뜸)
    poses["still"] = dict(angle=-30, K=1.2, G=squash(60, 89, dy=1.9, k=1.2),
                          shape=ham_still_legs(RAISE),
                          t=dict(body=mv(0, RAISE), head=mv(0, RAISE), tail=mv(0, RAISE)))
    # 쉼: 배를 바닥에 붙이고 엎드려 눈 감고 숨쉬기(들숨 → 날숨). 다리는 접어서 발끝만 보임
    down = 3.2
    for k, (sx, sy, hdy, ear) in enumerate(((1.0, 1.0, 0.0, 0), (1.035, 0.955, 0.9, 6))):
        poses[f"rest_{k + 1}"] = dict(
            angle=-30, K=1.2, closed=True, G=squash(60, 89, dy=1.9, r=-2, k=1.2),
            shape=ham_rest_legs(),
            t=dict(body=join(mv(0, down), squash(46, 87, sx, sy)), head=join(mv(0, down + hdy), squash(63, 84, sx, sy)),
                   tail=mv(0, down + 1), ear_l=rot(-ear, 50, 51), ear_l_in=rot(-ear, 50, 51),
                   ear_r=rot(ear, 73.5, 49), ear_r_in=rot(ear, 73.5, 49)))
    return poses


def ham_still_legs(body_dy):
    s = {}
    for k, (hip, dx) in enumerate(((HAM_HIP_H, 1.8), (HAM_HIP_H, -2.2))):
        x, y = hip[0] + dx, HAM_GROUND
        s[f"leg_h{k + 1}"] = capsule(hip[0], hip[1] + body_dy, x, y - 1.2, 2.5)
        s[f"foot_h{k + 1}"] = ("path", ellipse_path(x + 0.8, y, 3.5, 2.3, 0))
    for k, (hip, dx) in enumerate(((HAM_HIP_F, 1.6), (HAM_HIP_F, -2.0))):
        x, y = hip[0] + dx, HAM_GROUND
        s[f"leg_f{k + 1}"] = capsule(hip[0], hip[1] + body_dy, x, y - 1.2, 2.5)
        s[f"foot_f{k + 1}"] = ("path", ellipse_path(x + 0.8, y, 3.5, 2.3, 0))
    return s


def ham_rest_legs():
    # 엎드리면 다리는 몸 밑에 접혀 발만 살짝 나온다(다리 막대 없음)
    s = {}
    for k, (x, a) in enumerate(((41.5, 0), (35.5, 0))):
        s[f"foot_h{k + 1}"] = ("path", ellipse_path(x, HAM_GROUND + 0.4, 4.4, 2.6, a))
    for k, (x, a) in enumerate(((67.5, 0), (61.0, 0))):
        s[f"foot_f{k + 1}"] = ("path", ellipse_path(x, HAM_GROUND + 0.4, 4.0, 2.5, a))
    return s


# ---------- 포즈: 펭귄 ----------
PEN_K = 0.93   # 전체 배율: 머리깃(위)·발(아래)까지 축소 칸에서 보이는 띠 안에 들어오게
PEN_G = f"translate(54 56) scale({PEN_K}) translate(-54 -56)"


def penguin_poses():
    poses = {}
    # 정면이라 왼발·오른발이 구별되므로 4장에 두 걸음:
    #  1 왼발 접지·내려감(왼쪽으로 기움, 오른발 뒤로 차올림) → 2 지나감·올라감(오른발이 앞으로 넘어옴)
    #  3 오른발 접지·내려감 → 4 지나감·올라감(왼발이 넘어옴)
    r = [-5.0, 1.5, 5.0, -1.5]                    # 1라운드 ±8 → ±5.5: 몸 흔들림은 줄이고 발·팔로 달림을 냄
    dx = [-1.2, 0.3, 1.2, -0.3]
    dy = [0.5, -0.7, 0.5, -0.7]                    # 1라운드 -1.8 → 위아래 1.2 안쪽
    sxy = [(1.025, 0.975), (0.985, 1.015), (1.025, 0.975), (0.985, 1.015)]
    # 지느러미: 달리며 팔 흔들기. 디딘 발 반대쪽 팔이 앞(위)으로, 한 장 늦게 따라옴
    flip = [(2, 13), (8, 9), (13, 2), (9, 8)]
    # 발: (dx, dy, 기울기). 디딘 발은 땅에, 든 발은 뒤로 차올렸다(발바닥 보임) 앞으로 넘어옴
    lift_up = (3.0, -3.6, 20)
    lift_pass = (1.2, -1.8, 6)
    for i in range(4):
        tail = -r[i] * 0.8 + lag(r, i, 1.4)        # 목도리 꼬리: 중력 쪽으로 + 한 장 늦게
        tuft = lag(r, i, 1.6)                      # 머리깃: 몸이 기운 반대로 한 장 늦게 휘청
        fl, fr = flip[i]
        tt = dict(body=join(mv(dx[i], 0), squash(54, 89, sxy[i][0], sxy[i][1], dy=dy[i], r=r[i])),
                  flip_l=rot(fl, 31, 56), flip_r=rot(-fr, 77, 56), scarf_tail=rot(tail, 66, 64), tuft=rot(tuft, 55, 25))
        if i == 0:
            tt["foot_r"] = join(mv(lift_up[0], lift_up[1]), rot(lift_up[2], 65, 89.5))
        elif i == 1:
            tt["foot_r"] = join(mv(lift_pass[0], lift_pass[1]), rot(lift_pass[2], 65, 89.5))
        elif i == 2:
            tt["foot_l"] = join(mv(-lift_up[0], lift_up[1]), rot(-lift_up[2], 44, 89.5))
        else:
            tt["foot_l"] = join(mv(-lift_pass[0], lift_pass[1]), rot(-lift_pass[2], 44, 89.5))
        poses[f"run_{i + 1}"] = dict(t=tt, G=PEN_G, K=PEN_K)
    poses["still"] = dict(G=PEN_G, K=PEN_K, t=dict(flip_l=rot(6, 31, 56), flip_r=rot(-6, 77, 56)))
    poses["rest_1"] = dict(closed=True, G=PEN_G, K=PEN_K, t=dict(flip_l=rot(-3, 31, 56), flip_r=rot(3, 77, 56)))
    poses["rest_2"] = dict(closed=True, G=PEN_G, K=PEN_K, t=dict(body=squash(54, 89, 1.03, 0.965), flip_l=rot(-6, 31, 56), flip_r=rot(6, 77, 56),
                                                                 scarf_tail=rot(-3, 66, 64), tuft=rot(-6, 55, 25)))
    return poses


# ---------- 포즈: 로켓 ----------
def rocket_poses():
    poses = {}
    # 몸 위아래는 1라운드 2.6 → 1.4 로 줄이고, 불꽃 두 겹과 날개 떨림이 서로 다른 박자로 움직인다.
    dy = [0.0, -0.8, -1.4, -0.6]
    tilt = [0.0, -1.0, -1.6, -0.6]
    # 바깥 불꽃 (길이, 끝 흔들림, 뿌리 반폭, 갈래): 4단계
    fo = [(19, 0.0, 8.0, 0), (22, -2.0, 8.6, 3.0), (15, 2.0, 7.4, 0), (20.5, 1.2, 8.2, 2.4)]
    # 안쪽 불꽃은 바깥보다 한 장 늦게(위상차), 끝은 반대로 흔들림
    fi = [(13.5, 0.6, 5.2), (12, 0.0, 5.0), (15, 1.2, 5.4), (9.5, -1.0, 4.6)]
    for i in range(4):
        L, ty, h, fk = fo[i]
        Li, tyi, hi = fi[i]
        fin = 1.6 * math.sin(math.radians(90 * (i - 1)))   # 날개: 몸보다 한 장 늦게 떨림
        poses[f"run_{i + 1}"] = dict(
            G=join(mv(0, dy[i]), rot(tilt[i], 62, 54)),
            t=dict(fin_t=rot(-fin, 41, 40), fin_b=rot(fin, 41, 68)),
            shape=dict(flame_o=("path", flame_path(L, ty, h, fork=fk)), flame_i=("path", flame_path(Li, tyi, hi))))
    poses["still"] = dict(G=join(mv(0, -0.5), rot(-4, 62, 54)),
                          shape=dict(flame_o=("path", flame_path(17, 0.5, 7.8)), flame_i=("path", flame_path(10.5, 0, 4.8))))
    poses["rest_1"] = dict(closed=True, shape=dict(flame_o=("path", flame_path(10, 0, 6.2)), flame_i=("path", flame_path(5.5, 0, 3.6))))
    poses["rest_2"] = dict(closed=True, G=mv(0, 0.8),
                           shape=dict(flame_o=("path", flame_path(12.5, 0.6, 6.6)), flame_i=("path", flame_path(7, -0.4, 3.9))))
    return poses


POSES = {"hamster": hamster_poses, "penguin": penguin_poses, "rocket": rocket_poses}
FRAMES = ["run_1", "run_2", "run_3", "run_4", "rest_1", "rest_2", "still"]


def main():
    os.makedirs(SVG_DIR, exist_ok=True)
    jobs = []
    for name, fn in POSES.items():
        poses = fn()
        for fr in FRAMES:
            for sz, suf in ((108, ""), (240, "_L")):
                svg = os.path.join(SVG_DIR, f"{name}_{fr}{suf}.svg")
                open(svg, "w").write(char_svg(name, sz, poses[fr]))
                jobs.append((svg, sz, os.path.join(OUT, f"{name}_{fr}{suf}@3x.png")))
    cmds = "".join(f"file-open:{s}; export-width:{z}; export-height:{z}; export-background-opacity:0; export-filename:{o}; export-do; file-close\n"
                   for s, z, o in jobs)
    subprocess.run(["inkscape", "--shell"], input=cmds, text=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"{len(jobs)} 장 내보냄")


if __name__ == "__main__":
    main()
