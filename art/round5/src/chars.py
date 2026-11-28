"""5라운드 캐릭터 8종. 모두 오른쪽을 보는 3/4 시점(달리는 방향과 얼굴 방향을 맞춤).

각 함수 draw_xxx(c, p) 는 포즈 사전 p 를 받는다. 정지 아이콘은 기본값으로 그린다.
공통 포즈 키:
  dy: 몸 전체 위아래, lean: 기울기(도), sq: 세로 비율(눌림 <1, 늘임 >1)
  legs: [(앞다리 각도, 뒷다리 각도)] 등 종별, mood: 눈 표정, mouth: 입 모양
"""
import math
import numpy as np
from kit import crom, ellipse_pts, xform, eye, blush, svg_fill

GROUND = 212


def T(pts, p, ox=120, oy=GROUND):
    """포즈의 몸 전체 변환(바닥 중심 기준 눌림·기울기·이동)."""
    return xform(pts, dx=p.get("dx", 0), dy=p.get("dy", 0), rot=p.get("lean", 0),
                 sx=1 / math.sqrt(p.get("sq", 1)), sy=p.get("sq", 1), ox=ox, oy=oy)


def C(pts, p, n=16, closed=True):
    return crom(T(pts, p), closed=closed, n=n)


def limb(c, p, hip, length, ang, w, fill, line, shade=None, foot=1.0, seed=0, pad=None, toe=1.0):
    """통통한 다리 + 앞을 향한 발. hip 은 몸 좌표, ang 은 수직에서 앞(+)/뒤(-) 각도(도)."""
    hx, hy = hip
    a = math.radians(ang)
    dx, dy = math.sin(a), math.cos(a)
    ex, ey = hx + dx * length, hy + dy * length
    nx, ny = dy, -dx  # 다리 방향의 오른쪽 법선
    fw = w * 0.5 * foot
    L = fw * 1.55 * toe  # 발 길이(앞으로)
    pts = [(hx - nx * w * 0.55, hy - ny * w * 0.55),
           (ex - nx * fw - dx * fw * 0.2, ey - ny * fw * 0.6),
           (ex - nx * fw * 0.4 + dx * fw * 0.9, ey + dy * fw * 0.95),
           (ex + L * 0.85, ey + fw * 0.85),
           (ex + L, ey + fw * 0.1),
           (ex + nx * fw * 0.6 + L * 0.3, ey - fw * 0.7),
           (hx + nx * w * 0.55, hy + ny * w * 0.55), (hx, hy - w * 0.35)]
    P = C(pts, p, n=10)
    c.part(P, fill, line, shade, wmin=2.6, wmax=5.0, seed=seed, shade_off=4)
    if pad and c.lod != "small":
        q = T([(ex + L * 0.45, ey + fw * 0.62)], p)[0]
        c.fill(ellipse_pts(q[0], q[1], fw * 0.75, fw * 0.22, rot=p.get("lean", 0), n=8), pad)


# =====================================================================
# 1. 강아지 "보리": 살구색 몸, 귀 하나는 접히고 하나는 날림(비대칭), 흰 주둥이·가슴
# =====================================================================
DOG = dict(fill="#FFB65C", shade="#EE8A3C", line="#9C4A1C", cream="#FFF2DC", cream_sh="#F6CF9E",
           ear="#C9662C", ear_sh="#A54F1E", nose="#45201A", tongue="#FF6B7A", cheek="#FF8C8C",
           iris="#3B1D18", iris_lo="#8C4C30", hl="#FFE2B0")


