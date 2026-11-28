# 프레임 간 픽셀 차이 (108px, ImageMagick compare -metric AE -fuzz 3%)

숫자 = 달라진 픽셀 수(108x108=11664 중 비율). 달=달리기, 0 에 가까우면 같은 그림.

| 캐릭터 | 달1↔달2 | 달2↔달3 | 달3↔달4 | 달4↔달1 | 달1↔달3 | 달2↔달4 | rest_1↔rest_2 | still↔달1 |
|---|---|---|---|---|---|---|---|---|
| hamster | 3424 (29.4%) | 2433 (20.9%) | 3058 (26.2%) | 3053 (26.2%) | 3397 (29.1%) | 3283 (28.1%) | 2402 (20.6%) | 2386 (20.5%) |
| penguin | 4277 (36.7%) | 3900 (33.4%) | 4237 (36.3%) | 3969 (34.0%) | 4618 (39.6%) | 3525 (30.2%) | 2047 (17.5%) | 3799 (32.6%) |
| rocket | 1888 (16.2%) | 1741 (14.9%) | 1824 (15.6%) | 1621 (13.9%) | 2226 (19.1%) | 1275 (10.9%) | 1461 (12.5%) | 1887 (16.2%) |

# 파일 크기·투명 검사 (identify)

| 파일 | 크기 | 채널 | 최소 알파 | 용량 | 판정 |
|---|---|---|---|---|---|
| hamster_run_1@3x.png | 108x108 | srgba | 0 | 13KB | 통과 |
| hamster_run_1_L@3x.png | 240x240 | srgba | 0 | 33KB | 통과 |
| hamster_run_2@3x.png | 108x108 | srgba | 0 | 13KB | 통과 |
| hamster_run_2_L@3x.png | 240x240 | srgba | 0 | 34KB | 통과 |
| hamster_run_3@3x.png | 108x108 | srgba | 0 | 13KB | 통과 |
| hamster_run_3_L@3x.png | 240x240 | srgba | 0 | 33KB | 통과 |
| hamster_run_4@3x.png | 108x108 | srgba | 0 | 13KB | 통과 |
| hamster_run_4_L@3x.png | 240x240 | srgba | 0 | 34KB | 통과 |
| hamster_rest_1@3x.png | 108x108 | srgba | 0 | 13KB | 통과 |
| hamster_rest_1_L@3x.png | 240x240 | srgba | 0 | 34KB | 통과 |
| hamster_rest_2@3x.png | 108x108 | srgba | 0 | 13KB | 통과 |
| hamster_rest_2_L@3x.png | 240x240 | srgba | 0 | 33KB | 통과 |
| hamster_still@3x.png | 108x108 | srgba | 0 | 13KB | 통과 |
| hamster_still_L@3x.png | 240x240 | srgba | 0 | 34KB | 통과 |
| penguin_run_1@3x.png | 108x108 | srgba | 0 | 8KB | 통과 |
| penguin_run_1_L@3x.png | 240x240 | srgba | 0 | 19KB | 통과 |
| penguin_run_2@3x.png | 108x108 | srgba | 0 | 8KB | 통과 |
| penguin_run_2_L@3x.png | 240x240 | srgba | 0 | 21KB | 통과 |
| penguin_run_3@3x.png | 108x108 | srgba | 0 | 7KB | 통과 |
| penguin_run_3_L@3x.png | 240x240 | srgba | 0 | 19KB | 통과 |
| penguin_run_4@3x.png | 108x108 | srgba | 0 | 8KB | 통과 |
| penguin_run_4_L@3x.png | 240x240 | srgba | 0 | 21KB | 통과 |
| penguin_rest_1@3x.png | 108x108 | srgba | 0 | 8KB | 통과 |
| penguin_rest_1_L@3x.png | 240x240 | srgba | 0 | 19KB | 통과 |
| penguin_rest_2@3x.png | 108x108 | srgba | 0 | 7KB | 통과 |
| penguin_rest_2_L@3x.png | 240x240 | srgba | 0 | 19KB | 통과 |
| penguin_still@3x.png | 108x108 | srgba | 0 | 8KB | 통과 |
| penguin_still_L@3x.png | 240x240 | srgba | 0 | 20KB | 통과 |
| rocket_run_1@3x.png | 108x108 | srgba | 0 | 4KB | 통과 |
| rocket_run_1_L@3x.png | 240x240 | srgba | 0 | 13KB | 통과 |
| rocket_run_2@3x.png | 108x108 | srgba | 0 | 6KB | 통과 |
| rocket_run_2_L@3x.png | 240x240 | srgba | 0 | 14KB | 통과 |
| rocket_run_3@3x.png | 108x108 | srgba | 0 | 6KB | 통과 |
| rocket_run_3_L@3x.png | 240x240 | srgba | 0 | 14KB | 통과 |
| rocket_run_4@3x.png | 108x108 | srgba | 0 | 6KB | 통과 |
| rocket_run_4_L@3x.png | 240x240 | srgba | 0 | 14KB | 통과 |
| rocket_rest_1@3x.png | 108x108 | srgba | 0 | 4KB | 통과 |
| rocket_rest_1_L@3x.png | 240x240 | srgba | 0 | 11KB | 통과 |
| rocket_rest_2@3x.png | 108x108 | srgba | 0 | 5KB | 통과 |
| rocket_rest_2_L@3x.png | 240x240 | srgba | 0 | 12KB | 통과 |
| rocket_still@3x.png | 108x108 | srgba | 0 | 6KB | 통과 |
| rocket_still_L@3x.png | 240x240 | srgba | 0 | 14KB | 통과 |
