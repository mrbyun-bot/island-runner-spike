"""4라운드 캐릭터 가족 8종 정면 아이콘.

공통 구성 규칙(108 격자, 바닥선 y90):
  몸      한 덩어리 떡 모양(머리=몸). 폭 54~64, 높이 50~58. 선 없음, 단색 면 + 표식 1~2개.
  눈      먹색 점(rx3.3 ry3.9), 하이라이트 없음. 눈 높이 = 몸 꼭대기에서 몸 높이의 50~56%(이마를 넓게).
          눈 간격(중심 사이) = 몸 폭의 0.36~0.44. 종마다 이 범위 안에서 다르게.
  입·코   한 가지만 크게(종의 표식): 부리, ㅅ코, 웃는 입, 넓은 코 중 하나.
  볼      있으면 눈 아래 6px, 투명도 .5. 없는 종도 있음(얼굴 공식 복제 방지, 2라운드 QC Q1).
  팔레트  몸색 1 + 어두운 표식색 1 + 밝은 표식색 1 + 먹색. 몸색은 검정 대비 7:1 이상(research/palette.md).
"""
import math
from kit import *

SP = {}  # 종 이름 -> 함수(expr)


def eyes(cx, ey, gap, expr, rx=3.3, ry=3.9, col=INK):
    out = []
    for sx in (-1, 1):
        x = cx + sx * gap / 2
        if expr == "open":
            out.append(ell(x, ey, rx, ry, col))
        elif expr == "happy":   # 웃는 눈 ∩
            out.append(path(f"M{f(x-rx-0.6)},{f(ey+1.2)} Q{f(x)},{f(ey-ry-1.4)} {f(x+rx+0.6)},{f(ey+1.2)}", stroke=col, sw=2.2))
        elif expr == "sleep":   # 감은 눈 ︶ (아래로 볼록)
            out.append(path(f"M{f(x-rx-0.6)},{f(ey-0.4)} Q{f(x)},{f(ey+3.2)} {f(x+rx+0.6)},{f(ey-0.4)}", stroke=col, sw=2.0))
    return "".join(out)


def cheeks(cx, cy, gap, col, rx=4.2, ry=2.5, op=0.55):
    return ell(cx - gap / 2, cy, rx, ry, col, op=op) + ell(cx + gap / 2, cy, rx, ry, col, op=op)


SCALE = {"duckling":1.18,"rabbit":1.12,"hedgehog":1.14,"quokka":1.16,"chipmunk":1.1,"turtle":1.12,"otter":1.1,"tit":1.16}


def scaled(name, text):
    k = SCALE.get(name, 1.0)
    a = text.index(">", text.index("<svg")) + 1
    if "</defs>" in text:
        a = text.index("</defs>") + 7
    b = text.rindex("</svg>")
    # clipPath 도 같은 좌표계에 있어야 하므로 defs 안 clip 은 그대로 두고 그룹으로 감싸면 clip 좌표가 그룹 기준이 됨
    return text[:a] + f'<g transform="translate(54 91) scale({k}) translate(-54 -91)">' + text[a:b] + "</g></svg>"


def reg(name):
    def deco(fn):
        SP[name] = lambda expr="open": scaled(name, fn(expr))
        return fn
    return deco


# ---------------------------------------------------------------- 1 아기 청둥오리
@reg("duckling")
def duckling(expr="open"):
    body, cap, bill, foot, wing = "#F2D27E", "#8C6B4C", "#D98F6E", "#E39B5E", "#DDB868"
    cx, w, h = 54, 60, 54
    top = GROUND - h; cy = top + h / 2
    clip = f'<clipPath id="b">{mochi(cx, cy, w, h, "#000", n_top=2.1, n_bot=3.0, pear=0.06)}</clipPath>'
    s = ell(cx - 12, GROUND + 0.5, 6, 2.6, foot) + ell(cx + 12, GROUND + 0.5, 6, 2.6, foot)
    s += ell(cx - w / 2 + 1, cy + 8, 6, 9, wing, rot=18) + ell(cx + w / 2 - 1, cy + 8, 6, 9, wing, rot=-18)
    s += mochi(cx, cy, w, h, body, n_top=2.1, n_bot=3.0, pear=0.06)
    # 갈색 정수리(실제 청둥오리 새끼의 머리 무늬) + 눈 뒤 줄
    ey = top + h * 0.5
    s += f'<g clip-path="url(#b)">{ell(cx, top + 4, 34, 15, cap)}'
    s += path(f"M{f(cx-34)},{f(ey-1)} L{f(cx-19)},{f(ey-1)}", stroke=cap, sw=2.6)
    s += path(f"M{f(cx+19)},{f(ey-1)} L{f(cx+34)},{f(ey-1)}", stroke=cap, sw=2.6) + "</g>"
    s += eyes(cx, ey, 24, expr)
    # 납작한 부리: 넓고 낮은 둥근 사각
    by = ey + 6.5
    s += path(f"M{f(cx-8)},{f(by)} Q{f(cx)},{f(by-3)} {f(cx+8)},{f(by)} Q{f(cx+8.5)},{f(by+5)} {f(cx)},{f(by+5.2)} Q{f(cx-8.5)},{f(by+5)} {f(cx-8)},{f(by)}Z", fill=bill)
    return svg(s, clip)