def draw_dog(c, p=None):
    p = dict(dict(legs=((-16, 24), (30, -30)), lean=3, mood="bright", mouth="open", ear=0, tail=0, eyeh=24, ey=3, brow=False), **(p or {}))
    k = DOG
    (fa, fb), (ba, bb) = p["legs"]  # (앞 먼다리, 뒤 먼다리), (앞 가까운, 뒤 가까운)
    # 먼 쪽 다리(한 단계 어둡게)
    limb(c, p, (144, 180), 30, fa, 16, k["shade"], k["line"], seed=11)
    limb(c, p, (92, 180), 30, fb, 16, k["shade"], k["line"], seed=12)
    # 꼬리: 위로 말린 짧은 붓 모양
    t = p["tail"]
    tail = [(78, 176), (62, 166 - t), (54, 148 - t * 1.5), (60, 140 - t * 1.6), (68, 150 - t), (80, 166)]
    c.part(C(tail, p, 10), k["fill"], k["line"], k["shade"], 2.6, 5, seed=13, shade_off=4)
    # 몸통: 앞이 높은 콩 모양
    body = [(84, 168), (96, 154), (124, 150), (150, 156), (162, 174), (158, 198), (132, 206),
            (100, 205), (80, 194)]
    B = C(body, p)
    belly = svg_fill(C([(128, 168), (160, 166), (168, 200), (128, 212), (118, 190)], p), k["cream"])
    c.part(B, k["fill"], k["line"], k["shade"], 3.2, 6.5, seed=14, shade_off=8, extra=lambda cid: belly)
    # 가까운 다리
    limb(c, p, (148, 182), 30, ba, 17, k["fill"], k["line"], k["shade"], seed=15, pad=k["cream_sh"])
    limb(c, p, (96, 182), 30, bb, 17, k["fill"], k["line"], k["shade"], seed=16, pad=k["cream_sh"])
    # 먼 귀(머리 뒤, 오른쪽 위): 짧고 접힌 귀
    e = p["ear"]
    far_ear = [(150, 66), (166, 52 - e), (182, 60 - e), (178, 78), (164, 84)]
    c.part(C(far_ear, p, 10), k["ear"], k["line"], k["ear_sh"], 2.6, 5, seed=17, shade_off=4)
    # 머리: 약간 기울어진 큰 원, 오른쪽(얼굴 쪽)이 넓다
    head = [(68, 108), (78, 76), (106, 58), (142, 58), (170, 74), (184, 102), (180, 132),
            (160, 150), (124, 156), (90, 150), (72, 132)]
    H = C(head, p)
    c.part(H, k["fill"], k["line"], k["shade"], 3.4, 7.2, seed=18, shade_off=9,
           hl=(T([(86, 92), (96, 74), (114, 66)], p), k["hl"]), hl_w=5)
    # 주둥이: 오른쪽 아래로 나온 크림색 덩어리(3/4 시점의 핵심)
    muz = [(130, 118), (154, 108), (184, 112), (194, 128), (186, 144), (160, 150), (134, 144)]
    c.part(C(muz, p, 12), k["cream"], k["line"], k["cream_sh"], 2.4, 4.6, seed=19, shade_off=5)
    # 가까운 귀: 왼쪽에서 아래로 늘어진 큰 귀, 끝이 바람에 들림
    near_ear = [(74, 78), (86, 66), (100, 76), (98, 104), (88, 126 - e * 0.6), (70, 132 - e),
                (60, 120 - e), (62, 98)]
    c.part(C(near_ear, p, 12), k["ear"], k["line"], k["ear_sh"], 2.8, 6, seed=20, shade_off=6)
    # 얼굴
    m = p["mood"]
    eye(c, *T([(120, 104 + p["ey"])], p)[0], p["eyeh"], iris=k["iris"], iris_lo=k["iris_lo"], mood=m, lid=k["fill"],
        lid_col=k["line"], seed=21)
    eye(c, *T([(163, 99 + p["ey"])], p)[0], p["eyeh"] * 0.9, iris=k["iris"], iris_lo=k["iris_lo"], mood=m, far=True,
        lid=k["fill"], lid_col=k["line"], seed=22)
    # 눈썹 무늬(시바 계열과 갈라지게 점이 아니라 짧은 붓터치)
    if c.lod != "small" and p["brow"]:
        c.stroke(crom(T([(108, 84), (118, 80), (127, 83)], p), False, 8), k["ear"], 4.2, seed=23)
    nose = ellipse_pts(*T([(184, 118)], p)[0], 8, 6, rot=10, n=10)
    c.fill(nose, k["nose"])
    c.fill(ellipse_pts(*T([(181, 116)], p)[0], 3, 1.8, rot=10, n=6), "#FFFFFF", 0.8)
    if p["mouth"] == "open":
        mo = [(160, 130), (172, 133), (182, 128), (180, 142), (170, 148), (161, 141)]
        MO = C(mo, p, 8)
        tg = svg_fill(ellipse_pts(*T([(171, 147)], p)[0], 8, 6, n=10), k["tongue"])
        c.fill(MO, "#6B2420")
        c.clipped(MO, tg)
        c.ring(MO, k["line"], 1.8, 3.2, seed=24)
    else:
        c.stroke(crom(T([(162, 134), (171, 138), (180, 131)], p), False, 8), k["line"], 3.0, seed=24)
    blush(c, *T([(130, 130)], p)[0], 10, 6, k["cheek"], rot=-8)




