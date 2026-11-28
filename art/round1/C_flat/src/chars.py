# 공용 캐릭터 형태 정의 (좌표계: 108x108, @3x 기준 1단위 = 1 물리 픽셀)
# 아일랜드 축소 칸은 위아래가 잘려 실제로 보이는 높이가 약 26/36 → y 15~93 안에 핵심을 둔다.
# B(스티커)와 C(면 분할)가 같은 형태를 쓰고 그리는 방식만 다르다. A(3D)는 이 비율을 Blender 로 옮겼다.

# 팔레트: 디자인 캔버스 값을 그대로 쓰고, 검정 위 대비가 모자란 펭귄 등만 밝혔다(의견서에 재검토 제안으로 적음)
P = dict(
    ham_fur="#FFC27A", ham_fur_sh="#F0A060", ham_fur_hi="#FFD9A6",
    ham_cream="#FFF1DC", ham_cream_sh="#F6D9BC",
    ham_ear="#FFB066", pink="#FF9EAA", blush="#FF8FA3", nose="#FF7A90",
    eye="#2B1E16", white="#FFFFFF",
    ring="#7BE0C3", ring_sh="#4FBFA0", spoke="#BFEFE0", hub="#FFF1DC",
    pen_back="#6E7FA8", pen_back_sh="#56658C", pen_back_hi="#8696BE",
    pen_belly="#FFFFFF", pen_belly_sh="#E4E8F2",
    beak="#FFA94D", beak_sh="#E88A2E", scarf="#7BE0C3", scarf_sh="#4FBFA0",
    rk_body="#F7F3FF", rk_body_sh="#DCD3F5", rk_nose="#FF8FB1", rk_nose_sh="#E8708F",
    rk_fin="#7BE0C3", rk_fin_sh="#4FBFA0", flame="#FF9F0A", flame_in="#FFD66B",
)

import math


def wheel(angle0=-30):
    """쳇바퀴: 테 + 살 3갈래 + 살 끝 리벳 + 축. angle0 은 첫 살의 각도(도)."""
    cx, cy, r_mid, w = 54, 54, 37.5, 5
    spokes = []
    for k in range(3):
        a = math.radians(angle0 + 120 * k)
        spokes.append((cx, cy, cx + 34 * math.cos(a), cy + 34 * math.sin(a)))
    return dict(cx=cx, cy=cy, r=r_mid, w=w, spokes=spokes)


# 각 부위: (id, 모양, 칠, 역할)
#  모양: ("circle", cx, cy, r) / ("ellipse", cx, cy, rx, ry) / ("path", d)
#  역할: sil=바깥 실루엣에 들어감, line=부위 경계에 안쪽 선을 그림(스티커), shade=면 분할 그림자(C)
HAMSTER = [
    ("ear_l", ("circle", 49, 47.5, 6.8), "ham_ear", "sil line shade"),
    ("ear_r", ("circle", 74, 45.5, 6.8), "ham_ear", "sil line shade"),
    ("ear_l_in", ("circle", 49.6, 48.6, 3.6), "pink", ""),
    ("ear_r_in", ("circle", 73.4, 46.6, 3.6), "pink", ""),
    ("foot_b", ("ellipse", 41, 88.4, 5, 3), "pink", "sil line"),
    ("body", ("path", "M24 76 C22 63 33 55 46 55 L60 56 C70 60 72 80 66 86 C60 90 36 90 30 88 C26 86 24 82 24 76 Z"), "ham_fur", "sil line shade"),
    ("head", ("circle", 63, 64, 20), "ham_fur", "sil line shade"),
    ("mask", ("path", "M48 70 C50 62 58 61 63.5 63 C69 61 77 62 79 70 C80 78 72 83.5 63.5 83.5 C55 83.5 47 78 48 70 Z"), "ham_cream", "shade"),
    ("foot_f", ("ellipse", 60, 88.4, 5, 3), "pink", "sil line"),
    ("paw_l", ("ellipse", 58, 82.5, 3.2, 2.4), "ham_cream", "line"),
    ("paw_r", ("ellipse", 69, 82.5, 3.2, 2.4), "ham_cream", "line"),
]
# 얼굴(눈은 낮고 넓게: 머리 지름 40 중 가운데 아래, 간격 15)
HAMSTER_FACE = dict(eyes=[(55.5, 67, 4.4), (71.5, 67, 4.4)], blush=[(49.5, 74, 3.8, 2.4), (77.5, 74, 3.8, 2.4)],
                    nose=(63.5, 71.8, 1.7, 1.2), mouth="M60.8 74.2 Q62.2 75.8 63.5 74.4 Q64.8 75.8 66.2 74.2")

