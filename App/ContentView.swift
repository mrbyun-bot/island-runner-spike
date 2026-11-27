// 앱 본 화면: 단계 버튼과 미리보기. 미리보기는 위젯과 같은 RunnerSprite 를 쓴다
// (앱 안에서 마스크가 도는지 먼저 보면 위젯 문제와 폰트 문제를 가를 수 있다).

import SwiftUI

struct ContentView: View {
    @ObservedObject var controller: ActivityController
    let options: LaunchOptions
    @State private var previewAnchor = Date()

    private let tierNames = ["쉼 2초", "보통 1초", "빠름 0.5초", "최고 0.33초"]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("아일랜드 러너 스파이크")
                .font(.system(size: 20, weight: .bold))
            Text("그림 \(options.art) · 방식 \(options.mode) · \(controller.status)")
                .font(.system(size: 13))
                .foregroundStyle(Color.secondary)

            HStack(spacing: 24) {
                RunnerSprite(tier: controller.tier, anchor: previewAnchor, art: options.art, mode: options.mode)
                RunnerSprite(tier: controller.tier, anchor: previewAnchor, art: options.art, mode: options.mode,
                             size: 108)
            }
            .padding(12)
            .background(Color.black)

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
                        await controller.startOrUpdate(tier: controller.tier, art: options.art,
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
