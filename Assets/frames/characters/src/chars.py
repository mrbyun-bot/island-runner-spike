# 무료 3종 캐릭터 형태 정의 (B 윤곽선 스티커, 2026-11-28 확정판)
# 좌표계: 108x108. @3x 기준 1단위 = 1 물리 픽셀. 240px 판은 같은 좌표를 늘려 뽑는다.
# 아일랜드 축소 칸은 위아래가 약 15px씩 잘린다 → 눈·입 등 핵심은 y 15~93 안.
# 1라운드 시안(art-round1 브랜치 art/round1/B_sticker/src/chars.py)의 형태와 색을 그대로 이어받고,
# 움직이는 부위를 묶는 그룹 이름(grp)을 더했다.

P = dict(
    ham_fur="#FFC27A", ham_cream="#FFF1DC", ham_ear="#FFB066",
    pink="#FF9EAA", blush="#FF8FA3", nose="#FF7A90",
    eye="#2B1E16",
    ring="#7BE0C3", spoke="#BFEFE0", hub="#FFF1DC",
    pen_back="#6E7FA8", pen_belly="#FFFFFF",
    beak="#FFA94D", scarf="#7BE0C3",
    rk_body="#F7F3FF", rk_nose="#FF8FB1", rk_fin="#7BE0C3",
    flame="#FF9F0A", flame_in="#FFD66B",
)
LINE = "#3A2417"     # 윤곽선: 순검정 대신 따뜻한 짙은 갈색
BORDER = "#FFF4E2"   # 바깥 크림 테: 순수 검정 위에서 실루엣을 떼어 냄

# 부위: (id, 모양, 칠, 역할, 그룹)
#  모양: ("circle", cx, cy, r) / ("ellipse", cx, cy, rx, ry) / ("path", d)
#  역할: sil = 바깥 테·윤곽에 들어감, line = 안쪽 선을 그림
#  그룹: 포즈에서 같이 움직이는 묶음(head, body, feet 등)
HAMSTER = [
    ("ear_l", ("circle", 49, 47.5, 6.8), "ham_ear", "sil line", "head"),
    ("ear_r", ("circle", 74, 45.5, 6.8), "ham_ear", "sil line", "head"),
    ("ear_l_in", ("circle", 49.6, 48.6, 3.6), "pink", "", "head"),
    ("ear_r_in", ("circle", 73.4, 46.6, 3.6), "pink", "", "head"),
    ("foot_b", ("ellipse", 41, 88.4, 5, 3), "pink", "sil line", ""),
    ("body", ("path", "M24 76 C22 63 33 55 46 55 L60 56 C70 60 72 80 66 86 C60 90 36 90 30 88 C26 86 24 82 24 76 Z"), "ham_fur", "sil line", "body"),
    ("head", ("circle", 63, 64, 20), "ham_fur", "sil line", "head"),
    ("mask", ("path", "M48 70 C50 62 58 61 63.5 63 C69 61 77 62 79 70 C80 78 72 83.5 63.5 83.5 C55 83.5 47 78 48 70 Z"), "ham_cream", "", "head"),
    ("foot_f", ("ellipse", 60, 88.4, 5, 3), "pink", "sil line", ""),
    ("paw_l", ("ellipse", 58, 82.5, 3.2, 2.4), "ham_cream", "line", "head"),
    ("paw_r", ("ellipse", 69, 82.5, 3.2, 2.4), "ham_cream", "line", "head"),
]
HAMSTER_FACE = dict(grp="head", eyes=[(55.5, 67, 4.4), (71.5, 67, 4.4)],
                    blush=[(49.5, 74, 3.8, 2.4), (77.5, 74, 3.8, 2.4)],
                    nose=(63.5, 71.8, 1.7, 1.2), mouth="M60.8 74.2 Q62.2 75.8 63.5 74.4 Q64.8 75.8 66.2 74.2",
                    hl="M51 50.5 Q56 46.5 62 46.3")

