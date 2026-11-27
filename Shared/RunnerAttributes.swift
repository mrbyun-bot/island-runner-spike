// Live Activity 데이터 정의. 앱과 위젯 확장 둘 다 이 파일을 컴파일한다.
// 상태 데이터는 4KB 한도(애플 문서)가 있으므로 정수 하나와 시각 하나만 넣는다.

import ActivityKit
import Foundation

public struct RunnerAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        /// 0 쉼, 1 보통, 2 빠름, 3 최고(12fps, 선택). FrameSchedule.tiers 참고.
        public var speedTier: Int
        /// 프레임 배치의 기준 시각. 단계를 바꿔도 그대로 둔다(창 배치만 바뀐다).
        public var anchor: Date

        public init(speedTier: Int, anchor: Date) {
            self.speedTier = speedTier
            self.anchor = anchor
        }
    }

    /// 그림 묶음: "shape"(P1·P2, 1색 도형 4장) 또는 "hamster"(P3)
    public var art: String
    /// 표시 방식: "sprite"(기본, 마스크 애니메이션), "p0"(타이머 글자 1개만 흰색으로 보임),
    /// "still"(정지 포즈 강제, J8 미리보기), 2회차 시험 모드 "probe0"~"probe3", "p0w", "spritew"
    /// (전체 목록 SpikeConstants.modes, 뜻은 Shared/SpriteView.swift 머리말)
    public var mode: String

    public init(art: String, mode: String) {
        self.art = art
        self.mode = mode
    }
}

/// 그림 파일 이름. 파일은 Assets/frames/ (그래픽 디자이너 담당, @3x 108×108px).
public struct ArtSet {
    /// 움직임 층 밑에 고정으로 깔 바탕 (없으면 nil)
    public let base: String?
    public let frames: [String]
    public let still: String

    /// 단계별로 쓸 그림. 쉼은 호흡 2장(통그림이라 바탕을 깔지 않는다).
    public static func forTier(_ tier: Int, art: String) -> ArtSet {
        let plan = FrameSchedule.plan(tier: tier)
        if art == "hamster" {
            if plan.frameCount == 2 {
                return ArtSet(base: nil, frames: ["hamster_rest_1", "hamster_rest_2"], still: "hamster_still")
            }
            return ArtSet(base: "hamster_bg",
                          frames: ["hamster_run_1", "hamster_run_2", "hamster_run_3", "hamster_run_4"],
                          still: "hamster_still")
        }
        if plan.frameCount == 2 {
            return ArtSet(base: nil, frames: ["shape_1", "shape_3"], still: "shape_1")
        }
        return ArtSet(base: nil, frames: ["shape_1", "shape_2", "shape_3", "shape_4"], still: "shape_1")
    }
}

public enum SpikeConstants {
    public static let logSubsystem = "com.islandrunner.spike"
    public static let evenFont = "IRMaskEven"
    public static let oddFont = "IRMaskOdd"
    public static let fontFiles = ["IRMaskEven.ttf", "IRMaskOdd.ttf"]
    /// 축소 칸 캐릭터 크기(pt). 그림은 @3x 108px 이므로 표시 크기와 정확히 같다.
    public static let compactSize: CGFloat = 36
    /// 실행 인자 -mode 로 받을 수 있는 값 (뜻은 Shared/SpriteView.swift 머리말)
    public static let modes = ["sprite", "spritew", "p0", "p0w", "still", "probe0", "probe1", "probe2", "probe3"]
}
