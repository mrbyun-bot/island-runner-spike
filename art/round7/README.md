# 7라운드: 한 가지 색 실루엣 + 눈 두 개 (2026-11-29)

- 비교판: `compare/family_11.png` (검정 바탕, 36px 실제 줄 + 3배 확대 + 108 + 240, 판정 ○△×)
- 아일랜드 칸처럼 위아래 자른 한 줄: `compare/island_strip_x3.png` (실제 크기 `island_strip_actual.png`)
- 캐릭터: `characters/{id}/{id}_{run_1..4,rest_1..2,still}@3x.png`(108px), `_L@3x.png`(240px), 투명 배경
- 달리기 GIF(8fps): `gif/{id}_run_240_8fps.gif`, `gif/{id}_run_108_8fps.gif`
- 프레임 차이: `frame_diff.md` (기준 18%)
- 다시 만들기: `python3 art/round7/src/build_all.py` (약 30초, Python + Pillow + numpy만 사용)

규칙: 캐릭터당 몸색 하나, 보조 색 면·윤곽선·음영 없음. 눈만 먹색 `#1D1821` + 작은 흰 하이라이트.
도형을 겹쳐 2160px 에 그린 뒤 흐림→문턱으로 이음새를 녹여 한 덩어리 곡선으로 만들고, 정수배 상자 평균으로 줄인다.
판다는 36px 에서 판다로 읽히지 않아 탈락(파일은 비교용으로 남김).
