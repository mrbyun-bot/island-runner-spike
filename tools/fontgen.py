#!/usr/bin/env python3
"""깜빡임 마스크 폰트 2개를 만든다 (fontTools, 리눅스에서 실행).

실행:  python3 tools/fontgen.py            # Fonts/IRMaskEven.ttf, Fonts/IRMaskOdd.ttf 생성 + 검사
       python3 tools/fontgen.py --check    # 만들지 않고 있는 파일만 검사

설계
- IRMaskEven: 짝수 숫자(0 2 4 6 8) = 칸 전체를 채운 사각형, 홀수 숫자 = 빈 글리프.
- IRMaskOdd : 반대.
- 숫자는 모두 폭 1000(1em). 앱에서 글자 크기 = 칸 크기(36pt)로 쓰고 오른쪽 정렬 후 잘라 내면
  마지막 숫자 한 칸만 남는다. 콜론·공백 등 숫자 아닌 글자는 폭 0, 빈 글리프.
- 숫자 아닌 글자를 cmap 에 넣는 이유: 폰트에 없는 글자는 iOS 가 다른 폰트로 대신 그려서
  마스크에 구멍이 뚫릴 수 있다. 그래서 타이머에 나올 만한 글자를 모두 "빈 글리프"로 받는다.
- 지역 설정에 따라 숫자가 아라비아-인도 숫자 등으로 나올 수 있어 그 숫자들도 같은 짝홀로 넣었다.
- 격자 fps(8, 12)는 폰트와 관계없다. 12fps 용 폰트는 따로 만들지 않는다(tools/schedule.py --json 의 font.note).
- 외부 글꼴을 쓰지 않는다. 사각형 하나만 직접 그린다.
"""
import io
import json
import os
import subprocess
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "Fonts")
UPM = 1000
ASCENT, DESCENT = 800, -200          # 줄 높이 = 1000 = 글자 크기
FILL_Y = (-1000, 1800)               # 세로는 넉넉히 채운다(앱에서 칸 높이로 잘라 냄)
FAMILIES = {"IRMaskEven": "even", "IRMaskOdd": "odd"}

# 숫자 묶음: (이름 접두, 0 의 코드포인트)
DIGIT_SETS = [
    ("d", 0x0030),        # ASCII 0-9
    ("ar", 0x0660),       # 아라비아-인도 숫자
    ("fa", 0x06F0),       # 확장 아라비아-인도 숫자
    ("dv", 0x0966),       # 데바나가리 숫자
    ("fw", 0xFF10),       # 전각 숫자
]
# 폭 0 빈 글리프로 받을 글자: ASCII 인쇄 가능 문자 중 숫자 아닌 것 + 타이머에 나올 수 있는 공백·기호
BLANK_EXTRA = [0x00A0, 0x2007, 0x2008, 0x2009, 0x200A, 0x200B, 0x202F, 0x2212, 0x2236, 0xFF1A, 0x066B, 0x066C,
               0x200E, 0x200F, 0x061C, 0x2066, 0x2067, 0x2068, 0x2069]


def blank_codepoints():
    cps = [c for c in range(0x20, 0x7F) if not (0x30 <= c <= 0x39)]
    return cps + BLANK_EXTRA


def build(family, parity):
    glyph_order = [".notdef", "blank", "fill_digit", "empty_digit"]
    cmap = {}
    for prefix, zero in DIGIT_SETS:
        for d in range(10):
            filled = (d % 2 == 0) == (parity == "even")
            cmap[zero + d] = "fill_digit" if filled else "empty_digit"
    for cp in blank_codepoints():
        cmap[cp] = "blank"

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)

    def empty():
        return TTGlyphPen(None).glyph()

    pen = TTGlyphPen(None)
    x0, x1 = 0, UPM
    y0, y1 = FILL_Y
    pen.moveTo((x0, y0)); pen.lineTo((x0, y1)); pen.lineTo((x1, y1)); pen.lineTo((x1, y0)); pen.closePath()
    glyphs = {".notdef": empty(), "blank": empty(), "fill_digit": pen.glyph(), "empty_digit": empty()}
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({".notdef": (0, 0), "blank": (0, 0), "fill_digit": (UPM, 0), "empty_digit": (UPM, 0)})
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT, lineGap=0)
    fb.setupNameTable({
        "familyName": family,
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{family}-spike-1",
        "fullName": family,
        "psName": family,
        "version": "Version 1.000",
        "copyright": "Island Runner spike, original mask font (no third-party outlines)",
    })
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT, sTypoLineGap=0,
                usWinAscent=FILL_Y[1], usWinDescent=-FILL_Y[0], fsType=0)
    fb.setupPost()
    font = fb.font
    # 같은 입력이면 같은 파일이 나오게 시각 고정 (2026-11-27 00:00 UTC, 1904 기준 초)
    fixed = 3847219200
    font["head"].created = fixed
    font["head"].modified = fixed
    font.recalcTimestamp = False
    path = os.path.join(OUT_DIR, f"{family}.ttf")
    font.save(path)
    return path


