// 프레임 배치 계산 (순수 함수, Foundation 만 쓴다)
//
// 원리: Text(timerInterval:) 는 시스템이 1초마다 숫자를 바꿔 그린다. 시작 시각을
// 1/8초(또는 1/12초)씩 어긋나게 잡은 타이머 여러 개를 두면 각 타이머는 서로 다른
// 순간에 숫자가 바뀐다. 마스크 폰트는 마지막 숫자가 짝수(또는 홀수)일 때만 칸을
// 채우므로, 타이머 하나는 "2초 주기 중 정해진 1초 동안 열리는 창"이 된다.
// 창 두 개를 겹치면(마스크의 마스크 = 곱) 원하는 짧은 구간만 열린다.
//
// 원리 참고(코드는 보지 않고 새로 씀, 둘 다 MIT):
//   https://github.com/littleboy1941/widget-anim-lab  (PhaseWindow, 깜빡임 마스크 폰트)
//   https://github.com/brycebostwick/WidgetAnimation
//
// 시간 기호
//   w = 지금 - anchor (초). 모든 창은 2초 주기 v = w mod 2 위에서 정의한다.
//   offset o 인 타이머가 보여 주는 값 S = floor(w - o) (+ 짝수 상수).
//   Even(o): S 가 짝수  <=>  (w - o) mod 2 ∈ [0, 1)
//   Odd(o) : S 가 홀수  <=>  (w - o) mod 2 ∈ [1, 2)
//   구간 [a, b) (0 < b - a < 1)  = Even(a) ∧ Odd(b)
//   구간 [a, a + 1)              = Even(a)
// 쉼·보통·빠름·최고의 한 바퀴(2.0 / 1.0 / 0.5 / 0.333초)는 모두 2초를 나누므로
// 2초 주기 하나로 네 단계를 모두 표현할 수 있다.
//
// 같은 계산을 tools/schedule.py 가 파이썬으로 한다. 둘을 고치면 같이 고친다.

import Foundation

public enum MaskParity: String, Codable, Equatable {
    case even   // IRMaskEven 폰트: 마지막 숫자가 짝수면 칸을 채움
    case odd    // IRMaskOdd 폰트: 마지막 숫자가 홀수면 칸을 채움
}

/// 타이머 글자 하나가 만드는 1초짜리 창.
public struct TimerCondition: Equatable {
    /// 타이머 시작을 anchor 에서 몇 격자 칸 늦출지 (0 ..< gridFPS)
    public let offsetCells: Int
    public let parity: MaskParity
}

/// 창 1~2개를 곱해 만든 구간 하나. 이 구간 동안 해당 프레임이 보인다.
public struct MaskCell: Equatable {
    /// 2초 주기 안에서 [startCell, endCell) (격자 칸 단위)
    public let startCell: Int
    public let endCell: Int
    public let conditions: [TimerCondition]
}

public struct TierPlan: Equatable {
    public let tier: Int
    public let name: String
    public let gridFPS: Int
    public let frameCount: Int
    public let holdCells: Int
    /// frames[i] = i 번 프레임을 비추는 구간들
    public let frames: [[MaskCell]]

    public var holdSeconds: Double { Double(holdCells) / Double(gridFPS) }
    public var loopSeconds: Double { holdSeconds * Double(frameCount) }
    /// 이 단계를 그릴 때 화면에 놓이는 타이머 글자 수
    public var timerTextCount: Int { frames.reduce(0) { $0 + $1.reduce(0) { $0 + $1.conditions.count } } }
}

public enum FrameSchedule {
    /// 2초 주기. 모든 단계의 한 바퀴가 이 값을 나눠야 한다.
    public static let cycleSeconds = 2

    /// 결정 문서 "통일한 정의" 표 그대로. 0 쉼, 1 보통, 2 빠름, 3 최고(12fps, 선택)
    public static let tiers: [(name: String, gridFPS: Int, frameCount: Int, holdCells: Int)] = [
        ("rest", 8, 2, 8),     // 한 바퀴 2.0초, 장당 1.0초
        ("normal", 8, 4, 2),   // 한 바퀴 1.0초, 장당 0.25초
        ("fast", 8, 4, 1),     // 한 바퀴 0.5초, 장당 0.125초
        ("max", 12, 4, 1),     // 한 바퀴 0.333초, 장당 0.0833초
    ]