PENGUIN = [
    ("foot_l", ("ellipse", 44, 89.5, 7.5, 3.6), "beak", "sil line", ""),
    ("foot_r", ("ellipse", 65, 89.5, 7.5, 3.6), "beak", "sil line", ""),
    ("flip_l", ("path", "M31 56 C22 62 19 72 22 79 C27 76 31 70 33 64 Z"), "pen_back", "sil line", "body"),
    ("flip_r", ("path", "M77 56 C86 62 89 72 86 79 C81 76 77 70 75 64 Z"), "pen_back", "sil line", "body"),
    ("body", ("path", "M54 24 C72 24 81 40 81 58 C81 77 70 90 54 90 C38 90 27 77 27 58 C27 40 36 24 54 24 Z"), "pen_back", "sil line", "body"),
    ("tuft", ("path", "M51 25.5 C50 20 54 17 58.5 19 C55.5 19.8 54.6 22 55.6 25 Z"), "pen_back", "sil line", "body"),
    ("belly", ("path", "M54 40 C58 34 70 34 72 44 C75 56 74 72 67 81 C63 86 45 86 41 81 C34 72 33 56 36 44 C38 34 50 34 54 40 Z"), "pen_belly", "line", "body"),
    ("scarf", ("path", "M33 63 C45 69 63 69 75 63 L76 69 C63 75 45 75 32 69 Z"), "scarf", "line", "body"),
    ("scarf_tail", ("path", "M62 71 L70 70 L69 81 L63 79 Z"), "scarf", "line", "body"),
]
PENGUIN_FACE = dict(grp="body", eyes=[(46, 52.5, 4.3), (62, 52.5, 4.3)],
                    blush=[(40, 59, 3.6, 2.3), (68, 59, 3.6, 2.3)],
                    beak="M50 56.5 Q54 54.5 58 56.5 Q56 61 54 61 Q52 61 50 56.5 Z",
                    hl="M41.5 35.5 Q45.8 31 51.5 30.4")


def flame_path(L, ty, half, x0=27.0, cy=54.0, fork=0.0):
    """로켓 불꽃: 뿌리 x0, 길이 L, 끝 높이 흔들림 ty, 뿌리 반폭 half.
    fork>0 이면 끝이 두 갈래로 갈라진다(일렁임 단계 표현)."""
    tip = x0 - L
    a, b = cy - half, cy + half
    if fork <= 0:
        return (f"M{x0} {a:.2f} C{x0 - L * .4:.2f} {a - half * .45:.2f} {x0 - L * .86:.2f} {cy - half * .6 + ty * .5:.2f} "
                f"{tip:.2f} {cy + ty:.2f} C{x0 - L * .86:.2f} {cy + half * .6 + ty * .5:.2f} {x0 - L * .4:.2f} {b + half * .45:.2f} {x0} {b:.2f} Z")
    # 두 갈래: 위 끝(tip, cy+ty-fork) 과 아래 끝(tip+fork*1.4, cy+ty+fork) 사이가 안으로 파임
    t1y, t2x, t2y = cy + ty - fork, tip + fork * 1.4, cy + ty + fork
    return (f"M{x0} {a:.2f} C{x0 - L * .4:.2f} {a - half * .45:.2f} {x0 - L * .86:.2f} {t1y - half * .35:.2f} {tip:.2f} {t1y:.2f} "
            f"Q{tip + L * .28:.2f} {cy + ty:.2f} {t2x:.2f} {t2y:.2f} "
            f"C{x0 - L * .7:.2f} {cy + half * .7 + ty * .4:.2f} {x0 - L * .4:.2f} {b + half * .45:.2f} {x0} {b:.2f} Z")


ROCKET = [
    ("flame_o", ("path", flame_path(22, 0, 8)), "flame", "sil line", "flame"),
    ("flame_i", ("path", flame_path(14, 0, 5)), "flame_in", "", "flame"),
    ("fin_t", ("path", "M33 40 L27 28 C36 26 45 31 49 40 Z"), "rk_fin", "sil line", "ship"),
    ("fin_b", ("path", "M33 68 L27 80 C36 82 45 77 49 68 Z"), "rk_fin", "sil line", "ship"),
    ("body", ("path", "M28 44 C28 40 31 38 35 38 L66 38 C80 39 93 46 97 54 C93 62 80 69 66 70 L35 70 C31 70 28 68 28 64 Z"), "rk_body", "sil line", "ship"),
    ("nose", ("path", "M74 39.2 C84 41.5 93 47 97 54 C93 61 84 66.5 74 68.8 C77 60 77 48 74 39.2 Z"), "rk_nose", "line", "ship"),
]
ROCKET_FACE = dict(grp="ship", eyes=[(50, 54, 4.2), (64, 54, 4.2)],
                   blush=[(44.5, 60.5, 3.4, 2.2), (69.5, 60.5, 3.4, 2.2)],
                   mouth="M54.5 60 Q57 63 59.5 60", hl="M38 42.4 L56 42.4")

CHARS = {"hamster": (HAMSTER, HAMSTER_FACE), "penguin": (PENGUIN, PENGUIN_FACE), "rocket": (ROCKET, ROCKET_FACE)}
