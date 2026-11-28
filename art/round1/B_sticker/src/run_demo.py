"""달리기 4장 루프 시범(B 확대 구도). 사용: python3 run_demo.py <B|C> <출력 폴더>
원칙: 1 착지(눌림) → 2 박차기(늘어남·예비 동작 끝) → 3 공중(가장 높음, 극단 포즈) → 4 내려옴
살 3갈래는 120도마다 같은 모양이라 4장 x 30도 = 한 주기. 햄스터가 오른쪽으로 달리면 바닥이 뒤로 밀리므로 바퀴는 시계 방향으로 돈다.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vector import char_svg
POSES = [
    dict(angle=-30, sx=1.05, sy=0.94, dy=0.0, ff=3, fb=-3, ex=0.0, ey=1.2, px=1.0, py=0.6),    # 1 착지: 눌림, 귀가 늦게 내려옴
    dict(angle=0, sx=0.97, sy=1.05, dy=-1.2, ff=6, fb=-6, ex=0.0, ey=0.6, px=2.0, py=-0.6),  # 2 박차기: 늘어남, 다리 벌림
    dict(angle=30, sx=1.0, sy=1.02, dy=-2.4, ff=1, fb=1, ffy=-1.5, fby=-1.5, ex=0.0, ey=-0.8, px=0.0, py=-1.0),  # 3 공중: 가장 높음, 다리 모음
    dict(angle=60, sx=1.02, sy=0.98, dy=-1.0, ff=-3, fb=3, ex=0.0, ey=-0.2, px=-1.0, py=0.0),  # 4 내려옴: 다리 바꿔 딛기
]
style, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
for i, p in enumerate(POSES, 1):
    for sz in (108, 240):
        open(os.path.join(out, f"hamster_run_{i}_{sz}.svg"), "w").write(char_svg("hamster", style, sz, zoom=True, pose=p))
