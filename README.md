# 아일랜드 러너 스파이크

다이내믹 아일랜드 축소 칸(36pt)에서 캐릭터가 계속 달리는 것처럼 보이게 할 수 있는지, 속도 단계를 바꿀 수 있는지 시뮬레이터로 확인하는 시험용 저장소다. 결정 문서: `~/island-runner/docs/team/2026-11-27-la-animation-spike/3-decision.md` (방식 ② 타이머 글자 + 깜빡임 마스크 폰트).

- 이 서버(리눅스)에는 Swift·Xcode·XcodeGen 이 없다. Swift 코드는 아직 한 번도 컴파일하지 않았고, 첫 맥 실행(R2)이 첫 컴파일이다.
- 원격 저장소: `git@github.com:mrbyun-bot/island-runner-spike.git` (main 에 코드, `results` 브랜치에 맥 실행 결과).
- 그림·글꼴은 모두 팀이 직접 만들었다. `widget-anim-lab`, `WidgetAnimation`(둘 다 MIT)은 원리 설명만 참고했고 코드는 보지 않고 새로 썼다.

## 원리 한 단락

`Text(timerInterval:)` 는 시스템이 1초마다 숫자를 바꿔 그린다. 시작 시각을 1/8초씩 어긋나게 잡은 타이머를 여러 개 두면 숫자가 바뀌는 순간이 서로 다르다. 마스크 폰트는 마지막 숫자가 짝수(IRMaskEven) 또는 홀수(IRMaskOdd)일 때만 칸을 채우므로 타이머 하나가 "2초 중 정해진 1초 동안 열리는 창"이 되고, 창 두 개를 곱하면(마스크의 마스크) 1/8초 구간만 열린다. 프레임 그림(PNG)은 그 창으로만 보인다. 색은 PNG 가 내고 폰트는 언제 보일지만 정한다.

## 폴더

```
project.yml                     XcodeGen 정의 (맥에서 xcodegen generate)
App/                            앱: 실행 인자 자동 시작, 단계 버튼, 교정 화면, 로그
RunnerLiveActivity/             Live Activity 위젯 확장 (위젯 1개)
Shared/                         앱·확장 공용: 데이터 정의, 프레임 배치 계산, 캐릭터 뷰
Tests/                          프레임 배치 계산 단위 테스트 (XCTest)
Fonts/                          tools/fontgen.py 가 만든 마스크 폰트 2개 + ttx 덤프
Assets/frames/                  그래픽 디자이너 그림 (도형 4장, 햄스터 8장, 108×108px) — 개발자는 건드리지 않음
tools/schedule.py               프레임 배치 계산 파이썬판 + 검증표 출력
tools/fontgen.py                마스크 폰트 생성·검사
tools/ci/run_cases.sh           맥 러너 촬영 순서 (G1 → G2 → P0 → P1 → P2 → P2b → P3 → J7 시도)
tools/ci/pick_device.py         다이내믹 아일랜드가 있는 시뮬레이터 고르기
tools/ci/push_results.sh        결과를 results 브랜치에 커밋·push, 실행 횟수 기록
.github/workflows/spike.yml     클라우드 맥 워크플로 (손으로 실행)
tools/analyze.py                영상·스크린샷 판정 (G1·G2, J1~J5), 시험은 tools/test_analyze.py
```

## 결정 문서 할 일별 위치