    public static func clampTier(_ tier: Int) -> Int { min(max(tier, 0), tiers.count - 1) }

    public static func plan(tier rawTier: Int) -> TierPlan {
        let tier = clampTier(rawTier)
        let t = tiers[tier]
        let cellsPerCycle = cycleSeconds * t.gridFPS
        precondition(cellsPerCycle % (t.holdCells * t.frameCount) == 0, "한 바퀴가 2초를 나누지 않음")

        var frames = Array(repeating: [MaskCell](), count: t.frameCount)
        var start = 0
        while start < cellsPerCycle {
            let frame = (start / t.holdCells) % t.frameCount
            var end = start + 1
            while end < cellsPerCycle && (end / t.holdCells) % t.frameCount == frame { end += 1 }
            frames[frame].append(MaskCell(startCell: start, endCell: end,
                                          conditions: conditions(start: start, end: end, gridFPS: t.gridFPS)))
            start = end
        }
        return TierPlan(tier: tier, name: t.name, gridFPS: t.gridFPS, frameCount: t.frameCount,
                        holdCells: t.holdCells, frames: frames)
    }

    /// [start, end) 구간을 타이머 조건으로 바꾼다. 길이는 1초 이하여야 한다.
    static func conditions(start: Int, end: Int, gridFPS: Int) -> [TimerCondition] {
        let length = end - start
        precondition(length > 0 && length <= gridFPS, "구간이 1초보다 김")
        if length == gridFPS { return [normalized(.even, cells: start, gridFPS: gridFPS)] }
        return [normalized(.even, cells: start, gridFPS: gridFPS),
                normalized(.odd, cells: end, gridFPS: gridFPS)]
    }

    /// offset 을 0 ..< 1초로 줄인다. 1초를 뺄 때마다 짝홀이 뒤집힌다 (Even(o) = Odd(o - 1)).
    static func normalized(_ parity: MaskParity, cells: Int, gridFPS: Int) -> TimerCondition {
        let wholeSeconds = cells / gridFPS
        let flipped = wholeSeconds % 2 == 1
        let p: MaskParity = flipped ? (parity == .even ? .odd : .even) : parity
        return TimerCondition(offsetCells: cells % gridFPS, parity: p)
    }

    // MARK: - 시험용 계산 (단위 테스트와 로그에서 쓴다)

    /// 타이머가 보여 줄 값의 짝홀을 그대로 흉내 낸다. w = 지금 - anchor (초)
    public static func isOpen(_ c: TimerCondition, gridFPS: Int, elapsed w: Double) -> Bool {
        let o = Double(c.offsetCells) / Double(gridFPS)
        let s = Int(floor(w - o))
        let even = ((s % 2) + 2) % 2 == 0
        return c.parity == .even ? even : !even
    }

    /// w 순간에 보이는 프레임 번호들. 정상이면 항상 정확히 하나.
    public static func visibleFrames(_ plan: TierPlan, elapsed w: Double) -> [Int] {
        var out: [Int] = []
        for (i, cells) in plan.frames.enumerated() {
            let on = cells.contains { cell in
                cell.conditions.allSatisfy { isOpen($0, gridFPS: plan.gridFPS, elapsed: w) }
            }
            if on { out.append(i) }
        }
        return out
    }

    /// 설계상 w 순간에 보여야 할 프레임 (결정 문서 정의: floor(w / 장당 유지) mod 프레임 수)
    public static func designedFrame(_ plan: TierPlan, elapsed w: Double) -> Int {
        let cell = Int(floor(w * Double(plan.gridFPS)))
        return ((cell / plan.holdCells) % plan.frameCount + plan.frameCount) % plan.frameCount
    }

    /// 타이머의 시작 시각. 짝수 초(60)를 앞당겨 anchor 직후에도 이미 세고 있게 한다.
    public static let leadSeconds: Double = 60

    public static func timerStart(anchor: Date, condition c: TimerCondition, gridFPS: Int) -> Date {
        anchor.addingTimeInterval(Double(c.offsetCells) / Double(gridFPS) - leadSeconds)
    }
}
