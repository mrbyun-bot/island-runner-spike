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

    /// 그림 묶음: "hamster2"(새 햄스터, 기본), "penguin", "rocket", 시험·회귀용 "hamster"(옛 임시 햄스터), "shape"(1색 도형 4장).
    /// 허용 목록과 파일 이름 규칙은 Shared/ArtSet.swift 한 곳에 있다.
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