| 할 일 | 내용 | 파일:줄 |
|---|---|---|
| L1 | 타깃 3개 | `project.yml:21`(targets), `:22` 앱 `SpikeApp`, `:65` 확장 `RunnerLiveActivity`, `:98` 테스트 `SpikeTests` |
| L1 | `NSSupportsLiveActivities` | `project.yml:44` |
| L1 | 확장 `UIAppFonts` 폰트 등록 (앱에도 같은 등록) | `project.yml:90`(확장), `:51`(앱) |
| L1 | 위젯 확장 지정 | `project.yml:88` `com.apple.widgetkit-extension` |
| L1 | 시뮬레이터 임시 서명 | `project.yml:16-18` (`CODE_SIGN_IDENTITY: "-"`) |
| L1 | 스킴(빌드·테스트) | `project.yml:109` |
| L2 | `ActivityAttributes`, `ContentState { speedTier, anchor }` | `Shared/RunnerAttributes.swift:7`, `:8` |
| L2 | 정적 속성 그림 묶음·표시 방식(`art`, `mode`) | `Shared/RunnerAttributes.swift:21-23` |
| L2 | 단계별 그림 이름 (도형/햄스터, 쉼은 호흡 통그림) | `Shared/RunnerAttributes.swift:33` |
| L2 | 축소 칸 | `RunnerLiveActivity/RunnerLiveActivity.swift:33`(왼쪽 캐릭터), `:35`(오른쪽 고정 글자) |
| L2 | 최소 | `RunnerLiveActivity/RunnerLiveActivity.swift:41` |
| L2 | 확장 | `RunnerLiveActivity/RunnerLiveActivity.swift:20` |
| L2 | 잠금 화면 | `RunnerLiveActivity/RunnerLiveActivity.swift:14`(연결), `:56`(뷰) |
| L2 | 캐릭터 뷰(마스크 애니메이션) | `Shared/SpriteView.swift:11` `RunnerSprite`, `:65` `CellMask`, `:84` `TimerMaskText` |
| L2 | 상시표시 정지 포즈 분기 (`isLuminanceReduced`, `-mode still`) | `Shared/SpriteView.swift:38` |
| L2 | P0 모드 (타이머 글자 1개를 흰색으로) | `Shared/SpriteView.swift:32` |
| L2 | 실행 인자 `-autostart -speedTier N` 등 | `App/SpikeApp.swift:14`(정의), `:22`(해석), `:57`(바로 시작) |
| L2 | `Activity.request` | `App/ActivityController.swift:36` |
| L2 | 단계 바꾸기 (앱 버튼, 주소 `islandrunner://tier/N`) | `App/ContentView.swift:32`(버튼), `App/SpikeApp.swift:62`(주소), `App/ActivityController.swift:48`, `:57`(update) |
| L2 | G2 교정 화면 (앱 안 8Hz 두 색) | `App/ContentView.swift:61` |
| L2 | 시작·갱신 시각 로그 | `App/SpikeLog.swift:19`, 호출은 `App/ActivityController.swift` 전체(request_call/ok, update_call/done, end_call) |
| L2 | 폰트 파일 크기·PostScript 이름 로그 | `App/SpikeLog.swift:38` |
| L2 | 위젯이 그릴 때마다 로그 | `RunnerLiveActivity/RunnerLiveActivity.swift:49` |
| L3 | 단계 정의 표(쉼·보통·빠름·최고) | `Shared/FrameSchedule.swift:67`, `tools/schedule.py:18` |
| L3 | 배치 계산 순수 함수 | `Shared/FrameSchedule.swift:76`(plan), `:97`(구간→조건), `:106`(1초 안으로 줄이기), `tools/schedule.py:42` |
| L3 | 보이는 프레임 흉내·타이머 시작 시각 | `Shared/FrameSchedule.swift:124`, `:144` |
| L3 | 파이썬 검증(겹침·빈 시간·한 바퀴) | `tools/schedule.py:77` |
| L3 | Swift 단위 테스트 5개 | `Tests/FrameScheduleTests.swift:15`, `:26`, `:40`, `:54`, `:61` |
| L4 | 폰트 생성 | `tools/fontgen.py:53` |
| L4 | 숫자 묶음(아라비아-인도 숫자 등 포함) | `tools/fontgen.py:36` |
| L4 | ttx 덤프와 schedule 대조 검사 | `tools/fontgen.py:107`, `:115` |
| L7 | Xcode 선택 → xcodegen 설치 → generate | `.github/workflows/spike.yml:53`, `:65`, `:68` |
| L7 | 기기 고르기·`simctl list` 기록 | `.github/workflows/spike.yml:73` |
| L7 | 빌드·단위 테스트 | `.github/workflows/spike.yml:79`, `:89` |
| L7 | 부팅·상태 막대 고정·설치 | `.github/workflows/spike.yml:100` |
| L7 | 촬영 | `.github/workflows/spike.yml:117` → `tools/ci/run_cases.sh` |
| L7 | 대조 영상(G1) → 교정 영상(G2) | `tools/ci/run_cases.sh:106`, `:112` |
| L7 | P0 → P1 → P2(J6 단계 바꾸기, J5 60초) → P2b → P3(J8) → J7 잠금 시도 | `tools/ci/run_cases.sh:118`, `:128`, `:137`(`:157` J6, `:173` J5), `:177`, `:186`, `:222` |
| L7 | 녹화(파일, `kill -INT`) + 0.3~0.7초 무작위 스크린샷 | `tools/ci/run_cases.sh:65`, `:48` |
| L7 | 로그·artifact·results push (`if: always()`) | `.github/workflows/spike.yml:125`, `:143`, `:151` → `tools/ci/push_results.sh` |

