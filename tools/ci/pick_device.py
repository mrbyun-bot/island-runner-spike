#!/usr/bin/env python3
"""맥 러너에서 다이내믹 아일랜드가 있는 아이폰 시뮬레이터를 하나 고른다.

출력(GITHUB_OUTPUT 형식): udid=..., name=..., runtime=...
고를 수 없으면 종료 코드 1. 원본 목록은 첫 인자 경로에 저장한다(results 에 남김).
"""
import json
import re
import subprocess
import sys

PREFERRED = ["iPhone 17 Pro", "iPhone 16 Pro", "iPhone 17", "iPhone 16", "iPhone 15 Pro", "iPhone 15", "iPhone 14 Pro"]
# 다이내믹 아일랜드: 14 Pro 이후 Pro 전부, 15 이후 일반 모델. 16e·SE 는 없음.
ISLAND = re.compile(r"^iPhone (14 Pro( Max)?|1[5-9]( Plus| Pro| Pro Max)?|Air)$")


def runtime_version(key):
    m = re.search(r"iOS-(\d+)-(\d+)", key)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def main():
    raw = subprocess.run(["xcrun", "simctl", "list", "devices", "available", "-j"],
                         check=True, capture_output=True, text=True).stdout
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w") as f:
            f.write(raw)
    devices = json.loads(raw)["devices"]
    runtimes = sorted((k for k in devices if "iOS" in k), key=runtime_version, reverse=True)
    for rt in runtimes:
        avail = [d for d in devices[rt] if d.get("isAvailable", True)]
        by_name = {d["name"]: d for d in avail}
        pick = next((by_name[n] for n in PREFERRED if n in by_name), None)
        if pick is None:
            pick = next((d for d in avail if ISLAND.match(d["name"])), None)
        if pick:
            print(f"udid={pick['udid']}")
            print(f"name={pick['name']}")
            print(f"runtime={rt}")
            return 0
    print("다이내믹 아일랜드가 있는 시뮬레이터를 찾지 못함", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
