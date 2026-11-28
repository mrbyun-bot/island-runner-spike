"""포즈 표. 정지 아이콘은 각 캐릭터 기본값. 결선 2종의 달리기·쉼은 sequence 에서 정한다.

달리기 설계(8fps, 4장 한 바퀴 = 0.5초. 앱은 같은 4장을 느리게도 돌린다):
- 거북이: 대각선 다리 짝 종종걸음. 1 디딤(눌림) → 2 뜀(늘임, 다리 모음) → 3 반대 짝 디딤 → 4 뜀.
  머리는 몸보다 한 장 늦게 오르내린다(오버랩): 몸이 내려간 장에서 머리는 아직 위.
- 기차: 바퀴 허브가 장마다 90도 돈다(같은 바퀴가 4장 모두 다르게 보임), 차체는 덜컹(아래-위-아래-위)과
  앞뒤 기울기를 번갈아, 연기 3개가 1/4씩 흘러 반복 이음매가 없다.
"""
FINALISTS = ["turtle", "train"]


def still(n):
    return {}


def sequence(n):
    if n == "turtle":
        run = [
            dict(legs=((-26, 28), (32, -30)), dy=3, sq=0.95, lean=2, hdy=-3, hrot=-3, mouth="open"),
            dict(legs=((18, -12), (-12, 18)), dy=-9, sq=1.05, lean=-1, hdy=3, hrot=2, mouth="open"),
            dict(legs=((30, -26), (-28, 32)), dy=3, sq=0.95, lean=2, hdy=-3, hrot=-3, mouth="open"),
            dict(legs=((-12, 18), (18, -12)), dy=-9, sq=1.05, lean=-1, hdy=3, hrot=2, mouth="open"),
        ]
        rest = [
            dict(legs=((0, 0), (4, -4)), dy=6, sq=0.97, hdy=8, hrot=6, mood="closed", mouth="smile"),
            dict(legs=((0, 0), (4, -4)), dy=4, sq=1.01, hdy=6, hrot=4, mood="closed", mouth="smile"),
        ]
    elif n == "train":
        run = [
            dict(wheel=0, puff=0.00, dy=2, sq=0.97, lean=1.5, mouth="open"),
            dict(wheel=90, puff=0.25, dy=-5, sq=1.03, lean=-1.5, mouth="open"),
            dict(wheel=180, puff=0.50, dy=2, sq=0.97, lean=1.5, mouth="open"),
            dict(wheel=270, puff=0.75, dy=-5, sq=1.03, lean=-1.5, mouth="open"),
        ]
        rest = [
            dict(wheel=0, puff=0.15, psize=0.55, drift=0.4, rise=0.6, dy=2, sq=0.98, mood="closed", mouth="smile"),
            dict(wheel=0, puff=0.40, psize=0.6, drift=0.4, rise=0.6, dy=0, sq=1.01, mood="closed", mouth="smile"),
        ]
    else:
        raise KeyError(n)
    seq = [(f"run_{i+1}", p) for i, p in enumerate(run)]
    seq += [(f"rest_{i+1}", p) for i, p in enumerate(rest)]
    seq += [("still", still(n))]
    return seq
