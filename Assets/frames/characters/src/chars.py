# 무료 3종 캐릭터 형태 정의 (B 윤곽선 스티커)
# 좌표계: 108x108. @3x 기준 1단위 = 1 물리 픽셀. 240px 판은 같은 좌표를 늘려 뽑는다.
# 아일랜드 축소 칸은 위아래가 약 15px씩 잘린다 → 눈·입 등 핵심은 y 15~93 안.
#
# 2라운드(2026-11-28) 바뀐 점
# - 얼굴 공식을 캐릭터마다 다르게(QC Q1): 눈 모양·크기·하이라이트 수·볼터치 크기
#     햄스터: 눈꼬리가 처진 가로 타원, 하이라이트 1개(큼), 볼터치 큼          (눈 크기 기준 1.0)
#     펭귄  : 흰 눈테 안의 작은 동공(아델리펭귄의 흰 눈테에서 따옴), 하이라이트 0, 볼터치 작음 (눈테 0.9, 동공 0.55)
#     로켓  : 정원 눈, 하이라이트 2개, 볼터치 중간                            (0.88)
# - 광택 모양도 캐릭터마다 다르게(QC Q2): 햄스터 굽은 호 / 펭귄 비스듬한 타원 점 / 로켓 짧은 선+점
# - 변호사 제안: 햄스터 꿀색 털+등 반점+작은 귀, 펭귄 먼지 낀 남보라 몸+살구 코랄 부리·발+흰 배를 아래로
# - 달리기용 다리(햄스터 앞·뒤 각 2개)는 make_frames.py 가 장마다 모양을 계산해 넣는다.

P = dict(
    ham_fur="#E8A94A", ham_cream="#FFF1DC", ham_ear="#D4913A", ham_spot="#B8742F",
    ham_foot="#FFB3B8",
    pink="#FF9EAA", blush="#FF8FA3", nose="#FF7A90",
    eye="#2B1E16",
    ring="#7BE0C3", spoke="#BFEFE0", hub="#FFF1DC",
    pen_back="#7A6F9C", pen_belly="#FFFFFF", pen_ring="#FFFFFF",
    beak="#FF9A7A", scarf="#7BE0C3",
    rk_body="#F7F3FF", rk_nose="#FF8FB1", rk_fin="#7BE0C3",
    flame="#FF9F0A", flame_in="#FFD66B",
)
LINE = "#3A2417"     # 윤곽선: 순검정 대신 따뜻한 짙은 갈색
BORDER = "#FFF4E2"   # 바깥 크림 테: 순수 검정 위에서 실루엣을 떼어 냄

# 부위: (id, 모양, 칠, 역할, 그룹)
#  모양: ("circle", cx, cy, r) / ("ellipse", cx, cy, rx, ry) / ("path", d)
#  역할: sil = 바깥 테·윤곽에 들어감, line = 안쪽 선을 그림
#  그룹: 포즈에서 같이 움직이는 묶음(head, body 등). "" 은 그룹 없음(다리처럼 장마다 모양을 새로 줌)

