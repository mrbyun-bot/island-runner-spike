"""상위 후보 옆모습(오른쪽을 봄)과 달리기·쉼·정지 포즈.

로컬 좌표: 몸 바닥 가운데가 (0,0), 위가 음수. 포즈는 몸 그룹에 transform(이동·기울기·스쿼시)로 주고,
다리는 같은 변환으로 엉덩이 위치를 계산해 세계 좌표에서 그린다(발이 바닥선에 닿는지 계산 가능).
"""
import math
from kit import *
from family import eyes

LEG_FAR_DARK = 0.72   # 먼 쪽 다리 명도 배수


def darker(hexcol, k):
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % (int(r * k), int(g * k), int(b * k))


class Pose:
    def __init__(self, bob=0, sx=1, sy=1, tilt=0, legs=(0, 0, 0, 0), lift=(0, 0, 0, 0), wing=0, tail=0,
                 expr="open", sit=False, ear=0):
        self.__dict__.update(locals()); del self.__dict__["self"]


def xf(p, pose, S, ox, oy):
    """로컬 점 → 세계 점. 순서: 스쿼시 → 기울기(바닥 가운데 기준) → 배율 S → 이동."""
    x, y = p[0] * pose.sx, p[1] * pose.sy
    a = math.radians(pose.tilt)
    x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    return ox + x * S, oy + (y + pose.bob) * S


def group(inner, pose, S, ox, oy):
    return (f'<g transform="translate({f(ox)} {f(oy + pose.bob * S)}) scale({S}) rotate({f(pose.tilt)}) '
            f'scale({f(pose.sx)} {f(pose.sy)})">{inner}</g>')


def legs_svg(hips, pose, S, ox, oy, L, r1, r2, col, foot=None, which=(0, 1, 2, 3)):
    """hips: 로컬 엉덩이 4개(가까운 앞, 가까운 뒤, 먼 앞, 먼 뒤). 각도는 수직에서 앞(+)으로."""
    out = []
    for i in which:
        hx, hy = xf(hips[i], pose, S, ox, oy)
        a = math.radians(pose.legs[i])
        ln = (L - pose.lift[i]) * S
        fx, fy = hx + math.sin(a) * ln, hy + math.cos(a) * ln
        c = col if i < 2 else darker(col, LEG_FAR_DARK)
        out.append(capsule(hx, hy, fx, fy, r1 * S, r2 * S, c))
        if foot:
            fc = foot if i < 2 else darker(foot, LEG_FAR_DARK)
            out.append(ell(fx + 2.2 * S, fy, 3.6 * S, 1.8 * S, fc, rot=pose.legs[i] * 0.3))
    return "".join(out)


# ---------------------------------------------------------------- 고슴도치
def hedgehog_body(pose):
    spine, tipc, face, ear, nose, cheek = "#7E6A5D", "#A8968A", "#F1DEC6", "#D9B99B", "#3A2C27", "#EBA592"
    s = mochi(2, -23, 64, 44, face, n_top=2.1, n_bot=2.8)
    s += ell(28, -17, 12, 9.5, face, rot=-8)                       # 주둥이
    # 가시: 바깥 톱니 호(이마→등→엉덩이) + 안쪽 경계 곡선
    pts = []
    n = 13
    for i in range(n * 2 + 1):
        t = math.radians(76 + (224 - 76) * i / (n * 2))           # 수학 각도(위가 +)
        rad = (31 if i % 2 == 0 else 25.5) + pose.ear * (i % 2 == 0)
        pts.append((-2 + rad * 1.18 * math.cos(t), -24 - rad * math.sin(t)))
    inner = [(-26, -8), (-10, -11), (2, -19), (9, -33), (8, -46)]
    s += f'<path d="{poly_path(pts + inner)}" fill="{spine}"/>'
    for i in range(0, n * 2 + 1, 2):
        t = math.radians(76 + (224 - 76) * i / (n * 2))
        if 70 < math.degrees(t) < 230:
            s += ell(-2 + 27.5 * 1.18 * math.cos(t), -24 - 27.5 * math.sin(t), 1.5, 1.5, tipc)
    s += ell(10, -40, 5, 4.4, ear)
    s += eyes(19, -27, 0, pose.expr, rx=3.0, ry=3.6).split("/>")[0] + "/>" if pose.expr else ""
    s += ell(25, -18.5, 3.6, 2.2, cheek, op=0.55)
    s += ell(39.5, -19, 3.2, 2.6, nose)
    return s


HEDGEHOG = dict(body=hedgehog_body, hips=[(18, -5), (-14, -5), (13, -5), (-19, -5)],
                L=8, r1=3.8, r2=3.4, leg="#8A7466", foot=None)


