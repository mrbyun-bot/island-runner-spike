#!/usr/bin/env python3
"""그림 파일 점검. Shared/ArtSet.swift 가 돌려주는 이름과 같은 목록을 만들어 실제 파일과 대조한다.

  python3 tools/check_art_files.py            새 캐릭터 3종 + 옛 hamster·shape 모두 점검
  python3 tools/check_art_files.py penguin    한 가지만 (hamster2 penguin rocket hamster shape)

없는 파일, 크기가 다른 파일(작은 것 108×108, _L 240×240), 번들에서 겹치는 파일 이름이 있으면 종료 코드 1.
(번들에는 하위 폴더 구조 없이 평평하게 복사되므로 폴더가 달라도 이름이 같으면 충돌한다.)
ArtSet.swift 와 이름 규칙이 어긋나지 않게, 아래 규칙을 바꾸면 Swift 쪽과 Tests/FrameScheduleTests.swift 도 같이 바꾼다.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAMES = ROOT / "Assets" / "frames"
CHAR_DIR = FRAMES / "characters"
CHAR_PREFIX = {"hamster2": "hamster", "penguin": "penguin", "rocket": "rocket"}
ALL_ARTS = ["hamster2", "penguin", "rocket", "hamster", "shape"]
SMALL, LARGE = 108, 240


def required(art):
    """{파일 이름(확장자·@3x 없이): (찾을 폴더, 기대 크기)}"""
    out = {}
    if art in CHAR_PREFIX:
        p = CHAR_PREFIX[art]
        for suffix, px in (("", SMALL), ("_L", LARGE)):
            for i in range(1, 5):
                out[f"{p}_run_{i}{suffix}"] = (CHAR_DIR, px)
            for i in range(1, 3):
                out[f"{p}_rest_{i}{suffix}"] = (CHAR_DIR, px)
            out[f"{p}_still{suffix}"] = (CHAR_DIR, px)
    elif art == "hamster":
        names = [f"hamsterold_run_{i}" for i in range(1, 5)] + ["hamsterold_rest_1", "hamsterold_rest_2",
                                                                 "hamsterold_still", "hamsterold_bg"]
        for n in names:
            out[n] = (FRAMES, SMALL)
    elif art == "shape":
        for i in range(1, 5):
            out[f"shape_{i}"] = (FRAMES, SMALL)
    else:
        raise SystemExit(f"모르는 art: {art}")
    return out


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def bundle_names():
    """번들에 들어가는 PNG(src/, preview-*.png 제외)의 이름 → 경로 목록"""
    seen = {}
    for p in sorted(FRAMES.rglob("*@3x.png")):
        rel = p.relative_to(FRAMES)
        if rel.parts[0] == "src" or p.name.startswith("preview-"):
            continue
        seen.setdefault(p.name, []).append(rel)
    return seen


def main(argv):
    arts = argv or ALL_ARTS
    problems = []
    for art in arts:
        for name, (folder, px) in sorted(required(art).items()):
            path = folder / f"{name}@3x.png"
            if not path.exists():
                problems.append(f"[{art}] 없음: {path.relative_to(ROOT)}")
                continue
            size = png_size(path)
            if size is None:
                problems.append(f"[{art}] PNG 아님: {path.relative_to(ROOT)}")
            elif size != (px, px):
                problems.append(f"[{art}] 크기 {size[0]}×{size[1]} (기대 {px}×{px}): {path.relative_to(ROOT)}")
    for fname, paths in bundle_names().items():
        if len(paths) > 1:
            problems.append("번들에서 이름 겹침: " + fname + " ← " + ", ".join(str(p) for p in paths))
    n = sum(len(required(a)) for a in arts)
    if problems:
        print(f"실패: 문제 {len(problems)}건 (점검한 파일 {n}개)")
        for line in problems:
            print("  " + line)
        return 1
    print(f"통과: {', '.join(arts)} — 파일 {n}개 모두 있고 크기가 맞음, 이름 겹침 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
