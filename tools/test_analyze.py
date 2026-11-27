#!/usr/bin/env python3
"""tools/analyze.py 시험 (결정 문서 L6 완료 기준).

ffmpeg 로 합성 영상 5종을 만들어 analyze.py 에 넣고 기준을 확인한다.
  ① 4장 루프 빠름 0.5초   ② 보통 1.0초   ③ 프레임 사이 겹침 중간 프레임 섞음
  ④ 가변 프레임률          ⑤ 정지 대조
기준: ①② 변화율 설계값 ±5%, 한 바퀴 ±0.02초, ③ 중간 프레임이 세어지지 않음, ⑤ 변화 0.
덧붙여: G2 교정 영상, 스크린샷 모드, 섬 폭(J4), 판정표를 시험한다.

그림은 Assets/frames/shape_{1..4}@3x.png 를 검정 위에 얹어 쓴다. 임시 파일은 임시 폴더에 만들고 지운다.

사용: python3 tools/test_analyze.py [--keep DIR]   (실패하면 종료 코드 1)
"""
import argparse
import os
import random
import shutil
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402

FRAMES = os.path.join(os.path.dirname(HERE), "Assets", "frames")
SIZE = 108
results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(("통과  " if ok else "실패  ") + f"{name}: {detail}")


def sh(cmd):
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors="replace")[-500:])
    return p.stdout


def load_shape(i):
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i", f"color=black:s={SIZE}x{SIZE}",
           "-i", os.path.join(FRAMES, f"shape_{i}@3x.png"), "-filter_complex",
           "[0:v][1:v]overlay=shortest=1,format=rgb24", "-frames:v", "1", "-f", "rawvideo", "-"]
    return np.frombuffer(sh(cmd), np.uint8).reshape(SIZE, SIZE, 3)


def write_ppm(path, a):
    with open(path, "wb") as f:
        f.write(b"P6\n%d %d\n255\n" % (a.shape[1], a.shape[0]))
        f.write(a.tobytes())


def make_video(tmp, name, segments, cfr=None):
    """segments: [(길이초, rgb 배열)]. concat 으로 만들고 cfr 가 있으면 그 fps 로 고정, 없으면 가변."""
    d = os.path.join(tmp, name + "_src")
    os.makedirs(d)
    lst = []
    cache = {}
    for k, (dur, arr) in enumerate(segments):
        key = arr.tobytes()
        if key not in cache:
            cache[key] = os.path.join(d, f"{len(cache):04d}.ppm")
            write_ppm(cache[key], arr)
        lst.append(f"file '{cache[key]}'\nduration {dur:.6f}")
    lst.append(f"file '{cache[segments[-1][1].tobytes()]}'")  # concat 마지막 길이 처리
    lp = os.path.join(d, "list.txt")
    open(lp, "w").write("\n".join(lst) + "\n")
    out = os.path.join(tmp, name + ".mp4")
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "concat", "-safe", "0", "-i", lp]
    cmd += (["-vsync", "cfr", "-r", str(cfr)] if cfr else ["-vsync", "vfr"])
    cmd += ["-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", out]
    sh(cmd)
    return out


def make_cfr(tmp, name, frame_fn, total, fps):
    """프레임 k(시각 k/fps)의 그림을 frame_fn(k, fps) 로 받아 raw 파이프로 정확한 고정 프레임률 영상을 만든다."""
    out = os.path.join(tmp, name + ".mp4")
    n = int(round(total * fps))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", "%dx%d" % (SIZE, SIZE), "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "12",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(frame_fn(k, fps).tobytes())
    p.stdin.close()
    err = p.stderr.read()
    if p.wait():
        raise RuntimeError(err.decode(errors="replace"))
    return out


