"""무료 3종(햄스터·펭귄·로켓) 실제 사용 프레임을 B 윤곽선 스티커 방식으로 만든다.

사용: python3 make_frames.py            → src/svg/*.svg 를 쓰고 Inkscape 로 ../*.png 를 뽑는다
출력: {char}_run_1..4@3x.png, {char}_rest_1..2@3x.png, {char}_still@3x.png        (108x108)
      {char}_run_1..4_L@3x.png, {char}_rest_1..2_L@3x.png, {char}_still_L@3x.png (240x240)
한 장이 완성된 통그림이다(쳇바퀴·불꽃 등 고정 요소도 장마다 들어감).

애니메이션 원칙
- 극단 포즈를 먼저 정하고(햄스터 1 착지·3 공중, 펭귄 1·3 좌우 최대 기울기, 로켓 3 최고점) 사이 장을 넣는다.
- 스쿼시·스트레치는 가로x세로를 1 근처로 유지(부피 보존), 기준점은 발바닥.
- 겹침 동작: 머리·귀·지느러미·목도리 꼬리·불꽃이 몸보다 한 장 늦게 따라온다(앞 장의 몸 움직임에서 계산).
- 4장이 첫 장으로 이어진다: 쳇바퀴 살 3갈래는 120도마다 같은 모양이라 4장 x 30도 = 한 주기.
"""
import os, sys, subprocess, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from chars import P, LINE, BORDER, CHARS, flame_path

OUT = os.path.dirname(HERE)            # Assets/frames/characters
SVG_DIR = os.path.join(HERE, "svg")


# ---------- 기본 도형 ----------
def shape_el(shape, attrs, transform=""):
    t = f' transform="{transform}"' if transform else ""
    k = shape[0]
    if k == "circle":
        return f'<circle cx="{shape[1]}" cy="{shape[2]}" r="{shape[3]}" {attrs}{t}/>'
    if k == "ellipse":
        return f'<ellipse cx="{shape[1]}" cy="{shape[2]}" rx="{shape[3]}" ry="{shape[4]}" {attrs}{t}/>'
    return f'<path d="{shape[1]}" {attrs}{t}/>'


def rot(a, cx, cy):
    return f"rotate({a:.2f} {cx} {cy})" if a else ""


def mv(dx, dy):
    return f"translate({dx:.2f} {dy:.2f})" if (dx or dy) else ""


def squash(px, py, sx=1, sy=1, dy=0, r=0, k=1.0):
    """기준점 (px,py)(발바닥)를 중심으로 기울기 r, 가로 sx·세로 sy, 위아래 dy. k 는 전체 배율."""
    return f"translate({px} {py + dy:.2f}) rotate({r:.2f}) scale({k * sx:.3f} {k * sy:.3f}) translate({-px} {-py})"


def join(*ts):
    return " ".join(t for t in ts if t)


