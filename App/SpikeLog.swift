// 앱 로그: os.Logger(시스템 로그) + 앱 Documents/spike-log.txt 두 곳에 같은 줄을 남긴다.
// 워크플로가 `xcrun simctl get_app_container ... data` 로 파일을 꺼내 results 에 넣는다.
// 줄 형식: <유닉스 시각(초, 소수 3자리)>\t<사건>\t<내용>

import CoreText
import Foundation
import os
import UIKit

enum SpikeLog {
    private static let logger = Logger(subsystem: SpikeConstants.logSubsystem, category: "app")
    private static let queue = DispatchQueue(label: "spike.log")

    static var fileURL: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("spike-log.txt")
    }

    static func write(_ event: String, _ detail: String = "") {
        let now = Date().timeIntervalSince1970
        let line = String(format: "%.3f", now) + "\t" + event + "\t" + detail + "\n"
        logger.notice("\(event, privacy: .public) \(detail, privacy: .public) t=\(now)")
        queue.async {
            let url = fileURL
            if let data = line.data(using: .utf8) {
                if let handle = try? FileHandle(forWritingTo: url) {
                    handle.seekToEndOfFile()
                    handle.write(data)
                    try? handle.close()
                } else {
                    try? data.write(to: url)
                }
            }
        }
    }

    /// 폰트 파일 크기와 PostScript 이름을 남긴다. 앱 번들과 위젯 확장(.appex) 번들 둘 다 본다.
    static func logFonts() {
        var bundles: [(String, URL)] = [("app", Bundle.main.bundleURL)]
        if let plugins = Bundle.main.builtInPlugInsURL,
           let items = try? FileManager.default.contentsOfDirectory(at: plugins, includingPropertiesForKeys: nil) {
            for item in items where item.pathExtension == "appex" {
                bundles.append(("appex:" + item.lastPathComponent, item))
            }
        }
        for (label, dir) in bundles {
            for file in SpikeConstants.fontFiles {
                let url = dir.appendingPathComponent(file)
                let size = (try? FileManager.default.attributesOfItem(atPath: url.path))?[.size] as? Int
                var names: [String] = []
                if let descs = CTFontManagerCreateFontDescriptorsFromURL(url as CFURL) as? [CTFontDescriptor] {
                    for d in descs {
                        if let n = CTFontDescriptorCopyAttribute(d, kCTFontNameAttribute) as? String { names.append(n) }
                    }
                }
                write("font_file", "\(label) \(file) bytes=\(size.map(String.init) ?? "없음") psNames=\(names)")
            }
        }
        // 앱 Info.plist 의 UIAppFonts 로 등록됐는지 (위젯 확장도 같은 방식으로 등록한다)
        for name in [SpikeConstants.evenFont, SpikeConstants.oddFont] {
            write("font_loaded", "\(name) app=\(UIFont(name: name, size: 36) != nil)")
        }
    }
}
