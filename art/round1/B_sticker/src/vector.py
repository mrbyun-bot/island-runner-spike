"""B(두꺼운 윤곽선 스티커)·C(윤곽선 없는 면 분할) SVG 를 같은 형태 정의로 만든다.
사용: python3 vector.py <B|C> <출력 폴더>
크기별로 선 굵기를 따로 정한다(광학 보정): 108px 판은 선을 굵게, 240px 판은 상대적으로 얇게.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chars import P, wheel, HAMSTER, HAMSTER_FACE, PENGUIN, PENGUIN_FACE, ROCKET, ROCKET_FACE

LINE = "#3A2417"     # 스티커 윤곽선: 순검정 대신 따뜻한 짙은 갈색
BORDER = "#FFF4E2"   # 스티커 바깥 테(검정 바탕에서 실루엣을 읽히게 함)


def shape_el(shape, attrs, transform=None):
    t = f' transform="{transform}"' if transform else ""
    k = shape[0]
    if k == "circle":
        return f'<circle cx="{shape[1]}" cy="{shape[2]}" r="{shape[3]}" {attrs}{t}/>'
    if k == "ellipse":
        return f'<ellipse cx="{shape[1]}" cy="{shape[2]}" rx="{shape[3]}" ry="{shape[4]}" {attrs}{t}/>'
    return f'<path d="{shape[1]}" {attrs}{t}/>'


def wheel_parts(style, sz, front=False, zoom=False, angle=-30):
    w = wheel()
    if zoom:
        # 확대 구도: 바퀴를 칸 가장자리까지 키우고(위쪽 테는 축소 칸에서 잘려도 됨) 햄스터를 1.2배
        import math as _m
        w = dict(cx=54, cy=52, r=43, w=4.5, spokes=[(54, 52, 54 + 40.5 * _m.cos(_m.radians(angle + 120 * k)), 52 + 40.5 * _m.sin(_m.radians(angle + 120 * k))) for k in range(3)])
    out = []
    if front:
        return ""
    if style == "B":
        ow = 2.6 if sz == 108 else 2.0
        out.append(f'<circle cx="{w["cx"]}" cy="{w["cy"]}" r="{w["r"]}" fill="none" stroke="{BORDER}" stroke-width="{w["w"] + 2 * ow + 3}"/>')
        out.append(f'<circle cx="{w["cx"]}" cy="{w["cy"]}" r="{w["r"]}" fill="none" stroke="{LINE}" stroke-width="{w["w"] + 2 * ow}"/>')
        for x1, y1, x2, y2 in w["spokes"]:
            out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}" stroke-width="{3 + 2 * ow * .7:.2f}" stroke-linecap="round"/>')
        out.append(f'<circle cx="{w["cx"]}" cy="{w["cy"]}" r="{w["r"]}" fill="none" stroke="{P["ring"]}" stroke-width="{w["w"]}"/>')
        for x1, y1, x2, y2 in w["spokes"]:
            out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{P["spoke"]}" stroke-width="3" stroke-linecap="round"/>')
        out.append(f'<circle cx="{w["cx"]}" cy="{w["cy"]}" r="4.6" fill="{P["hub"]}" stroke="{LINE}" stroke-width="{ow * .8:.2f}"/>')
        for x1, y1, x2, y2 in w["spokes"]:
            out.append(f'<circle cx="{x2:.2f}" cy="{y2:.2f}" r="2.6" fill="{P["hub"]}" stroke="{LINE}" stroke-width="{ow * .7:.2f}"/>')
    else:
        # C: 테 바깥쪽 아래에 짙은 면, 안쪽 위에 밝은 띠 → 원통 느낌을 선 없이
        out.append(f'<circle cx="{w["cx"]}" cy="{w["cy"]}" r="{w["r"]}" fill="none" stroke="{P["ring_sh"]}" stroke-width="{w["w"]}"/>')
        out.append(f'<circle cx="{w["cx"] - .8}" cy="{w["cy"] - 1}" r="{w["r"]}" fill="none" stroke="{P["ring"]}" stroke-width="{w["w"] - 1.2}"/>')
        for x1, y1, x2, y2 in w["spokes"]:
            out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{P["ring_sh"]}" stroke-width="3.4" stroke-linecap="round"/>')
            out.append(f'<line x1="{x1}" y1="{y1 - .5}" x2="{x2}" y2="{y2 - .5}" stroke="{P["spoke"]}" stroke-width="2.2" stroke-linecap="round"/>')
        out.append(f'<circle cx="{w["cx"]}" cy="{w["cy"]}" r="4.6" fill="{P["ring_sh"]}"/>')
        for x1, y1, x2, y2 in w["spokes"]:
            out.append(f'<circle cx="{x2:.2f}" cy="{y2:.2f}" r="2.4" fill="{P["hub"]}"/>')
        out.append(f'<circle cx="{w["cx"] - .6}" cy="{w["cy"] - .6}" r="3.4" fill="{P["hub"]}"/>')
    return "\n".join(out)


def face(fd, style, sz):
    o = []
    for (x, y, rx, ry) in fd["blush"]:
        o.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{P["blush"]}" opacity="{0.95 if style == "B" else 0.8}"/>')
    for (x, y, r) in fd["eyes"]:
        o.append(f'<ellipse cx="{x}" cy="{y}" rx="{r * .92:.2f}" ry="{r}" fill="{P["eye"]}"/>')
        o.append(f'<circle cx="{x - r * .36:.2f}" cy="{y - r * .4:.2f}" r="{r * .38:.2f}" fill="#fff"/>')
        o.append(f'<circle cx="{x + r * .34:.2f}" cy="{y + r * .38:.2f}" r="{r * .16:.2f}" fill="#fff" opacity=".9"/>')
    if "nose" in fd:
        x, y, rx, ry = fd["nose"]
        o.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{P["nose"]}"/>')
    if "beak" in fd:
        st = f' stroke="{LINE}" stroke-width="1.1"' if style == "B" else ""
        o.append(f'<path d="{fd["beak"]}" fill="{P["beak"]}"{st}/>')
        if style == "C":
            o.append(f'<path d="M52 59.2 Q54 61 56 59.2 Q55 61 54 61 Q53 61 52 59.2 Z" fill="{P["beak_sh"]}"/>')
    if "mouth" in fd and sz >= 108:
        o.append(f'<path d="{fd["mouth"]}" fill="none" stroke="{P["eye"]}" stroke-width="{1.15 if sz == 108 else 0.95}" stroke-linecap="round" stroke-linejoin="round"/>')
    return "\n".join(o)


def char_svg(name, style, sz, zoom=False, pose=None):
    parts, fd = {"hamster": (HAMSTER, HAMSTER_FACE), "penguin": (PENGUIN, PENGUIN_FACE), "rocket": (ROCKET, ROCKET_FACE)}[name]
    pose = pose or {}
    if pose:
        # 달리기 포즈: 발은 앞뒤로, 귀는 몸보다 한 박자 늦게(겹침 동작)
        def mv(sh, dx, dy):
            if sh[0] in ("circle", "ellipse"):
                return (sh[0], sh[1] + dx, sh[2] + dy) + tuple(sh[3:])
            return sh
        np_ = []
        for pid, sh, col, role in parts:
            if pid == "foot_f": sh = mv(sh, pose.get("ff", 0), pose.get("ffy", 0))
            if pid == "foot_b": sh = mv(sh, pose.get("fb", 0), pose.get("fby", 0))
            if pid.startswith("ear"): sh = mv(sh, pose.get("ex", 0), pose.get("ey", 0))
            if pid.startswith("paw"): sh = mv(sh, pose.get("px", 0), pose.get("py", 0))
            np_.append((pid, sh, col, role))
        parts = np_
    body = []
    defs = []
    K = 1.2 if zoom else 1.0
    if name == "hamster":
        body.append(wheel_parts(style, sz, zoom=zoom, angle=pose.get("angle", -30)))
        if zoom:
            # 몸 전체 스쿼시·스트레치: 발바닥(60,89)을 기준점으로 sx, sy, 위아래 dy
            sx, sy, dy = pose.get("sx", 1), pose.get("sy", 1), pose.get("dy", 0)
            body.append(f'<g transform="translate(60 {92.4 + dy}) scale({1.2 * sx:.3f} {1.2 * sy:.3f}) translate(-60 -89)">')
    if style == "B":
        ow = (2.6 if sz == 108 else 2.0) / K     # 바깥 윤곽 반폭(확대 구도면 배율만큼 줄여 화면 굵기 유지)
        iw = (1.5 if sz == 108 else 1.1) / K     # 안쪽 선
        sil = [p for p in parts if "sil" in p[3]]
        body.append('<g id="border">' + "".join(shape_el(s, f'fill="{BORDER}" stroke="{BORDER}" stroke-width="{2 * ow + 3}" stroke-linejoin="round"') for _, s, _, _ in sil) + "</g>")
        body.append('<g id="outline">' + "".join(shape_el(s, f'fill="{LINE}" stroke="{LINE}" stroke-width="{2 * ow}" stroke-linejoin="round"') for _, s, _, _ in sil) + "</g>")
        for pid, s, col, role in parts:
            st = f' stroke="{LINE}" stroke-width="{iw}" stroke-linejoin="round"' if "line" in role else ""
            body.append(f'<g id="{pid}">' + shape_el(s, f'fill="{P[col]}"{st}') + "</g>")
            # 스티커풍 하이라이트: 큰 덩어리에만 짧은 흰 호 하나(광택 대신 그림 글씨처럼)
        hl = {"hamster": "M51 50.5 Q56 46.5 62 46.3", "penguin": "M40 33 Q45 28 51 27.6", "rocket": "M38 42.4 L56 42.4"}[name]
        body.append(f'<path d="{hl}" fill="none" stroke="#fff" stroke-width="{2.2 if sz == 108 else 1.8}" stroke-linecap="round" opacity=".85"/>')
    else:
        for pid, s, col, role in parts:
            if "shade" in role:
                sh = P.get(col + "_sh", P[col]); hi = P.get(col + "_hi")
                m1 = f"m_{name}_{pid}_sh"
                # 그림자 면 = 모양 - (왼쪽 위로 민 모양) → 오른쪽 아래 초승달
                defs.append(f'<mask id="{m1}" maskUnits="userSpaceOnUse" x="0" y="0" width="108" height="108">'
                            + shape_el(s, 'fill="#fff"') + shape_el(s, 'fill="#000"', "translate(-2.6 -3.0)") + "</mask>")
                g = [shape_el(s, f'fill="{P[col]}"'), f'<g mask="url(#{m1})">' + shape_el(s, f'fill="{sh}"') + "</g>"]
                if hi:
                    m2 = f"m_{name}_{pid}_hi"
                    defs.append(f'<mask id="{m2}" maskUnits="userSpaceOnUse" x="0" y="0" width="108" height="108">'
                                + shape_el(s, 'fill="#fff"') + shape_el(s, 'fill="#000"', "translate(1.8 2.4)") + "</mask>")
                    g.append(f'<g mask="url(#{m2})">' + shape_el(s, f'fill="{hi}"') + "</g>")
                body.append(f'<g id="{pid}">' + "".join(g) + "</g>")
            else:
                body.append(f'<g id="{pid}">' + shape_el(s, f'fill="{P[col]}"') + "</g>")
    body.append(f'<g id="face">{face(fd, style, sz)}</g>')
    if zoom:
        body.append("</g>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" width="{sz}" height="{sz}">'
            f'<defs>{"".join(defs)}</defs>' + "\n".join(body) + "</svg>")


if __name__ == "__main__":
    style, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    for n in ("hamster", "penguin", "rocket"):
        for sz in (108, 240):
            with open(os.path.join(outdir, f"{n}_{sz}.svg"), "w") as f:
                f.write(char_svg(n, style, sz))
    for sz in (108, 240):
        with open(os.path.join(outdir, f"hamster_zoom_{sz}.svg"), "w") as f:
            f.write(char_svg("hamster", style, sz, zoom=True))