# ---------- 쳇바퀴 ----------
def wheel(sz, angle):
    """확대 구도 쳇바퀴: 중심 (54,52), 반지름 43, 테 민트 #7BE0C3, 살 3갈래 + 살 끝 리벳 3개."""
    cx, cy, r, w = 54, 52, 43, 4.5
    ow = 2.6 if sz == 108 else 2.0
    sp = [(cx + 40.5 * math.cos(math.radians(angle + 120 * k)), cy + 40.5 * math.sin(math.radians(angle + 120 * k))) for k in range(3)]
    o = ['<g id="wheel">',
         f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{BORDER}" stroke-width="{w + 2 * ow + 3}"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINE}" stroke-width="{w + 2 * ow}"/>']
    for x, y in sp:
        o.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" stroke="{LINE}" stroke-width="{3 + 2 * ow * .7:.2f}" stroke-linecap="round"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{P["ring"]}" stroke-width="{w}"/>')
    for x, y in sp:
        o.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" stroke="{P["spoke"]}" stroke-width="3" stroke-linecap="round"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="4.6" fill="{P["hub"]}" stroke="{LINE}" stroke-width="{ow * .8:.2f}"/>')
    for x, y in sp:
        o.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.6" fill="{P["hub"]}" stroke="{LINE}" stroke-width="{ow * .7:.2f}"/>')
    o.append("</g>")
    return "\n".join(o)


# ---------- 얼굴 ----------
def face(fd, sz, closed=False):
    o = []
    for (x, y, rx, ry) in fd["blush"]:
        o.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{P["blush"]}" opacity=".95"/>')
    for (x, y, r) in fd["eyes"]:
        if closed:
            # 감은 눈: 아래로 둥근 짧은 선(편히 쉬는 표정). 눈 뜬 장과 같은 눈 자리·같은 색.
            w = 1.9 if sz == 108 else 1.5
            o.append(f'<path d="M{x - r * .95:.2f} {y - .2:.2f} Q{x:.2f} {y + r * .95:.2f} {x + r * .95:.2f} {y - .2:.2f}" fill="none" '
                     f'stroke="{P["eye"]}" stroke-width="{w}" stroke-linecap="round"/>')
        else:
            o.append(f'<ellipse cx="{x}" cy="{y}" rx="{r * .92:.2f}" ry="{r}" fill="{P["eye"]}"/>')
            o.append(f'<circle cx="{x - r * .36:.2f}" cy="{y - r * .4:.2f}" r="{r * .38:.2f}" fill="#fff"/>')
            o.append(f'<circle cx="{x + r * .34:.2f}" cy="{y + r * .38:.2f}" r="{r * .16:.2f}" fill="#fff" opacity=".9"/>')
    if "nose" in fd:
        x, y, rx, ry = fd["nose"]
        o.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{P["nose"]}"/>')
    if "beak" in fd:
        o.append(f'<path d="{fd["beak"]}" fill="{P["beak"]}" stroke="{LINE}" stroke-width="1.1"/>')
    if "mouth" in fd:
        o.append(f'<path d="{fd["mouth"]}" fill="none" stroke="{P["eye"]}" stroke-width="{1.15 if sz == 108 else 0.95}" '
                 f'stroke-linecap="round" stroke-linejoin="round"/>')
    return "\n".join(o)


# ---------- 한 장 그리기 ----------
def char_svg(name, sz, pose):
    """pose: G(전체 변환), t{그룹 또는 부위 id: 변환}, shape{부위 id: 바꾼 모양}, closed(눈 감음), angle(쳇바퀴), K(선 굵기 보정 배율)"""
    parts, fd = CHARS[name]
    t = pose.get("t", {})
    shp = pose.get("shape", {})
    K = pose.get("K", 1.0)

    def tf(pid, grp):
        return join(t.get(grp, ""), t.get(pid, ""))

    body = []
    if name == "hamster":
        body.append(wheel(sz, pose.get("angle", -30)))
    body.append(f'<g id="{name}" transform="{pose.get("G", "")}">' if pose.get("G") else f'<g id="{name}">')
    ow = (2.6 if sz == 108 else 2.0) / K     # 바깥 윤곽 반폭
    iw = (1.5 if sz == 108 else 1.1) / K     # 안쪽 선
    sil = [(pid, shp.get(pid, s), grp) for pid, s, _, role, grp in parts if "sil" in role]
    body.append('<g id="border">' + "".join(shape_el(s, f'fill="{BORDER}" stroke="{BORDER}" stroke-width="{2 * ow + 3:.2f}" stroke-linejoin="round"', tf(pid, g)) for pid, s, g in sil) + "</g>")
    body.append('<g id="outline">' + "".join(shape_el(s, f'fill="{LINE}" stroke="{LINE}" stroke-width="{2 * ow:.2f}" stroke-linejoin="round"', tf(pid, g)) for pid, s, g in sil) + "</g>")
    for pid, s, col, role, grp in parts:
        s = shp.get(pid, s)
        st = f' stroke="{LINE}" stroke-width="{iw:.2f}" stroke-linejoin="round"' if "line" in role else ""
        body.append(f'<g id="{pid}">' + shape_el(s, f'fill="{P[col]}"{st}', tf(pid, grp)) + "</g>")
    g = t.get(fd["grp"], "")
    gt = f' transform="{g}"' if g else ""
    # 광택 대신 짧은 흰 호 하나(가족 공통 규칙)
    body.append(f'<path d="{fd["hl"]}" fill="none" stroke="#fff" stroke-width="{2.2 if sz == 108 else 1.8}" stroke-linecap="round" opacity=".85"{gt}/>')
    body.append(f'<g id="face"{gt}>{face(fd, sz, pose.get("closed", False))}</g>')
    body.append("</g>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" width="{sz}" height="{sz}">\n'
            + "\n".join(body) + "\n</svg>\n")


# ---------- 포즈: 햄스터 ----------
def lag(seq, i, k):
    """겹침 동작: 앞 장에서 이번 장으로 몸이 움직인 양의 k 배만큼 반대로 뒤처진다(4장 루프라 i-1 은 돌아감)."""
    return k * (seq[i - 1] - seq[i])


def hamster_poses():
    poses = {}
    # 몸: 1 착지(눌림) → 2 박차기(늘어남, 앞으로 숙임) → 3 공중(가장 높음) → 4 내려옴(뒤로 젖힘)
    dy = [0.0, -1.4, -2.8, -1.0]
    sxy = [(1.06, 0.93), (0.96, 1.06), (1.0, 1.02), (1.02, 0.98)]
    tilt = [0.0, 4.0, 2.0, -2.5]
    angle = [-30, 0, 30, 60]                       # 시계 방향 30도씩, 다음 장(90)은 -30 과 같은 모양
    feet = [((3, 0), (-3, 0)), ((6.5, -1.6), (-6, 0)), ((1, -2.2), (1.5, -2.0)), ((-3, 0), (3.5, -1.6))]   # (앞발, 뒷발)
    paws = [((0, 0.8), (0, -1.0)), ((1.5, -0.6), (1.5, -0.2)), ((0, -1.0), (0, 0.8)), ((-0.8, 0.2), (-0.8, 0.2))]
    for i in range(4):
        hd = lag(dy, i, 0.6)                       # 머리는 몸보다 늦게
        ea = lag(dy, i, 4.0)                       # 귀는 더 늦게, 바깥으로 젖힘
        sx, sy = sxy[i]
        (ffx, ffy), (fbx, fby) = feet[i]
        (plx, ply), (prx, pry) = paws[i]
        poses[f"run_{i + 1}"] = dict(
            angle=angle[i], K=1.2,
            G=squash(60, 89, sx, sy, dy=dy[i] + 1.9, r=tilt[i], k=1.2),
            t=dict(head=mv(0, hd), ear_l=rot(-ea, 49, 53), ear_l_in=rot(-ea, 49, 53),
                   ear_r=rot(ea, 74, 51), ear_r_in=rot(ea, 74, 51),
                   foot_f=mv(ffx, ffy), foot_b=mv(fbx, fby), paw_l=mv(plx, ply), paw_r=mv(prx, pry)))
    poses["still"] = dict(angle=-30, K=1.2, G=squash(60, 89, dy=1.9, k=1.2))
    # 쉼: 바퀴 멈춤, 살짝 뒤로 기대 눈 감고 숨쉬기(들숨 → 날숨)
    poses["rest_1"] = dict(angle=-30, K=1.2, closed=True, G=squash(60, 89, 1.0, 1.0, dy=1.9, r=-2, k=1.2),
                           t=dict(foot_f=mv(-1.5, 0), foot_b=mv(1.5, 0)))
    poses["rest_2"] = dict(angle=-30, K=1.2, closed=True, G=squash(60, 89, 1.035, 0.955, dy=1.9, r=-2, k=1.2),
                           t=dict(head=mv(0, 0.9), ear_l=rot(-6, 49, 53), ear_l_in=rot(-6, 49, 53),
                                  ear_r=rot(6, 74, 51), ear_r_in=rot(6, 74, 51),
                                  foot_f=mv(-1.5, 0), foot_b=mv(1.5, 0), paw_l=mv(0, 0.6), paw_r=mv(0, 0.6)))
    return poses


# ---------- 포즈: 펭귄 ----------
PEN_K = 0.93   # 전체 배율: 머리깃(위)·발(아래)까지 축소 칸에서 보이는 띠 안에 들어오게
PEN_G = f"translate(54 56) scale({PEN_K}) translate(-54 -56)"

def penguin_poses():
    poses = {}
    # 뒤뚱: 1 왼쪽 최대 기울기(왼발 디딤, 눌림) → 2 가운데 지나며 솟음(오른발 내려옴)
    #       → 3 오른쪽 최대(오른발 디딤) → 4 가운데 지나며 솟음(왼발 내려옴)
    r = [-8.0, 2.5, 8.0, -2.5]                    # 가운데 장은 가는 방향으로 살짝 기운 채 지나감
    dx = [-1.6, 0.4, 1.6, -0.4]                    # 디딘 발 쪽으로 몸무게 이동
    dy = [0.0, -1.8, 0.0, -1.8]
    sxy = [(1.03, 0.96), (0.98, 1.03), (1.03, 0.96), (0.98, 1.03)]
    # 지느러미: 기우는 쪽이 균형 잡듯 벌어지고, 가운데 장에서는 한 장 늦게 따라옴 (바깥으로 벌어지는 각도)
    flip = [(14, -4), (4, 10), (-4, 14), (10, 4)]
    # 발: 들린 발은 위로 올라가며 발끝이 들림
    feet = [(None, (2.0, -3.6, 10)), (None, (1.0, -1.2, 4)), ((-2.0, -3.6, -10), None), ((-1.0, -1.2, -4), None)]
    for i in range(4):
        tail = -r[i] * 0.8 + lag(r, i, 1.2)        # 목도리 꼬리: 중력 쪽으로 + 한 장 늦게 흔들림
        fl, fr = flip[i]
        lf, rf = feet[i]
        tt = dict(body=join(mv(dx[i], 0), squash(54, 89, sxy[i][0], sxy[i][1], dy=dy[i], r=r[i])),
                  flip_l=rot(fl, 31, 58), flip_r=rot(-fr, 77, 58), scarf_tail=rot(tail, 66, 71))
        if lf:
            tt["foot_l"] = join(mv(lf[0], lf[1]), rot(lf[2], 44, 89.5))
        if rf:
            tt["foot_r"] = join(mv(rf[0], rf[1]), rot(rf[2], 65, 89.5))
        poses[f"run_{i + 1}"] = dict(t=tt, G=PEN_G, K=PEN_K)
    poses["still"] = dict(G=PEN_G, K=PEN_K)
    poses["rest_1"] = dict(closed=True, G=PEN_G, K=PEN_K, t=dict(flip_l=rot(-3, 31, 58), flip_r=rot(3, 77, 58)))
    poses["rest_2"] = dict(closed=True, G=PEN_G, K=PEN_K, t=dict(body=squash(54, 89, 1.03, 0.965), flip_l=rot(-6, 31, 58), flip_r=rot(6, 77, 58),
                                               scarf_tail=rot(-3, 66, 71)))
    return poses


# ---------- 포즈: 로켓 ----------
def rocket_poses():
    poses = {}
    # 위아래로 살짝 튐: 3번이 최고점. 코가 오를 때 살짝 들림(기울기), 불꽃은 4단계로 일렁임
    dy = [0.0, -1.6, -2.6, -1.2]
    tilt = [0.0, -1.5, -2.5, -1.0]
    # 불꽃 (바깥 길이, 끝 흔들림, 뿌리 반폭, 갈래), (안쪽 길이, 끝 흔들림, 반폭)
    fl = [((19, 0.0, 8.0, 0), (12, 0.0, 5.0)),
          ((22, -2.0, 8.6, 3.0), (15, 1.2, 5.4)),
          ((15, 2.0, 7.4, 0), (9.5, -1.0, 4.6)),
          ((20.5, 1.2, 8.2, 2.4), (13.5, -0.6, 5.2))]
    for i in range(4):
        (L, ty, h, fk), (Li, tyi, hi) = fl[i]
        poses[f"run_{i + 1}"] = dict(
            G=join(mv(0, dy[i]), rot(tilt[i], 62, 54)),
            shape=dict(flame_o=("path", flame_path(L, ty, h, fork=fk)), flame_i=("path", flame_path(Li, tyi, hi))))
    # 정지: 코를 4도 들고 막 출발하려는 자세, 불꽃은 중간 길이로 고르게
    poses["still"] = dict(G=join(mv(0, -0.5), rot(-4, 62, 54)),
                          shape=dict(flame_o=("path", flame_path(17, 0.5, 7.8)), flame_i=("path", flame_path(10.5, 0, 4.8))))
    # 쉼: 엔진 약하게(작은 불꽃 두 크기), 눈 감고 둥둥
    poses["rest_1"] = dict(closed=True, shape=dict(flame_o=("path", flame_path(10, 0, 6.2)), flame_i=("path", flame_path(5.5, 0, 3.6))))
    poses["rest_2"] = dict(closed=True, G=mv(0, 0.8),
                           shape=dict(flame_o=("path", flame_path(12.5, 0.6, 6.6)), flame_i=("path", flame_path(7, -0.4, 3.9))))
    return poses


POSES = {"hamster": hamster_poses, "penguin": penguin_poses, "rocket": rocket_poses}
FRAMES = ["run_1", "run_2", "run_3", "run_4", "rest_1", "rest_2", "still"]


def main():
    os.makedirs(SVG_DIR, exist_ok=True)
    jobs = []
    for name, fn in POSES.items():
        poses = fn()
        for fr in FRAMES:
            for sz, suf in ((108, ""), (240, "_L")):
                svg = os.path.join(SVG_DIR, f"{name}_{fr}{suf}.svg")
                open(svg, "w").write(char_svg(name, sz, poses[fr]))
                jobs.append((svg, sz, os.path.join(OUT, f"{name}_{fr}{suf}@3x.png")))
    # Inkscape 한 번 띄워 여러 장 내보내기(셸 모드)
    cmds = "".join(f"file-open:{s}; export-width:{z}; export-height:{z}; export-background-opacity:0; export-filename:{o}; export-do; file-close\n"
                   for s, z, o in jobs)
    subprocess.run(["inkscape", "--shell"], input=cmds, text=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"{len(jobs)} 장 내보냄")


if __name__ == "__main__":
    main()
