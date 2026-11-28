// 그림 파일 이름을 정하는 단 한 곳. 뷰·위젯·테스트는 모두 여기서 이름을 받는다.
// Foundation 만 쓰므로 단위 테스트 타깃(SpikeTests)도 이 파일을 컴파일한다.
//
// art 값과 파일 (모두 @3x PNG, 번들 맨 위에 평평하게 복사됨 — project.yml 머리말 참고)
//   hamster2 / penguin / rocket   Assets/frames/characters/{char}_run_1..4, _rest_1..2, _still
//                                 작은 칸(compact·minimal) 108×108px, 큰 칸(확장·잠금 화면) 이름 끝에 _L, 240×240px
//                                 각 장이 완성된 통그림이라 base(바탕)는 없다.
//   hamster   시험·회귀용 옛 임시 햄스터 Assets/frames/hamsterold_*.png (바탕 hamsterold_bg 를 따로 깐다)
//   shape     시험·회귀용 1색 도형      Assets/frames/shape_1..4.png
//   큰 칸 그림이 없는 옛 두 묶음(hamster, shape)은 큰 칸에서도 같은 파일을 쓴다.

import Foundation

/// 그림 파일 이름. 파일은 Assets/frames/ (그래픽 디자이너 담당).
public struct ArtSet {
    /// 움직임 층 밑에 고정으로 깔 바탕 (없으면 nil)
    public let base: String?
    public let frames: [String]
    public let still: String

    /// 새 캐릭터 3종: art 값 → 파일 이름 앞부분
    public static let characterPrefix: [String: String] = [
        "hamster2": "hamster",
        "penguin": "penguin",
        "rocket": "rocket",
    ]
    /// 앱이 받아들이는 art 값. 첫 번째가 기본값.
    public static let allArts = ["hamster2", "penguin", "rocket", "hamster", "shape"]
    public static let defaultArt = "hamster2"

    /// 단계별로 쓸 그림. 쉼은 호흡 2장, 나머지는 달리기 4장.
    /// large 가 true 면 확장·잠금 화면용 큰 파일(_L, 240px)을 돌려준다.
    public static func forTier(_ tier: Int, art: String, large: Bool = false) -> ArtSet {
        let rest = FrameSchedule.plan(tier: tier).frameCount == 2
        if let prefix = characterPrefix[art] {
            let suffix = large ? "_L" : ""
            let frames = rest
                ? ["\(prefix)_rest_1\(suffix)", "\(prefix)_rest_2\(suffix)"]
                : (1...4).map { "\(prefix)_run_\($0)\(suffix)" }
            return ArtSet(base: nil, frames: frames, still: "\(prefix)_still\(suffix)")
        }
        if art == "hamster" {
            if rest {
                return ArtSet(base: nil, frames: ["hamsterold_rest_1", "hamsterold_rest_2"], still: "hamsterold_still")
            }
            return ArtSet(base: "hamsterold_bg",
                          frames: ["hamsterold_run_1", "hamsterold_run_2", "hamsterold_run_3", "hamsterold_run_4"],
                          still: "hamsterold_still")
        }
        if rest {
            return ArtSet(base: nil, frames: ["shape_1", "shape_3"], still: "shape_1")
        }
        return ArtSet(base: nil, frames: ["shape_1", "shape_2", "shape_3", "shape_4"], still: "shape_1")
    }

    /// 이 art 가 모든 단계·두 크기에서 쓰는 파일 이름(확장자·@3x 없이) 전체. 테스트와 tools/check_art_files.py 가 쓴다.
    public static func requiredNames(art: String) -> Set<String> {
        var names = Set<String>()
        for large in [false, true] {
            for tier in 0..<FrameSchedule.tiers.count {
                let set = forTier(tier, art: art, large: large)
                names.formUnion(set.frames)
                names.insert(set.still)
                if let base = set.base { names.insert(base) }
            }
        }
        return names
    }
}

public enum SpikeConstants {
    public static let logSubsystem = "com.islandrunner.spike"
    public static let evenFont = "IRMaskEven"
    public static let oddFont = "IRMaskOdd"
    public static let fontFiles = ["IRMaskEven.ttf", "IRMaskOdd.ttf"]
    /// 축소 칸 캐릭터 크기(pt). 그림은 @3x 108px 이므로 표시 크기와 정확히 같다.
    public static let compactSize: CGFloat = 36
    /// 확장·잠금 화면 캐릭터 크기(pt). 그림은 @3x 240px.
    public static let largeSize: CGFloat = 80
    /// 실행 인자 -mode 로 받을 수 있는 값 (뜻은 Shared/SpriteView.swift 머리말)
    public static let modes = ["sprite", "spritew", "p0", "p0w", "still", "probe0", "probe1", "probe2", "probe3"]
}
