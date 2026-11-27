// Live Activity 위젯 확장. 위젯은 이것 하나만 둔다
// (위젯이 여러 개면 아일랜드가 안 뜬다는 보고를 피하려는 결정 문서 L1).

import ActivityKit
import SwiftUI
import WidgetKit

@main
struct RunnerLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: RunnerAttributes.self) { context in
            LockScreenView(context: context)
                .activityBackgroundTint(Color.black)
                .activitySystemActionForegroundColor(Color.white)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    sprite(context, place: "expanded")
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Text(tierLabel(context.state.speedTier))
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundStyle(Color.white)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    Text("스파이크 · \(context.attributes.art) · \(context.attributes.mode)")
                        .font(.system(size: 12))
                        .foregroundStyle(Color.gray)
                }
            } compactLeading: {
                sprite(context, place: "compactLeading")
            } compactTrailing: {
                // 오른쪽 칸은 고정 글자. 타이머 글자를 여기 두면 아일랜드 폭이 늘어난다는 보고(A5)가 있다.
                Text(tierShort(context.state.speedTier))
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(Color(red: 1.0, green: 0.62, blue: 0.04))
                    .frame(width: 20)
            } minimal: {
                sprite(context, place: "minimal")
            }
        }
    }

    private func sprite(_ context: ActivityViewContext<RunnerAttributes>, place: String) -> some View {
        let plan = FrameSchedule.plan(tier: context.state.speedTier)
        _ = WidgetLog.startupCheck
        WidgetLog.write("render", "\(place) tier=\(plan.tier) timers=\(plan.timerTextCount) art=\(context.attributes.art) mode=\(context.attributes.mode) anchor=\(context.state.anchor.timeIntervalSince1970)")
        return RunnerSprite(tier: context.state.speedTier, anchor: context.state.anchor,
                            art: context.attributes.art, mode: context.attributes.mode,
                            size: SpikeConstants.compactSize)
    }
}

struct LockScreenView: View {
    let context: ActivityViewContext<RunnerAttributes>

    var body: some View {
        HStack(spacing: 12) {
            RunnerSprite(tier: context.state.speedTier, anchor: context.state.anchor,
                         art: context.attributes.art, mode: context.attributes.mode,
                         size: SpikeConstants.compactSize)
            VStack(alignment: .leading, spacing: 2) {
                Text("아일랜드 러너 스파이크")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(Color.white)
                Text(tierLabel(context.state.speedTier))
                    .font(.system(size: 13))
                    .foregroundStyle(Color.gray)
            }
            Spacer()
        }
        .padding(16)
    }
}

func tierLabel(_ tier: Int) -> String {
    let p = FrameSchedule.plan(tier: tier)
    let names = ["쉼", "보통", "빠름", "최고"]
    return "\(names[p.tier]) \(String(format: "%.3g", p.loopSeconds))초"
}

func tierShort(_ tier: Int) -> String {
    ["쉼", "보", "빠", "최"][FrameSchedule.clampTier(tier)]
}
