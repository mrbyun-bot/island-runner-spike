# 개발자용 화면 명세 (1라운드, 2026-11-29)

기준 기기 iPhone 17 Pro(402×874pt), 다크 우선·라이트 점검. 값 이름은 `tokens.md`, 부품은 `components.md`. 캡처는 `screens/`, 소스는 `src/`(`flock -w 900 /var/tmp/claude-browser.lock node design/src/render.mjs` 로 다시 찍음, Playwright 필요).

지금 `App/ContentView.swift` 의 시험 화면(단계 버튼, 시작/종료)을 아래 구조로 바꾼다. 시험용 버튼은 `#if DEBUG` 설정 아래 "개발" 구역으로 옮긴다.

## 0. 앱 뼈대

```
RootTabView (TabView, 탭 3)
├─ RunnerTab      NavigationStack { HomeView }         gauge.with.needle  "러너"
├─ CharactersTab  NavigationStack { CharacterPickerView } square.grid.2x2 "캐릭터"
└─ SettingsTab    NavigationStack { SettingsView }      gearshape          "설정"
```

- 제목은 `.navigationTitle` + `.navigationBarTitleDisplayMode(.large)`.
- 색은 Asset 카탈로그 Color Set(Any/Dark)로 `irBackground` 등 토큰 이름 그대로 만든다. `.tint(.irAccentText)` 를 루트에.
- 글자는 시스템 텍스트 스타일만. 고정 크기는 큰 숫자 2개(56, 34)뿐이며 `@ScaledMetric(relativeTo: .largeTitle)` 로 키운다.

## 1. 홈 `HomeView` (screens/home-dark.png, home-light.png)

| 순서 | 부품 | 값 |
|---|---|---|
| 1 | `PreviewStage(mode: .live)` 검정 무대, 가로 꽉 참 | 위 16, 좌우 16. 캐릭터 132pt, 사이 16. 오른쪽: caption2 "기기 전체 CPU" / 56pt 숫자 / subheadline "보통 · 한 바퀴 1초" |
| 2 | `CPUSparkline` | 무대 안 아래, 위 14 아래 10, 높이 44 |
| 3 | `MetricStrip` | 3칸, 칸 안쪽 14/16, 아래 0.5 선 |
| 4 | 구역 "속도 단계" + `TierRuler` | 구역 제목 위 20 아래 8, 자 높이 28 |
| 5 | 구역 "다이내믹 아일랜드" + `LiveActivityRow` | surface, 반경 14 |
| 6 | 안내 한 줄(footnote) | "iOS는 8시간이 지나면 아일랜드를 내립니다. 끝나기 10분 전에 알림을 드리니 눌러서 다시 켜 주세요." |
| 7 | 이동 행 "위젯·잠금 화면 기준 · 배터리 ›" | 설정 탭의 같은 항목으로 |

데이터와 갱신
- `MetricsSampler`(앱이 앞에 있을 때만): 1초마다 `host_processor_info` 차이로 CPU, `host_statistics64` 로 메모리, `UIDevice.batteryLevel`(`isBatteryMonitoringEnabled = true`). 화면이 뒤로 가면 멈춤(`scenePhase`).
- 단계 = CPU 0~9 쉼 / 10~49 보통 / 50~79 빠름 / 80~ 최고(제안). 단계가 바뀔 때만 Live Activity 갱신(값 갱신은 아래 6절).
- 앱 안 캐릭터는 `TimelineView(.animation)` 으로 부드럽게(프레임 교체, 단계별 한 바퀴 2.0/1.0/0.5/0.33초 = `FrameSchedule.tiers`). 지금 `RunnerSprite` 재사용.
- 손쉬운 사용 "동작 줄이기" 켜짐: 앱 안 캐릭터는 정지 포즈 + 단계 글자만. 그래프는 그대로.

## 2. 캐릭터 선택 `CharacterPickerView` (screens/characters-dark.png, -light.png, characters-pack-sheet-dark.png)

| 순서 | 부품 | 값 |
|---|---|---|
| 1 | `PreviewStage(mode: .browse)` | 캐릭터 116, 이름 title2, 상태 줄, `SpeedPicker` 위 12, 버튼 위 12, 아래 줄 "아일랜드에서는 [알약 120×30, 캐릭터 22]" |
| 2 | 구역 "기본" + "무료 3종" | |
| 3 | `LazyVGrid(columns: 3, spacing: 8)` 세로 간격 16 | `CharacterTile` |
| 4 | 구역 "동물 팩" + 가격 링크 "1,100원 ›" → `PackSheet` | |
| 5 | 칸 6개(잠김) | |
| 6 | 구역 "탈것·사물 팩" + 칸 5개 | (캡처에서는 스크롤 아래) |

