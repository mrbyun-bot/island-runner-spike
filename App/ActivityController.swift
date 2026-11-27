// Live Activity 시작·갱신·종료. 모든 호출의 시각과 결과를 SpikeLog 에 남긴다(J6 반영 시간 측정용).

import ActivityKit
import Foundation

@MainActor
final class ActivityController: ObservableObject {
    @Published private(set) var status: String = "대기"
    @Published private(set) var tier: Int = 1

    private var current: Activity<RunnerAttributes>? {
        Activity<RunnerAttributes>.activities.first
    }

    /// 실행 인자나 버튼에서 부른다. 같은 그림·방식의 활동이 이미 있으면 갱신만 하고, 없으면 새로 연다.
    func startOrUpdate(tier rawTier: Int, art: String, mode: String, reset: Bool) async {
        let tier = FrameSchedule.clampTier(rawTier)
        SpikeLog.write("enabled", "areActivitiesEnabled=\(ActivityAuthorizationInfo().areActivitiesEnabled)")
        if reset {
            await endAll()
        }
        if let existing = current, existing.attributes.art == art, existing.attributes.mode == mode {
            await update(existing, tier: tier)
            return
        }
        if current != nil {
            // 그림이나 방식이 다르면 새로 열어야 한다(정적 속성은 바꿀 수 없음).
            await endAll()
        }
        let anchor = Date()
        let attributes = RunnerAttributes(art: art, mode: mode)
        let state = RunnerAttributes.ContentState(speedTier: tier, anchor: anchor)
        let plan = FrameSchedule.plan(tier: tier)
        SpikeLog.write("request_call", "tier=\(tier) art=\(art) mode=\(mode) anchor=\(anchor.timeIntervalSince1970) timers=\(plan.timerTextCount)")
        do {
            let activity = try Activity.request(attributes: attributes,
                                                content: ActivityContent(state: state, staleDate: nil),
                                                pushType: nil)
            self.tier = tier
            status = "시작됨 \(activity.id)"
            SpikeLog.write("request_ok", "id=\(activity.id)")
        } catch {
            status = "시작 실패: \(error.localizedDescription)"
            SpikeLog.write("request_fail", String(describing: error))
        }
    }

    func setTier(_ rawTier: Int) async {
        guard let existing = current else {
            SpikeLog.write("update_skip", "활동 없음")
            status = "활동이 없습니다. 먼저 시작하세요"
            return
        }
        await update(existing, tier: FrameSchedule.clampTier(rawTier))
    }

    private func update(_ activity: Activity<RunnerAttributes>, tier: Int) async {
        let anchor = activity.content.state.anchor
        let state = RunnerAttributes.ContentState(speedTier: tier, anchor: anchor)
        let plan = FrameSchedule.plan(tier: tier)
        SpikeLog.write("update_call", "id=\(activity.id) tier=\(tier) anchor=\(anchor.timeIntervalSince1970) timers=\(plan.timerTextCount)")
        await activity.update(ActivityContent(state: state, staleDate: nil))
        SpikeLog.write("update_done", "id=\(activity.id) tier=\(tier)")
        self.tier = tier
        status = "단계 \(tier)"
    }

    func endAll() async {
        for activity in Activity<RunnerAttributes>.activities {
            SpikeLog.write("end_call", "id=\(activity.id)")
            await activity.end(nil, dismissalPolicy: .immediate)
        }
        status = "종료됨"
    }
}