# ---------------------------------------------------------------- 아기 청둥오리
def duck_body(pose):
    body, cap, bill, wing = "#F2D27E", "#8C6B4C", "#D98F6E", "#DDB868"
    clip = f'<clipPath id="db">{mochi(0, -26, 56, 50, "#000", n_top=2.1, n_bot=2.6)}</clipPath>'
    # 꼬리 끝(뒤 위로 살짝)
    s = f'<defs>{clip}</defs>'
    s += path(f"M-22,-30 Q-34,{f(-38 - pose.tail)} -31,{f(-44 - pose.tail)} Q-24,-38 -16,-36Z", fill=body)
    s += mochi(0, -26, 56, 50, body, n_top=2.1, n_bot=2.6)
    s += f'<g clip-path="url(#db)">{ell(8, -51, 26, 13, cap)}'
    s += "</g>"
    s += eyes(13, -31, 0, pose.expr).split("/>")[0] + "/>"
    # 부리: 앞으로 납작하게
    s += path("M24,-28 Q34,-29 37,-24 Q34,-19.5 24,-20.5Z", fill=bill)
    # 날개: 어깨(0,-28) 기준 회전
    s += f'<g transform="rotate({f(-pose.wing)} 0 -28)">{ell(-6, -20, 11, 7.5, wing, rot=-4)}</g>'
    return s


DUCK = dict(body=duck_body, hips=[(7, -3), (-6, -3), (4, -3), (-9, -3)],
            L=9, r1=2.2, r2=1.8, leg="#E39B5E", foot="#E39B5E")


# ---------------------------------------------------------------- 뱁새
def tit_body(pose):
    body, cap, wing, tail, beak, cheek = "#E2B597", "#C47F5E", "#A9785E", "#8E6450", "#4C3A30", "#EE9C8A"
    a = math.radians(16 + pose.tail)
    tx, ty = -20 - math.cos(a) * 25, -26 - math.sin(a) * 25
    s = capsule(-16, -26, tx, ty, 5.4, 2.6, tail)
    s += f'<defs><clipPath id="tb">{mochi(0, -25, 54, 48, "#000", n_top=2.0, n_bot=2.2)}</clipPath></defs>'
    s += mochi(0, -25, 54, 48, body, n_top=2.0, n_bot=2.2)
    s += f'<g clip-path="url(#tb)">{ell(6, -47, 28, 13, cap)}</g>'
    s += f'<g transform="rotate({f(-pose.wing)} -2 -32)">{ell(-6, -24, 13, 9, wing, rot=-2)}</g>'
    s += eyes(14, -29, 0, pose.expr, rx=2.7, ry=3.2).split("/>")[0] + "/>"
    s += ell(17, -21, 3.6, 2.2, cheek, op=0.55)
    s += path("M25,-28.5 L31,-26 L25,-23.5Z", fill=beak)
    return s


TIT = dict(body=tit_body, hips=[(5, -2), (-1, -2), (3, -2), (-3, -2)],
           L=7, r1=1.4, r2=1.2, leg="#6E5040", foot="#6E5040")

CHARS = {"hedgehog": HEDGEHOG, "duckling": DUCK, "tit": TIT}