# ---------------- 공통 얼굴 ----------------
def face(c, p, k, near, far, h, mouth_at, cheek_at, mood=None, mouth=None, mw=1.0, Tf=None):
    """3/4 시점 얼굴. near/far: 가까운 눈·먼 눈 위치(몸 좌표). 먼 눈은 좁고 작다."""
    Tf = Tf or (lambda pts: T(pts, p))
    m = mood or p.get("mood", "bright")
    look = p.get("look", (0.3, 0))
    eye(c, *Tf([near])[0], h, iris=k["iris"], iris_lo=k["iris_lo"], mood=m, lid=k["fill"],
        lid_col=k["line"], look=look, seed=31)
    eye(c, *Tf([far])[0], h * 0.9, iris=k["iris"], iris_lo=k["iris_lo"], mood=m, far=True,
        lid=k["fill"], lid_col=k["line"], look=look, seed=32)
    mx, my = mouth_at
    mo = mouth or p.get("mouth", "smile")
    if mo == "open":
        pts = [(mx - 8 * mw, my - 2), (mx, my), (mx + 8 * mw, my - 3), (mx + 6 * mw, my + 7), (mx, my + 10),
               (mx - 6 * mw, my + 6)]
        MO = crom(Tf(pts), True, 8)
        c.fill(MO, "#6B2420")
        c.clipped(MO, svg_fill(ellipse_pts(*Tf([(mx, my + 11)])[0], 7 * mw, 5.5, n=10), "#FF6B7A"))
        c.ring(MO, k["line"], 1.6, 3.0, seed=33)
    elif mo == "w":
        c.stroke(crom(Tf([(mx - 8, my - 1), (mx - 4, my + 4), (mx, my), (mx + 4, my + 4), (mx + 8, my - 1)]),
                      False, 6), k["line"], 2.8, taper=(0.2, 0.2), seed=33)
    elif mo == "o":
        O = ellipse_pts(*Tf([(mx, my + 2)])[0], 4 * mw, 5, n=10)
        c.fill(O, "#6B2420"); c.ring(O, k["line"], 1.4, 2.4, seed=33)
    else:
        c.stroke(crom(Tf([(mx - 8 * mw, my - 2), (mx, my + 4), (mx + 8 * mw, my - 3)]), False, 8), k["line"],
                 3.0, taper=(0.25, 0.25), seed=33)
    if cheek_at:
        blush(c, *Tf([cheek_at])[0], 9, 5.5, k["cheek"], rot=-8)


def TH(p):
    """머리용 변환: 몸 변환 뒤에 머리만 따로 늦게 움직이는 양(hdy, hrot)을 더한다(오버랩)."""
    def f(pts):
        q = xform(pts, dy=p.get("hdy", 0), rot=p.get("hrot", 0), ox=124, oy=150)
        return T(q, p)
    return f


def CH(pts, p, n=16):
    return crom(TH(p)(pts), True, n)


# =====================================================================
# 2. 토끼: 크림 몸에 장밋빛 색선, 가까운 귀는 서고 먼 귀는 끝이 접힘(비대칭)
# =====================================================================
RAB = dict(fill="#FFF3E8", shade="#F3C9C6", line="#B24E72", inner="#FF9DB6", inner_sh="#F07C9C",
           cheek="#FF8FA8", iris="#3A1830", iris_lo="#A04A72", hl="#FFFFFF", nose="#FF6F91")


