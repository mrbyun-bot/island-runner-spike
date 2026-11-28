// 캐릭터 칸 뷰. 위젯 확장(축소·최소·확장·잠금 화면)과 앱 미리보기가 같이 쓴다.
//
// 그리는 방식 (FrameSchedule.swift 머리말 참고)
//   프레임 그림 i  .mask { ZStack { 구간마다 [타이머 글자 1~2개를 마스크로 곱한 것] } }
//   타이머 글자 = Text(timerInterval:) + IRMaskEven/IRMaskOdd 폰트, 칸 크기로 오른쪽 정렬해 자름
// 상시표시(isLuminanceReduced) 중에는 애플이 애니메이션을 끄므로 정지 포즈 한 장만 그린다.
//
// 표시 방식(mode) — 2회차에 원인을 가르려고 단계적 시험 모드를 더했다 (SpikeConstants.modes)
//   probe0   고정 주황 사각형만. 칸이 그려지는지, 보이는 높이가 얼마인지
//   probe1   주황 사각형 + 흰 일반 글자 "가1". 글자가 그려지는지
//   probe2   주황 사각형 + 타이머 글자(시스템 폰트 11pt, 자르기 없음). 타이머 글자 자체가 그려지는지
//   probe3   회색 바탕 + 마스크 폰트 타이머 글자를 작게(칸/6) 통째로. 폰트가 렌더러에서 먹는지, 글자가 어디 붙는지
//   p0       마스크 폰트 타이머 1개, 1회차 배치(.fixedSize + 36pt 틀 + 자르기)  ← 1회차에 빈칸
//   p0w      마스크 폰트 타이머 1개, 애플 문서 방식 배치(넓은 고정 틀 + 오른쪽 정렬 + 자르기)
//   sprite   그림 + 마스크 애니메이션, 1회차 배치                             ← 1회차에 빈칸
//   spritew  그림 + 마스크 애니메이션, p0w 와 같은 배치
//   still    정지 포즈 한 장 (1회차에 보인 대조군)

import SwiftUI
import UIKit

/// 타이머 글자를 칸에 앉히는 방법
enum TimerLayout {
    /// 1회차: .fixedSize() 로 글자 원래 폭을 쓰고 36pt 틀에 오른쪽 정렬 후 자름
    case fixedSize
    /// 2회차 후보: 애플 문서("위젯 안의 타이머 Text 는 가로로 늘어나 가능한 폭을 채운다. 폭은
    /// frame(width:height:alignment:)로 정하고 multilineTextAlignment 로 정렬하라")대로
    /// 칸의 8배 폭 고정 틀에 오른쪽 정렬한 뒤, 바깥 36pt 틀에 오른쪽을 맞춰 자름
    case wideFrame
}

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
        // 큰 칸(확장·잠금 화면)이면 _L 파일. 이름은 ArtSet 한 곳에서만 정한다.
        let assets = ArtSet.forTier(tier, art: art, large: size > SpikeConstants.compactSize)
        let layout: TimerLayout = (mode == "p0w" || mode == "spritew") ? .wideFrame : .fixedSize
        Group {
            switch mode {
            case "probe0":
                ProbeBox(size: size)
            case "probe1":
                ZStack {
                    ProbeBox(size: size)
                    Text("가1")
                        .font(.system(size: size * 0.4, weight: .bold))
                        .foregroundStyle(Color.white)
                }
            case "probe2":
                ZStack {
                    ProbeBox(size: size)
                    Text(timerInterval: FrameSchedule.probeRange(anchor: anchor), countsDown: false, showsHours: false)
                        .font(.system(size: 11, weight: .bold))
                        .monospacedDigit()
                        .foregroundStyle(Color.white)
                        .multilineTextAlignment(.center)
                        .lineLimit(1)
                        .frame(width: size, height: size)
                }
            case "probe3":
                ZStack {
                    Rectangle()
                        .fill(Color(white: 0.3))
                    Text(timerInterval: FrameSchedule.probeRange(anchor: anchor), countsDown: false, showsHours: false)
                        .font(.custom(SpikeConstants.evenFont, fixedSize: size / 6))
                        .foregroundStyle(Color.white)
                        .multilineTextAlignment(.trailing)
                        .lineLimit(1)
                        .frame(width: size, height: size / 2, alignment: .trailing)
                }
            case "p0", "p0w":
                // 타이머 글자 1개를 흰색으로. 1초마다 칸이 채워졌다 비면 폰트와 배치가 맞은 것.
                TimerMaskText(anchor: anchor,
                              condition: TimerCondition(offsetCells: 0, parity: .even),
                              gridFPS: plan.gridFPS, size: size, layout: layout)
            case "still":
                SpriteImage(name: assets.still, size: size)
            default:
                if isLuminanceReduced {
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
                                                     gridFPS: plan.gridFPS, size: size, layout: layout)
                                        }
                                    }
                                    .frame(width: size, height: size)
                                }
                        }
                    }
                }
            }
        }
        .frame(width: size, height: size)
    }
}

