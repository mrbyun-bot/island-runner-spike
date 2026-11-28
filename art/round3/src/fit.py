#!/usr/bin/env python3
"""세트별 바깥 상자를 재서 cat.FIT 에 넣을 배율·이동값 계산. 목표: 가로 2~106, 세로 띠 17~91 안."""
import os, subprocess, sys, tempfile, json
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import cat

def bbox_of(style, pose):
    with tempfile.TemporaryDirectory() as t:
        svg = os.path.join(t, "a.svg"); png = os.path.join(t, "a.png")
        open(svg, "w").write(cat.cat_svg(style, pose))
        subprocess.run(["inkscape", "--export-type=png", "--export-width=432", f"--export-filename={png}", svg], check=True, capture_output=True)
        b = Image.open(png).getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
        return [v / 4 for v in b]

def fit_set(poses, style="d", box=(2, 17, 106, 91), cy=None):
    cat.FIT.clear()
    bs = [bbox_of(style, p) for p in poses]
    x0 = min(b[0] for b in bs); y0 = min(b[1] for b in bs); x1 = max(b[2] for b in bs); y1 = max(b[3] for b in bs)
    s = min((box[2] - box[0]) / (x1 - x0), (box[3] - box[1]) / (y1 - y0))
    tx = (box[0] + box[2]) / 2 - s * (x0 + x1) / 2
    ty = ((box[1] + box[3]) / 2 if cy is None else cy) - s * (y0 + y1) / 2
    return (round(s, 4), round(tx, 2), round(ty, 2)), (x0, y0, x1, y1)

if __name__ == "__main__":
    print(fit_set(["run_1", "run_2", "run_3", "run_4"]))
