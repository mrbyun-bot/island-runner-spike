#!/usr/bin/env python3
"""프레임 배치 계산 (Shared/FrameSchedule.swift 와 같은 계산을 파이썬으로).

실행:  python3 tools/schedule.py            # 표 출력 + 검증, 실패하면 종료 코드 1
       python3 tools/schedule.py --json     # 계산 결과를 JSON 으로 (fontgen 검사, QC 분석용)

검증은 분수(Fraction)로 정확히 한다. 창이 바뀔 수 있는 순간은 모두 1/gridFPS 의 배수이므로
2초 주기를 1/gridFPS 칸으로 나눈 각 칸의 가운데 한 점만 보면 그 칸 전체 결과와 같다.
경계 순간 자체도 따로 본다(경계에서는 새 칸의 결과와 같아야 한다).
"""
import json
import sys
from fractions import Fraction
from math import floor

CYCLE_SECONDS = 2
# 결정 문서 "통일한 정의" 표: (이름, 한국어, 격자 fps, 프레임 수, 장당 격자 칸)
TIERS = [
    ("rest", "쉼", 8, 2, 8),
    ("normal", "보통", 8, 4, 2),
    ("fast", "빠름", 8, 4, 1),
    ("max", "최고(선택)", 12, 4, 1),
]
DESIGN_LOOP = {"rest": Fraction(2), "normal": Fraction(1), "fast": Fraction(1, 2), "max": Fraction(1, 3)}


def normalized(parity, cells, fps):
    whole = cells // fps
    if whole % 2 == 1:
        parity = "odd" if parity == "even" else "even"
    return {"offsetCells": cells % fps, "parity": parity}


def conditions(start, end, fps):
    length = end - start
    assert 0 < length <= fps, "구간이 1초보다 김"
    if length == fps:
        return [normalized("even", start, fps)]
    return [normalized("even", start, fps), normalized("odd", end, fps)]