줄 번호는 2026-11-27 첫 커밋 기준이다.

## 단계별 숫자 (python3 tools/schedule.py 출력 요약)

| 단계 | 격자 | 프레임 | 장당 유지 | 한 바퀴 | 변화율 | 화면에 놓이는 타이머 글자 |
|---|---|---|---|---|---|---|
| 쉼 | 8fps | 2 | 1.0초(8칸) | 2.0초 | 1회/초 | 2 |
| 보통 | 8fps | 4 | 0.25초(2칸) | 1.0초 | 4회/초 | 16 |
| 빠름 | 8fps | 4 | 0.125초(1칸) | 0.5초 | 8회/초 | 32 |
| 최고(선택) | 12fps | 4 | 0.0833초(1칸) | 0.333초 | 12회/초 | 48 |

타이머 글자 수는 결정 문서의 추정(6~16개, 12fps 9~24개)보다 많다. 1/8초 구간 하나를 짝홀 폰트로 만들려면 타이머 2개를 곱해야 하고, 2초 주기 안에 구간이 16개(빠름) 있기 때문이다. 줄이는 방법은 아래 "R2에서 확인할 것" 6번.

## 실행 방법

리눅스(이 서버)에서:

```bash
cd ~/island-runner-spike
python3 tools/schedule.py          # 단계 표 + 겹침·빈 시간 0 검증, 실패하면 종료 코드 1
python3 tools/schedule.py --json   # 같은 계산을 JSON 으로 (QC 분석 스크립트가 읽을 수 있음)
python3 tools/fontgen.py           # Fonts/IRMaskEven.ttf, IRMaskOdd.ttf 생성 + ttx 덤프 + 검사
# 서버에 `ttx` 명령이 없으면 `python3 -m fontTools.ttx <폰트>` 로 같은 덤프를 볼 수 있다
python3 tools/fontgen.py --check   # 만들지 않고 검사만
```

클라우드 맥(저장소가 생긴 뒤, R1):

1. GitHub 저장소 Actions 탭 → `spike` → Run workflow.
2. 입력: `stage`(probe/all/p0/p1/p2/p3, 기본 probe), `include_max`(12fps, 빠름 합격 뒤에만), `screenshots`, `runner`(macos-26/macos-15), `xcode`(비우면 가장 새 것).
3. 결과는 artifact `spike-<실행번호>-<재시도>` 와 `results` 브랜치 `runs/<실행번호>-<재시도>/` 두 곳. 실행 횟수는 `results` 브랜치 `RUNS.md` 에 "n/12" 로 쌓인다(상한 12회, U3).
4. 서버에서 받기: `git fetch origin results && git worktree add ../spike-results origin/results`