def draw_rabbit(c, p=None):
    p = dict(dict(legs=((-20, 26), (34, -40)), lean=3, mood="bright", mouth="w", ear=0), **(p or {}))
    k = RAB
    (fa, fb), (ba, bb) = p["legs"]
    limb(c, p, (142, 182), 26, fa, 14, k["shade"], k["line"], seed=41)
    limb(c, p, (98, 186), 24, fb, 18, k["shade"], k["line"], seed=42, toe=1.5)
    # 꼬리 방울
    c.part(crom(T(ellipse_pts(80, 178, 15, 14, n=9, wob=0.12, seed=4), p), True, 8), k["fill"], k["line"],
           k["shade"], 2.4, 4.6, seed=43, shade_off=4)
    body = [(86, 170), (100, 154), (128, 150), (152, 158), (160, 178), (154, 200), (126, 206), (98, 204), (82, 190)]
    c.part(C(body, p), k["fill"], k["line"], k["shade"], 3.0, 6.0, seed=44, shade_off=8)
    limb(c, p, (146, 184), 26, ba, 15, k["fill"], k["line"], k["shade"], seed=45, pad=k["inner"])
    limb(c, p, (102, 188), 24, bb, 19, k["fill"], k["line"], k["shade"], seed=46, toe=1.5, pad=k["inner"])
    Th = TH(p); e = p["ear"]
    # 먼 귀: 위로 섰다가 끝이 앞으로 접힘
    far_ear = [(136, 76), (138, 44), (150, 26), (168, 28 + e * 0.5), (182, 42 + e), (170, 46 + e), (158, 46),
               (154, 74)]
    c.part(crom(Th(far_ear), True, 10), k["fill"], k["line"], k["shade"], 2.6, 5.2, seed=47, shade_off=5)
    head = [(70, 112), (78, 80), (104, 62), (140, 62), (168, 78), (182, 106), (176, 134), (154, 152),
            (120, 158), (90, 150), (74, 134)]
    c.part(crom(Th(head), True, 16), k["fill"], k["line"], k["shade"], 3.2, 7.0, seed=48, shade_off=9,
           hl=(Th([(86, 94), (96, 76), (114, 68)]), "#FFFFFF"), hl_w=5)
    # 가까운 귀: 똑바로, 뒤로 살짝 젖힘
    near_ear = [(94, 78), (82, 50), (80, 22 - e * 0.3), (92, 8 - e * 0.5), (106, 14 - e * 0.3), (114, 42),
                (118, 74)]
    inner = svg_fill(crom(Th([(98, 70), (91, 46), (91, 24), (98, 16), (104, 26), (107, 48), (108, 68)]), True, 8),
                     k["inner"])
    c.part(crom(Th(near_ear), True, 10), k["fill"], k["line"], k["shade"], 2.8, 5.6, seed=49, shade_off=5,
           extra=lambda cid: inner)
    face(c, p, k, (122, 110), (162, 104), 24, (166, 132), (134, 134), Tf=Th)
    c.fill(crom(Th([(170, 118), (178, 117), (175, 124)]), True, 5), k["nose"])


# =====================================================================
# 3. 다람쥐: 선명한 주황, 머리 위까지 말려 올라가는 큰 꼬리(실루엣 담당)
# =====================================================================
SQ = dict(fill="#F08A4B", shade="#D0643A", line="#8E3212", cream="#FFEBD0", cream_sh="#F7C79A",
          tail="#FFB866", tail_sh="#F08E3E", tip="#FFE6BE", cheek="#FF7A7A", iris="#35160E", iris_lo="#93482A",
          hl="#FFD9A8")


