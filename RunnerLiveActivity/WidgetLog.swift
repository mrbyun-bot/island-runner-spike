// 위젯 확장 로그. 1회차에는 Logger.info 만 써서 `log show`(기본은 info 제외)에 0건이었다.
// 2회차부터 세 곳에 같은 줄을 남긴다.
//   1) 확장 자신의 데이터 폴더 Documents/widget-log.txt
//      (설치 로그에 "Data container for com.islandrunner.spike.app.liveactivity" 가 있어 확장 전용 폴더가 있다.
//       워크플로가 시뮬레이터 폴더에서 이 파일 이름으로 찾아 꺼낸다. App Group 은 서명·권한이 필요해 쓰지 않았다.)
//   2) Logger.notice (기본 수준이라 log show 에 남는다)
//   3) NSLog (앞머리 IRSPIKE, log stream 으로 잡기 쉽게)
// 확장 프로세스는 언제 멈출지 모르므로 파일 쓰기는 비동기 큐 없이 바로 한다.
// 줄 형식은 앱 로그와 같다: <유닉스 시각>\t<사건>\t<내용>

import Foundation
import os
import UIKit

enum WidgetLog {
    private static let logger = Logger(subsystem: SpikeConstants.logSubsystem, category: "widget")
    private static let lock = NSLock()

    static var fileURL: URL? {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first?
            .appendingPathComponent("widget-log.txt")
    }

    static func write(_ event: String, _ detail: String = "") {
        let now = Date().timeIntervalSince1970
        logger.notice("\(event, privacy: .public) \(detail, privacy: .public) t=\(now)")
        NSLog("IRSPIKE %@ %@", event, detail)
        let line = String(format: "%.3f", now) + "\t" + event + "\t" + detail + "\n"
        guard let url = fileURL, let data = line.data(using: .utf8) else { return }
        lock.lock()
        defer { lock.unlock() }
        try? FileManager.default.createDirectory(at: url.deletingLastPathComponent(),
                                                 withIntermediateDirectories: true)
        if let handle = try? FileHandle(forWritingTo: url) {
            handle.seekToEndOfFile()
            handle.write(data)
            try? handle.close()
        } else {
            try? data.write(to: url)
        }
    }

    /// 확장 프로세스에서 마스크 폰트가 등록됐는지, 그림을 찾는지 (프로세스마다 한 번)
    static let startupCheck: Void = {
        let fonts = [SpikeConstants.evenFont, SpikeConstants.oddFont]
            .map { "\($0)=\(UIFont(name: $0, size: 36) != nil)" }
            .joined(separator: " ")
        let images = ["shape_1", "hamster_still"]
            .map { "\($0)=\(UIImage(named: $0, in: .main, with: nil) != nil)" }
            .joined(separator: " ")
        write("ext_start", "\(fonts) \(images) bundle=\(Bundle.main.bundleURL.lastPathComponent) home=\(NSHomeDirectory())")
    }()
}