def plan(tier):
    name, ko, fps, n, hold = TIERS[tier]
    cells_per_cycle = CYCLE_SECONDS * fps
    assert cells_per_cycle % (hold * n) == 0, "한 바퀴가 2초를 나누지 않음"
    frames = [[] for _ in range(n)]
    start = 0
    while start < cells_per_cycle:
        frame = (start // hold) % n
        end = start + 1
        while end < cells_per_cycle and (end // hold) % n == frame:
            end += 1
        frames[frame].append({"startCell": start, "endCell": end, "conditions": conditions(start, end, fps)})
        start = end
    return {"tier": tier, "name": name, "ko": ko, "gridFPS": fps, "frameCount": n, "holdCells": hold,
            "frames": frames}


def is_open(cond, fps, w):
    o = Fraction(cond["offsetCells"], fps)
    s = floor(w - o)
    even = s % 2 == 0
    return even if cond["parity"] == "even" else not even


def visible(p, w):
    fps = p["gridFPS"]
    return [i for i, cells in enumerate(p["frames"])
            if any(all(is_open(c, fps, w) for c in cell["conditions"]) for cell in cells)]


def designed(p, w):
    cell = floor(w * p["gridFPS"])
    return (cell // p["holdCells"]) % p["frameCount"]


def verify(p, cycles=3):
    """여러 주기에 걸쳐(음수 시각 포함) 칸마다 보이는 프레임을 센다."""
    fps = p["gridFPS"]
    step = Fraction(1, fps)
    overlap = Fraction(0)
    gap = Fraction(0)
    mismatch = Fraction(0)
    boundary_bad = 0
    seq = []  # (시작 시각, 프레임)
    total_cells = cycles * CYCLE_SECONDS * fps
    for k in range(-CYCLE_SECONDS * fps, total_cells):  # -2초부터: 음수 floor 처리도 확인
        mid = (k + Fraction(1, 2)) * step
        v = visible(p, mid)
        if len(v) > 1:
            overlap += step
        if len(v) == 0:
            gap += step
        if v != [designed(p, mid)]:
            mismatch += step
        if visible(p, k * step) != v:
            boundary_bad += 1
        if k >= 0 and len(v) == 1 and (not seq or seq[-1][1] != v[0]):
            seq.append((k * step, v[0]))
    holds = [seq[i + 1][0] - seq[i][0] for i in range(len(seq) - 1)]
    # 한 바퀴: 0번 프레임이 다시 시작하는 간격
    starts0 = [t for t, f in seq if f == 0]
    loops = [starts0[i + 1] - starts0[i] for i in range(len(starts0) - 1)]
    order_ok = all(seq[i + 1][1] == (seq[i][1] + 1) % p["frameCount"] for i in range(len(seq) - 1))
    return {"overlap": overlap, "gap": gap, "mismatch": mismatch, "boundary_bad": boundary_bad,
            "hold_set": sorted(set(holds)), "loop_set": sorted(set(loops)), "order_ok": order_ok}


def text_count(p):
    return sum(len(cell["conditions"]) for cells in p["frames"] for cell in cells)


def fmt(fr):
    return f"{float(fr):.4f}".rstrip("0").rstrip(".") if fr != 0 else "0"


def font_requirements(plans):
    used = sorted({c["parity"] for p in plans for cells in p["frames"] for cell in cells for c in cell["conditions"]})
    return {
        "fonts": {"even": "IRMaskEven", "odd": "IRMaskOdd"},
        "parities_used": used,
        # 폰트가 지켜야 할 것: 마지막 숫자 짝홀로 칸을 채우거나 비운다. 숫자 말고는 폭 0, 빈 글리프.
        "filled_digits": {"even": [0, 2, 4, 6, 8], "odd": [1, 3, 5, 7, 9]},
        "note": "격자 fps(8, 12)는 타이머 시작 시각에만 들어가고 폰트에는 들어가지 않는다. 12fps 용 폰트는 따로 필요 없다.",
    }


def main():
    plans = [plan(i) for i in range(len(TIERS))]
    if "--json" in sys.argv:
        print(json.dumps({"cycleSeconds": CYCLE_SECONDS, "tiers": plans, "font": font_requirements(plans)},
                         ensure_ascii=False, indent=1))
        return 0
    ok = True
    print("단계 | 격자 fps | 프레임 | 장당 격자 칸 | 장당 유지(초) | 한 바퀴(초) | 설계 한 바퀴 | 변화율(회/초) | 타이머 글자 수 | 겹침(초) | 빈 시간(초) | 설계와 다름(초) | 경계 불일치 | 순서")
    for p in plans:
        r = verify(p)
        hold = Fraction(p["holdCells"], p["gridFPS"])
        loop = hold * p["frameCount"]
        good = (r["overlap"] == 0 and r["gap"] == 0 and r["mismatch"] == 0 and r["boundary_bad"] == 0
                and r["hold_set"] == [hold] and r["loop_set"] == [loop] and loop == DESIGN_LOOP[p["name"]]
                and r["order_ok"])
        ok &= good
        print(f"{p['ko']} | {p['gridFPS']} | {p['frameCount']} | {p['holdCells']} | {fmt(hold)} | "
              f"측정 {','.join(fmt(x) for x in r['loop_set'])} | {fmt(DESIGN_LOOP[p['name']])} | "
              f"{fmt(p['frameCount'] / loop)} | {text_count(p)} | {fmt(r['overlap'])} | {fmt(r['gap'])} | "
              f"{fmt(r['mismatch'])} | {r['boundary_bad']} | {'정상' if r['order_ok'] else '틀림'}"
              f"  -> {'통과' if good else '실패'}")
    print()
    for p in plans:
        print(f"[{p['ko']}] 프레임별 구간 (2초 주기, 격자 칸 [시작, 끝) : 조건)")
        for i, cells in enumerate(p["frames"]):
            parts = []
            for cell in cells:
                cs = " ∧ ".join(f"{'짝' if c['parity'] == 'even' else '홀'}@{c['offsetCells']}" for c in cell["conditions"])
                parts.append(f"[{cell['startCell']},{cell['endCell']}) {cs}")
            print(f"  프레임 {i + 1}: " + "; ".join(parts))
    fr = font_requirements(plans)
    print()
    print(f"폰트 요구: 쓰는 짝홀 {fr['parities_used']} -> 파일 2개 {list(fr['fonts'].values())}")
    print(f"  {fr['note']}")
    print()
    print("전체:", "통과" if ok else "실패")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
