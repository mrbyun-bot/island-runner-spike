// FrameSchedule 단위 테스트. tools/schedule.py 의 검증과 같은 내용을 Swift 쪽에서 한다.
// 이 서버에는 Swift 가 없어 R2(첫 맥 실행)에서 처음 돈다.

import XCTest

final class FrameScheduleTests: XCTestCase {
    /// 결정 문서 정의 표: (단계, 한 바퀴 초, 장당 격자 칸, 타이머 글자 수(schedule.py 출력))
    private let expected: [(tier: Int, loop: Double, holdCells: Int, timers: Int)] = [
        (0, 2.0, 8, 2),
        (1, 1.0, 2, 16),
        (2, 0.5, 1, 32),
        (3, 1.0 / 3.0, 1, 48),
    ]

    func testLoopAndHoldMatchDecisionTable() {
        for e in expected {
            let p = FrameSchedule.plan(tier: e.tier)
            XCTAssertEqual(p.loopSeconds, e.loop, accuracy: 1e-9, "단계 \(e.tier) 한 바퀴")
            XCTAssertEqual(p.holdCells, e.holdCells, "단계 \(e.tier) 장당 격자 칸")
            XCTAssertEqual(p.timerTextCount, e.timers, "단계 \(e.tier) 타이머 글자 수")
        }
    }

    /// 2초 주기 여러 번(음수 시각 포함)을 격자 칸의 1/10 간격 가운데 점으로 훑어,
    /// 항상 정확히 한 프레임만 보이고 그 프레임이 설계값과 같은지 본다 (겹침 0, 빈 시간 0).
    func testExactlyOneFrameVisibleAndMatchesDesign() {
        for tier in 0..<FrameSchedule.tiers.count {
            let p = FrameSchedule.plan(tier: tier)
            let sub = 10
            let steps = 3 * FrameSchedule.cycleSeconds * p.gridFPS * sub
            for k in (-FrameSchedule.cycleSeconds * p.gridFPS * sub)..<steps {
                let w = (Double(k) + 0.5) / Double(p.gridFPS * sub)
                let v = FrameSchedule.visibleFrames(p, elapsed: w)
                XCTAssertEqual(v, [FrameSchedule.designedFrame(p, elapsed: w)], "단계 \(tier) w=\(w)")
                if v.count != 1 { return }
            }
        }
    }

    func testOffsetsAreInsideOneSecond() {
        for tier in 0..<FrameSchedule.tiers.count {
            let p = FrameSchedule.plan(tier: tier)
            for cells in p.frames {
                for cell in cells {
                    XCTAssertTrue((1...2).contains(cell.conditions.count))
                    for c in cell.conditions {
                        XCTAssertTrue((0..<p.gridFPS).contains(c.offsetCells))
                    }
                }
            }
        }
    }

    func testTimerStartIsBeforeAnchor() {
        // 타이머가 anchor 직후부터 이미 세고 있어야 한다(시작 전이면 0:00 에 멈춰 보임).
        let anchor = Date(timeIntervalSince1970: 1_800_000_000)
        let c = TimerCondition(offsetCells: 7, parity: .odd)
        XCTAssertLessThan(FrameSchedule.timerStart(anchor: anchor, condition: c, gridFPS: 8), anchor)
    }

    /// 1회차 실패 원인(정수 나눗셈 방향) 재발 방지
    func testFloorDivAndNegativeDesignedFrame() {
        XCTAssertEqual(FrameSchedule.floorDiv(-15, 8), -2)
        XCTAssertEqual(FrameSchedule.floorDiv(-16, 8), -2)
        XCTAssertEqual(FrameSchedule.floorDiv(15, 8), 1)
        let rest = FrameSchedule.plan(tier: 0)
        // w = -1.86875 → 칸 -15 → 장 -2 → 프레임 0 (1회차에는 1 이 나왔다)
        XCTAssertEqual(FrameSchedule.designedFrame(rest, elapsed: -1.86875), 0)
    }

    func testTierIsClamped() {
        XCTAssertEqual(FrameSchedule.plan(tier: -5).tier, 0)
        XCTAssertEqual(FrameSchedule.plan(tier: 99).tier, 3)
    }

    // MARK: ArtSet (그림 파일 이름)

    func testCharacterArtsReturnAllNamesForBothSizes() {
        for (art, prefix) in ArtSet.characterPrefix {
            for large in [false, true] {
                let suffix = large ? "_L" : ""
                for tier in 0..<FrameSchedule.tiers.count {
                    let set = ArtSet.forTier(tier, art: art, large: large)
                    XCTAssertNil(set.base, "\(art) 는 통그림이라 바탕이 없다")
                    XCTAssertEqual(set.still, "\(prefix)_still\(suffix)")
                    if FrameSchedule.plan(tier: tier).frameCount == 2 {
                        XCTAssertEqual(set.frames, ["\(prefix)_rest_1\(suffix)", "\(prefix)_rest_2\(suffix)"])
                    } else {
                        XCTAssertEqual(set.frames, (1...4).map { "\(prefix)_run_\($0)\(suffix)" })
                    }
                }
            }
            // run 4 + rest 2 + still 1 = 7장, 큰 것까지 14장
            let all = ArtSet.requiredNames(art: art)
            XCTAssertEqual(all.count, 14, art)
            XCTAssertTrue(all.contains("\(prefix)_run_4_L"))
            XCTAssertTrue(all.contains("\(prefix)_rest_2"))
        }
    }

    func testEveryArtHasNonEmptyUniqueFrames() {
        for art in ArtSet.allArts {
            for large in [false, true] {
                for tier in 0..<FrameSchedule.tiers.count {
                    let set = ArtSet.forTier(tier, art: art, large: large)
                    let n = FrameSchedule.plan(tier: tier).frameCount
                    XCTAssertEqual(set.frames.count, n, "\(art) 단계 \(tier)")
                    XCTAssertFalse(set.still.isEmpty)
                    // shape 의 쉼 2장은 shape_1, shape_3 (서로 달라야 호흡이 보인다)
                    XCTAssertEqual(Set(set.frames).count, n, "\(art) 단계 \(tier) 장 이름 중복")
                }
            }
        }
        XCTAssertEqual(ArtSet.allArts.first, ArtSet.defaultArt)
        XCTAssertEqual(ArtSet.defaultArt, "hamster2")
    }

    func testLegacyArtsKeepTheirFiles() {
        XCTAssertEqual(ArtSet.forTier(2, art: "hamster").base, "hamsterold_bg")
        XCTAssertEqual(ArtSet.forTier(0, art: "hamster").frames, ["hamsterold_rest_1", "hamsterold_rest_2"])
        XCTAssertEqual(ArtSet.forTier(2, art: "shape", large: true).frames, ["shape_1", "shape_2", "shape_3", "shape_4"])
        // 모르는 값은 shape 로
        XCTAssertEqual(ArtSet.forTier(1, art: "없는그림").still, "shape_1")
    }
}