def draw_squirrel(c, p=None):
    p = dict(dict(legs=((-18, 24), (30, -34)), lean=3, mood="bright", mouth="smile", tail=0), **(p or {}))
    k = SQ; (fa, fb), (ba, bb) = p["legs"]; t = p["tail"]
    tail = [(92, 186), (58, 184), (34, 158), (26, 118), (34, 76), (58, 44 + t), (90, 30 + t), (116, 40 + t),
            (124, 62 + t), (112, 80 + t), (96, 82 + t), (88, 70 + t), (98, 62 + t), (90, 54 + t), (70, 62),
            (62, 88), (66, 124), (80, 154), (102, 170)]
    tip = svg_fill(T([(20, 20), (140, 20), (140, 96), (60, 70), (20, 80)], p), k["tip"])
    c.part(C(tail, p), k["tail"], k["line"], k["tail_sh"], 3.0, 6.2, seed=51, shade_off=7, extra=lambda cid: tip)
    if c.lod != "small":  # 꼬리 털 결 몇 획
        for i, q in enumerate([[(46, 130), (42, 104), (48, 82)], [(56, 160), (50, 144)], [(70, 52), (86, 44)]]):
            c.stroke(crom(T(q, p), False, 8), k["tail_sh"], 3.2, seed=52 + i)
    limb(c, p, (144, 180), 26, fa, 14, k["shade"], k["line"], seed=53)
    limb(c, p, (100, 182), 26, fb, 16, k["shade"], k["line"], seed=54, toe=1.3)
    body = [(88, 168), (100, 154), (128, 150), (152, 158), (160, 178), (154, 200), (126, 206), (98, 204), (84, 190)]
    belly = svg_fill(C([(128, 166), (162, 164), (168, 204), (126, 212), (118, 188)], p), k["cream"])
    c.part(C(body, p), k["fill"], k["line"], k["shade"], 3.0, 6.0, seed=55, shade_off=8, extra=lambda cid: belly)
    limb(c, p, (148, 182), 26, ba, 15, k["fill"], k["line"], k["shade"], seed=56)
    limb(c, p, (104, 186), 24, bb, 17, k["fill"], k["line"], k["shade"], seed=57, toe=1.3)
    Th = TH(p)
    far_ear = [(146, 70), (150, 52), (162, 46), (172, 56), (168, 74)]
    c.part(crom(Th(far_ear), True, 10), k["fill"], k["line"], k["shade"], 2.6, 5.0, seed=58, shade_off=4)
    head = [(72, 112), (80, 82), (106, 64), (140, 62), (168, 76), (184, 104), (180, 132), (158, 152),
            (122, 158), (92, 150), (76, 134)]
    cheekp = svg_fill(crom(Th([(150, 124), (172, 114), (192, 120), (188, 146), (164, 154), (148, 142)]), True, 10),
                      k["cream"])
    c.part(crom(Th(head), True, 16), k["fill"], k["line"], k["shade"], 3.2, 7.0, seed=59, shade_off=9,
           hl=(Th([(88, 94), (98, 78), (116, 70)]), k["hl"]), hl_w=5, extra=lambda cid: cheekp)
    near_ear = [(90, 82), (84, 60), (92, 46), (106, 46), (114, 60), (114, 78)]
    inner = svg_fill(crom(Th([(95, 74), (92, 62), (99, 54), (106, 60), (107, 72)]), True, 6), k["shade"])
    c.part(crom(Th(near_ear), True, 10), k["fill"], k["line"], k["shade"], 2.8, 5.4, seed=60, shade_off=4,
           extra=lambda cid: inner)
    face(c, p, k, (124, 106), (164, 100), 24, (172, 132), (136, 132), Tf=Th)
    c.fill(ellipse_pts(*Th([(184, 120)])[0], 6, 4.5, rot=10, n=8), "#4A1C10")


# =====================================================================
# 4. 거북이: 민트 등껍질 + 연두 피부, 큰 머리가 앞으로 나온 옆모습
# =====================================================================
TUR = dict(fill="#B4E682", shade="#86C65E", line="#2C6A3A", shell="#36BE8C", shell_sh="#22997A",
           plate="#7FE2B8", rim="#FFE7A6", rim_sh="#F2C672", cheek="#FF8C8C", iris="#1F2A1E", iris_lo="#4F7A4A",
           hl="#E4FFC8")


