// 앱 본 화면: 단계 버튼과 미리보기. 미리보기는 위젯과 같은 RunnerSprite 를 쓴다
// (앱 안에서 마스크가 도는지 먼저 보면 위젯 문제와 폰트 문제를 가를 수 있다).

import SwiftUI

struct ContentView: View {
    @ObservedObject var controller: ActivityController
    let options: LaunchOptions
    @State private var previewAnchor = Date()
    /// 고른 캐릭터. 처음엔 실행 인자(기본 hamster2).
    @State private var selectedArt: String

    init(controller: ActivityController, options: LaunchOptions) {
        self.controller = controller
        self.options = options
        _selectedArt = State(initialValue: options.art)
    }

    private let tierNames = ["쉼 2초", "보통 1초", "빠름 0.5초", "최고 0.33초"]
    /// 고르는 캐릭터(무료 3종). 옛 hamster·shape 는 -art 실행 인자로만 고른다.
    private let characters: [(art: String, label: String)] = [
        ("hamster2", "햄스터"), ("penguin", "펭귄"), ("rocket", "로켓"),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("아일랜드 러너 스파이크")
                .font(.system(size: 20, weight: .bold))
            Text("그림 \(selectedArt) · 방식 \(options.mode) · \(controller.status)")
                .font(.system(size: 13))
                .foregroundStyle(Color.secondary)

            HStack(spacing: 24) {
                RunnerSprite(tier: controller.tier, anchor: previewAnchor, art: selectedArt, mode: options.mode)
                RunnerSprite(tier: controller.tier, anchor: previewAnchor, art: selectedArt, mode: options.mode,
                             size: SpikeConstants.largeSize)
            }
            .padding(12)
            .background(Color.black)

            Text("캐릭터")
                .font(.system(size: 15, weight: .semibold))
            HStack(spacing: 8) {
                ForEach(0..<characters.count, id: \.self) { i in
                    Button(characters[i].label) {
                        // art 는 Activity 의 정적 속성이라 갱신이 안 된다. startOrUpdate 가 다르면 끝내고 다시 연다.
                        selectedArt = characters[i].art
                        Task {
                            await controller.startOrUpdate(tier: controller.tier, art: characters[i].art,
                                                           mode: options.mode, reset: false)
                        }
                    }
                    .buttonStyle(.bordered)
                    .tint(selectedArt == characters[i].art ? Color.orange : Color.gray)
                }
            }
            Text("단계")
                .font(.system(size: 15, weight: .semibold))
            HStack(spacing: 8) {
                ForEach(0..<tierNames.count, id: \.self) { i in
                    Button(tierNames[i]) {
                        Task { await controller.setTier(i) }
                    }
                    .buttonStyle(.bordered)
                    .tint(controller.tier == i ? Color.orange : Color.gray)
                }
            }
            HStack(spacing: 8) {
                Button("시작") {
                    Task {
                        await controller.startOrUpdate(tier: controller.tier, art: selectedArt,
                                                       mode: options.mode, reset: false)
                    }
                }
                .buttonStyle(.borderedProminent)
                Button("모두 종료") {
                    Task { await controller.endAll() }
                }
                .buttonStyle(.bordered)
            }
            Spacer()
        }
        .padding(16)
    }
}

/// G2 교정 화면: 화면 전체가 hz 마다 검정·흰색으로 바뀐다(8Hz 면 초당 8번 변화).
/// 앱 안이라 TimelineView 가 제대로 돈다. 녹화 영상에서 변화율이 8±0.8 이면 녹화가 믿을 만하다.
struct CalibrationView: View {
    let hz: Double

    var body: some View {
        TimelineView(.animation) { context in
            let phase = Int(floor(context.date.timeIntervalSince1970 * hz))
            (phase % 2 == 0 ? Color.black : Color.white)
                .ignoresSafeArea()
        }
        .onAppear { SpikeLog.write("calibrate_start", "hz=\(hz)") }
    }
}