결과 폴더 안: `video/*.mp4`, `shots/<케이스>/*.png` + `shots.csv`(찍기 전·후 호스트 시각), `timeline.csv`(녹화 시작·끝, 앱 실행, 단계 바꾸기 호출 시각), `cases.csv`(케이스별 단계·그림·초), `app-log.txt`(앱 로그: request/update 시각, 폰트 크기), `oslog-*.txt`(위젯 렌더 로그), `build.log`, `test.log`, `tests.xcresult`, `env.txt`(Xcode·macOS 버전), `simctl-list.txt`.

시뮬레이터에서 손으로 볼 때:

```bash
xcrun simctl launch booted com.islandrunner.spike.app -autostart -reset -art shape -speedTier 2
xcrun simctl launch booted com.apple.Preferences          # 우리 앱을 뒤로 → 아일랜드 축소 칸
xcrun simctl openurl booted islandrunner://tier/1          # 단계 바꾸기
xcrun simctl launch booted com.islandrunner.spike.app -calibrate 8   # G2 교정 화면
```

## 애플 문서로 확인한 선언 (2026-11-27, developer.apple.com 문서 JSON)

| API | 선언 | 최소 iOS |
|---|---|---|
| `Text(timerInterval:)` | `init(timerInterval: ClosedRange<Date>, pauseTime: Date? = nil, countsDown: Bool = true, showsHours: Bool = true)` | 16.0 |
| `Activity.request` | `static func request(attributes:content:pushType: PushType? = nil) throws -> Activity<Attributes>` | 16.2 |
| `ActivityContent` | `init(state: State, staleDate: Date?, relevanceScore: Double = 0.0)` | 16.2 |
| `Activity.update` | `func update(_ content: ActivityContent<...>) async` (throws 없음) | 16.2 |
| `Activity.end` | `func end(_ content: ActivityContent<...>?, dismissalPolicy: ActivityUIDismissalPolicy = .default) async` | 16.2 |
| `contentTransition(_:)` | `func contentTransition(_ transition: ContentTransition) -> some View`, 애니메이션 안에서만 효과 | 16.0 |
| `isLuminanceReduced` | `var isLuminanceReduced: Bool` (`@Environment`) | 16.0 |
| `ActivityConfiguration` | `init(for:content:dynamicIsland:)` | 16.1 |

문서에는 `countsDown: false` 일 때 무엇을 보여 주는지(경과 시간, 내림 여부) 설명이 없다. 아래 4번으로 R2에서 확인한다. 배포 대상은 iOS 17.0 으로 두었다(`project.yml:8`).

## R2에서 확인할 것 (컴파일하지 못해 확신 없는 것)