def draw_turtle(c, p=None):
    p = dict(dict(legs=((-22, 26), (28, -28)), lean=0, mood="bright", mouth="open"), **(p or {}))
    k = TUR; (fa, fb), (ba, bb) = p["legs"]
    limb(c, p, (138, 186), 18, fa, 17, k["shade"], k["line"], seed=71)
    limb(c, p, (78, 186), 18, fb, 17, k["shade"], k["line"], seed=72)
    c.part(C([(52, 184), (36, 186), (40, 178), (54, 176)], p, 6), k["fill"], k["line"], k["shade"], 2.2, 4, seed=73)
    shell = [(46, 182), (50, 146), (72, 116), (104, 104), (138, 110), (160, 134), (168, 166), (164, 184), (104, 190)]
    def plates(cid):
        s = ""
        for (x, y, rx, ry) in [(104, 128, 20, 14), (74, 148, 14, 14), (136, 150, 14, 14), (104, 160, 18, 11)]:
            s += svg_fill(T(ellipse_pts(x, y, rx, ry, n=8, wob=0.08, seed=x), p), k["plate"])
        s += svg_fill(T([(30, 176), (200, 176), (200, 200), (30, 200)], p), k["rim"])
        return s
    c.part(C(shell, p), k["shell"], k["line"], k["shell_sh"], 3.2, 6.6, seed=74, shade_off=8, extra=plates,
           hl=(T([(66, 140), (80, 122), (100, 114)], p), "#C9FFE6"), hl_w=4.5)
    limb(c, p, (142, 188), 18, ba, 18, k["fill"], k["line"], k["shade"], seed=75)
    limb(c, p, (82, 190), 18, bb, 18, k["fill"], k["line"], k["shade"], seed=76)
    Th = lambda pts: TH(p)(xform(pts, ox=124, oy=150))
    neck = [(150, 150), (160, 128), (176, 132), (180, 164), (160, 172)]
    c.part(crom(Th(neck), True, 8), k["fill"], k["line"], k["shade"], 2.6, 5, seed=77, shade_off=5)
    head = [(140, 104), (150, 78), (176, 64), (206, 70), (224, 94), (222, 124), (204, 142), (174, 146), (150, 134)]
    c.part(crom(Th(head), True, 14), k["fill"], k["line"], k["shade"], 3.0, 6.6, seed=78, shade_off=8,
           hl=(Th([(154, 96), (162, 80), (178, 72)]), k["hl"]), hl_w=4.5)
    face(c, p, k, (180, 100), (212, 96), 22, (206, 124), (182, 122), Tf=Th, mw=0.9)


# =====================================================================
# 5. 로켓: 크림 몸 + 산호색 코·날개, 엔진 불꽃은 앱 강조색 주황 #FF9F0A
# =====================================================================
RKT = dict(fill="#FFF4E4", shade="#EBCDB8", line="#8C3A34", coral="#FF6A58", coral_sh="#D94640",
           cheek="#FF8C8C", iris="#2E1A22", iris_lo="#8A4A5A", flame="#FF9F0A", flame_in="#FFE15A", hl="#FFFFFF")


def draw_rocket(c, p=None):
    p = dict(dict(lean=-14, mood="bright", mouth="open", flame=1.0, ox=124, oy=124), **(p or {}))
    k = RKT
    R = lambda pts: xform(pts, dx=p.get("dx", 0), dy=p.get("dy", 0), rot=p["lean"], ox=124, oy=124)
    f = p["flame"]
    fl = [(70, 112), (52, 104 - 4 * f), (30, 112 - 6 * f), (14 - 10 * f, 122), (30, 132 + 6 * f), (52, 140 + 4 * f),
          (70, 132)]
    c.part(crom(R(fl), True, 10), k["flame"], "#C0560A", None, 2.2, 4.4, seed=81)
    c.fill(crom(R([(70, 116), (48, 114), (34 - 6 * f, 122), (48, 130), (70, 128)]), True, 8), k["flame_in"])
    # 먼 날개(위)
    fin_top = [(84, 96), (72, 70), (88, 64), (112, 92)]
    c.part(crom(R(fin_top), True, 8), k["coral_sh"], k["line"], None, 2.6, 5, seed=82)
    body = [(64, 122), (72, 98), (110, 86), (156, 88), (192, 104), (210, 122), (192, 140), (156, 156), (110, 158),
            (72, 146)]
    def nose(cid):
        return (svg_fill(R([(176, 70), (240, 70), (240, 180), (176, 180), (182, 150), (186, 122), (182, 94)]),
                         k["coral"]) +
                svg_fill(R([(84, 70), (94, 70), (96, 180), (86, 180)]), k["coral"]))
    c.part(crom(R(body), True, 14), k["fill"], k["line"], k["shade"], 3.2, 7, seed=83, shade_off=9, extra=nose,
           hl=(R([(90, 102), (120, 94), (150, 94)]), k["hl"]), hl_w=5)
    fin_bot = [(80, 150), (66, 178), (86, 180), (114, 152)]
    c.part(crom(R(fin_bot), True, 8), k["coral"], k["line"], k["coral_sh"], 2.6, 5.4, seed=84, shade_off=4)
    face(c, p, k, (132, 120), (164, 116), 23, (152, 138), (126, 140), Tf=R, mw=0.9)


