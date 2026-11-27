#!/usr/bin/env bash
# 시뮬레이터 촬영 순서 (맥 러너에서 실행). 한 실행에 케이스를 몰아서 찍는다.
#
# 사용: tools/ci/run_cases.sh <UDID> <OUT_DIR> <STAGE> <INCLUDE_MAX> <SCREENSHOTS>
#   STAGE: all | p0 | p1 | p2 | p3      (G1·G2 는 항상 먼저 찍는다)
#   INCLUDE_MAX: true 면 12fps 최고 단계(P2b)도 찍는다 (사용자 결정 U2: 빠름 합격 뒤)
#   SCREENSHOTS: true 면 녹화와 같이 0.3~0.7초 무작위 간격 연속 스크린샷
#
# 순서: G1 대조 → G2 교정 → P0 → P1 → P2(쉼·보통·빠름, J6 단계 바꾸기, J5 뒤 60초) → P2b → P3(햄스터, J8 정지)
# 남기는 것 (OUT_DIR 아래)
#   video/<케이스>.mp4         simctl recordVideo (kill -INT 로 끝냄)
#   shots/<케이스>/NNNN.png    연속 스크린샷, shots.csv 에 찍기 전·후 호스트 시각
#   timeline.csv               호스트 시각,사건,케이스  (녹화 시작·끝, 앱 실행, 단계 바꾸기 호출)
#   cases.csv                  케이스,판정용 단계,그림,녹화 초,메모
# 이 스크립트는 중간에 실패해도 다음 케이스로 넘어간다(set -e 를 쓰지 않음).

set -uo pipefail
# 작업 제어를 켠다. 끄면 비대화형 bash 가 백그라운드 명령의 SIGINT 를 무시하게 만들어
# recordVideo 를 kill -INT 로 끝낼 수 없다(리눅스에서 가짜 xcrun 으로 시험해 확인).
set -m

UDID="$1"; OUT="$2"; STAGE="${3:-all}"; INCLUDE_MAX="${4:-false}"; SHOTS="${5:-true}"
BUNDLE="com.islandrunner.spike.app"
SETTINGS="com.apple.Preferences"
mkdir -p "$OUT/video" "$OUT/shots"
echo "host_time,event,case" > "$OUT/timeline.csv"
echo "case,tier,art,seconds,note" > "$OUT/cases.csv"
echo "case,index,host_before,host_after,file" > "$OUT/shots.csv"

now() { python3 -c 'import time; print(f"{time.time():.3f}")'; }
mark() { echo "$(now),$1,${2:-}" >> "$OUT/timeline.csv"; }
want() { [ "$STAGE" = "all" ] || [ "$STAGE" = "$1" ]; }

launch_app() {
  # 이미 떠 있으면 끄고 다시 띄운다. 앱은 켜지자마자 실행 인자대로 시작·갱신한다.
  mark "launch_app" "$*"
  xcrun simctl launch --terminate-running-process "$UDID" "$BUNDLE" "$@" >> "$OUT/launch.log" 2>&1 \
    || echo "앱 실행 실패: $*" | tee -a "$OUT/errors.log"
}

to_background() {
  # 설정 앱을 앞으로 띄워 우리 앱을 뒤로 보낸다 → 아일랜드 축소 칸이 보인다.
  mark "to_background" "$1"
  xcrun simctl launch "$UDID" "$SETTINGS" >> "$OUT/launch.log" 2>&1 \
    || echo "설정 앱 실행 실패" | tee -a "$OUT/errors.log"
}

screenshot_loop() {
  local name="$1" secs="$2" i=0
  mkdir -p "$OUT/shots/$name"
  local deadline
  deadline=$(python3 -c "import time; print(time.time() + $secs)")
  while python3 -c "import sys, time; sys.exit(0 if time.time() < $deadline else 1)"; do
    i=$((i + 1))
    local f="$OUT/shots/$name/$(printf '%04d' "$i").png"
    local t0 t1
    t0=$(now)
    xcrun simctl io "$UDID" screenshot --type=png "$f" > /dev/null 2>&1
    t1=$(now)
    echo "$name,$i,$t0,$t1,shots/$name/$(basename "$f")" >> "$OUT/shots.csv"
    sleep "$(python3 -c 'import random; print(f"{random.uniform(0.3, 0.7):.3f}")')"
  done
}

