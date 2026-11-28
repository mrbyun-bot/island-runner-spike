"""7라운드 그림 도구: 한 가지 색 실루엣을 부드럽게 이어 붙이고, 눈만 따로 그린다.

좌표는 108×108 단위(=36pt@3x). 실제로는 K배(2160px)에 그린 뒤
가우시안 흐림 → 반 넘으면 채움(threshold) 으로 이음새를 곡선으로 녹이고,
상자 평균으로 줄여 240·108·36px 를 만든다.
"""
import math
from PIL import Image, ImageDraw, ImageFilter

K = 20                     # 1 단위 = 20px
N = 108 * K                # 2160
EYE = (29, 24, 33)         # 눈 먹색 #1D1821
HL = (255, 255, 255)       # 눈 하이라이트


# ------------------------------------------------------------ 도형(다각형 점 목록)
def ell(cx, cy, rx, ry, rot=0.0, n=72):
    a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


def circ(cx, cy, r):
    return ell(cx, cy, r, r)


def cap(x1, y1, x2, y2, w, n=18):
    """둥근 끝 막대(캡슐)."""
    r = w / 2
    a = math.atan2(y2 - y1, x2 - x1)
    pts = []
    for i in range(n + 1):
        t = a - math.pi / 2 - math.pi * i / n          # 시작점 쪽 반원
        pts.append((x1 + r * math.cos(t), y1 + r * math.sin(t)))
    for i in range(n + 1):
        t = a + math.pi / 2 - math.pi * i / n          # 끝점 쪽 반원
        pts.append((x2 + r * math.cos(t), y2 + r * math.sin(t)))
    return pts


def limb(x, y, length, ang, w):
    """(x,y)에서 아래로 뻗는 다리. ang: 아래 기준 각도, +는 앞(오른쪽)."""
    a = math.radians(ang)
    return cap(x, y, x + length * math.sin(a), y + length * math.cos(a), w)


def bez(segs, n=24):
    """segs: 시작점 p0 와 (c1, c2, p) 묶음 목록 → 닫힌 다각형."""
    p0 = segs[0]; pts = [p0]
    cur = p0
    for (c1, c2, p) in segs[1:]:
        for i in range(1, n + 1):
            t = i / n; u = 1 - t
            x = u**3 * cur[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t**3 * p[0]
            y = u**3 * cur[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t**3 * p[1]
            pts.append((x, y))
        cur = p
    return pts


def chain(points, radii, sub=4):
    """점 사이를 촘촘히 메운 원으로 이어지는 덩어리(꼬리). 울퉁불퉁하지 않게 sub 개씩 보간."""
    out = []
    for k in range(len(points) - 1):
        (x0, y0), (x1, y1) = points[k], points[k + 1]
        r0, r1 = radii[k], radii[k + 1]
        for j in range(sub):
            t = j / sub
            out.append(circ(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r0 + (r1 - r0) * t))
    out.append(circ(*points[-1], radii[-1]))
    return out


def aff(polys, sx=1, sy=1, ox=54, oy=90, rot=0, dx=0, dy=0, rox=None, roy=None):
    """(ox,oy) 기준 늘이기·줄이기 → 회전 → 이동."""
    a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)
    rox = ox if rox is None else rox; roy = oy if roy is None else roy
    out = []
    for poly in polys:
        q = []
        for (x, y) in poly:
            x = ox + (x - ox) * sx; y = oy + (y - oy) * sy
            x, y = rox + (x - rox) * ca - (y - roy) * sa, roy + (x - rox) * sa + (y - roy) * ca
            q.append((x + dx, y + dy))
        out.append(q)
    return out


def apt(p, **kw):
    return aff([[p]], **kw)[0][0]


# ------------------------------------------------------------ 그리기
def _mask(add, cut=()):
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    for poly in add:
        d.polygon([(x * K, y * K) for x, y in poly], fill=255)
    for poly in cut:
        d.polygon([(x * K, y * K) for x, y in poly], fill=0)
    return m


def _smooth(m, sigma):
    if sigma <= 0:
        return m
    return m.filter(ImageFilter.GaussianBlur(sigma * K)).point(lambda v: 255 if v >= 128 else 0)


def _dilate(m, g):
    return m.filter(ImageFilter.GaussianBlur(g * K / 1.9)).point(lambda v: 255 if v >= 8 else 0)


class Part:
    """같은 색 덩어리 하나. smooth: 이음새 녹이는 정도(단위), gap: 먼저 그린 것과 띄울 틈(단위)."""
    def __init__(self, add, cut=(), smooth=1.6, gap=0.0):
        self.add, self.cut, self.smooth, self.gap = add, cut, smooth, gap


def render(color, parts, eyes=(), closed=(), extra_dark=()):
    """parts 를 차례로 합치고(틈 지정 시 깎은 뒤) 눈을 얹어 2160px RGBA 로 돌려준다.
    eyes: (cx, cy, rx, ry, rot) 뜬 눈. closed: (cx, cy, w) 감은 눈(아래로 휜 선)."""
    final = Image.new("L", (N, N), 0)
    for p in parts:
        m = _smooth(_mask(p.add, p.cut), p.smooth)
        if p.gap > 0:
            hole = _dilate(m, p.gap)
            final.paste(0, mask=hole)
        final.paste(255, mask=m)
    rgb = Image.new("RGB", (N, N), color)
    d = ImageDraw.Draw(rgb)
    for (cx, cy, rx, ry, rot) in eyes:
        d.polygon([(x * K, y * K) for x, y in ell(cx, cy, rx, ry, rot)], fill=EYE)
        hr = max(0.9, min(rx, ry) * 0.34)
        hx, hy = cx + min(rx, ry) * 0.32, cy - min(rx, ry) * 0.36
        d.polygon([(x * K, y * K) for x, y in circ(hx, hy, hr)], fill=HL)
    for (cx, cy, w) in closed:
        pts = [(cx + w * math.cos(t), cy + w * 0.55 * math.sin(t))
               for t in [math.pi * i / 16 for i in range(17)]]
        d.line([(x * K, y * K) for x, y in pts], fill=EYE, width=int(2.3 * K), joint="curve")
        for x, y in (pts[0], pts[-1]):
            r = 1.15 * K
            d.ellipse([x * K - r, y * K - r, x * K + r, y * K + r], fill=EYE)
    img = rgb.convert("RGBA")
    img.putalpha(final)
    return img


def shrink(img, color, size):
    """상자 평균으로 정수배 축소. 투명 부분 색을 몸색으로 두어 가장자리가 어두워지지 않게."""
    f = N // size
    a = img.getchannel("A")
    rgb = img.convert("RGB")
    bg = Image.new("RGB", (N, N), color)
    bg.paste(rgb, mask=a.point(lambda v: 255 if v > 0 else 0))
    out = bg.reduce(f).convert("RGBA")
    out.putalpha(a.reduce(f))
    return out