/// 시험용 고정 사각형 (CPU 주황 #FF9F0A)
struct ProbeBox: View {
    let size: CGFloat

    var body: some View {
        Rectangle()
            .fill(Color(red: 1.0, green: 0.62, blue: 0.04))
            .frame(width: size, height: size)
    }
}

/// 구간 하나: 조건이 1개면 타이머 글자 1개, 2개면 첫 글자를 둘째 글자로 마스크(곱)한다.
struct CellMask: View {
    let cell: MaskCell
    let anchor: Date
    let gridFPS: Int
    let size: CGFloat
    let layout: TimerLayout

    var body: some View {
        if cell.conditions.count == 1 {
            TimerMaskText(anchor: anchor, condition: cell.conditions[0], gridFPS: gridFPS, size: size, layout: layout)
        } else {
            TimerMaskText(anchor: anchor, condition: cell.conditions[0], gridFPS: gridFPS, size: size, layout: layout)
                .mask {
                    TimerMaskText(anchor: anchor, condition: cell.conditions[1], gridFPS: gridFPS, size: size,
                                  layout: layout)
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
    let layout: TimerLayout

    var body: some View {
        let start = FrameSchedule.timerStart(anchor: anchor, condition: condition, gridFPS: gridFPS)
        // 끝은 Live Activity 최대 수명(8시간)보다 넉넉히. 끝에 닿으면 타이머가 멈춘다.
        let end = start.addingTimeInterval(12 * 60 * 60)
        let fontName = condition.parity == .even ? SpikeConstants.evenFont : SpikeConstants.oddFont
        switch layout {
        case .fixedSize:
            Text(timerInterval: start...end, countsDown: false, showsHours: false)
                .font(.custom(fontName, fixedSize: size))
                .foregroundStyle(Color.white)
                .multilineTextAlignment(.trailing)
                .lineLimit(1)
                .contentTransition(.identity)
                .fixedSize()
                .frame(width: size, height: size, alignment: .trailing)
                .clipped()
        case .wideFrame:
            // 마스크 폰트는 숫자만 폭 1em, 나머지 글자는 폭 0 이라 "720:00"(12시간 끝)도 5em.
            // 8em 틀이면 넘치지 않는다. 바깥 틀이 오른쪽 36pt 만 남긴다.
            Text(timerInterval: start...end, countsDown: false, showsHours: false)
                .font(.custom(fontName, fixedSize: size))
                .foregroundStyle(Color.white)
                .multilineTextAlignment(.trailing)
                .lineLimit(1)
                // 숫자가 바뀔 때 시스템이 넣는 전환(섞임)이 깜빡임으로 보인다. 끈다.
                .contentTransition(.identity)
                .transaction { $0.animation = nil }
                .frame(width: size * 8, height: size, alignment: .trailing)
                .frame(width: size, height: size, alignment: .trailing)
                .clipped()
        }
    }
}

/// 번들 안 PNG(@3x)를 읽는다. 없으면 눈에 띄는 빨간 칸을 그려 바로 알 수 있게 한다.
/// XcodeGen 은 그림을 번들 맨 위에 평평하게 복사하지만(project.yml 머리말), 폴더 구조로 남은 경우에 대비해
/// Assets/frames/characters 하위 폴더도 직접 찾아본다.
struct SpriteImage: View {
    let name: String
    let size: CGFloat

    var body: some View {
        if let image = SpriteImage.load(name) {
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

    static func load(_ name: String) -> UIImage? {
        if let image = UIImage(named: name, in: .main, with: nil) {
            return image
        }
        for dir in ["characters", "frames/characters", "Assets/frames/characters", "frames", "Assets/frames"] {
            if let path = Bundle.main.path(forResource: "\(name)@3x", ofType: "png", inDirectory: dir),
               let data = UIImage(contentsOfFile: path)?.cgImage {
                return UIImage(cgImage: data, scale: 3, orientation: .up)
            }
        }
        return nil
    }
}