# ---------------------------------------------------------------- 포즈 설계
# 고슴도치: 짧은 다리 "통통통" 종종걸음. 2박자(1·3 디딤 눌림, 2·4 뜀 늘임), 다리는 대각선 짝(트롯).
#  3번 장은 1번과 다리 짝이 반대라 겹치지 않음(3라운드 3번 장 뭉침 재발 방지).
POSES = {
    "hedgehog": {
        "run_1": Pose(bob=0, sx=1.05, sy=0.95, tilt=2, legs=(28, -26, -22, 24), ear=0),
        "run_2": Pose(bob=-5, sx=0.97, sy=1.04, tilt=-3, legs=(8, -8, -6, 6), lift=(3, 3, 3, 3), ear=1),
        "run_3": Pose(bob=0, sx=1.05, sy=0.95, tilt=2, legs=(-24, 26, 26, -22), ear=0),
        "run_4": Pose(bob=-5, sx=0.97, sy=1.04, tilt=-3, legs=(-6, 6, 8, -8), lift=(3, 3, 3, 3), ear=1),
        "rest_1": Pose(bob=6, sx=1.03, sy=0.97, expr="sleep", sit=True),
        "rest_2": Pose(bob=6, sx=1.0, sy=1.0, expr="sleep", sit=True, ear=0.8),
        "still": Pose(bob=0, expr="open", legs=(4, -4, 2, -2)),
    },
    # 오리: 뒤뚱 달리기. 몸을 앞뒤로 흔들고(기울기 ±5) 날개를 한 장 늦게 퍼덕임(오버랩).
    "duckling": {
        "run_1": Pose(bob=0, sx=1.05, sy=0.95, tilt=6, legs=(32, -30, -26, 28), wing=4, tail=0),
        "run_2": Pose(bob=-5, sx=0.97, sy=1.04, tilt=-2, legs=(6, -10, -4, 4), lift=(2, 4, 2, 2), wing=16, tail=3),
        "run_3": Pose(bob=0, sx=1.05, sy=0.95, tilt=6, legs=(-28, 32, 30, -26), wing=6, tail=0),
        "run_4": Pose(bob=-5, sx=0.97, sy=1.04, tilt=-2, legs=(-8, 6, 6, -4), lift=(4, 2, 2, 2), wing=18, tail=3),
        "rest_1": Pose(bob=8, sx=1.04, sy=0.96, expr="sleep", sit=True, wing=0),
        "rest_2": Pose(bob=8, sx=1.0, sy=1.01, expr="sleep", sit=True, wing=4, tail=2),
        "still": Pose(bob=0, expr="open", legs=(4, -4, 2, -2), wing=4),
    },
    # 뱁새: 두 발 모아 깡충(새의 hop). 1 웅크림 → 2 박차기(늘임) → 3 정점(다리 접고 꼬리 내림) → 4 착지(눌림, 꼬리 위로 늦게 튐).
    "tit": {
        "run_1": Pose(bob=0, sx=1.07, sy=0.93, tilt=6, legs=(-20, -20, -22, -22), wing=0, tail=6),
        "run_2": Pose(bob=-6, sx=0.94, sy=1.07, tilt=-8, legs=(-34, -34, -36, -36), wing=14, tail=-4),
        "run_3": Pose(bob=-11, sx=1.0, sy=1.0, tilt=-2, legs=(30, 30, 28, 28), lift=(3, 3, 3, 3), wing=6, tail=-10),
        "run_4": Pose(bob=-3, sx=1.04, sy=0.96, tilt=4, legs=(18, 18, 16, 16), wing=-6, tail=12),
        "rest_1": Pose(bob=6, sx=1.04, sy=0.96, expr="sleep", sit=True, tail=-2),
        "rest_2": Pose(bob=6, sx=1.0, sy=1.01, expr="sleep", sit=True, tail=0, wing=3),
        "still": Pose(bob=0, expr="open", legs=(0, 0, 2, 2)),
    },
}

FIT = {}  # 종 -> (S, ox, oy)
FRAMES = ["run_1", "run_2", "run_3", "run_4", "rest_1", "rest_2", "still"]


def fit_char(char, box=(3, 17, 105, 91)):
    """7장 전체의 바깥 상자를 재서 배율 하나·위치 하나를 정함(장마다 크기가 튀지 않게)."""
    import tempfile, os
    from PIL import Image
    S0, ox0, oy0 = 1.0, 54.0, 70.0
    xs0, ys0, xs1, ys1 = [], [], [], []
    with tempfile.TemporaryDirectory() as t:
        for fr in FRAMES:
            png = os.path.join(t, "a.png")
            render(side_svg(char, fr, (S0, ox0, oy0)), png, 432)
            b = Image.open(png).getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
            xs0.append(b[0] / 4); ys0.append(b[1] / 4); xs1.append(b[2] / 4); ys1.append(b[3] / 4)
    x0, y0, x1, y1 = min(xs0), min(ys0), max(xs1), max(ys1)
    S = min((box[2] - box[0]) / (x1 - x0), (box[3] - box[1]) / (y1 - y0))
    ox = (box[0] + box[2]) / 2 - S * ((x0 + x1) / 2 - ox0)
    oy = box[3] - S * (y1 - oy0)
    FIT[char] = (round(S, 4), round(ox, 2), round(oy, 2))
    return FIT[char]


def side_svg(char, frame, fit=None):
    c = CHARS[char]; p = POSES[char][frame]
    S, ox, oy = fit or FIT.get(char, (1.2, 52, 82))
    s = ""
    if not p.sit:
        s += legs_svg(c["hips"], p, S, ox, oy, c["L"], c["r1"], c["r2"], c["leg"], c["foot"], which=(2, 3))
        s += legs_svg(c["hips"], p, S, ox, oy, c["L"], c["r1"], c["r2"], c["leg"], c["foot"], which=(0, 1))
    s += group(c["body"](p), p, S, ox, oy)
    return svg(s)