def loop_fn(poses, hold, blend=False):
    """한 장 hold 초씩 poses 를 돈다. blend 면 전환 직후 한 프레임을 앞뒤 포즈 50% 혼합 장으로 한다."""
    def fn(k, fps):
        i = int(k / fps / hold + 1e-9)
        cur = poses[i % len(poses)]
        if blend and i > 0 and int((k - 1) / fps / hold + 1e-9) != i:
            prev = poses[(i - 1) % len(poses)]
            return ((prev.astype(np.uint16) + cur.astype(np.uint16)) // 2).astype(np.uint8)
        return cur
    return fn


def seq_fn(parts):
    """parts: [(초, 함수)] 를 이어 붙인다."""
    def fn(k, fps):
        t = k / fps
        for dur, f in parts:
            if t < dur - 1e-9:
                return f(int(round(t * fps)), fps)
            t -= dur
        return parts[-1][1](0, fps)
    return fn


def vfr_segments(poses, hold, total, rnd):
    """실제 전환은 일정하고 영상 프레임이 불규칙한 시각(8~60ms)에 찍힌 것처럼 만든다."""
    times, t = [], 0.0
    while t < total:
        times.append(t)
        t += rnd.uniform(0.008, 0.060)
    segs = []
    for k, tk in enumerate(times):
        nxt = times[k + 1] if k + 1 < len(times) else total
        pose = poses[int(tk / hold + 1e-9) % len(poses)]
        segs.append((nxt - tk, pose))
    return segs


def run_measure(path, **kw):
    t, X = analyze.decode_thumbs(path)
    return analyze.analyze_series(t, X, **kw)


def pct(a, b):
    return abs(a - b) / b * 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep")
    args = ap.parse_args()
    tmp = args.keep or tempfile.mkdtemp(prefix="analyze-test-")
    os.makedirs(tmp, exist_ok=True)
    try:
        sh(["ffmpeg", "-version"])
        poses = [load_shape(i) for i in range(1, 5)]
        black = np.zeros_like(poses[0])
        rnd = random.Random(20261127)

        # ① 4장 루프 빠름: 한 장 0.125초, 한 바퀴 0.5초, 20초, 48fps
        v1 = make_cfr(tmp, "v1_fast", loop_fn(poses, 0.125), 20.0, 48)
        m1 = run_measure(v1)
        check("① 빠름 변화율 8/초 ±5%", pct(m1["pose_rate"], 8.0) <= 5, f"측정 {m1['pose_rate']:.3f}/초 (오차 {pct(m1['pose_rate'], 8.0):.2f}%), 포즈 {m1['poses']}종, 순서 어긋남 {m1['order_violations']}")
        check("① 빠름 한 바퀴 0.5초 ±0.02", m1["period"] and abs(m1["period"] - 0.5) <= 0.02, f"측정 {m1['period']:.4f}초, {m1['cycles']:.1f}바퀴")

        # ② 보통: 한 장 0.25초, 한 바퀴 1.0초
        v2 = make_cfr(tmp, "v2_normal", loop_fn(poses, 0.25), 20.0, 48)
        m2 = run_measure(v2)
        check("② 보통 변화율 4/초 ±5%", pct(m2["pose_rate"], 4.0) <= 5, f"측정 {m2['pose_rate']:.3f}/초 (오차 {pct(m2['pose_rate'], 4.0):.2f}%)")
        check("② 보통 한 바퀴 1.0초 ±0.02", m2["period"] and abs(m2["period"] - 1.0) <= 0.02, f"측정 {m2['period']:.4f}초, {m2['cycles']:.1f}바퀴")

        # ③ 전환마다 겹침 중간 프레임(1/48초, 50% 혼합) 한 장씩. 단순 계수는 두 배로 부풀고, 포즈 계수는 그대로여야 한다
        v3 = make_cfr(tmp, "v3_blend", loop_fn(poses, 0.125, blend=True), 20.0, 48)
        m3 = run_measure(v3)
        check("③ 중간 프레임이 변화율에 세어지지 않음", pct(m3["pose_rate"], 8.0) <= 5 and m3["transient_frames"] > 100,
              f"포즈 계수 {m3['pose_rate']:.3f}/초, 포즈가 아닌 프레임 {m3['transient_frames']}장, 순서 어긋남 {m3['order_violations']}")
        check("③ 같은 영상을 단순 계수하면 부풀어 보임(대조)", m3["naive_rate"] > 10,
              f"단순 변화 계수 {m3['naive_rate']:.2f}/초 (이 값을 쓰면 오판)")
        check("③ 한 바퀴 주기도 0.5초 ±0.02", m3["period"] and abs(m3["period"] - 0.5) <= 0.02, f"측정 {m3['period']:.4f}초")

        # ④ 가변 프레임률: 영상 프레임 시각이 불규칙(8~60ms). 프레임 수로 fps 를 재면 틀리고 pts 로 재면 맞다
        v4 = make_video(tmp, "v4_vfr", vfr_segments(poses, 0.125, 20.0, rnd))
        m4 = run_measure(v4)
        check("④ 가변 프레임률 변화율 8/초 ±5%", pct(m4["pose_rate"], 8.0) <= 5 and m4["vfr"],
              f"pts 기반 {m4['pose_rate']:.3f}/초, 가변 판정 {m4['vfr']}, (프레임 수 기반 fps {m4['frame_count_fps']:.1f} 은 쓰지 않는 값)")
        check("④ 가변 프레임률 한 바퀴 0.5초 ±0.02", m4["period"] and abs(m4["period"] - 0.5) <= 0.02, f"측정 {m4['period']:.4f}초")

        # ⑤ 정지 대조: 포즈 하나만 20초
        v5 = make_cfr(tmp, "v5_still", lambda k, f: poses[0], 20.0, 48)
        m5 = run_measure(v5)
        g = analyze.g1(v5, None)
        check("⑤ 정지 대조 변화 0", m5["naive_changes"] == 0 and m5["pose_transitions"] == 0 and m5["pose_rate"] == 0.0,
              f"단순 계수 {m5['naive_changes']}, 전환 {m5['pose_transitions']}, 최장 무변화 {m5['max_gap']:.1f}초")
        check("⑤ G1 통과", g["pass"], f"프레임 간 최대 변화 {g['max_between_frames']:.3f}, 중앙값 대비 {g['max_from_median']:.3f}")

        # 그림 순서 파일 지정 모드: 같은 결과가 나와야 한다
        refp = [os.path.join(FRAMES, f"shape_{i}@3x.png") for i in range(1, 5)]
        mr = run_measure_refs(v3, refp)
        check("(덤) --poses 순서 모드 ③ 에서도 8/초 ±5%", pct(mr["pose_rate"], 8.0) <= 5,
              f"측정 {mr['pose_rate']:.3f}/초, 순서 어긋남 {mr['order_violations']}, 포즈 아닌 프레임 {mr['transient_frames']}장")

        # 순서가 틀린 영상(1,3,2,4 반복)은 어긋남으로 잡혀야 한다
        wrong = [poses[0], poses[2], poses[1], poses[3]]
        v6 = make_cfr(tmp, "v6_wrong", loop_fn(wrong, 0.125), 8.0, 48)
        mw = run_measure_refs(v6, refp)
        check("(덤) 순서가 틀린 루프를 어긋남으로 셈", mw["order_violations"] > 10 and mw["pose_rate"] < 8 * 0.6,
              f"어긋남 {mw['order_violations']}회, 기대 순서 일치 변화율 {mw['pose_rate']:.2f}/초")

        # 쉼: 호흡 2장 2.0초 한 바퀴(장당 1.0초)
        vr = make_cfr(tmp, "v7_rest", loop_fn(poses[:2], 1.0), 20.0, 48)
        mrst = run_measure(vr)
        check("(덤) 쉼 한 바퀴 2.0초 ±0.1, 변화율 1/초", mrst["period"] and abs(mrst["period"] - 2.0) <= 0.1 and pct(mrst["pose_rate"], 1.0) <= 5,
              f"주기 {mrst['period']:.3f}초({mrst['cycles']:.0f}바퀴), 변화율 {mrst['pose_rate']:.3f}/초, 멈춤 {len(mrst['stalls'])}회")

        # 멈춤: 10초 달리다 5초 멈추고 재개
        vs = make_cfr(tmp, "v8_stall", seq_fn([(10.0, loop_fn(poses, 0.125)), (5.0, lambda k, f: poses[0]), (10.0, loop_fn(poses, 0.125))]), 25.0, 48)
        ms = run_measure(vs)
        check("(덤) 멈춤 5초를 찾고 재개로 판정", len(ms["stalls"]) == 1 and ms["stall_resumed"] and abs(ms["stalls"][0]["sec"] - 5.1) < 0.3,
              f"멈춤 {ms['stalls']}, 재개 {ms['stall_resumed']}")

        # 60fps 에서도 같은 값(한 장이 7.5프레임이라 7/8 프레임으로 번갈아 보인다)
        v9 = make_cfr(tmp, "v9_60fps", loop_fn(poses, 0.125), 20.0, 60)
        m9 = run_measure(v9)
        check("(덤) 60fps 에서도 변화율 8/초 ±5%, 주기 ±0.02", pct(m9["pose_rate"], 8.0) <= 5 and abs(m9["period"] - 0.5) <= 0.02,
              f"{m9['pose_rate']:.3f}/초, {m9['period']:.4f}초")

        # G2: 교정 영상(8Hz 검정·흰색) 변화율 8±0.8, 길이비 95~105%
        vc = make_cfr(tmp, "v10_cal", lambda k, f: np.full_like(poses[0], 0 if int(k / f * 8 + 1e-9) % 2 == 0 else 255), 10.0, 48)
        c = analyze.g2(vc, None, wall_seconds=10.2)
        check("(덤) G2 교정 8Hz 영상 통과", c["pass"] and abs(c["rate"] - 8) <= 0.8,
              f"변화율 {c['rate']:.2f}/초, 영상 {c['duration']:.2f}초, 길이비 {c['ratio']:.3f}")
        c2 = analyze.g2(vc, None, wall_seconds=13.0)
        check("(덤) G2 길이비 77% 는 실패", not c2["pass"] and c2["length_ok"] is False, f"길이비 {c2['ratio']:.3f}")
        vc6 = make_cfr(tmp, "v11_cal6", lambda k, f: np.full_like(poses[0], 0 if int(k / f * 6 + 1e-9) % 2 == 0 else 255), 10.0, 48)
        c3 = analyze.g2(vc6, None, wall_seconds=10.0)
        check("(덤) G2 교정 6Hz 영상(8±0.8 밖)은 실패", not c3["pass"], f"변화율 {c3['rate']:.2f}/초")

        # 스크린샷 모드: 빠름 영상에서 0.3~0.7초 간격으로 40장
        sd = os.path.join(tmp, "shots")
        os.makedirs(sd)
        t, rows = 0.3, ["case,index,host_before,host_after,file"]
        for k in range(1, 41):
            sh(["ffmpeg", "-v", "error", "-nostdin", "-y", "-ss", f"{t:.3f}", "-i", v1, "-frames:v", "1", os.path.join(sd, f"{k:04d}.png")])
            rows.append(f"c,{k},{1000 + t - 0.05:.3f},{1000 + t + 0.05:.3f},shots/{k:04d}.png")
            t += rnd.uniform(0.3, 0.7)
            if t > 19.5:
                break
        os.makedirs(os.path.join(tmp, "shotsroot"), exist_ok=True)
        shutil.move(sd, os.path.join(tmp, "shotsroot", "shots"))
        os.makedirs(os.path.join(tmp, "shotsroot", "shots", "c"))
        for fn in os.listdir(os.path.join(tmp, "shotsroot", "shots")):
            if fn.endswith(".png"):
                shutil.move(os.path.join(tmp, "shotsroot", "shots", fn), os.path.join(tmp, "shotsroot", "shots", "c", fn))
        rows = [r.replace("shots/0", "shots/c/0") for r in rows]
        open(os.path.join(tmp, "shotsroot", "shots.csv"), "w").write("\n".join(rows) + "\n")
        sr = analyze.shots(os.path.join(tmp, "shotsroot", "shots", "c"), os.path.join(tmp, "shotsroot", "shots.csv"), "c")
        check("(덤) 스크린샷 모드: 움직임 있음, 포즈 4종", sr["motion_seen"] and sr["distinct_poses"] == 4,
              f"{sr['shots']}장, 포즈 {sr['distinct_poses']}종, 이웃 달라짐 {sr['different_pairs']*100:.0f}%")
        v5shots = os.path.join(tmp, "shots5")
        os.makedirs(v5shots)
        for k in range(1, 11):
            sh(["ffmpeg", "-v", "error", "-nostdin", "-y", "-ss", f"{k}", "-i", v5, "-frames:v", "1", os.path.join(v5shots, f"{k:04d}.png")])
        sr5 = analyze.shots(v5shots)
        check("(덤) 스크린샷 모드: 정지 영상은 움직임 없음", not sr5["motion_seen"], f"{sr5['shots']}장, 포즈 {sr5['distinct_poses']}종")

        # J4 섬 폭: 밝은 바탕에 검정 섬 폭 90px 고정 vs 12px 늘어나는 영상
        def island_fn(wid_list):
            def fn(k, fps):
                wid = wid_list[min(int(k / fps / 0.125), len(wid_list) - 1)]
                a = np.full((SIZE, SIZE, 3), 235, np.uint8)
                x0 = (SIZE - wid) // 2
                a[20:80, x0:x0 + wid] = 0
                a[40:60, 44:64] = 255 if int(k / fps / 0.125) % 2 else 200  # 섬 안 움직임
                return a
            return fn
        vw_ok = make_cfr(tmp, "w_ok", island_fn([90] * 40), 5.0, 48)
        vw_bad = make_cfr(tmp, "w_bad", island_fn([90] * 20 + [102] * 20), 5.0, 48)
        wok = analyze.island_width(vw_ok, (0, 0, SIZE, SIZE))
        wbad = analyze.island_width(vw_bad, (0, 0, SIZE, SIZE))
        check("(덤) J4 폭 90px 고정은 변화 0px", analyze.width_change(wok, wok["median"]) <= 1, f"중앙 {wok['median']:.0f}px, 범위 {wok['min']}~{wok['max']}")
        check("(덤) J4 폭이 12px 늘면 기준 밖으로 잡힘", analyze.width_change(wbad, 90) >= 10, f"범위 {wbad['min']}~{wbad['max']}px")

        # 판정표 전체(CLI): 합성 영상으로 judge. ① 를 빠름, ② 를 보통, 쉼을 쉼, G1·G2 를 위 영상으로
        rc, out = run_cli(["judge", "--g1", v5, "--g2", vc, "--g2-wall", "10.2", "--fast", v1, "--normal", v2,
                           "--rest", vr, "--bg60", v1])
        print(out)
        check("(덤) judge CLI 종료 코드 0 과 판정표 출력", rc == 0 and "J1" in out and "전체:" in out, f"종료 코드 {rc}")
        jr = analyze.judge(argparse.Namespace(roi=None, island_roi=None, noise_floor=0.5, poses_n=0, poses=None,
                                              g1=v5, g2=vc, g2_wall=10.2, fast=v1, normal=v2, rest=vr, bg60=v1, baseline=None))
        got = {k: v[0] for k, v in jr["J"].items()}
        check("(덤) judge 값: J1 합격, J2 합격(보통·빠름 20바퀴 이상 + 쉼은 10바퀴라 근거에서 뺌), J3 합격, J4 확인 못 함, J5 확인 못 함(20초 영상은 60초가 아님)",
              got["J1"] == "합격" and got["J2"] == "합격" and got["J3"] == "합격" and got["J4"] == "확인 못 함" and got["J5"] == "확인 못 함",
              str(got))
        check("(덤) 확인 못 함이 있으면 전체는 최대 조건부", jr["overall"][0].startswith("조건부"), jr["overall"][0])

        # 입력 오류는 종료 코드 2
        rc2, out2 = run_cli(["measure", os.path.join(tmp, "없는파일.mp4")])
        check("(덤) 없는 파일은 종료 코드 2", rc2 == 2, f"종료 코드 {rc2}")
    finally:
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)

    bad = [r for r in results if not r[1]]
    print(f"\n합계 {len(results)}개 중 통과 {len(results) - len(bad)}, 실패 {len(bad)}")
    return 1 if bad else 0


def run_measure_refs(path, ref_paths):
    t, X = analyze.decode_thumbs(path)
    refs = analyze.decode_refs(ref_paths, None, SIZE, SIZE)
    return analyze.analyze_series(t, X, refs=refs)


def run_cli(argv):
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = analyze.main(argv)
    return rc, buf.getvalue()


if __name__ == "__main__":
    sys.exit(main())