PENGUIN = [
    ("foot_l", ("ellipse", 44, 89.5, 7.5, 3.6), "beak", "sil line"),
    ("foot_r", ("ellipse", 65, 89.5, 7.5, 3.6), "beak", "sil line"),
    ("flip_l", ("path", "M31 56 C22 62 19 72 22 79 C27 76 31 70 33 64 Z"), "pen_back", "sil line shade"),
    ("flip_r", ("path", "M77 56 C86 62 89 72 86 79 C81 76 77 70 75 64 Z"), "pen_back", "sil line shade"),
    ("body", ("path", "M54 24 C72 24 81 40 81 58 C81 77 70 90 54 90 C38 90 27 77 27 58 C27 40 36 24 54 24 Z"), "pen_back", "sil line shade"),
    ("tuft", ("path", "M51 25.5 C50 20 54 17 58.5 19 C55.5 19.8 54.6 22 55.6 25 Z"), "pen_back", "sil line"),
    ("belly", ("path", "M54 40 C58 34 70 34 72 44 C75 56 74 72 67 81 C63 86 45 86 41 81 C34 72 33 56 36 44 C38 34 50 34 54 40 Z"), "pen_belly", "line shade"),
    ("scarf", ("path", "M33 63 C45 69 63 69 75 63 L76 69 C63 75 45 75 32 69 Z"), "scarf", "line shade"),
    ("scarf_tail", ("path", "M62 71 L70 70 L69 81 L63 79 Z"), "scarf", "line shade"),
]
PENGUIN_FACE = dict(eyes=[(46, 52.5, 4.3), (62, 52.5, 4.3)], blush=[(40, 59, 3.6, 2.3), (68, 59, 3.6, 2.3)],
                    beak="M50 56.5 Q54 54.5 58 56.5 Q56 61 54 61 Q52 61 50 56.5 Z")

ROCKET = [
    ("flame_o", ("path", "M27 46 C18 39 9 44 5 54 C9 64 18 69 27 62 Z"), "flame", "sil line"),
    ("flame_i", ("path", "M27 49 C21 46 15 49 13 54 C15 59 21 62 27 59 Z"), "flame_in", ""),
    ("fin_t", ("path", "M33 40 L27 28 C36 26 45 31 49 40 Z"), "rk_fin", "sil line shade"),
    ("fin_b", ("path", "M33 68 L27 80 C36 82 45 77 49 68 Z"), "rk_fin", "sil line shade"),
    ("body", ("path", "M28 44 C28 40 31 38 35 38 L66 38 C80 39 93 46 97 54 C93 62 80 69 66 70 L35 70 C31 70 28 68 28 64 Z"), "rk_body", "sil line shade"),
    ("nose", ("path", "M74 39.2 C84 41.5 93 47 97 54 C93 61 84 66.5 74 68.8 C77 60 77 48 74 39.2 Z"), "rk_nose", "line shade"),
]
ROCKET_FACE = dict(eyes=[(50, 54, 4.2), (64, 54, 4.2)], blush=[(44.5, 60.5, 3.4, 2.2), (69.5, 60.5, 3.4, 2.2)],
                   mouth="M54.5 60 Q57 63 59.5 60")
