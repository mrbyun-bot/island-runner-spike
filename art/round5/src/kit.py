"""5라운드 그리기 도구.

전문 일러스트레이터 공정을 코드로 옮긴 것:
- 곡선: 구심 캐트멀롬(centripetal Catmull-Rom)으로 조절점 사이를 매끈하게 잇는다(펜 툴 대신).
- 선: 가변 폭 선(Inkscape Power Stroke 와 같은 원리). 중심선의 법선 방향으로 폭 함수만큼 양쪽을 띄워
  채운 다각형을 만든다. 폭은 빛(왼쪽 위)의 반대편, 즉 아래·오른쪽에서 두꺼워지고(무게 선),
  저주파 잡음으로 미세하게 흔들린다(손맛).
- 색선: 검정 대신 같은 계열의 어두운 색.
- 셀 음영 1단: 부위 모양을 왼쪽 위로 민 사본을 기본색으로 덮어, 오른쪽 아래 초승달만 음영색으로 남긴다.
- 하이라이트: 왼쪽 위에 끝이 가는 밝은 획.
좌표계는 240×240, 바닥선 y=212. 모든 크기는 이 좌표 기준.
"""
import math, os, subprocess, tempfile
import numpy as np

LIGHT = np.array([-0.55, -0.83])  # 빛이 오는 방향(왼쪽 위)
SHADOW_DIR = -LIGHT / np.linalg.norm(LIGHT)


def crom(pts, closed=True, n=18, alpha=0.5):
    """구심 캐트멀롬 곡선. pts: [(x,y),...] → (N,2) 배열."""
    P = np.asarray(pts, float)
    if closed:
        P = np.vstack([P[-1], P, P[0], P[1]])
    else:
        P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        def tj(ti, a, b):
            return ti + max(np.linalg.norm(b - a), 1e-6) ** alpha
        t0 = 0; t1 = tj(t0, p0, p1); t2 = tj(t1, p1, p2); t3 = tj(t2, p2, p3)
        for t in np.linspace(t1, t2, n, endpoint=False):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    if not closed:
        out.append(P[-2])
    return np.array(out)


def ellipse_pts(cx, cy, rx, ry, rot=0, n=10, wob=0.0, seed=0):
    rng = np.random.default_rng(seed)
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    r = 1 + wob * rng.uniform(-1, 1, n)
    x = rx * np.cos(a) * r; y = ry * np.sin(a) * r
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(cx + c * xi - s * yi, cy + s * xi + c * yi) for xi, yi in zip(x, y)]


def xform(pts, dx=0, dy=0, rot=0, sx=1, sy=1, ox=0, oy=0):
    """원점 (ox,oy) 기준 비율·회전 후 이동."""
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for x, y in pts:
        x = (x - ox) * sx; y = (y - oy) * sy
        out.append((ox + c * x - s * y + dx, oy + s * x + c * y + dy))
    return out


def _normals(P, closed):
    if closed:
        T = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    else:
        T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    N = np.stack([T[:, 1], -T[:, 0]], 1)
    return N


