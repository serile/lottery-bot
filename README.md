# 동행복권 자동 구매·당첨 확인

동행복권 계정의 예치금을 사용해 로또645와 연금복권720+를 구매하고, 당첨 결과를 Discord 채널에 알립니다. GitHub Actions가 실행하므로 개인 컴퓨터를 계속 켜 둘 필요가 없습니다.

> 자동 구매는 실제 결제를 발생시킵니다. 처음에는 `LOTTO645_COUNT=1`, `BUY_WIN720=false`, `MAX_WEEKLY_SPEND=1000`으로 수동 실행해 결과와 알림을 확인하세요.

## 동작 일정

- 구매: 매주 월요일 19:00 KST
- 당첨 확인: 매주 토요일 22:00 KST

GitHub Actions의 예약 실행은 혼잡할 때 정확한 분 단위로 시작되지 않을 수 있습니다. 판매 마감 직전 실행 용도로 사용하지 마세요.

## GitHub에서 설정하기

1. 이 저장소를 본인 계정으로 올리거나 fork합니다.
2. 동행복권 계정에 필요한 예치금을 충전합니다.
3. 저장소 `Settings → Secrets and variables → Actions → Secrets`에 아래 비밀값을 추가합니다.

   | 이름 | 값 |
   | --- | --- |
   | `USERNAME` | 동행복권 아이디 |
   | `PASSWORD` | 동행복권 비밀번호 |
   | `DISCORD_WEBHOOK_URL` | 선택 사항. Discord 채널 Webhook URL |

4. 같은 화면의 `Variables`에 구매 방식을 정합니다.

   | 이름 | 권장 시작값 | 설명 |
   | --- | --- | --- |
   | `LOTTO645_COUNT` | `1` | 로또645 자동 게임 수. 1~5 |
   | `BUY_LOTTO645` | `true` | 로또645 구매 여부 |
   | `BUY_WIN720` | `false` | 연금복권720+ 구매 여부. 한 번에 5,000원 |
   | `MAX_WEEKLY_SPEND` | `1000` | 두 상품을 합친 주간 구매 상한(원) |
   | `CHECK_LOTTO645` | `true` | 로또645 당첨 확인 여부 |
   | `CHECK_WIN720` | `true` | 연금복권720+ 당첨 확인 여부 |

5. `Actions` 탭에서 **Buy lotto**를 수동 실행해 1회 검증합니다. 성공과 Discord 알림을 확인한 뒤 예약 실행을 사용하세요.

`DISCORD_WEBHOOK_URL`은 Discord 봇 토큰이 아닙니다. Discord 채널 설정에서 만든 Incoming Webhook URL이며, 값을 절대로 코드나 Actions 로그에 적지 마세요.

## 로컬 실행

```bash
cp .env.sample .env
# .env에 본인 값 입력
make install
make buy
make check
```

설정 검증만 하려면 다음 테스트를 실행합니다.

```bash
make test
```

## 개별 실행 명령

```bash
make buy_lotto
make buy_win720
make check_lotto
make check_win720
```

## 주의사항

- 이 프로젝트는 동행복권 웹사이트의 동작 변경에 영향을 받을 수 있습니다.
- 알림 전송 실패가 구매 작업을 실패로 표시하지 않도록 처리했습니다. 구매 완료 후 작업을 무심코 재실행하면 중복 구매가 될 수 있습니다.
- 계정 비밀번호는 `.env` 또는 GitHub Secrets에만 저장합니다. `.env`는 Git에 포함되지 않습니다.