# =====================================================================
# 6. 종이비행기: 흰 종이 + 푸른 색선, 접힌 날개 면에 얼굴
# =====================================================================
PLN = dict(fill="#F7F9FF", shade="#CFDAF4", line="#3B5CA6", keel="#DCE5FA", keel_sh="#B3C4EC", cheek="#FF9AAE",
           iris="#1E2440", iris_lo="#5A6AA8", hl="#FFFFFF")


def draw_plane(c, p=None):
    p = dict(dict(lean=-6, mood="happy", mouth="open", flap=0), **(p or {}))
    k = PLN
    R = lambda pts: xform(pts, dx=p.get("dx", 0), dy=p.get("dy", 0), rot=p["lean"], ox=124, oy=124)
    fp = p["flap"]
    far_w = [(58, 70 - fp), (120, 98), (214, 128), (150, 104), (70, 62 - fp)]
    c.part(crom(R(far_w), True, 8), k["keel"], k["line"], None, 2.2, 4.4, seed=91)
    keel = [(76, 150), (214, 128), (116, 186), (94, 182)]
    c.part(crom(R(keel), True, 8), k["keel"], k["line"], k["keel_sh"], 2.6, 5.6, seed=92, shade_off=5)
    wing = [(34, 80 + fp), (50, 84 + fp), (216, 126), (206, 134), (84, 160), (66, 154)]
    c.part(crom(R(wing), True, 10), k["fill"], k["line"], k["shade"], 3.0, 6.6, seed=93, shade_off=8,
           hl=(R([(70, 104), (110, 114), (150, 120)]), "#FFFFFF"), hl_w=4)
    face(c, p, k, (110, 122), (142, 120), 24, (130, 140), (96, 140), Tf=R, mw=0.9)


# =====================================================================
# 7. 열기구: 산호·노랑 줄무늬 풍선에 얼굴, 아래에 작은 바구니
# =====================================================================
BAL = dict(fill="#FFD24D", shade="#F0A830", line="#97372C", coral="#FF6E5E", coral_sh="#DA4A40",
           basket="#E8A25A", basket_sh="#C27A3A", cheek="#FF7F6E", iris="#2E1A16", iris_lo="#8A4A3A", hl="#FFF6D6")


def draw_balloon(c, p=None):
    p = dict(dict(lean=4, mood="bright", mouth="smile", sway=0), **(p or {}))
    k = BAL
    R = lambda pts: xform(pts, dx=p.get("dx", 0), dy=p.get("dy", 0), rot=p["lean"], ox=120, oy=120)
    sw = p["sway"]
    # 줄
    for a, b in [((98, 160), (106 + sw, 186)), ((142, 160), (134 + sw, 186))]:
        c.stroke(R([a, b]), k["line"], 2.4, taper=(0, 0), seed=101)
    bk = [(100 + sw, 184), (140 + sw, 184), (136 + sw, 210), (104 + sw, 210)]
    weave = svg_fill(R([(96 + sw, 192), (150 + sw, 192), (150 + sw, 196), (96 + sw, 196)]), k["basket_sh"])
    c.part(crom(R(bk), True, 4), k["basket"], "#7A3E18", k["basket_sh"], 2.6, 5, seed=102, shade_off=4,
           extra=lambda cid: weave)
    env = [(120, 26), (160, 36), (186, 72), (184, 112), (160, 148), (138, 166), (102, 166), (80, 148), (56, 112),
           (54, 72), (80, 36)]
    def stripes(cid):
        s = ""
        for x0 in (64, 118, 172):
            s += svg_fill(R([(x0 - 2, 20), (x0 + 14, 20), (x0 + 6 + (x0 - 120) * 0.15, 170),
                              (x0 - 8 + (x0 - 120) * 0.15, 170)]), k["coral"])
        return s
    c.part(crom(R(env), True, 16), k["fill"], k["line"], k["shade"], 3.2, 7, seed=103, shade_off=10, extra=stripes,
           hl=(R([(72, 86), (82, 60), (104, 44)]), k["hl"]), hl_w=5)
    face(c, p, k, (110, 104), (146, 102), 24, (128, 128), (98, 126), Tf=R)


