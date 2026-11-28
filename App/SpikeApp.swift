// 스파이크 앱. 실행 인자로 바로 Live Activity 를 열어 클라우드 맥에서 사람 손 없이 찍는다.
//
// 실행 인자 (xcrun simctl launch <기기> com.islandrunner.spike.app <인자...>)
//   -autostart            켜지자마자 Activity.request (이미 있으면 갱신)
//   -speedTier N          0 쉼, 1 보통, 2 빠름, 3 최고(12fps)
//   -art hamster2|penguin|rocket|hamster|shape   그림 묶음 (기본 hamster2, hamster 는 옛 임시 햄스터)
//   -mode <방식>          sprite(기본)|spritew|p0|p0w|still|probe0|probe1|probe2|probe3 (SpikeConstants.modes)
//   -reset                시작 전에 있던 활동을 모두 끝냄
//   -calibrate [Hz]       교정 화면(두 색 교대, 기본 8Hz). G2 녹화 검증용
// 주소로 단계 바꾸기 (앱이 앞으로 나오며 갱신): xcrun simctl openurl <기기> islandrunner://tier/2

import SwiftUI

struct LaunchOptions {
    var autostart = false
    var speedTier = 1
    var art = ArtSet.defaultArt
    var mode = "spritew"
    var reset = false
    var calibrateHz: Double? = nil

    static func parse(_ args: [String]) -> LaunchOptions {
        var o = LaunchOptions()
        func value(after flag: String) -> String? {
            guard let i = args.firstIndex(of: flag), i + 1 < args.count, !args[i + 1].hasPrefix("-") else { return nil }
            return args[i + 1]
        }
        o.autostart = args.contains("-autostart")
        o.reset = args.contains("-reset")
        if let v = value(after: "-speedTier"), let n = Int(v) { o.speedTier = FrameSchedule.clampTier(n) }
        if let v = value(after: "-art"), ArtSet.allArts.contains(v) { o.art = v }
        if let v = value(after: "-mode"), SpikeConstants.modes.contains(v) { o.mode = v }
        if args.contains("-calibrate") {
            o.calibrateHz = value(after: "-calibrate").flatMap(Double.init) ?? 8
        }
        return o
    }
}

@main
struct SpikeApp: App {
    @StateObject private var controller = ActivityController()
    private let options = LaunchOptions.parse(ProcessInfo.processInfo.arguments)

    var body: some Scene {
        WindowGroup {
            Group {
                if let hz = options.calibrateHz {
                    CalibrationView(hz: hz)
                } else {
                    ContentView(controller: controller, options: options)
                }
            }
            .task {
                SpikeLog.write("launch", ProcessInfo.processInfo.arguments.dropFirst().joined(separator: " "))
                SpikeLog.logFonts()
                if options.autostart {
                    await controller.startOrUpdate(tier: options.speedTier, art: options.art,
                                                   mode: options.mode, reset: options.reset)
                }
            }
            .onOpenURL { url in
                // islandrunner://tier/2
                SpikeLog.write("open_url", url.absoluteString)
                guard url.host == "tier", let n = Int(url.lastPathComponent) else { return }
                Task { await controller.setTier(n) }
            }
        }
    }
}