상태
- `selectedID`(저장: App Group `UserDefaults`, 키 `selectedCharacterID`) / `previewID`(화면 안에서만) / `previewTier`(기본 = 지금 단계).
- 무료 칸 탭 → `selectedID` 저장 → 아일랜드가 켜져 있으면 다시 시작(`art` 는 Activity 정적 속성이라 갱신 불가, 지금 `startOrUpdate` 가 끝내고 다시 엶). 다시 여는 동안 아일랜드가 잠깐 비는 것은 받아들임. 햅틱 `UISelectionFeedbackGenerator`(SwiftUI `.sensoryFeedback(.selection, trigger: selectedID)`).
- 잠긴 칸 탭 → `previewID` 만 바뀜. 선택 체크는 그대로.
- 팩 시트: `.sheet(item:)` + `.presentationDetents([.medium, .large])` + `.presentationDragIndicator(.visible)`. MVP 는 구매 버튼 꺼짐.
- 구매 후(MVP 이후): StoreKit 2 `Transaction.currentEntitlements` 로 `ownedPackIDs` 계산 → 칸 잠김 해제, `.sensoryFeedback(.success, …)`.

## 3. 설정 `SettingsView` (screens/settings-dark.png, -light.png)

`Form`:
1. "위젯·잠금 화면이 따르는 값": 배터리 잔량(기본) / 마지막으로 잰 CPU. `Picker(.inline)`. footer: "앱이 꺼져 있으면 iOS가 CPU를 계속 재지 못하게 합니다. 앱 안에서는 항상 실시간 CPU로 달립니다."
2. "다이내믹 아일랜드": `Toggle` "끝나기 전에 알림"(로컬 알림, 시작 + 7시간 50분), 행 "움직임 줄이기 · iOS 설정 따름 ›"(설명 화면). footer: "iOS는 아일랜드를 최대 8시간 띄웁니다. 끝나기 10분 전 알림을 누르면 다시 켜집니다."
3. "구매": [구매 복원] (`AppStore.sync()`).
4. "정보": 개인정보 처리방침 ↗, 이용약관 ↗(`Link`, 주소는 변호사·개인정보 담당 확정 후), 문의하기 ›, 버전.
5. `#if DEBUG` "개발": 지금 ContentView 의 단계 버튼, 방식(mode), 모두 종료.

## 4. Live Activity (screens/island-expanded.png, island-states-spec.png, lockscreen-live-activity.png)

| 모양 | 내용 | 값 |
|---|---|---|
| compact leading | 캐릭터 36 | 카메라에 붙임 |
| compact trailing | 따르는 값 숫자 "42%" | 15pt semibold, 지표 색, 4글자 이하 |
| minimal | 캐릭터만 | 28pt 원 안에 들어가게(좁은 폭) |
| expanded leading | 캐릭터 80 | 좌 20 위 14 |
| expanded trailing | caption2 "CPU" + 34pt 숫자 | 우 22 위 16, 오른쪽 정렬 |
| expanded center | "보통 · 한 바퀴 1초" | subheadline |
| expanded bottom | 단계 띠 4pt + "메모리 64% · 배터리 78% · 5시간 48분 남음" | footnote |
| 잠금 화면 | 캐릭터 80 + 오른쪽 열(머리 줄 "러너 · 배터리 기준 · 9:38 갱신" / 34pt 숫자 + 단계 / 띠 / 나머지 값) | 안쪽 14(HIG 표준), 배경 `.activityBackgroundTint(.black)`, 글자 뼈색 |

- 키라인: `.keylineTint(Color.irAccent.opacity(0.3))`.
- 애니메이션은 캐릭터 프레임 교체와 숫자 `.contentTransition(.numericText())` 뿐(HIG: 2초 이하, Always-On 저휘도에서는 시스템이 멈춤).
- 잠금 화면은 라이트·다크 모두 검정 배경으로 고정(캐릭터가 검정 기준으로 그려짐). Always-On 저휘도에서 주황·초록 숫자가 읽히는지 실기기 확인 필요.

## 5. 위젯 (선택, screens/widgets-small-medium.png)

소: 캐릭터 정지 64 + 값 + "배터리 · 9:38". 중: 캐릭터 96 + 값 + 두 줄 표. 배경 `.containerBackground(.black, for: .widget)`. 캐릭터는 `still` 한 장.

## 6. ContentState 확장 제안 (지금은 `speedTier`, `anchor` 둘뿐)

확장·잠금 화면이 숫자를 보이려면 값이 필요하다. 4KB 한도 안.

