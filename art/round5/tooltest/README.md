# 도구 시험 기록 (2026-11-29, 이 서버에서 직접 실행)

| 시험 | 명령/파일 | 결과 |
|---|---|---|
| Inkscape 1.1.2 Power Stroke / Taper Stroke(라이브 패스 이펙트)를 손으로 쓴 SVG XML 로 넣고 CLI 내보내기 | `lpe_test.svg` → `inkscape lpe_test.svg --export-type=png` | **안 됨.** 이펙트가 계산되지 않고 원래 `d`(점 하나)만 그려짐(`lpe_test.png` 는 거의 빈 그림). `--export-plain-svg` 결과 `lpe_out.svg` 에도 `d="M 20,60"` 그대로. `taperstroke` 는 `Unknown LPE type` 경고 |
| 같은 파일을 `--actions="select-all;object-to-path;..."`(이펙트를 경로로 굳히기) | 같은 파일 | **안 됨.** 화면(GUI) 없이 실행하면 `Inkscape encountered an internal error` 로 비정상 종료. `xvfb-run`(가상 화면)도 서버에 없음 |
| Blender 3.0.1 그리스 펜슬(손그림 스트로크) 헤드리스 렌더 | `gp_test.py`, 엔진 CYCLES / BLENDER_EEVEE / BLENDER_WORKBENCH 세 가지 | **안 됨.** 세 엔진 모두 `Unable to open a display`. 그리스 펜슬은 GPU 화면 그리기가 필요함 |
| Blender Cycles 일반 메쉬(대조군) | `cy_test.py` | 됨(`cy_test.png`). 다만 이번 화풍(2D 선화)에는 쓰지 않음 |
| Inkscape 로 일반 SVG(경로·clipPath) → PNG | `src/kit.py render_many` (`inkscape --shell`) | 됨. 54장 약 7초 |
| Python 가변 폭 선 직접 생성 | `src/kit.py Canvas.ring / stroke` | 됨. Power Stroke 와 같은 원리(중심선 법선 방향으로 폭 함수만큼 띄운 다각형)를 직접 구현. 폭은 빛 반대편(오른쪽 아래)에서 두껍고, 저주파 잡음으로 ±10~12% 흔들림 |

결론: Inkscape 의 라이브 패스 이펙트와 Blender 그리스 펜슬은 이 서버(화면 없음)에서 못 쓴다. 대신 같은 결과를 내는 계산을 Python 으로 직접 짰다.