# ---------------------------------------------------------------- 2 토끼(갈색 산토끼톤, 귀 끝 짙음)
@reg("rabbit")
def rabbit(expr="open"):
    body, tip, inner, muzzle, cheek = "#D5C3AF", "#8B7260", "#E7B7A6", "#F2E8DA", "#E9A797"
    cx, w, h = 54, 56, 52
    top = GROUND - h; cy = top + h / 2
    s = ""
    for sx in (-1, 1):
        bx, by = cx + sx * 11, top + 6
        ang = math.radians(sx * 13)
        tx, ty = bx + math.sin(ang) * 17, by - math.cos(ang) * 17
        ear = capsule(bx, by, tx, ty, 6.6, 6.4, body)
        s += f'<clipPath id="e{sx}">{ear.replace(body, "#000")}</clipPath>'
        s += ear
        s += capsule(bx + math.sin(ang) * 6, by - math.cos(ang) * 6, tx, ty + 1, 2.4, 2.2, inner)
        s += f'<g clip-path="url(#e{sx})">{ell(tx, ty - 2, 9, 5.5, tip, rot=sx*13)}</g>'
    s += mochi(cx, cy, w, h, body, n_top=2.2, n_bot=3.2)
    ey = top + h * 0.53
    s += ell(cx, ey + 7, 9.5, 6.2, muzzle)
    s += eyes(cx, ey, 22, expr)
    s += cheeks(cx, ey + 6, 34, cheek)
    # ㅅ 모양 코·입(X 입 아님)
    s += ell(cx, ey + 4.6, 2.0, 1.5, "#B9786C")
    s += path(f"M{f(cx)},{f(ey+5.6)} L{f(cx)},{f(ey+7.4)} M{f(cx-3)},{f(ey+9.4)} Q{f(cx)},{f(ey+6.6)} {f(cx+3)},{f(ey+9.4)}", stroke=INK, sw=1.3)
    return svg(s)


# ---------------------------------------------------------------- 3 고슴도치
@reg("hedgehog")
def hedgehog(expr="open"):
    spine, tipc, face, ear, nose, cheek = "#7E6A5D", "#A8968A", "#F1DEC6", "#D9B99B", "#3A2C27", "#EBA592"
    cx = 54
    # 가시 덩어리: 둥근 톱니(뾰족하지 않게 끝을 둥글림)
    R, r, n = 37, 30, 15
    pts = []
    for i in range(n * 2):
        a = math.pi + math.pi * 1.25 * i / (n * 2 - 1) - math.pi * 0.125
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(a), 63 + rad * math.sin(a) * 0.95))
    pts += [(cx + 33, GROUND - 4), (cx, GROUND + 1), (cx - 33, GROUND - 4)]
    s = f'<path d="{poly_path(pts)}" fill="{spine}"/>'
    # 가시 끝 밝은 점(질감 하나만)
    for i in range(0, n * 2, 2):
        a = math.pi + math.pi * 1.25 * i / (n * 2 - 1) - math.pi * 0.125
        if math.sin(a) < 0.15:
            s += ell(cx + (R - 4) * math.cos(a), 63 + (R - 4) * math.sin(a) * 0.95, 1.6, 1.6, tipc)
    w, h = 46, 40
    top = GROUND - h; fcy = top + h / 2
    s += ell(cx - 15, top + 4, 5, 4.4, ear) + ell(cx + 15, top + 4, 5, 4.4, ear)
    s += mochi(cx, fcy, w, h, face, n_top=2.0, n_bot=3.0)
    ey = top + h * 0.48
    s += eyes(cx, ey, 18, expr, rx=3.0, ry=3.6)
    s += cheeks(cx, ey + 6, 30, cheek, rx=3.6, ry=2.2)
    s += ell(cx, ey + 6.2, 3.2, 2.5, nose)
    return svg(s)


