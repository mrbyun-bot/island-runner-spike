#!/usr/bin/env python3
"""시뮬레이터 녹화 영상(또는 스크린샷)에서 Live Activity 애니메이션을 판정한다.

결정 문서 3-decision.md 의 G1·G2 관문과 J1~J5 를 계산한다. 리눅스 서버에서 돌린다
(ffmpeg/ffprobe + numpy 만 쓴다. PIL 없음, 설치 없음).

핵심 방법
  - 프레임 시각은 영상 컨테이너의 pts 로 읽는다(`-vsync 0` + showinfo). 프레임 개수/길이로
    fps 를 구하지 않는다. 가변 프레임률에서도 같은 값이 나온다.
  - 캐릭터 칸(--roi)을 32x32 로 줄여 '포즈 지문'으로 쓴다. 지문이 서로 다른 덩어리(군집)를
    찾고, 점유율이 큰 군집만 포즈로 인정한다. 전환 중간에 섞여 찍힌 프레임(겹침 중간 프레임)은
    점유율이 작아 포즈로 인정하지 않으므로 변화 횟수에 세지 않는다.
    포즈 그림 파일을 --poses 로 주면 그 순서가 기대 순서다. 안 주면 처음 한 바퀴의 등장 순서가 기대 순서다.
  - 변화율 = 기대한 다음 포즈로 바뀐 횟수 / 초 = (횟수-1) / (마지막 전환 시각 - 첫 전환 시각).
  - 한 바퀴 주기 = 지문 시계열의 자기상관. 첫 봉우리로 대략을 잡고, 여러 바퀴 뒤 봉우리를
    그 바퀴 수로 나눠 평균 주기를 낸다.
  - 가로 폭 = 섬(어두운 픽셀)의 bbox 가로 길이.

사용 예
  tools/analyze.py measure fast.mp4 --roi 40,10,60,40
  tools/analyze.py g1 control.mp4
  tools/analyze.py g2 calib.mp4 --wall-seconds 10.2
  tools/analyze.py shots out/shots/p2_shape_fast --csv out/shots.csv --case p2_shape_fast
  tools/analyze.py judge --g1 g1.mp4 --g2 g2.mp4 --g2-wall 10.1 --fast f.mp4 --normal n.mp4 --rest r.mp4 --bg60 b.mp4
  tools/analyze.py results <results/runs/N-1>     # CI 결과 폴더 구조를 읽어 judge 실행

종료 코드: 0 = 계산을 끝냄(판정이 실패여도 0), 2 = 입력 오류.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys

import numpy as np

THUMB = 32            # 지문 한 변 픽셀 수
GRID_HZ = 480         # 자기상관용 균일 격자
STALL_SEC = 2.0       # 멈춤 기준(결정 문서 용어표)
NOISE_FLOOR = 0.5     # 지문 평균 절대차(0~255) 이하는 압축 잡음으로 본다


class InputError(Exception):
    pass


# ----------------------------------------------------------------------------- 입력

def _run(cmd, binary=True):
    try:
        p = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError as e:
        raise InputError(f"실행 파일 없음: {cmd[0]} ({e})")
    if p.returncode != 0:
        raise InputError(f"{' '.join(cmd[:6])} ... 실패: {p.stderr.decode(errors='replace')[-300:]}")
    return p


def parse_roi(s):
    if not s:
        return None
    try:
        x, y, w, h = [int(v) for v in s.split(",")]
    except ValueError:
        raise InputError(f"--roi 는 x,y,w,h 정수 4개여야 한다: {s}")
    return x, y, w, h


def probe_duration(path):
    p = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "default=nw=1:nk=1", path])
    try:
        return float(p.stdout.decode().strip())
    except ValueError:
        raise InputError(f"길이를 못 읽음: {path}")


def decode_thumbs(path, roi=None, size=THUMB, frames=None, extra_in=()):
    """(pts 배열, N x size x size float32 회색 지문). 영상은 -vsync 0 으로 프레임을 그대로 받는다."""
    if not os.path.exists(path):
        raise InputError(f"파일 없음: {path}")
    vf = []
    if roi:
        x, y, w, h = roi
        vf.append(f"crop={w}:{h}:{x}:{y}")
    vf += [f"scale={size}:{size}:flags=area", "showinfo", "format=gray"]
    cmd = ["ffmpeg", "-v", "info", "-nostdin", *extra_in, "-i", path, "-vsync", "0"]
    if frames:
        cmd += ["-frames:v", str(frames)]
    cmd += ["-vf", ",".join(vf), "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    p = _run(cmd)
    pts = [float(m) for m in re.findall(r"pts_time:(-?[0-9.]+)", p.stderr.decode(errors="replace"))]
    X = np.frombuffer(p.stdout, np.uint8).reshape(-1, size, size).astype(np.float32)
    if len(pts) != len(X):
        raise InputError(f"프레임 수 {len(X)} 와 pts 수 {len(pts)} 가 다르다: {path}")
    if len(X) == 0:
        raise InputError(f"프레임이 없다: {path}")
    return np.array(pts), X


def decode_gray_full(path, roi):
    """roi 를 자르지 않은 원래 해상도 회색 프레임들 (폭 측정용)."""
    x, y, w, h = roi
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-vsync", "0",
           "-vf", f"crop={w}:{h}:{x}:{y},format=gray", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    p = _run(cmd)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w)


# ----------------------------------------------------------------------------- 군집·포즈

def _dist_to(F, v):
    return np.abs(F - v).mean(axis=1)


def pairwise_scale(F, sample=300):
    idx = np.unique(np.linspace(0, len(F) - 1, min(sample, len(F))).astype(int))
    S = F[idx]
    d = np.concatenate([_dist_to(S[i + 1:], S[i]) for i in range(len(S) - 1)]) if len(S) > 1 else np.zeros(1)
    return float(np.percentile(d, 95)) if len(d) else 0.0


def leader_clusters(F, theta):
    centers, labels = [], np.zeros(len(F), int)
    for i, f in enumerate(F):
        if centers:
            d = _dist_to(np.array(centers), f)
            j = int(d.argmin())
            if d[j] <= theta:
                labels[i] = j
                continue
        centers.append(f)
        labels[i] = len(centers) - 1
    return np.array(centers), labels


def decode_refs(paths, roi, w, h):
    """포즈 그림 파일(투명 PNG 가능)을 검정 위에 얹어 지문으로 만든다."""
    out = []
    for pth in paths:
        if not os.path.exists(pth):
            raise InputError(f"포즈 그림 없음: {pth}")
        cmd = ["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i", f"color=black:s={w}x{h}",
               "-i", pth, "-filter_complex",
               f"[1:v]scale={w}:{h}[a];[0:v][a]overlay=shortest=1,scale={THUMB}:{THUMB}:flags=area,format=gray",
               "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
        out.append(np.frombuffer(_run(cmd).stdout, np.uint8).astype(np.float32))
    return np.array(out)


def analyze_series(t, X, poses_n=0, refs=None, stall=STALL_SEC, floor=NOISE_FLOOR):
    n = len(t)
    F = X.reshape(n, -1)
    t_end = t[-1] + (float(np.median(np.diff(t))) if n > 1 else 0.0)
    span = t_end - t[0]
    dmax = pairwise_scale(F)
    theta = max(floor, 0.2 * dmax)

    # 변화 사건(겹침 중간 프레임까지 모두 센 값 = 단순 계수)
    d_prev = np.array([0.0] + [float(np.abs(F[i] - F[i - 1]).mean()) for i in range(1, n)])
    change_t = t[d_prev > theta]

    # 멈춤: 변화 사이 간격 (시작·끝 포함)
    edges = np.concatenate([[t[0]], change_t, [t_end]])
    gaps = np.diff(edges)
    stalls = [(float(edges[i]), float(gaps[i])) for i in range(len(gaps)) if gaps[i] > stall]
    resumed = [i < len(gaps) - 1 for i in range(len(gaps)) if gaps[i] > stall]
    resume_gap = None
    for i in range(len(gaps)):
        if gaps[i] > stall and i < len(gaps) - 1:
            resume_gap = float(gaps[i])

    # 포즈 라벨
    if refs is not None:
        rd = np.array([[float(np.abs(a - b).mean()) for b in refs] for a in refs])
        theta_ref = max(floor, 0.2 * float(rd.max()))
        D = np.stack([_dist_to(F, r) for r in refs], axis=1)
        near = D.argmin(axis=1)
        labels = np.where(D.min(axis=1) <= theta_ref, near, -1)
        n_poses = len(refs)
    else:
        centers, cl = leader_clusters(F, theta)
        counts = np.bincount(cl, minlength=len(centers))
        if poses_n > 0:
            keep = list(np.argsort(-counts)[:poses_n])
        else:
            keep = [c for c in range(len(centers)) if counts[c] >= 0.4 * counts.max()]
        first = {c: int(np.argmax(cl == c)) for c in keep}
        order = sorted(keep, key=lambda c: first[c])
        remap = {c: k for k, c in enumerate(order)}
        labels = np.array([remap.get(c, -1) for c in cl])
        n_poses = len(order)

    transitions, bad_order, last = [], 0, None
    for i in range(n):
        lb = int(labels[i])
        if lb < 0:
            continue
        if last is not None and lb != last:
            if n_poses >= 2 and lb == (last + 1) % n_poses:
                transitions.append(float(t[i]))
            else:
                bad_order += 1
        last = lb

    def rate_from(times, count_span):
        if len(times) >= 2:
            return (len(times) - 1) / (times[-1] - times[0])
        return 0.0

    res = {
        "frames": n,
        "pts_start": float(t[0]),
        "window_sec": float(span),
        "frame_count_fps": float(n / span) if span > 0 else 0.0,   # 틀린 방법(참고용)
        "vfr": bool(n > 2 and np.ptp(np.diff(t)) > 0.25 * np.median(np.diff(t))),
        "distance_scale": dmax,
        "threshold": theta,
        "poses": n_poses,
        "transient_frames": int((labels < 0).sum()),
        "naive_changes": int(len(change_t)),
        "naive_rate": float(len(change_t) / span) if span > 0 else 0.0,
        "pose_transitions": len(transitions),
        "order_violations": bad_order,
        "pose_rate": rate_from(transitions, span),
        "max_gap": float(gaps.max()) if len(gaps) else 0.0,
        "stalls": [{"at": a, "sec": b} for a, b in stalls],
        "stall_resumed": bool(stalls) and any(resumed),
        "stall_resume_gap": resume_gap,
    }
    res.update(period_estimate(t, F, t_end))
    return res


# ----------------------------------------------------------------------------- 한 바퀴 주기

def period_estimate(t, F, t_end):
    out = {"period": None, "cycles": 0.0, "period_note": ""}
    n = len(t)
    if n < 8:
        out["period_note"] = "프레임 부족"
        return out
    Xc = F - F.mean(axis=0)
    k = int(min(8, min(Xc.shape) - 1))
    if k < 1 or float(np.abs(Xc).max()) < 1e-6:
        out["period_note"] = "변화 없음"
        return out
    U, S, _ = np.linalg.svd(Xc, full_matrices=False)
    Y = U[:, :k] * S[:k]
    grid = np.arange(t[0], t_end, 1.0 / GRID_HZ)
    idx = np.clip(np.searchsorted(t, grid, side="right") - 1, 0, n - 1)
    G = Y[idx]
    G = G - G.mean(axis=0)
    N = len(G)
    nfft = 1 << int(np.ceil(np.log2(2 * N)))
    R = np.zeros(nfft)
    for j in range(k):
        f = np.fft.rfft(G[:, j], nfft)
        R += np.fft.irfft(f * np.conj(f), nfft)
    R = R[:N] / (N - np.arange(N))
    if R[0] <= 0:
        out["period_note"] = "변화 없음"
        return out
    rho = R / R[0]
    lmax = N // 3
    below = np.where(rho[:lmax] < 0.2)[0]
    if len(below) == 0:
        out["period_note"] = "주기성 없음(상관이 안 떨어짐)"
        return out
    lo = int(below[0])
    seg = rho[lo:lmax]
    if len(seg) == 0 or seg.max() < 0.5:
        out["period_note"] = "주기성 약함(최대 상관 %.2f)" % (seg.max() if len(seg) else 0)
        return out
    # 첫 봉우리: 최대 상관의 60% 를 처음 넘는 곳에서 꼭대기까지 올라간다.
    # (타이밍 흔들림이 있으면 첫 봉우리가 낮을 수 있어 95% 가 아니라 60% 로 잡고, 아래 여러 바퀴 평균으로 바로잡는다)
    p0 = lo + int(np.argmax(seg >= 0.6 * seg.max()))
    while p0 + 1 < lmax and rho[p0 + 1] >= rho[p0]:
        p0 += 1
    # 여러 바퀴 뒤 봉우리의 위치를 바퀴 수로 나눠 평균 주기를 낸다.
    # 한 바퀴마다 추정이 갱신되므로 처음 추정이 5% 틀려도 바퀴가 쌓이면서 따라 잡는다.
    best_lag, best_m, est = p0, 1, float(p0)
    m = 2
    while m * est * 1.25 < N // 2 + 0.25 * est:
        c = m * est
        a, b = int(c - 0.25 * p0), int(c + 0.25 * p0)
        if b >= N:
            break
        lag = a + int(np.argmax(rho[a:b]))
        if rho[lag] >= 0.5:
            best_lag, best_m, est = lag, m, lag / m
        m += 1
    out["period"] = best_lag / best_m / GRID_HZ
    out["cycles"] = (t_end - t[0]) / out["period"]
    out["period_note"] = f"{best_m}바퀴 봉우리로 평균"
    return out


# ----------------------------------------------------------------------------- 폭(J4)

def island_width(path, roi, dark_thr=60):
    G = decode_gray_full(path, roi)
    mask = G < dark_thr
    cols = mask.any(axis=1)  # (N, W): 각 열에 어두운 픽셀이 있는가
    widths = []
    for c in cols:
        xs = np.where(c)[0]
        widths.append(int(xs[-1] - xs[0] + 1) if len(xs) else 0)
    w = np.array(widths)
    return {"frames": len(w), "median": float(np.median(w)), "min": int(w.min()), "max": int(w.max()),
            "series": w}


def width_change(case_w, baseline_median):
    return float(np.abs(case_w["series"] - baseline_median).max())


# ----------------------------------------------------------------------------- 관문

def g1(path, roi, floor=NOISE_FLOOR):
    t, X = decode_thumbs(path, roi)
    F = X.reshape(len(X), -1)
    ref = np.median(F, axis=0)
    d = _dist_to(F, ref)
    prev = np.array([float(np.abs(F[i] - F[i - 1]).mean()) for i in range(1, len(F))] or [0.0])
    ok = bool(d.max() <= floor and prev.max() <= floor)
    return {"pass": ok, "frames": len(F), "max_from_median": float(d.max()),
            "max_between_frames": float(prev.max()), "floor": floor}


def g2(path, roi, wall_seconds=None, target_hz=8.0, tol=0.8, calibration=True):
    dur = probe_duration(path)
    out = {"duration": dur, "wall": wall_seconds, "length_ok": None, "ratio": None,
           "rate": None, "rate_ok": None}
    if wall_seconds:
        out["ratio"] = dur / wall_seconds
        out["length_ok"] = bool(0.95 <= out["ratio"] <= 1.05)
    if calibration:
        t, X = decode_thumbs(path, roi)
        lum = X.reshape(len(X), -1).mean(axis=1)
        lo, hi = float(lum.min()), float(lum.max())
        if hi - lo < 10:
            out["rate_note"] = "두 색이 안 보임(밝기 차 %.1f)" % (hi - lo)
            out["rate_ok"] = False
        else:
            st = lum > (lo + hi) / 2
            ch = t[1:][st[1:] != st[:-1]]
            if len(ch) >= 3:
                out["rate"] = (len(ch) - 1) / (ch[-1] - ch[0])
                out["rate_ok"] = bool(abs(out["rate"] - target_hz) <= tol)
            else:
                out["rate_note"] = "전환이 3번 미만"
                out["rate_ok"] = False
    out["pass"] = bool(out["length_ok"] is not False and (out["rate_ok"] is not False)
                       and (out["length_ok"] is not None or out["rate_ok"] is not None))
    return out


# ----------------------------------------------------------------------------- 스크린샷 대체 모드

def shots(directory, csv_path=None, case=None, roi=None, poses_n=0):
    files, times = [], []
    if csv_path:
        with open(csv_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if case and r["case"] != case:
                    continue
                p = os.path.join(os.path.dirname(os.path.abspath(csv_path)), r["file"])
                if os.path.exists(p):
                    files.append(p)
                    times.append((float(r["host_before"]) + float(r["host_after"])) / 2)
    if not files:
        files = sorted(os.path.join(directory, n) for n in os.listdir(directory) if n.lower().endswith(".png"))
        times = [float(i) for i in range(len(files))]
    if len(files) < 3:
        raise InputError(f"스크린샷이 3장 미만: {directory}")
    Xs = [decode_thumbs(p, roi, frames=1)[1][0] for p in files]
    X = np.array(Xs)
    F = X.reshape(len(X), -1)
    dmax = pairwise_scale(F)
    theta = max(NOISE_FLOOR, 0.2 * dmax)
    centers, cl = leader_clusters(F, theta)
    counts = np.bincount(cl, minlength=len(centers))
    keep = list(np.argsort(-counts)[:poses_n]) if poses_n > 0 else [c for c in range(len(centers)) if counts[c] >= 0.4 * counts.max()]
    labels = np.array([c if c in keep else -1 for c in cl])
    stable = labels[labels >= 0]
    diff_frac = float(np.mean(stable[1:] != stable[:-1])) if len(stable) > 1 else 0.0
    dt = np.diff(np.array(times))
    return {"shots": len(files), "distinct_poses": len(keep), "different_pairs": diff_frac,
            "median_interval": float(np.median(dt)) if len(dt) else None,
            "motion_seen": bool(len(keep) >= 2),
            "note": "스크린샷은 간격이 불규칙하고 길어 변화율·주기를 잴 수 없다. 움직임 있음/없음까지만 증명하고 판정 상한은 조건부다."}


# ----------------------------------------------------------------------------- 판정

def judge_j1(m):
    if m is None:
        return "확인 못 함", "빠름 단계 영상 없음"
    r, st = m["pose_rate"], m["stalls"]
    note = f"평균 {r:.2f}/초, 멈춤 {len(st)}회"
    if r >= 6 and not st:
        return "합격", note
    if r < 1 or (st and not m["stall_resumed"]):
        return "실패", note
    if st and m["stall_resume_gap"] is not None and m["stall_resume_gap"] > 5:
        return "실패", note + f" (재개까지 {m['stall_resume_gap']:.1f}초)"
    return "조건부", note


def _period_verdict(m, design):
    if m is None:
        return None, "영상 없음"
    if m["period"] is None:
        return "실패", f"주기를 못 잡음({m['period_note']})"
    err = abs(m["period"] - design)
    tight = 0.05 if design <= 0.5 else 0.1
    note = f"{m['period']:.3f}초 (설계 {design}, 오차 {err:.3f}, {m['cycles']:.0f}바퀴)"
    if m["cycles"] < 20:
        note += " [20바퀴 미만]"
    if err <= tight:
        return "합격", note
    if err <= 2 * tight:
        return "조건부", note
    return "실패", note


def judge_j2(rest, normal, fast):
    parts = {"쉼": (rest, 2.0), "보통": (normal, 1.0), "빠름": (fast, 0.5)}
    got = {k: _period_verdict(m, d) for k, (m, d) in parts.items()}
    have = {k: v for k, v in got.items() if v[0] is not None}
    note = "; ".join(f"{k} {v[0]}: {v[1]}" for k, v in got.items() if v[0])
    if len(have) < 2:
        return "확인 못 함", "두 단계 이상 필요. " + note
    vs = [v[0] for v in have.values()]
    if "실패" in vs:
        return "실패", note
    # 결정 문서: "20바퀴 이상 평균". 20바퀴를 채운 단계가 두 개 이상이어야 합격이다.
    # 바퀴 수가 모자란 단계는 근거로만 적고 합격 개수에서 뺀다(쉼은 20초 녹화로 10바퀴밖에 안 나온다).
    qualified = [k for k, (m, _) in parts.items() if m is not None and m["period"] is not None and m["cycles"] >= 20
                 and got[k][0] == "합격"]
    if "조건부" in vs:
        return "조건부", note
    if len(qualified) < 2:
        return "조건부", note + f" (20바퀴 채운 합격 단계 {len(qualified)}개 < 2)"
    return "합격", note + f" (20바퀴 채운 단계: {', '.join(qualified)})"


def judge_j3(normal, fast, j2):
    if normal is None or fast is None or normal["period"] is None or fast["period"] is None:
        return "확인 못 함", "보통·빠름 주기 필요"
    ratio = normal["period"] / fast["period"]
    note = f"주기 비 {ratio:.2f} (보통 {normal['period']:.3f} / 빠름 {fast['period']:.3f})"
    v = "합격" if ratio >= 2 else "조건부" if ratio >= 1.5 else "실패"
    if j2 != "합격":
        note += f" [J2 {j2}이므로 단독 근거 약함]"
    return v, note


def judge_j4(wcase, baseline_median, own):
    if wcase is None:
        return "확인 못 함", "섬 폭 영역(--island-roi)과 영상이 필요"
    ch = width_change(wcase, baseline_median)
    note = f"기준 {baseline_median:.0f}px 대비 최대 {ch:.0f}px 변화" + (" (자체 기준: 안정성만 본 값)" if own else "")
    if ch <= 2:
        return "합격", note
    if ch <= 6:
        return "조건부", note
    return "실패", note


def judge_j5(m):
    if m is None:
        return "확인 못 함", "백그라운드 60초 영상 없음"
    note = f"{m['window_sec']:.0f}초, 평균 {m['pose_rate']:.2f}/초, 멈춤 {len(m['stalls'])}회"
    if m["window_sec"] < 55 and not m["stalls"]:
        return "확인 못 함", note + " (60초 영상이 아님. 멈춤은 없었으나 판정 기준 60초에 못 미침)"
    if m["stalls"]:
        return "실패", note
    if m["pose_rate"] >= 6:
        return "합격", note
    if m["pose_rate"] >= 1:
        return "조건부", note
    return "실패", note


def overall(g1r, g2r, js):
    if g1r is None or g2r is None:
        return "무효(재촬영)", "G1 또는 G2 영상이 없다"
    if not g1r["pass"] or not g2r["pass"]:
        return "무효(재촬영)", "G1 또는 G2 미통과: 나머지 판정은 모두 무효"
    vs = [v for v, _ in js.values()]
    if "실패" in vs:
        return "실패", "J1~J5 중 실패가 있다(규칙 2)"
    if "확인 못 함" in vs:
        return "조건부(최대)", "필수 항목에 확인 못 함이 있어 최대 조건부(규칙 5)"
    if "조건부" in vs:
        return "조건부", "J1~J5 에 조건부가 있다(규칙 3)"
    return "합격(시뮬) · 실기기 미확인", "J1~J5 전부 합격(규칙 4). [실기기 필수] 9개 판정 보류"


def judge(args):
    roi = parse_roi(args.roi)
    g1r = g1(args.g1, roi, args.noise_floor) if args.g1 else None
    g2r = g2(args.g2, roi, args.g2_wall) if args.g2 else None

    def meas(p):
        if not p:
            return None
        t, X = decode_thumbs(p, roi)
        return analyze_series(t, X, poses_n=args.poses_n, refs=load_refs(args, roi, p))

    fast, normal, rest, bg = meas(args.fast), meas(args.normal), meas(args.rest), meas(args.bg60)
    iroi = parse_roi(args.island_roi)
    wcase = island_width(args.fast, iroi) if (iroi and args.fast) else None
    own = True
    base_med = wcase["median"] if wcase else 0.0
    if wcase and args.baseline:
        base_med = island_width(args.baseline, iroi)["median"]
        own = False

    j = {}
    j["J1"] = judge_j1(fast)
    j["J2"] = judge_j2(rest, normal, fast)
    j["J3"] = judge_j3(normal, fast, j["J2"][0])
    j["J4"] = judge_j4(wcase, base_med, own)
    j["J5"] = judge_j5(bg)
    ov = overall(g1r, g2r, j)
    return {"G1": g1r, "G2": g2r, "J": j, "overall": ov,
            "measures": {"fast": fast, "normal": normal, "rest": rest, "bg60": bg}}


def load_refs(args, roi, video):
    if not getattr(args, "poses", None):
        return None
    if roi:
        w, h = roi[2], roi[3]
    else:
        p = _run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                  "stream=width,height", "-of", "csv=p=0", video])
        w, h = [int(v) for v in p.stdout.decode().strip().split(",")[:2]]
    return decode_refs(args.poses, roi, w, h)


# ----------------------------------------------------------------------------- 출력

def fmt_measure(m, name=""):
    L = []
    L.append(f"[{name}] 프레임 {m['frames']}장, 창 {m['window_sec']:.2f}초, 가변 프레임률 {'예' if m['vfr'] else '아니오'}")
    L.append(f"  포즈 {m['poses']}종, 변화율(포즈 순서 일치) {m['pose_rate']:.3f}/초 (전환 {m['pose_transitions']}회, 순서 어긋남 {m['order_violations']}회)")
    L.append(f"  단순 변화 계수 {m['naive_rate']:.3f}/초 (참고: 겹침 중간 프레임까지 센 값), 포즈 아닌 프레임 {m['transient_frames']}장")
    L.append(f"  프레임 수/길이 fps {m['frame_count_fps']:.2f} (참고: 쓰지 않는 값)")
    per = f"{m['period']:.4f}초 ({m['cycles']:.1f}바퀴, {m['period_note']})" if m["period"] else f"없음 ({m['period_note']})"
    L.append(f"  한 바퀴 주기 {per}")
    L.append(f"  최장 무변화 {m['max_gap']:.2f}초, 멈춤(>2초) {len(m['stalls'])}회" + (", 재개함" if m["stall_resumed"] else ""))
    return "\n".join(L)


def fmt_judge(r):
    L = ["== 판정표 ==", ""]
    for k in ("G1", "G2"):
        v = r[k]
        if v is None:
            L.append(f"{k}: 확인 못 함 (영상 없음)")
        elif k == "G1":
            L.append(f"G1 대조 영상: {'통과' if v['pass'] else '실패'}  프레임 간 최대 변화 {v['max_between_frames']:.3f}, 중앙값 대비 {v['max_from_median']:.3f} (허용 {v['floor']})")
        else:
            rt = f"길이비 {v['ratio']:.3f}" if v["ratio"] else "길이비 확인 못 함(--g2-wall 없음)"
            rr = f"교정 변화율 {v['rate']:.2f}/초" if v["rate"] else "교정 변화율 측정 못 함"
            L.append(f"G2 녹화 유효성: {'통과' if v['pass'] else '실패'}  {rt} (95~105%), {rr} (8±0.8)")
    L.append("")
    L.append("| 항목 | 판정 | 근거 |")
    L.append("|---|---|---|")
    tags = {"J1": "[실기기 참고]", "J2": "[실기기 참고]", "J3": "[시뮬 충분, J2 통과 시]", "J4": "[실기기 참고]", "J5": "[실기기 필수]"}
    for k, (v, note) in r["J"].items():
        L.append(f"| {k} {tags[k]} | {v} | {note} |")
    L.append("")
    L.append(f"전체: {r['overall'][0]}  ({r['overall'][1]})")
    return "\n".join(L)


# ----------------------------------------------------------------------------- results 폴더

def _wall(out_dir, case):
    p = os.path.join(out_dir, "timeline.csv")
    if not os.path.exists(p):
        return None
    st = en = None
    with open(p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["case"] == case and r["event"] == "record_start":
                st = float(r["host_time"])
            if r["case"] == case and r["event"] == "record_stopped":
                en = float(r["host_time"])
    return (en - st) if st is not None and en is not None else None


def results(args):
    out = args.dir
    v = lambda n: (os.path.join(out, "video", n + ".mp4") if os.path.exists(os.path.join(out, "video", n + ".mp4")) else None)
    a = argparse.Namespace(
        roi=args.roi, island_roi=args.island_roi, noise_floor=args.noise_floor, poses_n=args.poses_n, poses=None,
        g1=v("g1_control"), g2=v("g2_calibrate_8hz"), g2_wall=_wall(out, "g2_calibrate_8hz"),
        fast=v("p2_shape_fast"), normal=v("p2_shape_normal"), rest=v("p2_shape_rest"), bg60=v("p2_fast_bg60"),
        baseline=v("j8_still") or v("p0_timer_font") if args.island_roi else None)
    return judge(a)


# ----------------------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--roi", help="캐릭터 칸 x,y,w,h (영상 픽셀). 없으면 전체 화면")
        p.add_argument("--poses-n", type=int, default=0, help="포즈 종류 수(0 이면 점유율로 자동)")
        p.add_argument("--noise-floor", type=float, default=NOISE_FLOOR)
        p.add_argument("--json", action="store_true")

    p = sub.add_parser("measure", help="영상 한 개의 변화율·주기·멈춤")
    p.add_argument("video"); common(p)
    p.add_argument("--poses", nargs="+", help="기대 순서의 포즈 그림 파일들")
    p.add_argument("--start", type=float, default=0.0, help="앞에서 버릴 초")
    p.add_argument("--end", type=float, default=None, help="이 시각(영상 pts, 초) 이후는 버림")

    p = sub.add_parser("g1", help="대조 영상: 변화 0 인가")
    p.add_argument("video"); common(p)

    p = sub.add_parser("g2", help="녹화 유효성: 길이비, 교정 변화율")
    p.add_argument("video"); common(p)
    p.add_argument("--wall-seconds", type=float, help="date 두 시각 차 또는 timeline.csv 의 녹화 초")
    p.add_argument("--no-calibration", action="store_true", help="교정 화면이 아닌 영상은 길이비만")
    p.add_argument("--target-hz", type=float, default=8.0)

    p = sub.add_parser("shots", help="스크린샷 대체 모드")
    p.add_argument("dir"); common(p)
    p.add_argument("--csv"); p.add_argument("--case")

    p = sub.add_parser("judge", help="G1·G2·J1~J5 판정표")
    common(p)
    for n in ("g1", "g2", "fast", "normal", "rest", "bg60", "baseline"):
        p.add_argument("--" + n)
    p.add_argument("--g2-wall", type=float)
    p.add_argument("--island-roi", help="섬 폭 측정 영역 x,y,w,h (J4)")
    p.add_argument("--poses", nargs="+")

    p = sub.add_parser("results", help="CI 결과 폴더(video/, timeline.csv)로 judge")
    p.add_argument("dir"); common(p)
    p.add_argument("--island-roi")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "measure":
            roi = parse_roi(args.roi)
            t, X = decode_thumbs(args.video, roi)
            keep = (t >= t[0] + args.start) & (t <= (args.end if args.end is not None else 1e18))
            t, X = t[keep], X[keep]
            m = analyze_series(t, X, args.poses_n, load_refs(args, roi, args.video), floor=args.noise_floor)
            print(json.dumps(m, ensure_ascii=False, indent=1) if args.json else fmt_measure(m, os.path.basename(args.video)))
        elif args.cmd == "g1":
            r = g1(args.video, parse_roi(args.roi), args.noise_floor)
            print(json.dumps(r, ensure_ascii=False) if args.json else
                  f"G1 {'통과' if r['pass'] else '실패'}: 프레임 {r['frames']}장, 프레임 간 최대 변화 {r['max_between_frames']:.3f}, 중앙값 대비 최대 {r['max_from_median']:.3f} (허용 {r['floor']})")
        elif args.cmd == "g2":
            r = g2(args.video, parse_roi(args.roi), args.wall_seconds, args.target_hz, calibration=not args.no_calibration)
            print(json.dumps(r, ensure_ascii=False) if args.json else
                  f"G2 {'통과' if r['pass'] else '실패'}: 영상 {r['duration']:.3f}초, 길이비 {r['ratio'] if r['ratio'] is None else round(r['ratio'], 3)}, 교정 변화율 {r['rate'] if r['rate'] is None else round(r['rate'], 2)}/초")
        elif args.cmd == "shots":
            r = shots(args.dir, args.csv, args.case, parse_roi(args.roi), args.poses_n)
            print(json.dumps(r, ensure_ascii=False) if args.json else
                  f"스크린샷 {r['shots']}장, 포즈 {r['distinct_poses']}종, 이웃 장 포즈 달라짐 {r['different_pairs']*100:.0f}%, 움직임 {'있음' if r['motion_seen'] else '없음'}\n{r['note']}")
        else:
            r = judge(args) if args.cmd == "judge" else results(args)
            if args.json:
                print(json.dumps(r, ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
            else:
                print(fmt_judge(r))
                for k, m in r["measures"].items():
                    if m:
                        print(fmt_measure(m, k))
    except InputError as e:
        print(f"입력 오류: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