```swift
public struct ContentState: Codable, Hashable {
    public var speedTier: Int
    public var anchor: Date
    public var basis: MetricBasis      // .cpu(앱이 앞에 있을 때) / .battery / .lastCPU
    public var cpu: UInt8?             // 0~100
    public var memory: UInt8?          // 0~100
    public var battery: UInt8?         // 0~100
    public var measuredAt: Date        // "9:38 갱신"
    public var endsAt: Date            // 시작 + 8시간, "남음" 계산
}
```

- 앱이 앞: basis `.cpu`, 단계가 바뀌거나 값이 5%p 넘게 바뀔 때 갱신(너무 잦은 갱신 피함, 최소 간격 개발자 판단).
- 앱이 뒤: 사용자가 고른 기준으로 전환. 배터리는 `UIDevice.batteryLevelDidChangeNotification` 을 받을 수 있을 때만 갱신(백그라운드에서 언제 깨는지는 실기기 확인 필요, 확인 못 함).

## 7. 캐릭터 데이터 구조 제안

```swift
enum PackID: String, Codable { case free, animals, vehicles, seasonal }

struct CharacterInfo: Identifiable, Hashable {
    let id: String            // 파일 이름 앞부분과 같음. 예: "hamster", "dog", "paper_plane"
    let nameKey: String       // Localizable 키. 예: "character.hamster" → "햄스터"
    let pack: PackID
    let order: Int            // 팩 안 순서
    var isFree: Bool { pack == .free }
}

struct PackInfo: Identifiable {
    let id: PackID
    let productID: String?    // StoreKit. 예: "com.<팀>.islandrunner.pack.animals" (번들 ID 정해지면)
    let characterIDs: [String]
}
```

- 목록은 코드 상수(`CharacterCatalog.all`)로 둔다. 서버 불필요.
- 파일 이름 규칙: `{id}_{run_1..4, rest_1..2, still}@3x.png`(36pt용, 108px), 큰 그림은 끝에 `_L`(`{id}_run_1_L@3x.png`, 80pt용 240px). 지금 `ArtSet.characterPrefix` 의 "hamster2" → "hamster" 같은 별칭은 정식판에서 없애고 id = 파일 앞부분으로 맞춘다.
- 잠금 여부 = `!isFree && !ownedPacks.contains(pack)`. 미리보기는 잠겨 있어도 가능(그림은 앱에 다 들어 있음).
- 임시 id: 무료 `hamster`, `penguin`, `rocket` / 동물 `dog`, `rabbit`, `turtle`, `duck`, `squirrel`, `panda` / 탈것·사물 `bicycle`, `skateboard`, `balloon`, `paper_plane`, `train`. 캐릭터가 바뀌면 이 목록만 고친다.

## 8. 접근성 확인표

- [ ] 모든 누르는 곳 44×44pt 이상(작은 버튼은 `.contentShape` 로 넓힘). 캐릭터 칸 118pt.
- [ ] Dynamic Type: 기본~AX5 에서 홈 무대가 가로 배치 → 세로 배치로 바뀜(`ViewThatFits` 또는 `dynamicTypeSize >= .accessibility1` 분기). 캐릭터 칸은 AX 크기에서 2열.
- [ ] VoiceOver 레이블: 무대 "햄스터, 보통 속도로 달리는 중", 칸 "토끼, 동물 팩, 잠김", 그래프 요약 한 줄, 아일랜드 행 "달리는 중, 5시간 48분 남음".
- [ ] 선택 상태는 테두리 색만이 아니라 체크 배지와 "사용 중" 글자로도 보임(색만으로 구분 금지).
- [ ] 동작 줄이기: 앱 안 캐릭터 정지 + 단계 글자. 아일랜드 쪽은 프레임 교체가 시스템 동작 줄이기에 걸리는지 확인 못 함 → 실기기 확인.
- [ ] 라이트 모드 주황 글자는 `irAccentText`(#A34A00)만.
- [ ] 햅틱: 선택 `.selection`, 구매 성공 `.success`, 그 외 없음.

## 9. 확인 못 한 것

- iPhone 17 Pro(402pt) 기종의 확장 아일랜드·잠금 화면·위젯 정확한 크기: HIG 표에 393·430 값만 있음. 목업은 393 값과 22pt 차이로 추정(380pt).
- SF Pro, SF Symbols 는 이 서버(리눅스)에 없어 목업은 Noto Sans CJK KR 과 흉내 낸 선 아이콘으로 그림. 실제 글자 폭은 조금 다르다.
- 애니메이션은 캡처(정지 PNG)라 보이지 않는다. 클라우드 맥 시뮬레이터 `xcrun simctl io booted recordVideo` 로 확인 계획.