1. 컴파일 자체. 특히 `Text(timerInterval:pauseTime:countsDown:showsHours:)`, `Activity.request(attributes:content:pushType:)`, `ActivityContent(state:staleDate:)`, `.contentTransition(.identity)`, `CTFontManagerCreateFontDescriptorsFromURL` 결과를 `[CTFontDescriptor]` 로 바꾸는 부분.
2. XcodeGen 이 `Generated/*.plist` 를 만들고 `UIAppFonts`·`NSExtension`·`NSSupportsLiveActivities` 가 실제 번들 Info.plist 에 들어가는지 (`appex-info-plist.txt`, `app-info-plist.txt` 로 확인). 폰트·PNG 가 앱과 `.appex` 양쪽 번들 맨 위에 복사되는지(`app-bundle.txt`).
3. 서명 `CODE_SIGN_IDENTITY: "-"` 로 시뮬레이터 빌드·설치가 되는지, 확장이 로드되는지.
4. 타이머 글자 배치: `countsDown: false` 가 경과 시간을 내림(floor)으로 보여 주는지, 시작 시각의 소수 초가 바뀌는 순간에 그대로 반영되는지(방식 전체의 전제). 모든 타이머가 같은 방향으로 어긋나면(반올림 등) 결과는 같다.
5. 오른쪽 정렬 + 자르기(`.multilineTextAlignment(.trailing)`, `.fixedSize()`, `.frame(alignment: .trailing)`, `.clipped()`)로 마지막 숫자 한 칸만 남는지. 타이머가 가장 넓은 값만큼 자리를 잡는다는 보고(A5)가 있어, 정렬이 왼쪽으로 붙으면 칸이 비거나 엉뚱한 숫자가 보인다. P0 모드 캡처로 먼저 본다. 앱 미리보기(`ContentView`)도 같은 뷰라 앱 화면 캡처로 위젯과 앱을 비교할 수 있다.
6. 빠름 단계 타이머 글자 32개, 최고 48개를 축소 칸이 감당하는지. 안 되면: (가) `blendMode(.difference)` 로 두 타이머의 짝홀 차이(XOR)를 바로 만들면 구간당 글자 1쌍이 아니라 프레임당 2~4개로 절반이 된다(빠름 16, 보통 8). 위젯에서 혼합 모드가 그려지는지는 확인 못 함. (나) 결정 D8 후퇴선.
7. 마스크 폰트에 없는 글자를 iOS 가 다른 폰트로 대신 그리는지. 타이머에 나올 만한 글자(ASCII, 각종 공백, 콜론 변형, 아라비아-인도·데바나가리·전각 숫자)는 넣어 두었다. 시뮬레이터 지역 설정이 영어(미국)가 아니면 다른 숫자가 나올 수 있다.
8. 위젯 확장 안에서 `UIImage(named:in:with:)` 로 번들 PNG(@3x) 를 읽는지. 못 읽으면 빨간 칸이 보인다.
9. `isLuminanceReduced` 를 시뮬레이터에서 켤 방법은 확인 못 함. J8 은 `-mode still` 캡처(미리보기 대체)로만 본다.
10. `xcrun simctl io recordVideo` 와 연속 스크린샷을 동시에 돌려도 둘 다 되는지. 리눅스에서 가짜 `xcrun` 으로 순서만 시험했고, 그때 `set -m` 이 없으면 백그라운드 녹화가 `kill -INT` 를 무시하는 문제를 찾아 고쳤다. 실제 `simctl` 이 INT 로 영상을 마무리하는지는 R1에서 본다(10초 안에 안 끝나면 TERM 을 보내고 `errors.log` 에 남김).
11. 잠금 화면 자동화: `notifyutil -p com.apple.springboard.lockcomplete` 는 근거 없는 시도다. 확장 화면(길게 누르기)과 최소 화면은 자동화하지 않았다. J7 은 "확인 못 함"이 될 가능성이 높다.
12. `simctl status_bar override` 로 시계를 고정해도 G1 대조 영역에 다른 변화가 끼는지.
13. 러너 이미지 이름 `macos-26` 과 그 안의 Xcode·시뮬레이터 이름(`iPhone 17 Pro` 등). 없으면 `pick_device.py` 가 다이내믹 아일랜드 기종 중 아무거나 고르고, 그것도 없으면 실패한다.

## 2회차(probe) 준비 (2026-11-27)

1회차 결과(`results` 브랜치 `runs/1-1/`): 빌드·설치·`Activity.request` 는 됐고, 오른쪽 고정 글자와 **정지 그림(`j8_still_compact.png`)은 축소 칸에 보였다.** 타이머 글자를 쓰는 p0·sprite 만 빈칸이었다. 단위 테스트 실패는 테스트의 기준값 함수(`designedFrame`)가 음수 칸에서 Swift 정수 나눗셈(0 쪽 버림)을 쓴 탓이라 고쳤다(`python3 tools/schedule.py` 의 "Swift 정수 규칙 대조" 표가 1회차 실패 수 140·80 을 그대로 재현하고, 고친 식은 0).

`stage=probe` 는 아래를 케이스마다 8~10초씩 찍는다. 케이스마다 앱 화면(`<케이스>_app.png`), 축소 칸(`<케이스>_compact.png`), 영상(`video/<케이스>.mp4`)이 남는다.

