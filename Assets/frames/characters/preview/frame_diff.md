# 프레임 간 픽셀 차이 (108px, ImageMagick compare -metric AE -fuzz 3%)

숫자 = 달라진 픽셀 수(108x108=11664 중 비율). 달=달리기, 0 에 가까우면 같은 그림.

| 캐릭터 | 달1↔달2 | 달2↔달3 | 달3↔달4 | 달4↔달1 | 달1↔달3 | 달2↔달4 | rest_1↔rest_2 | still↔달1 |
|---|---|---|---|---|---|---|---|---|
| hamster | 2918 (25.0%) | 2639 (22.6%) | 2924 (25.1%) | 2630 (22.5%) | 2567 (22.0%) | 3341 (28.6%) | 2514 (21.6%) | 1864 (16.0%) |
| penguin | 3367 (28.9%) | 3026 (25.9%) | 3309 (28.4%) | 3107 (26.6%) | 3804 (32.6%) | 2761 (23.7%) | 1863 (16.0%) | 3101 (26.6%) |
| rocket | 1553 (13.3%) | 1563 (13.4%) | 1594 (13.7%) | 1412 (12.1%) | 1821 (15.6%) | 1057 (9.1%) | 1431 (12.3%) | 1882 (16.1%) |

# 파일 크기·투명 검사 (identify)

| 파일 | 크기 | 채널 | 최소 알파 | 용량 | 판정 |
|---|---|---|---|---|---|
| hamster_run_1@3x.png | 108x108 | srgba | 0 | 14KB | 통과 |
| hamster_run_1_L@3x.png | 240x240 | srgba | 0 | 36KB | 통과 |
| hamster_run_2@3x.png | 108x108 | srgba | 0 | 14KB | 통과 |
| hamster_run_2_L@3x.png | 240x240 | srgba | 0 | 36KB | 통과 |
| hamster_run_3@3x.png | 108x108 | srgba | 0 | 14KB | 통과 |
| hamster_run_3_L@3x.png | 240x240 | srgba | 0 | 36KB | 통과 |
| hamster_run_4@3x.png | 108x108 | srgba | 0 | 14KB | 통과 |
| hamster_run_4_L@3x.png | 240x240 | srgba | 0 | 36KB | 통과 |
| hamster_rest_1@3x.png | 108x108 | srgba | 0 | 13KB | 통과 |
| hamster_rest_1_L@3x.png | 240x240 | srgba | 0 | 33KB | 통과 |
| hamster_rest_2@3x.png | 108x108 | srgba | 0 | 13KB | 통과 |
| hamster_rest_2_L@3x.png | 240x240 | srgba | 0 | 33KB | 통과 |
| hamster_still@3x.png | 108x108 | srgba | 0 | 14KB | 통과 |
| hamster_still_L@3x.png | 240x240 | srgba | 0 | 36KB | 통과 |
| penguin_run_1@3x.png | 108x108 | srgba | 0 | 7KB | 통과 |
| penguin_run_1_L@3x.png | 240x240 | srgba | 0 | 19KB | 통과 |
| penguin_run_2@3x.png | 108x108 | srgba | 0 | 7KB | 통과 |
| penguin_run_2_L@3x.png | 240x240 | srgba | 0 | 19KB | 통과 |
| penguin_run_3@3x.png | 108x108 | srgba | 0 | 7KB | 통과 |
| penguin_run_3_L@3x.png | 240x240 | srgba | 0 | 18KB | 통과 |
| penguin_run_4@3x.png | 108x108 | srgba | 0 | 7KB | 통과 |
| penguin_run_4_L@3x.png | 240x240 | srgba | 0 | 19KB | 통과 |
| penguin_rest_1@3x.png | 108x108 | srgba | 0 | 7KB | 통과 |
| penguin_rest_1_L@3x.png | 240x240 | srgba | 0 | 18KB | 통과 |
| penguin_rest_2@3x.png | 108x108 | srgba | 0 | 7KB | 통과 |
| penguin_rest_2_L@3x.png | 240x240 | srgba | 0 | 18KB | 통과 |
| penguin_still@3x.png | 108x108 | srgba | 0 | 7KB | 통과 |
| penguin_still_L@3x.png | 240x240 | srgba | 0 | 19KB | 통과 |
| rocket_run_1@3x.png | 108x108 | srgba | 0 | 5KB | 통과 |
| rocket_run_1_L@3x.png | 240x240 | srgba | 0 | 13KB | 통과 |
| rocket_run_2@3x.png | 108x108 | srgba | 0 | 6KB | 통과 |
| rocket_run_2_L@3x.png | 240x240 | srgba | 0 | 14KB | 통과 |
| rocket_run_3@3x.png | 108x108 | srgba | 0 | 5KB | 통과 |
| rocket_run_3_L@3x.png | 240x240 | srgba | 0 | 14KB | 통과 |
| rocket_run_4@3x.png | 108x108 | srgba | 0 | 5KB | 통과 |
| rocket_run_4_L@3x.png | 240x240 | srgba | 0 | 13KB | 통과 |
| rocket_rest_1@3x.png | 108x108 | srgba | 0 | 4KB | 통과 |
| rocket_rest_1_L@3x.png | 240x240 | srgba | 0 | 11KB | 통과 |
| rocket_rest_2@3x.png | 108x108 | srgba | 0 | 5KB | 통과 |
| rocket_rest_2_L@3x.png | 240x240 | srgba | 0 | 11KB | 통과 |
| rocket_still@3x.png | 108x108 | srgba | 0 | 6KB | 통과 |
| rocket_still_L@3x.png | 240x240 | srgba | 0 | 14KB | 통과 |