def load_schedule():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "schedule.py"), "--json"],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def ttx_dump(path):
    """ttx 로 cmap·hmtx·GlyphOrder 를 XML 로 덤프한다 (fontTools.ttx, ttx 명령과 같음)."""
    xml_path = path[:-4] + ".ttx"
    subprocess.run([sys.executable, "-m", "fontTools.ttx", "-q", "-o", xml_path, "-t", "cmap", "-t", "hmtx",
                    "-t", "GlyphOrder", "-t", "name", path], check=True)
    return xml_path


def check(path, parity, schedule):
    font = TTFont(path)
    problems = []
    order = font.getGlyphOrder()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"].metrics
    filled_expected = set(schedule["font"]["filled_digits"][parity])
    for prefix, zero in DIGIT_SETS:
        for d in range(10):
            g = cmap.get(zero + d)
            want = "fill_digit" if d in filled_expected else "empty_digit"
            if g != want:
                problems.append(f"U+{zero + d:04X} -> {g}, 기대 {want}")
    for cp in blank_codepoints():
        if cmap.get(cp) != "blank":
            problems.append(f"U+{cp:04X} 가 빈 글리프가 아님")
    if hmtx["fill_digit"][0] != UPM or hmtx["empty_digit"][0] != UPM or hmtx["blank"][0] != 0:
        problems.append(f"폭이 틀림: {hmtx}")
    glyf = font["glyf"]
    fill = glyf["fill_digit"]
    if (fill.xMin, fill.xMax) != (0, UPM):
        problems.append(f"채움 사각형 가로 범위 {fill.xMin}..{fill.xMax}")
    for g in (".notdef", "blank", "empty_digit"):
        if glyf[g].numberOfContours != 0:
            problems.append(f"{g} 가 비어 있지 않음")
    ps = font["name"].getDebugName(6)
    size = os.path.getsize(path)
    ttx = ttx_dump(path)
    print(f"{os.path.relpath(path, ROOT)}: PostScript 이름 {ps}, 글리프 {len(order)}개 {order}, "
          f"cmap {len(cmap)}개 (채움 {sum(1 for v in cmap.values() if v == 'fill_digit')}, "
          f"빈 숫자 {sum(1 for v in cmap.values() if v == 'empty_digit')}, 폭 0 {sum(1 for v in cmap.values() if v == 'blank')}), "
          f"파일 {size} 바이트, ttx 덤프 {os.path.relpath(ttx, ROOT)}")
    if size > 100 * 1024:
        problems.append(f"파일이 100KB 초과: {size}")
    if ps != os.path.basename(path)[:-4]:
        problems.append(f"PostScript 이름 {ps} 가 파일 이름과 다름")
    return problems


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    schedule = load_schedule()
    used = schedule["font"]["parities_used"]
    paths = {}
    for family, parity in FAMILIES.items():
        path = os.path.join(OUT_DIR, f"{family}.ttf")
        if "--check" not in sys.argv:
            path = build(family, parity)
        paths[family] = (path, parity)
    all_problems = []
    for family, (path, parity) in paths.items():
        if parity not in used:
            print(f"주의: {family} 는 schedule 에서 쓰지 않음")
        all_problems += [f"{family}: {p}" for p in check(path, parity, schedule)]
    missing = [p for p in used if p not in FAMILIES.values()]
    if missing:
        all_problems.append(f"schedule 이 쓰는데 폰트가 없는 짝홀: {missing}")
    print("schedule.py 가 요구한 짝홀:", used, "-> 만든 폰트:", list(FAMILIES))
    if all_problems:
        print("검사 실패:")
        for p in all_problems:
            print("  -", p)
        return 1
    print("검사 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