# =====================================================================
# 8. 기차: 하늘색 보일러 + 산호색 기관실, 얼굴은 앞면이 아닌 보일러 옆(유명 기차 캐릭터와 갈라 둠)
# =====================================================================
TRN = dict(fill="#5CCBE0", shade="#2FA2BF", line="#1B5670", cab="#FF6E5E", cab_sh="#D94A42", wheel="#FFC94A",
           wheel_sh="#E39A22", cheek="#FF8C9A", iris="#14263A", iris_lo="#3F6E92", hl="#D8F6FF", smoke="#F2F5F8",
           smoke_sh="#C9D3DE")


def draw_train(c, p=None):
    p = dict(dict(lean=0, mood="bright", mouth="open", puff=0, wheel=0), **(p or {}))
    k = TRN
    R = lambda pts: T(pts, p)
    pf = p["puff"] % 1.0
    # 연기 3개가 굴뚝에서 왼쪽 위로 흘러가며 커진다. 위상 pf(0~1)가 1/3 씩 어긋나 4장 반복이 끊기지 않는다.
    for i in range(3):
        u = (pf + i) / 3.0  # 0(막 나옴) → 1(사라짐)
        if u < 0.06:
            continue
        x = 166 - u * 70 * p.get("drift", 1); y = 70 - u * 52 * p.get("rise", 1)
        r = (6 + u * 12) * (1 - max(0, u - 0.8) * 2.5) * p.get("psize", 1)
        if r < 2:
            continue
        c.part(crom(R(ellipse_pts(x, y, r, r * 0.88, n=8, wob=0.1, seed=i)), True, 8), k["smoke"], k["smoke_sh"],
               None, 1.8, 3.4, seed=110 + i)
    chim = [(158, 92), (154, 66), (178, 66), (174, 92)]
    c.part(crom(R(chim), True, 4), k["cab"], k["line"], k["cab_sh"], 2.6, 5, seed=112, shade_off=4)
    cab = [(50, 96), (58, 72), (104, 70), (110, 96), (112, 176), (52, 178)]
    win = svg_fill(crom(R([(64, 86), (98, 86), (98, 112), (64, 112)]), True, 4), "#FFF2D8")
    c.part(crom(R(cab), True, 6), k["cab"], k["line"], k["cab_sh"], 3.0, 6.4, seed=113, shade_off=7,
           extra=lambda cid: win)
    boil = [(100, 104), (150, 92), (190, 98), (206, 124), (204, 162), (186, 178), (104, 178)]
    band = svg_fill(R([(96, 166), (220, 166), (220, 190), (96, 190)]), k["shade"])
    c.part(crom(R(boil), True, 10), k["fill"], k["line"], k["shade"], 3.2, 7, seed=114, shade_off=9,
           extra=lambda cid: band, hl=(R([(114, 112), (140, 102), (168, 100)]), k["hl"]), hl_w=5)
    a = math.radians(p["wheel"])
    for i, (x, r) in enumerate([(78, 18), (136, 16), (180, 16)]):
        W = crom(R(ellipse_pts(x, 192, r, r, n=10)), True, 6)
        hub = svg_fill(R(ellipse_pts(x + math.cos(a + i) * r * 0.45, 192 + math.sin(a + i) * r * 0.45, r * 0.22,
                                     r * 0.22, n=8)), k["wheel_sh"])
        c.part(W, k["wheel"], "#8A4A10", k["wheel_sh"], 2.6, 5, seed=115 + i, shade_off=4, extra=lambda cid: hub)
    face(c, p, k, (148, 130), (184, 126), 24, (170, 152), (138, 152), Tf=R)


CHARS = {"dog": draw_dog, "rabbit": draw_rabbit, "squirrel": draw_squirrel, "turtle": draw_turtle,
         "rocket": draw_rocket, "plane": draw_plane, "balloon": draw_balloon, "train": draw_train}