# ---------------------------------------------------------------- 4 쿼카
@reg("quokka")
def quokka(expr="open"):
    body, ear, inner, muzzle, nose, cheek = "#B39A86", "#97806D", "#D2B7A2", "#DCCAB8", "#3F302A", "#E59C88"
    cx, w, h = 54, 58, 56
    top = GROUND - h; cy = top + h / 2
    s = ell(cx - 21, top + 9, 6, 5.6, ear) + ell(cx + 21, top + 9, 6, 5.6, ear)
    s += ell(cx - 21, top + 9.5, 3.2, 3, inner) + ell(cx + 21, top + 9.5, 3.2, 3, inner)
    s += mochi(cx, cy, w, h, body, n_top=2.0, n_bot=3.4, pear=0.12)
    ey = top + h * 0.47
    s += ell(cx, ey + 9.5, 10.5, 7.5, muzzle)
    s += eyes(cx, ey, 21, expr)
    s += cheeks(cx, ey + 8, 36, cheek)
    s += ell(cx, ey + 5.5, 3.4, 2.4, nose)
    # 쿼카의 웃는 입: 넓은 U
    s += path(f"M{f(cx-6.5)},{f(ey+9)} Q{f(cx)},{f(ey+15)} {f(cx+6.5)},{f(ey+9)}", stroke=INK, sw=1.6)
    # 짧은 앞발 두 개
    return svg(s)


# ---------------------------------------------------------------- 5 줄무늬 다람쥐
@reg("chipmunk")
def chipmunk(expr="open"):
    body, dark, light, tail, cheek = "#DCA36B", "#6F4A31", "#F5E4CC", "#B9824F", "#EC9F86"
    cx, w, h = 52, 52, 52
    top = GROUND - h; cy = top + h / 2
    # 꼬리: 오른쪽 뒤에서 머리 높이까지 올라오는 굵은 관(소용돌이 아님)
    tp = [(cx + 18, GROUND - 4), (cx + 34, GROUND - 14), (cx + 38, top + 8), (cx + 30, top - 6)]
    s = ""
    for i in range(len(tp) - 1):
        r1 = [9, 10, 9.5][i]; r2 = [10, 9.5, 7][i]
        s += capsule(*tp[i], *tp[i + 1], r1, r2, tail)
    s += capsule(*tp[2], *tp[3], 5, 4, "#D59A62")
    s += ell(cx - 15, top + 4, 5, 6, body, rot=-15) + ell(cx + 15, top + 4, 5, 6, body, rot=15)
    s += ell(cx - 15, top + 5, 2.6, 3.4, dark, rot=-15) + ell(cx + 15, top + 5, 2.6, 3.4, dark, rot=15)
    clip = f'<clipPath id="b">{mochi(cx, cy, w, h, "#000", n_top=2.1, n_bot=3.2)}</clipPath>'
    s += mochi(cx, cy, w, h, body, n_top=2.1, n_bot=3.2)
    ey = top + h * 0.5
    g = f'<g clip-path="url(#b)">'
    g += capsule(cx, top - 2, cx, ey - 7, 3.0, 2.0, dark)               # 이마 줄 하나
    for sx in (-1, 1):                                                    # 눈 밑 흰 줄 + 짙은 줄
        g += path(f"M{f(cx+sx*6)},{f(ey-6.5)} Q{f(cx+sx*14)},{f(ey-8.5)} {f(cx+sx*24)},{f(ey-5)}", stroke=light, sw=3.0)
    g += ell(cx, ey + 8, 10, 6.5, light) + ell(cx, GROUND - 2, 14, 11, light) + "</g>"
    s += g
    s += eyes(cx, ey, 20, expr)
    s += cheeks(cx, ey + 7, 30, cheek, rx=3.6)
    s += ell(cx, ey + 5, 2.2, 1.6, "#5A3A2A")
    s += path(f"M{f(cx-2.6)},{f(ey+8)} Q{f(cx)},{f(ey+9.6)} {f(cx+2.6)},{f(ey+8)}", stroke=INK, sw=1.2)
    return svg(s, clip)


# ---------------------------------------------------------------- 6 거북이
@reg("turtle")
def turtle(expr="open"):
    shell, scute, rim, skin, cheek = "#7FAA7A", "#9DC58F", "#5E8A5C", "#D3E2A8", "#E9A08C"
    cx = 54
    s = ell(cx - 22, GROUND - 1, 8, 4.5, skin) + ell(cx + 22, GROUND - 1, 8, 4.5, skin)
    # 등껍질 돔
    sh = mochi(cx, 58, 74, 46, shell, n_top=2.0, n_bot=6, pear=-0.02)
    s += sh
    clip = f'<clipPath id="s">{sh.replace(shell, "#000")}</clipPath>'
    g = '<g clip-path="url(#s)">'
    g += ell(cx, 46, 11, 9, scute) + ell(cx - 23, 52, 9, 9, scute) + ell(cx + 23, 52, 9, 9, scute)
    g += f'<rect x="0" y="74" width="108" height="10" fill="{rim}"/></g>'
    s += g
    # 머리: 껍질 아래 가장자리에서 앞으로 나온 둥근 머리
    hw, hh = 36, 30
    htop = GROUND - hh - 2; hcy = htop + hh / 2
    s += mochi(cx, hcy, hw, hh, skin, n_top=2.0, n_bot=2.4)
    ey = htop + hh * 0.45
    s += eyes(cx, ey, 15, expr, rx=2.9, ry=3.5)
    s += cheeks(cx, ey + 6, 25, cheek, rx=3.2, ry=2.0)
    s += path(f"M{f(cx-3)},{f(ey+6.5)} Q{f(cx)},{f(ey+8.6)} {f(cx+3)},{f(ey+6.5)}", stroke=INK, sw=1.3)
    return svg(s, clip)