# 햄스터: 달릴 때 다리가 보이도록 몸·머리를 땅에서 3 띄운 자리로 그렸다(쉼은 make_frames 에서 다시 내려 엎드림).
HAM_HIP_H = (38.0, 80.0)     # 뒷다리 뿌리
HAM_HIP_F = (63.0, 78.0)     # 앞다리 뿌리(턱 밑)
HAM_GROUND = 88.6            # 발 중심 높이
_EMPTY = ("ellipse", 0, 0, 0.01, 0.01)
HAMSTER = [
    ("tail", ("ellipse", 23.5, 70, 3.4, 2.4), "ham_fur", "sil line", "tail"),
    ("leg_h2", _EMPTY, "ham_fur", "sil line", ""),
    ("foot_h2", _EMPTY, "ham_foot", "sil line", ""),
    ("leg_h1", _EMPTY, "ham_fur", "sil line", ""),
    ("foot_h1", _EMPTY, "ham_foot", "sil line", ""),
    ("ear_l", ("circle", 50, 45.5, 5.6), "ham_ear", "sil line", "head"),
    ("ear_r", ("circle", 73.5, 43.5, 5.6), "ham_ear", "sil line", "head"),
    ("ear_l_in", ("path", "M46.6 46.8 A3.4 3.4 0 0 1 53.4 46.8 Z"), "pink", "", "head"),
    ("ear_r_in", ("path", "M70.1 44.8 A3.4 3.4 0 0 1 76.9 44.8 Z"), "pink", "", "head"),
    ("body", ("path", "M24 72 C22 60 33 52 46 52 L60 53 C70 57 72 76 66 82 C60 86 36 86 30 84 C26 82 24 78 24 72 Z"), "ham_fur", "sil line", "body"),
    ("spot", ("path", "M28.5 64 C29.5 57.5 36 55 42 56.5 C44.5 60 43 67 37.5 68.5 C33 69.5 28.5 68 28.5 64 Z"), "ham_spot", "", "body"),
    ("leg_f2", _EMPTY, "ham_fur", "sil line", ""),
    ("foot_f2", _EMPTY, "ham_foot", "sil line", ""),
    ("leg_f1", _EMPTY, "ham_fur", "sil line", ""),
    ("foot_f1", _EMPTY, "ham_foot", "sil line", ""),
    ("head", ("circle", 63, 61, 20), "ham_fur", "sil line", "head"),
    ("mask", ("path", "M48 67 C50 59 58 58 63.5 60 C69 58 77 59 79 67 C80 75 72 80.5 63.5 80.5 C55 80.5 47 75 48 67 Z"), "ham_cream", "", "head"),
]
HAMSTER_FACE = dict(grp="head", eye_style="droop",
                    eyes=[(55.5, 64.5, 4.4), (71.5, 64.5, 4.4)],
                    blush=[(49.0, 71.8, 4.3, 2.7), (78.0, 71.8, 4.3, 2.7)],
                    nose=(63.5, 69.3, 1.7, 1.2), mouth="M60.8 71.7 Q62.2 73.3 63.5 71.9 Q64.8 73.3 66.2 71.7",
                    hl=("arc", "M52.5 47.6 Q56.5 44.4 61.5 44.2"))

# 펭귄: 흰 배는 목도리 아래로만(얼굴은 몸색 그대로), 눈은 흰 눈테.
PENGUIN = [
    ("foot_l", ("ellipse", 44, 89.5, 7.5, 3.6), "beak", "sil line", "foot_l"),
    ("foot_r", ("ellipse", 65, 89.5, 7.5, 3.6), "beak", "sil line", "foot_r"),
    ("flip_l", ("path", "M31 54 C22 60 19 70 22 77 C27 74 31 68 33 62 Z"), "pen_back", "sil line", "body"),
    ("flip_r", ("path", "M77 54 C86 60 89 70 86 77 C81 74 77 68 75 62 Z"), "pen_back", "sil line", "body"),
    ("body", ("path", "M54 24 C72 24 81 40 81 58 C81 77 70 90 54 90 C38 90 27 77 27 58 C27 40 36 24 54 24 Z"), "pen_back", "sil line", "body"),
    ("tuft", ("path", "M51 25.5 C50 20 54 17 58.5 19 C55.5 19.8 54.6 22 55.6 25 Z"), "pen_back", "sil line", "body"),
    ("belly", ("path", "M54 63 C64 59 73 63 73.5 72 C74 81 65.5 87 54 87 C42.5 87 34 81 34.5 72 C35 63 44 59 54 63 Z"), "pen_belly", "line", "body"),
    ("scarf", ("path", "M33 56 C45 62 63 62 75 56 L76 62 C63 68 45 68 32 62 Z"), "scarf", "line", "body"),
    ("scarf_tail", ("path", "M62 64 L70 63 L69 74 L63 72 Z"), "scarf", "line", "body"),
]
PENGUIN_FACE = dict(grp="body", eye_style="ring",
                    eyes=[(47.2, 44.5, 3.9), (60.8, 44.5, 3.9)],
                    blush=[(41.2, 51.0, 2.3, 1.45), (66.8, 51.0, 2.3, 1.45)],
                    beak="M50.4 48.8 Q54 47.2 57.6 48.8 Q55.9 53.6 54 53.6 Q52.1 53.6 50.4 48.8 Z",
                    hl=("spot", 41.0, 33.5, 2.7, 1.5, -38))


