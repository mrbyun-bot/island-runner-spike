#!/usr/bin/env bash
# 이번 실행 결과를 results 브랜치의 runs/<실행번호>-<재시도>/ 에 커밋해 push 한다.
# 실행 횟수(상한 12회)를 RUNS.md 에 한 줄씩 적는다. 실패해도 워크플로를 멈추지 않는다.
#
# 사용: tools/ci/push_results.sh <OUT_DIR> <STAGE> <빌드 결과> <테스트 결과> <촬영 결과>
# 서버에서 받기: git fetch origin results && git worktree add ../spike-results origin/results

set -uo pipefail
OUT="$1"; STAGE="$2"; BUILD="$3"; TEST="$4"; CAPTURE="$5"
RUN_ID="${GITHUB_RUN_NUMBER:-local}-${GITHUB_RUN_ATTEMPT:-1}"
RUN_DIR="runs/$RUN_ID"

# git 설정 파일은 건드리지 않고 이 스크립트 안에서만 작성자를 정한다
export GIT_AUTHOR_NAME="github-actions[bot]" GIT_COMMITTER_NAME="github-actions[bot]"
export GIT_AUTHOR_EMAIL="41898282+github-actions[bot]@users.noreply.github.com"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

WT="$(mktemp -d)"
REPO="$(pwd)"
cleanup() { cd "$REPO" && git worktree remove --force "$WT" > /dev/null 2>&1; }
trap cleanup EXIT
if git ls-remote --exit-code --heads origin results > /dev/null 2>&1; then
  git fetch --depth=1 origin "+refs/heads/results:refs/remotes/origin/results"
  git worktree add -B results "$WT" origin/results
else
  git worktree add --detach "$WT"
  (cd "$WT" && git checkout --orphan results && git rm -rfq . && git clean -fdq)
fi

cd "$WT" || exit 0
mkdir -p "$RUN_DIR"
cp -R "$OUT"/. "$RUN_DIR"/
# GitHub 파일 한도(100MB) 넘는 것은 빼고 목록만 남긴다(artifact 에는 있음)
find "$RUN_DIR" -type f -size +95M -print -delete > "$RUN_DIR/skipped-large-files.txt"

if [ ! -f RUNS.md ]; then
  {
    echo "# 맥 실행 기록 (상한 12회, 사용자 결정 U3)"
    echo
    echo "| 회차 | 실행 | 시각(UTC) | 단계 | 빌드 | 단위 테스트 | 촬영 | 커밋 |"
    echo "|---|---|---|---|---|---|---|---|"
  } > RUNS.md
fi
COUNT=$(( $(grep -c '^| [0-9]' RUNS.md) + 1 ))
echo "| $COUNT/12 | $RUN_ID | $(date -u +%Y-%m-%dT%H:%M:%SZ) | $STAGE | $BUILD | $TEST | $CAPTURE | ${GITHUB_SHA:-?} |" >> RUNS.md

git add -A
git commit -qm "실행 $RUN_ID 결과 ($COUNT/12회, 단계 $STAGE, 빌드 $BUILD, 테스트 $TEST, 촬영 $CAPTURE)"
for attempt in 1 2 3; do
  if git push origin results; then
    echo "results 브랜치에 push 함: $RUN_DIR ($COUNT/12회)"
    exit 0
  fi
  echo "push 실패, 다시 시도 $attempt"
  git pull --rebase origin results || true
done
echo "results push 를 끝내 못 함 (artifact 는 따로 올라감)"
exit 0
