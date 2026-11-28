# 8라운드 캐릭터 (7라운드를 더 귀엽게, 10종)

스타일은 7라운드 그대로(캐릭터마다 밝은 색 하나 + 어두운 눈 두 개). 판다는 뺐다.

- 전/후 비교: `compare/before_after.png` (윗줄 7라운드, 아랫줄 8라운드)
- 가족 비교판: `compare/family_10.png`, 아일랜드 한 줄: `compare/island_strip_x3.png`
- 프레임: `characters/{id}/{id}_{run_1..4,rest_1..2,still}@3x.png`(108px), `_L@3x.png`(240px), 투명 배경
- 달리기 GIF(8fps): `gif/{id}_run_{108,240}_8fps.gif`
- 프레임 차이: `frame_diff.md`, 대비·차이 원자료: `src/contrast.json`, 크기 맞춤: `src/fit.json`

다시 만들기: `python3 art/round8/src/build_all.py` (약 1분, Python Pillow·numpy). `--keep-fit` 를 붙이면 크기 맞춤을 다시 계산하지 않는다.
전/후 비교판은 `origin/art-round7` 브랜치의 7라운드 프레임을 git 으로 꺼내 쓴다.