def _area(P):
    x, y = P[:, 0], P[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def jitter(n, seed, amp, cycles=5, closed=True):
    """저주파 잡음(손 떨림). 닫힌 곡선이면 주기적으로 이어진다."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, n, endpoint=False)
    v = np.zeros(n)
    for k in range(1, cycles + 1):
        v += rng.normal() / k * np.sin(2 * math.pi * k * t + rng.uniform(0, 6.28))
    v /= (np.abs(v).max() + 1e-9)
    return 1 + amp * v


def path_d(P, close=True):
    s = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in P)
    return s + ("Z" if close else "")


class Canvas:
    def __init__(self, size=240, lod="full"):
        self.size = size
        self.lod = lod  # "full" | "small"(36px 용: 안쪽 가는 선 생략)
        self.mode = "final"  # 공정 시연용: rough(구성 형태) / line(선만) / flat(평면색+선) / final
        self.items = []
        self.defs = []
        self._id = 0

    def nid(self, p="c"):
        self._id += 1
        return f"{p}{self._id}"

    def raw(self, s):
        self.items.append(s)

    def _thin(self, P, color="#6FA8FF", w=1.4):
        P = np.asarray(P, float)
        self.items.append(f'<path d="{path_d(P)}" fill="none" stroke="{color}" stroke-width="{w}" stroke-opacity="0.85"/>')

    def fill(self, P, color, opacity=1.0):
        if self.mode == "rough":
            return self._thin(P)
        if self.mode == "line":
            r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
            color = color if (0.3 * r + 0.59 * g + 0.11 * b) < 90 else "#FFFFFF"
        op = f' fill-opacity="{opacity}"' if opacity < 1 else ""
        self.items.append(f'<path d="{path_d(P)}" fill="{color}"{op}/>')

    # ---- 가변 폭 닫힌 선 ----
    def ring(self, P, color, wmin, wmax, seed=0, jit=0.12):
        if self.mode == "rough":
            return self._thin(P)
        P = np.asarray(P, float)
        if _area(P) < 0:
            P = P[::-1]
        N = _normals(P, True)
        # 화면 좌표에서 y 가 아래로 커지므로, 면적 부호를 맞춘 뒤 바깥 법선을 고른다
        c = P.mean(0)
        if np.mean(np.sum((P - c) * N, 1)) < 0:
            N = -N
        d = N @ SHADOW_DIR
        w = wmin + (wmax - wmin) * np.clip(0.5 + 0.6 * d, 0, 1)
        w = w * jitter(len(P), seed, jit, 6)
        outer = P + N * (w[:, None] * 0.55)
        inner = P - N * (w[:, None] * 0.45)
        self.items.append(
            f'<path d="{path_d(outer)} {path_d(inner[::-1])}" fill="{color}" fill-rule="evenodd"/>')

    # ---- 끝이 가는 열린 선(Taper Stroke 원리) ----
    def stroke(self, P, color, w, taper=(0.35, 0.35), seed=0, jit=0.1, min_w=0.25, small_keep=True):
        if self.lod == "small" and not small_keep:
            return
        if self.mode == "rough":
            return self._thin(P)
        P = np.asarray(P, float)
        n = len(P)
        N = _normals(P, False)
        t = np.linspace(0, 1, n)
        prof = np.ones(n)
        a, b = taper
        if a > 0:
            m = t < a
            prof[m] = np.sin(t[m] / a * math.pi / 2) ** 0.8
        if b > 0:
            m = t > 1 - b
            prof[m] = np.minimum(prof[m], np.sin((1 - t[m]) / b * math.pi / 2) ** 0.8)
        prof = np.maximum(prof, min_w)
        ww = w * prof * jitter(n, seed, jit, 3, closed=False)
        L = P + N * ww[:, None] / 2
        R = P - N * ww[:, None] / 2
        # 둥근 끝
        poly = np.vstack([L, R[::-1]])
        self.items.append(f'<path d="{path_d(poly)}" fill="{color}"/>')
        for e in (0, -1):
            r = ww[e] / 2
            if r > 0.4:
                self.items.append(f'<circle cx="{P[e,0]:.2f}" cy="{P[e,1]:.2f}" r="{r:.2f}" fill="{color}"/>')

    # ---- 한 부위: 채움 + 셀 음영 + 하이라이트 + 가변 폭 선 ----
    def part(self, P, fill, line, shade=None, wmin=3.0, wmax=7.0, seed=0, shade_off=7.0,
             hl=None, hl_w=4.0, extra=None, line_on=True):
        P = np.asarray(P, float)
        if self.mode == "rough":
            return self._thin(P)
        if self.mode in ("line", "flat"):
            shade = None; hl = None
            if self.mode == "line":
                extra = None
        if shade:
            cid = self.nid("clip")
            self.defs.append(f'<clipPath id="{cid}"><path d="{path_d(P)}"/></clipPath>')
            off = -SHADOW_DIR * shade_off
            cen = P.mean(0)
            Q = (P - cen) * 1.02 + cen + off
            g = [f'<g clip-path="url(#{cid})">', f'<path d="{path_d(P)}" fill="{shade}"/>',
                 f'<path d="{path_d(Q)}" fill="{fill}"/>']
            if extra:
                g.append(extra(cid))
            g.append('</g>')
            self.items.append("".join(g))
        else:
            self.fill(P, fill)
            if extra:
                cid = self.nid("clip")
                self.defs.append(f'<clipPath id="{cid}"><path d="{path_d(P)}"/></clipPath>')
                self.items.append(f'<g clip-path="url(#{cid})">{extra(cid)}</g>')
        if hl is not None:
            pts, col = hl
            self.stroke(crom(pts, closed=False, n=10), col, hl_w, taper=(0.45, 0.45), seed=seed + 7,
                        small_keep=False)
        if line_on:
            self.ring(P, line, wmin, wmax, seed=seed)

    def clipped(self, P, inner_svg):
        """P 모양 안에만 보이게(무늬, 배 색 등)."""
        if self.mode in ("rough", "line"):
            return
        cid = self.nid("clip")
        self.defs.append(f'<clipPath id="{cid}"><path d="{path_d(np.asarray(P, float))}"/></clipPath>')
        self.items.append(f'<g clip-path="url(#{cid})">{inner_svg}</g>')

    def svg(self, bg=None, vb=(0, 0, 240, 240)):
        s = self.size
        bgs = f'<rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="{bg}"/>' if bg else ""
        v = " ".join(f"{x:.2f}" for x in vb)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="{v}">'
                f'<defs>{"".join(self.defs)}</defs>{bgs}{"".join(self.items)}</svg>')


def svg_fill(P, color, opacity=1.0):
    op = f' fill-opacity="{opacity}"' if opacity < 1 else ""
    return f'<path d="{path_d(np.asarray(P, float))}" fill="{color}"{op}/>'


# ---------------- 눈: 표정이 들어가는 곳 ----------------
def eye(c, cx, cy, h, w_ratio=0.72, iris="#2A1A22", iris_lo="#6B3A48", lid=None, lid_col="#2A1A22",
        look=(0.0, 0.0), squash=1.0, tilt=0, mood="bright", far=False, seed=0):
    """큰 세로 타원 눈.
    h: 눈 높이, w_ratio: 폭/높이, far: 3/4 시점의 먼 눈(좁게).
    mood: bright(기본, 하이라이트 둘) / happy(웃는 눈 ^ 모양) / focus(위 눈꺼풀이 살짝 덮음)
          / sleepy(반쯤 감김) / closed(감은 선)
    하이라이트는 빛 방향(왼쪽 위)에 맞춰 왼쪽 위 큰 점 + 오른쪽 아래 작은 점.
    """
    w = h * w_ratio * (0.8 if far else 1.0)
    hh = h * squash
    if mood in ("happy", "closed"):
        k = 1 if mood == "happy" else -1
        P = crom([(cx - w * 0.6, cy + hh * 0.1 * k), (cx, cy - hh * 0.32 * k), (cx + w * 0.6, cy + hh * 0.1 * k)],
                 closed=False, n=10)
        c.stroke(P, iris, max(2.2, h * 0.16), taper=(0.25, 0.25), seed=seed)
        return
    P = ellipse_pts(cx, cy, w / 2, hh / 2, rot=tilt, n=14)
    c.fill(P, iris)
    # 아래쪽 밝은 반달(홍채 반사)
    lo = ellipse_pts(cx + look[0] * w * 0.1, cy + hh * 0.26, w * 0.34, hh * 0.2, rot=tilt, n=12)
    c.clipped(P, svg_fill(lo, iris_lo))
    if c.lod != "small" or True:
        hx, hy = cx - w * 0.16 + look[0] * w * 0.12, cy - hh * 0.2 + look[1] * hh * 0.1
        c.fill(ellipse_pts(hx, hy, w * 0.24, hh * 0.17, rot=-20, n=12), "#FFFFFF")
        if c.lod != "small":
            c.fill(ellipse_pts(cx + w * 0.2, cy + hh * 0.2, w * 0.09, w * 0.09, n=8), "#FFFFFF")
    if mood in ("focus", "sleepy"):
        cover = 0.32 if mood == "focus" else 0.55
        top = cy - hh / 2 - 2
        y0 = cy - hh / 2 + hh * cover
        lidp = [(cx - w, top - 6), (cx + w, top - 6), (cx + w, y0 - (2 if mood == "focus" else 0)),
                (cx - w, y0 + (3 if mood == "focus" else 0))]
        c.clipped(P, svg_fill(lidp, lid or "#000"))
        c.stroke([(cx - w * 0.62, y0 + (3 if mood == "focus" else 0) * 0.8),
                  (cx + w * 0.62, y0 - (2 if mood == "focus" else 0) * 0.8)],
                 lid_col, max(2.0, h * 0.13), taper=(0.15, 0.3), seed=seed)


def blush(c, cx, cy, rx, ry, color, rot=0):
    c.fill(ellipse_pts(cx, cy, rx, ry, rot=rot, n=12), color, opacity=0.85)
    if c.lod != "small":
        c.fill(ellipse_pts(cx - rx * 0.35, cy - ry * 0.3, rx * 0.28, ry * 0.22, rot=rot, n=8), "#FFFFFF", 0.55)


# ---------------- 렌더 ----------------
def render_many(jobs):
    """jobs: [(svg_text, out_png, width)] → Inkscape 셸 모드로 한 번에 내보낸다."""
    tmp = tempfile.mkdtemp(prefix="r5svg_")
    cmds = []
    for i, (svg, out, w) in enumerate(jobs):
        p = os.path.join(tmp, f"{i}.svg")
        with open(p, "w") as f:
            f.write(svg)
        cmds.append(f"file-open:{p}; export-filename:{os.path.abspath(out)}; export-width:{w}; "
                    f"export-height:{w}; export-background-opacity:0; export-do; file-close")
    script = "\n".join(cmds) + "\nquit\n"
    subprocess.run(["inkscape", "--shell"], input=script.encode(), stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=1200)
    missing = [o for _, o, _ in jobs if not os.path.exists(o)]
    if missing:
        raise RuntimeError(f"렌더 실패 {len(missing)}개: {missing[:3]}")