def flame_path(L, ty, half, x0=27.0, cy=54.0, fork=0.0):
    """로켓 불꽃: 뿌리 x0, 길이 L, 끝 높이 흔들림 ty, 뿌리 반폭 half.
    fork>0 이면 끝이 두 갈래로 갈라진다(일렁임 단계 표현)."""
    tip = x0 - L
    a, b = cy - half, cy + half
    if fork <= 0:
        return (f"M{x0} {a:.2f} C{x0 - L * .4:.2f} {a - half * .45:.2f} {x0 - L * .86:.2f} {cy - half * .6 + ty * .5:.2f} "
                f"{tip:.2f} {cy + ty:.2f} C{x0 - L * .86:.2f} {cy + half * .6 + ty * .5:.2f} {x0 - L * .4:.2f} {b + half * .45:.2f} {x0} {b:.2f} Z")
    t1y, t2x, t2y = cy + ty - fork, tip + fork * 1.4, cy + ty + fork
    return (f"M{x0} {a:.2f} C{x0 - L * .4:.2f} {a - half * .45:.2f} {x0 - L * .86:.2f} {t1y - half * .35:.2f} {tip:.2f} {t1y:.2f} "
            f"Q{tip + L * .28:.2f} {cy + ty:.2f} {t2x:.2f} {t2y:.2f} "
            f"C{x0 - L * .7:.2f} {cy + half * .7 + ty * .4:.2f} {x0 - L * .4:.2f} {b + half * .45:.2f} {x0} {b:.2f} Z")


ROCKET = [
    ("flame_o", ("path", flame_path(22, 0, 8)), "flame", "sil line", "flame"),
    ("flame_i", ("path", flame_path(14, 0, 5)), "flame_in", "", "flame"),
    ("fin_t", ("path", "M33 40 L27 28 C36 26 45 31 49 40 Z"), "rk_fin", "sil line", "fin_t"),
    ("fin_b", ("path", "M33 68 L27 80 C36 82 45 77 49 68 Z"), "rk_fin", "sil line", "fin_b"),
    ("body", ("path", "M28 44 C28 40 31 38 35 38 L66 38 C80 39 93 46 97 54 C93 62 80 69 66 70 L35 70 C31 70 28 68 28 64 Z"), "rk_body", "sil line", "ship"),
    ("nose", ("path", "M74 39.2 C84 41.5 93 47 97 54 C93 61 84 66.5 74 68.8 C77 60 77 48 74 39.2 Z"), "rk_nose", "line", "ship"),
]
ROCKET_FACE = dict(grp="ship", eye_style="round2",
                   eyes=[(50.5, 53.5, 3.9), (63.5, 53.5, 3.9)],
                   blush=[(45.0, 60.2, 2.9, 1.8), (69.0, 60.2, 2.9, 1.8)],
                   mouth="M54.8 59.6 Q57 62.2 59.2 59.6",
                   hl=("glint", "M37 42.6 L46 42.6", (50.2, 42.6)))

CHARS = {"hamster": (HAMSTER, HAMSTER_FACE), "penguin": (PENGUIN, PENGUIN_FACE), "rocket": (ROCKET, ROCKET_FACE)}