record() {
  # record <케이스> <초> <단계> <그림> [메모]
  local name="$1" secs="$2"
  echo "$name,$3,$4,$secs,${5:-}" >> "$OUT/cases.csv"
  local file="$OUT/video/$name.mp4" errlog="$OUT/video/$name.log"
  xcrun simctl io "$UDID" recordVideo --codec=h264 --force "$file" 2> "$errlog" &
  local pid=$!
  # "Recording started" 가 찍힐 때까지 최대 10초 기다린다(녹화가 실제로 시작된 시각을 남기려고).
  for _ in $(seq 1 50); do
    grep -q "Recording started" "$errlog" 2>/dev/null && break
    sleep 0.2
  done
  mark "record_start" "$name"
  local shots_pid=""
  if [ "$SHOTS" = "true" ]; then
    screenshot_loop "$name" "$secs" &
    shots_pid=$!
  fi
  sleep "$secs"
  mark "record_stop_call" "$name"
  kill -INT "$pid" 2>/dev/null
  # 10초 안에 안 끝나면 TERM (영상 끝부분이 깨질 수 있어 errors.log 에 남김)
  for _ in $(seq 1 50); do kill -0 "$pid" 2>/dev/null || break; sleep 0.2; done
  if kill -0 "$pid" 2>/dev/null; then
    echo "녹화가 INT 로 안 끝나 TERM 보냄: $name" | tee -a "$OUT/errors.log"
    kill -TERM "$pid" 2>/dev/null
  fi
  wait "$pid" 2>/dev/null
  mark "record_stopped" "$name"
  if [ -n "$shots_pid" ]; then wait "$shots_pid"; fi
  [ -s "$file" ] || echo "녹화 파일 비어 있음: $name" | tee -a "$OUT/errors.log"
}

still_shot() {
  mark "screenshot" "$1"
  xcrun simctl io "$UDID" screenshot --type=png "$OUT/$1.png" > /dev/null 2>&1 \
    || echo "스크린샷 실패: $1" | tee -a "$OUT/errors.log"
}

settle() { sleep "${1:-2}"; }

# ---- G1 대조: 우리 앱을 띄우지 않은 화면(설정 앱) ----
xcrun simctl terminate "$UDID" "$BUNDLE" > /dev/null 2>&1
to_background "g1"
settle 3
record g1_control 10 - - "앱 없음, 같은 영역 변화 0 이어야 함"

# ---- G2 교정: 앱 안 8Hz 두 색 교대 ----
launch_app -calibrate 8
settle 3
record g2_calibrate_8hz 10 - - "화면 전체 8Hz 교대, 측정 8±0.8"
xcrun simctl terminate "$UDID" "$BUNDLE" > /dev/null 2>&1

# ---- P0: 타이머 글자 1개 + 마스크 폰트 (흰 칸이 1초마다 켜졌다 꺼짐) ----
if want p0; then
  launch_app -autostart -reset -mode p0 -speedTier 1
  settle 3
  to_background "p0"
  settle 2
  still_shot p0_compact
  record p0_timer_font 10 p0 - "J4 폭, 폰트 로드"
fi

# ---- P1: 1색 도형 4장, 보통 단계 ----
if want p1; then
  launch_app -autostart -reset -art shape -speedTier 1
  settle 3
  to_background "p1"
  settle 2
  record p1_shape_normal 20 1 shape "포즈 4종 순서, 변화율 3/초 이상"
fi

