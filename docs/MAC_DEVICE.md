# 맥북에서 아이폰에 직접 설치해 보기 (무료 애플 계정)

준비물: 맥북(Xcode 설치됨), 아이폰(iOS 17 이상, 다이내믹 아일랜드 있는 기종), 충전 케이블, 애플 계정(무료).
주의: 서명 팀은 반드시 **본인 이름의 "(Personal Team)"**. 회사(Hotel Lotte) 팀을 고르지 않는다.

## 1. 코드 받기와 프로젝트 만들기
터미널(응용 프로그램 > 유틸리티 > 터미널)에서 한 줄씩.

```
git clone https://github.com/mrbyun-bot/island-runner-spike.git
cd island-runner-spike
brew install xcodegen      # brew 가 없다고 나오면 https://brew.sh 안내대로 먼저 설치
xcodegen generate
open IslandRunnerSpike.xcodeproj
```

`xcodegen generate` 끝에 "Created project at ..." 가 나오면 된다. 프로젝트 파일 이름이 다르면 `ls *.xcodeproj` 로 확인(이름은 IslandRunnerSpike.xcodeproj 일 것).

## 2. Xcode 에서 서명 설정 (한 번만)
1. 메뉴 Xcode > Settings > Accounts > 왼쪽 아래 `+` > Apple ID 로그인.
2. 왼쪽 맨 위 `SpikeApp` 프로젝트 클릭 > TARGETS 에서 `SpikeApp` 선택 > **Signing & Capabilities**.
3. "Automatically manage signing" 체크, Team 은 **(Personal Team)** 선택.
4. TARGETS 의 `RunnerLiveActivity` 도 똑같이 설정(Team 같은 것).
5. 빨간 오류가 나오면 오류 문구를 캡처해서 알려 준다(번들 ID 가 이미 쓰인다는 오류면 이름을 바꿔 준다).

## 3. 아이폰 준비
1. 케이블로 맥북에 연결, 아이폰에서 "이 컴퓨터를 신뢰" 허용.
2. 아이폰 설정 > 개인정보 보호 및 보안 > 맨 아래 **개발자 모드** 켜기 > 재시동 > 다시 켜기 허용.
3. 설정 > (앱 목록에서 스파이크 앱이 설치된 뒤) Live Activity 허용.

## 4. 실행
1. Xcode 위쪽 가운데에서 실행 대상(Scheme)을 `SpikeApp`, 기기를 연결한 아이폰으로 고른다.
2. ▶ 실행. 처음 한 번은 아이폰 설정 > 일반 > VPN 및 기기 관리 > 개발자 앱 > **신뢰**.
3. 앱에서 단계(쉼/보통/빠름) 선택 후 **시작**. 아이폰 홈 화면으로 나가서 아일랜드 왼쪽을 본다.

## 5. 봐 줄 것 (사장님 눈으로)
- 아일랜드 왼쪽에서 햄스터가 계속 달리는가, 쉼/보통/빠름이 눈으로 구분되는가.
- 홈 화면에서 5분 두었을 때 계속 움직이는가. 화면을 잠갔다가 켰을 때는?
- 아일랜드를 길게 눌러 펼친 화면, 잠금 화면에서의 모습.
- 폭이 늘어나거나 글자가 깨지는 곳, 앱이 뜨거워지는지.
- 가능하면 화면 녹화(제어 센터)로 20초 찍어서 보내 주기.

설치한 앱은 7일 뒤 꺼진다(무료 계정). 그때 ▶ 를 다시 누르면 된다.