# ---------------------------------------------------------------- 7 수달
@reg("otter")
def otter(expr="open"):
    body, mask, paw, nose = "#A57B5C", "#EAD7C1", "#8B6449", "#3B2B24"
    cx, w, h = 54, 50, 60
    top = GROUND - h; cy = top + h / 2
    s = ell(cx - 19, top + 9, 4.4, 4, paw) + ell(cx + 19, top + 9, 4.4, 4, paw)
    s += mochi(cx, cy, w, h, body, n_top=2.0, n_bot=3.0, pear=0.1)
    ey = top + h * 0.38
    clip = f'<clipPath id="b">{mochi(cx, cy, w, h, "#000", n_top=2.0, n_bot=3.0, pear=0.1)}</clipPath>'
    # 넓은 밝은 주둥이 판(눈 아래만, 눈 주위로 올라오지 않게)
    s += f'<g clip-path="url(#b)">{ell(cx, ey + 9, 17, 9.5, mask)}</g>'
    s += eyes(cx, ey, 20, expr, rx=3.0, ry=3.6)
    s += path(f"M{f(cx-4)},{f(ey+4.8)} Q{f(cx)},{f(ey+3.4)} {f(cx+4)},{f(ey+4.8)} Q{f(cx)},{f(ey+9)} {f(cx-4)},{f(ey+4.8)}Z", fill=nose)
    for sx in (-1, 1):
        for k in range(2):
            s += ell(cx + sx * (9 + k * 3), ey + 9.5 + k * 1.5, 0.7, 0.7, "#B39680")
    s += path(f"M{f(cx)},{f(ey+8)} L{f(cx)},{f(ey+10)}", stroke=INK, sw=1.2)
    # 가슴에 모은 앞발
    s += ell(cx - 5.5, cy + 15, 5, 4, paw) + ell(cx + 5.5, cy + 15, 5, 4, paw)
    return svg(s, clip)


# ---------------------------------------------------------------- 8 붉은머리오목눈이(뱁새)
@reg("tit")
def tit(expr="open"):
    body, cap, wing, tail, beak, cheek = "#E2B597", "#C47F5E", "#A9785E", "#8E6450", "#4C3A30", "#EE9C8A"
    cx, w, h = 52, 58, 52
    top = GROUND - h; cy = top + h / 2
    # 긴 꼬리: 오른쪽 아래로 비스듬히
    s = capsule(cx + 14, GROUND - 12, cx + 42, GROUND - 4, 6.4, 4.6, tail)
    s += ell(cx - 12, GROUND + 0.5, 3.8, 1.8, "#7A5A48") + ell(cx + 8, GROUND + 0.5, 3.8, 1.8, "#7A5A48")
    s += mochi(cx, cy, w, h, body, n_top=2.0, n_bot=2.3)
    clip = f'<clipPath id="b">{mochi(cx, cy, w, h, "#000", n_top=2.0, n_bot=2.3)}</clipPath>'
    s += f'<g clip-path="url(#b)">{ell(cx, top + 6, 33, 15, cap)}'
    s += ell(cx - w / 2 + 2, cy + 9, 8, 13, wing, rot=14) + ell(cx + w / 2 - 2, cy + 9, 8, 13, wing, rot=-14) + "</g>"
    ey = top + h * 0.5
    s += eyes(cx, ey, 19, expr, rx=2.7, ry=3.2)
    s += cheeks(cx, ey + 5.5, 33, cheek, rx=3.8, ry=2.3)
    s += path(f"M{f(cx-2.8)},{f(ey+3)} L{f(cx+2.8)},{f(ey+3)} L{f(cx)},{f(ey+6.4)}Z", fill=beak)
    return svg(s, clip)


ORDER = ["duckling", "rabbit", "hedgehog", "quokka", "chipmunk", "turtle", "otter", "tit"]
KO = {"duckling": "아기 청둥오리", "rabbit": "갈색 토끼", "hedgehog": "고슴도치", "quokka": "쿼카",
      "chipmunk": "줄무늬 다람쥐", "turtle": "거북이", "otter": "수달", "tit": "뱁새(붉은머리오목눈이)"}
