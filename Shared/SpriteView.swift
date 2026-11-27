// 캐릭터 칸 뷰. 위젯 확장(축소·최소·확장·잠금 화면)과 앱 미리보기가 같이 쓴다.
//
// 그리는 방식 (FrameSchedule.swift 머리말 참고)
//   프레임 그림 i  .mask { ZStack { 구간마다 [타이머 글자 1~2개를 마스크로 곱한 것] } }
//   타이머 글자 = Text(timerInterval:) + IRMaskEven/IRMaskOdd 폰트, 칸 크기로 오른쪽 정렬해 자름
// 상시표시(isLuminanceReduced) 중에는 애플이 애니메이션을 끄므로 정지 포즈 한 장만 그린다.

import SwiftUI
import UIKit

public struct RunnerSprite: View {
    let tier: Int
    let anchor: Date
    let art: String
    let mode: String
    let size: CGFloat

    @Environment(\.isLuminanceReduced) private var isLuminanceReduced

    public init(tier: Int, anchor: Date, art: String, mode: String, size: CGFloat = SpikeConstants.compactSize) {
        self.tier = tier
        self.anchor = anchor
        self.art = art
        self.mode = mode
        self.size = size
    }

    public var body: some View {
        let plan = FrameSchedule.plan(tier: tier)
        let assets = ArtSet.forTier(tier, art: art)
        Group {
            if mode == "p0" {
                // P0: 타이머 글자 1개를 흰색으로 그대로 보여 준다. 1초마다 칸이 채워졌다 비면 폰트가 로드된 것.
                TimerMaskText(anchor: anchor,
                              condition: TimerCondition(offsetCells: 0, parity: .even),
                              gridFPS: plan.gridFPS, size: size)
                    .foregroundStyle(Color.white)
            } else if isLuminanceReduced || mode == "still" {
                SpriteImage(name: assets.still, size: size)
            } else {
                ZStack {
                    if let base = assets.base {
                        SpriteImage(name: base, size: size)
                    }
                    ForEach(0..<plan.frameCount, id: \.self) { i in
                        SpriteImage(name: assets.frames[i], size: size)
                            .mask {
                                ZStack {
                                    ForEach(0..<plan.frames[i].count, id: \.self) { j in
                                        CellMask(cell: plan.frames[i][j], anchor: anchor,
                                                 gridFPS: plan.gridFPS, size: size)
                                    }
                                }
                                .frame(width: size, height: size)
                            }
                    }
                }
            }
        }
        .frame(width: size, height: size)
    }
}

/// 구간 하나: 조건이 1개면 타이머 글자 1개, 2개면 첫 글자를 둘째 글자로 마스크(곱)한다.
struct CellMask: View {
    let cell: MaskCell
    let anchor: Date
    let gridFPS: Int
    let size: CGFloat

    var body: some View {
        if cell.conditions.count == 1 {
            TimerMaskText(anchor: anchor, condition: cell.conditions[0], gridFPS: gridFPS, size: size)
        } else {
            TimerMaskText(anchor: anchor, condition: cell.conditions[0], gridFPS: gridFPS, size: size)
                .mask {
                    TimerMaskText(anchor: anchor, condition: cell.conditions[1], gridFPS: gridFPS, size: size)
                }
        }
    }
}

/// 마스크 폰트로 그린 타이머 글자. 마지막 숫자 한 칸(size × size)만 남긴다.
struct TimerMaskText: View {
    let anchor: Date
    let condition: TimerCondition
    let gridFPS: Int
    let size: CGFloat

    var body: some View {
        let start = FrameSchedule.timerStart(anchor: anchor, condition: condition, gridFPS: gridFPS)
        // 끝은 Live Activity 최대 수명(8시간)보다 넉넉히. 끝에 닿으면 타이머가 멈춘다.
        let end = start.addingTimeInterval(12 * 60 * 60)
        Text(timerInterval: start...end, countsDown: false, showsHours: false)
            .font(.custom(condition.parity == .even ? SpikeConstants.evenFont : SpikeConstants.oddFont,
                          fixedSize: size))
            .foregroundStyle(Color.white)
            .multilineTextAlignment(.trailing)
            .lineLimit(1)
            .contentTransition(.identity)
            .fixedSize()
            .frame(width: size, height: size, alignment: .trailing)
            .clipped()
    }
}

/// 번들 안 PNG(@3x)를 읽는다. 없으면 눈에 띄는 빨간 칸을 그려 바로 알 수 있게 한다.
struct SpriteImage: View {
    let name: String
    let size: CGFloat

    var body: some View {
        if let image = UIImage(named: name, in: .main, with: nil) {
            Image(uiImage: image)
                .resizable()
                .interpolation(.high)
                .frame(width: size, height: size)
        } else {
            Rectangle()
                .fill(Color.red)
                .frame(width: size, height: size)
        }
    }
}