| 케이스 | 방식 | 보이면 | 안 보이면 |
|---|---|---|---|
| q_still | 정지 그림 | 대조군(1회차에 보임) | 시뮬레이터·촬영 자체 문제 |
| q_probe0 | 주황 사각형 | 칸이 그려짐. 사각형이 잘린 높이 = 쓸 수 있는 높이 | — |
| q_probe1 | 주황 + 흰 글자 | 일반 글자 됨 | — |
| q_probe2 | 주황 + 시스템 폰트 타이머 | 타이머 글자 자체는 됨 | 축소 칸에서 타이머 글자가 안 그려짐 → 방식 ② 불가, 후퇴선 |
| q_probe3 | 회색 + 마스크 폰트 타이머(작게, 통째로) | 흰 네모 줄 = 렌더러에서 폰트가 먹음, 줄 위치 = 정렬 | 숫자 모양이 보이면 폰트가 렌더러에 없음(시스템 폰트로 대신 그림) |
| q_p0 | 1회차 배치(`.fixedSize`) | — | 1회차와 같음 |
| q_p0w | 넓은 고정 틀 + 오른쪽 정렬 | 1초 켜짐·1초 꺼짐이면 `.fixedSize` 가 원인 | probe2·3 결과와 같이 본다 |
| q_sprite / q_spritew | 도형 보통, 두 배치 | spritew 만 돌면 배치 문제 확정 | — |
| q_spritew_h | 햄스터 빠름, 넓은 틀 | 사용자에게 보여 줄 영상 | — |

로그: 확장은 `RunnerLiveActivity/WidgetLog.swift` 로 파일·`Logger.notice`·`NSLog`(앞머리 `IRSPIKE`) 세 곳에 남긴다. 워크플로가 `widget-log.txt`(확장 데이터 폴더에서 찾아 꺼냄), `oslog-stream.txt`(촬영 중 실시간), `oslog-spike.txt`(`--info --debug`), `oslog-renderer.txt`(`WidgetRenderer_Activities`·확장 프로세스)를 모은다.

### 2회차 맥에서 확인할 것 (이 서버에서 컴파일하지 못함)

1. `RunnerSprite.body` 안 `switch mode { case "probe0": ... default: if ... }` 가 ViewBuilder 로 컴파일되는지(Swift 5.3 이후 지원으로 알고 있음).
2. `TimerMaskText.body` 의 `switch layout` 두 갈래가 서로 다른 뷰 타입이어도 되는지(ViewBuilder 가 묶어 줄 것으로 봄).
3. `WidgetLog.startupCheck` 를 `static let ...: Void = { ... }()` 로 한 번만 돌리고 `_ = WidgetLog.startupCheck` 로 부르는 방식.
4. `NSLog("IRSPIKE %@ %@", event, detail)` 에 Swift `String` 을 바로 넘기는 것(CVarArg 로 연결된다고 알고 있음).
5. 위젯 확장의 `FileManager ... .documentDirectory` 가 쓰기 가능한 확장 전용 폴더인지. 1회차 설치 로그에 `Data container for com.islandrunner.spike.app.liveactivity` 가 있어 폴더는 있다. `simctl get_app_container ... com.islandrunner.spike.app.liveactivity data` 가 확장 번들 ID 를 받는지는 확인 못 함(그래서 `find` 로도 찾는다, `widget-log-where.txt`).
6. `log stream --predicate 'subsystem == "..." OR eventMessage BEGINSWITH "IRSPIKE"'` 와 `log show --info --debug` 가 `simctl spawn` 안에서 그대로 되는지.
7. `.font(.custom(_, fixedSize: 6))` 처럼 아주 작은 크기가 축소 칸에서 그대로 그려지는지(probe3).
8. 넓은 틀(`.frame(width: 36 * 8)`)을 바깥 36pt 틀에 오른쪽 정렬하면 SwiftUI 가 왼쪽으로 넘치게 두고 `.clipped()` 가 잘라 내는지. 앱 화면 캡처(`q_p0w_app.png`)로 앱 안에서 먼저 본다.

## 하지 않은 것

- `tools/analyze.py`(영상 판정): QC 담당.
- 배포 키·원격 설정(L8): 사용자 결정 U1 에 따라 보류.
- 비공개 `_clockHandRotationEffect`(결정 D9).
