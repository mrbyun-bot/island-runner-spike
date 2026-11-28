"""4라운드 공통 도구: 108 격자 SVG 조각, 떡(mochi) 몸 모양, 렌더, 대비 계산.
모든 좌표는 108x108 캔버스(아일랜드 칸 36pt @3x) 기준. 핵심 띠 y15~93, 바닥선 y90.
"""
import math, os, subprocess, tempfile
from PIL import Image

INK = "#2A211D"      # 눈·코 공통 먹색(순수 검정 대신 아주 짙은 밤색: 검정 배경에서 테가 없어도 몸 위에서만 보임)
GROUND = 90


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def mochi_pts(cx, cy, w, h, n_top=2.3, n_bot=3.4, sx=1.0, sy=1.0, tilt=0.0, steps=120, pear=0.0):
    """떡 모양: 위는 둥글고(n_top) 아래는 납작(n_bot). pear>0 이면 아래가 넓은 배 모양.
    sx, sy 는 스쿼시·스트레치(부피 보존은 호출 쪽에서 sx*sy≈1 로 맞춤). 바닥은 cy+h/2 에 고정."""
    pts = []
    ca, sa = math.cos(tilt), math.sin(tilt)
    for i in range(steps):
        t = 2 * math.pi * i / steps
        c, s = math.cos(t), math.sin(t)
        n = n_bot if s > 0 else n_top
        x = math.copysign(abs(c) ** (2 / n), c) * w / 2
        y = math.copysign(abs(s) ** (2 / n), s) * h / 2   # 중심 기준, 아래가 +
        x *= (1 + pear * (y / (h / 2))) * sx               # 배 모양 + 가로 스쿼시
        yb = (y - h / 2) * sy                               # 바닥(0) 기준, 위가 -
        x, yb = x * ca - yb * sa, x * sa + yb * ca          # 바닥 중심 기준 기울기
        pts.append((cx + x, cy + h / 2 + yb))
    return pts


def poly_path(pts, close=True):
    """점 목록을 부드러운 곡선 경로로(Catmull-Rom → 베지어)."""
    n = len(pts)
    d = [f"M{f(pts[0][0])},{f(pts[0][1])}"]
    rng = range(n) if close else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n]; p1 = pts[i]; p2 = pts[(i + 1) % n]; p3 = pts[(i + 2) % n]
        if not close:
            p0 = pts[max(i - 1, 0)]; p3 = pts[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}")
    if close:
        d.append("Z")
    return "".join(d)


def mochi(cx, cy, w, h, fill, **kw):
    sid = kw.pop("id", None)
    pts = mochi_pts(cx, cy, w, h, steps=48, **kw)
    a = f' id="{sid}"' if sid else ""
    return f'<path{a} d="{poly_path(pts)}" fill="{fill}"/>'


def ell(cx, cy, rx, ry, fill, rot=0, op=1.0):
    t = f' transform="rotate({f(rot)} {f(cx)} {f(cy)})"' if rot else ""
    o = f' opacity="{op}"' if op != 1 else ""
    return f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" fill="{fill}"{t}{o}/>'


def path(d, fill="none", stroke=None, sw=0, cap="round", op=1.0):
    s = f' stroke="{stroke}" stroke-width="{f(sw)}" stroke-linecap="{cap}" stroke-linejoin="round"' if stroke else ""
    o = f' opacity="{op}"' if op != 1 else ""
    return f'<path d="{d}" fill="{fill}"{s}{o}/>'


def capsule(x1, y1, x2, y2, r1, r2, fill):
    """굵기가 r1 → r2 로 줄어드는 관(다리·귀·꼬리)."""
    ang = math.atan2(y2 - y1, x2 - x1)
    nx, ny = -math.sin(ang), math.cos(ang)
    pts = []
    for k in range(9):
        a = ang + math.pi / 2 + math.pi * k / 8
        pts.append((x1 + r1 * math.cos(a), y1 + r1 * math.sin(a)))
    for k in range(9):
        a = ang - math.pi / 2 + math.pi * k / 8
        pts.append((x2 + r2 * math.cos(a), y2 + r2 * math.sin(a)))
    d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + "Z"
    return f'<path d="{d}" fill="{fill}"/>'


def svg(inner, defs=""):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="108" height="108" viewBox="0 0 108 108">'
            + (f"<defs>{defs}</defs>" if defs else "") + inner + "</svg>")


def render(svg_text, out_png, width):
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as t:
        t.write(svg_text); name = t.name
    subprocess.run(["inkscape", "--export-type=png", f"--export-width={width}",
                    f"--export-filename={out_png}", name], check=True, capture_output=True)
    os.unlink(name)


def rel_lum(hexcol):
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a, b):
    la, lb = sorted([rel_lum(a), rel_lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)