# ---- P2: 쉼·보통·빠름, 단계 바꾸기(J6), 뒤에서 60초(J5) ----
if want p2; then
  launch_app -autostart -reset -art shape -speedTier 0
  settle 3
  to_background "p2_rest"
  settle 2
  record p2_shape_rest 20 0 shape "한 바퀴 2.0초"

  launch_app -autostart -art shape -speedTier 1
  settle 3
  to_background "p2_normal"
  settle 2
  record p2_shape_normal 20 1 shape "한 바퀴 1.0초"

  launch_app -autostart -art shape -speedTier 2
  settle 3
  to_background "p2_fast"
  settle 2
  record p2_shape_fast 20 2 shape "J1 판정 단계, 한 바퀴 0.5초"

  # J6: 보통으로 돌리다가 앱을 앞으로 불러 빠름으로 갱신 → 다시 뒤로. 녹화는 끊지 않는다.
  launch_app -autostart -art shape -speedTier 1
  settle 3
  to_background "p2_j6"
  settle 2
  (
    sleep 8
    mark "tier_change_call" "p2_j6_switch tier=2"
    xcrun simctl openurl "$UDID" "islandrunner://tier/2" >> "$OUT/launch.log" 2>&1
    sleep 2
    to_background "p2_j6_after"
  ) &
  j6_pid=$!
  record p2_j6_switch 30 "1->2" shape "8초 뒤 단계 바꾸기 호출, 앱 로그 update_call 시각과 비교"
  wait "$j6_pid"

  # J5: 빠름 단계로 뒤에서 60초
  record p2_fast_bg60 60 2 shape "J5 백그라운드 60초 멈춤 없음"
fi

# ---- P2b: 12fps 최고 단계 (선택) ----
if [ "$INCLUDE_MAX" = "true" ] && { want p2 || want p3; }; then
  launch_app -autostart -art shape -speedTier 3
  settle 3
  to_background "p2b"
  settle 2
  record p2b_shape_max 20 3 shape "12fps, 한 바퀴 0.333초"
fi

# ---- P3: 햄스터 색 PNG, 정지 포즈(J8) ----
if want p3; then
  launch_app -autostart -reset -art hamster -speedTier 0
  settle 3
  to_background "p3_rest"
  settle 2
  record p3_hamster_rest 10 0 hamster "사용자 보기용 쉼"

  launch_app -autostart -art hamster -speedTier 1
  settle 3
  to_background "p3_normal"
  settle 2
  record p3_hamster_normal 10 1 hamster "사용자 보기용 보통"

  launch_app -autostart -art hamster -speedTier 2
  settle 3
  to_background "p3_fast"
  settle 2
  record p3_hamster_fast 20 2 hamster "사용자 보기용 빠름 20초, P2 숫자 유지 확인"

  if [ "$INCLUDE_MAX" = "true" ]; then
    launch_app -autostart -art hamster -speedTier 3
    settle 3
    to_background "p3_max"
    settle 2
    record p3_hamster_max 10 3 hamster "12fps"
  fi

  launch_app -autostart -reset -art hamster -mode still -speedTier 2
  settle 3
  to_background "p3_still"
  settle 2
  still_shot j8_still_compact
  record j8_still 5 still hamster "정지 포즈 한 장, 변화 0 이어야 함"
fi

# ---- J7 시도: 잠금 화면 (공개된 simctl 잠금 명령을 확인 못 함. 안 되면 확인 못 함으로 기록) ----
if want p3; then
  launch_app -autostart -reset -art hamster -speedTier 2
  settle 3
  to_background "j7"
  settle 2
  mark "lock_attempt" "j7"
  xcrun simctl spawn "$UDID" notifyutil -p com.apple.springboard.lockcomplete >> "$OUT/launch.log" 2>&1 \
    || echo "잠금 시도 명령 실패" >> "$OUT/errors.log"
  settle 3
  still_shot j7_lock_attempt
  record j7_lock_attempt 10 2 hamster "잠금 화면이 보이면 J7 잠금 판정, 아니면 확인 못 함"
fi

mark "cases_done" "$STAGE"
echo "촬영 끝: $(grep -c record_stopped "$OUT/timeline.csv")개 녹화"
