import datetime
import os
import sys
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

import auth
import lotto645
import win720
import notification
import state_store
import time
from config import ConfigurationError, Settings


def _setup_and_login():
    load_dotenv(override=True)
    settings = Settings.from_environment()

    auth_ctrl = auth.AuthController()
    auth_ctrl.login(settings.username, settings.password)

    return auth_ctrl, settings


def _ensure_scheduled_purchase_is_still_valid():
    """Reject a severely delayed scheduled run before it can buy next week's draw."""
    if os.getenv("GITHUB_EVENT_NAME") != "schedule":
        return

    now = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
    # Scheduled purchase attempts are intentionally limited to Thu~Sat. A run
    # delivered after the Saturday sales deadline must not roll into next week.
    if now.weekday() not in {3, 4, 5} or (
        now.weekday() == 5 and now.time() >= datetime.time(20, 0)
    ):
        raise RuntimeError(
            "예약 구매 실행이 이번 회차 판매 기간을 벗어나 도착했습니다. 다음 회차 구매를 방지하기 위해 중단합니다."
        )


def _is_scheduled_execution() -> bool:
    return os.getenv("GITHUB_EVENT_NAME") == "schedule"

def buy_lotto645(authCtrl: auth.AuthController, cnt: int, mode: str):
    lotto = lotto645.Lotto645()
    _mode = lotto645.Lotto645Mode[mode.upper()]
    requirements = lotto.get_purchase_requirements(authCtrl)
    target_round = requirements[3]
    existing_ticket = lotto.find_ticket_for_round(authCtrl, target_round)
    if existing_ticket:
        print(f"[Info] {target_round}회 로또645 구매 이력이 이미 있어 추가 구매하지 않습니다.")
        state_store.record_round("purchases", target_round, "confirmed", source="lottery_ledger")
        return {"purchase_state": "already_purchased", "round": target_round}

    response = lotto.buy_lotto645(authCtrl, cnt, _mode, requirements=requirements)
    result = response.get("result", {})
    if result.get("resultMsg", "FAILURE").upper() != "SUCCESS":
        raise RuntimeError(f"로또645 구매 요청 실패: {result.get('resultMsg', 'Unknown Error')}")

    # The purchase response alone is not enough to safely retry after a later
    # network failure. Confirm the ticket appears in the account ledger first.
    for _ in range(3):
        time.sleep(2)
        if lotto.find_ticket_for_round(authCtrl, target_round):
            break
    else:
        raise RuntimeError(
            f"{target_round}회 구매 응답은 성공했지만 구매 이력을 확인하지 못했습니다. "
            "다음 예약 실행에서 이력을 다시 확인합니다."
        )

    response['balance'] = authCtrl.get_user_balance()
    state_store.record_round("purchases", target_round, "confirmed", source="lottery_ledger")
    return response

def check_winning_lotto645(authCtrl: auth.AuthController) -> dict:
    lotto = lotto645.Lotto645()
    item = lotto.check_winning(authCtrl)
    item['balance'] = authCtrl.get_user_balance()
    return item

def buy_win720(authCtrl: auth.AuthController, username: str):
    pension = win720.Win720()
    response = pension.buy_Win720(authCtrl, username)
    response['balance'] = authCtrl.get_user_balance()
    return response

def check_winning_win720(authCtrl: auth.AuthController) -> dict:
    pension = win720.Win720()
    item = pension.check_winning(authCtrl)
    item['balance'] = authCtrl.get_user_balance()
    return item

def send_message(mode: int, lottery_type: int, response: dict, webhook_url: str):
    notify = notification.Notification()

    if mode == 0:
        if lottery_type == 0:
            notify.send_lotto_winning_message(response, webhook_url)
        else:
            notify.send_win720_winning_message(response, webhook_url)
    elif mode == 1: 
        if lottery_type == 0:
            notify.send_lotto_buying_message(response, webhook_url)
        else:
            notify.send_win720_buying_message(response, webhook_url)

def check():
    auth_ctrl, settings = _setup_and_login()

    if settings.check_lotto645:
        lotto = lotto645.Lotto645()
        latest_round = lotto.get_latest_drawn_round()
        if latest_round and state_store.get_round("winning_checks", latest_round):
            print(f"[Info] {latest_round}회 당첨 확인은 이미 기록되어 있어 건너뜁니다.")
        else:
            response = check_winning_lotto645(auth_ctrl)
            round_no = str(response.get("round") or latest_round or "").strip()
            send_message(0, 0, response=response, webhook_url=settings.discord_webhook_url)
            if round_no:
                # Record only after the result notification has been delivered.
                # A notification failure should be retried by the backup run.
                state_store.record_round("winning_checks", round_no, "checked", source="lottery_result")

    if settings.check_lotto645 and settings.check_win720:
        time.sleep(10)

    if settings.check_win720:
        response = check_winning_win720(auth_ctrl)
        send_message(0, 1, response=response, webhook_url=settings.discord_webhook_url)

def buy():
    auth_ctrl, settings = _setup_and_login()
    settings.validate_weekly_purchase()
    _ensure_scheduled_purchase_is_still_valid()
    if _is_scheduled_execution() and settings.buy_win720:
        raise ConfigurationError(
            "반복 예약 구매는 로또645만 지원합니다. 연금복권720+는 중복 방지 기능을 추가하기 전까지 수동 실행해 주세요."
        )

    if settings.buy_lotto645:
        response = buy_lotto645(auth_ctrl, settings.lotto645_count, "AUTO")
        if response.get("purchase_state") != "already_purchased":
            send_message(1, 0, response=response, webhook_url=settings.discord_webhook_url)

    if settings.buy_lotto645 and settings.buy_win720:
        time.sleep(10)
        auth_ctrl.http_client.session.cookies.clear()
        auth_ctrl, settings = _setup_and_login()

    if settings.buy_win720:
        response = buy_win720(auth_ctrl, settings.username)
        send_message(1, 1, response=response, webhook_url=settings.discord_webhook_url)

def lotto_buy():
    auth_ctrl, settings = _setup_and_login()
    settings.validate_single_purchase(settings.lotto645_count * 1_000, settings.buy_lotto645, "로또645")
    
    response = buy_lotto645(auth_ctrl, settings.lotto645_count, "AUTO")
    send_message(1, 0, response=response, webhook_url=settings.discord_webhook_url)

def win720_buy():
    auth_ctrl, settings = _setup_and_login()
    settings.validate_single_purchase(5_000, settings.buy_win720, "연금복권720+")

    response = buy_win720(auth_ctrl, settings.username)
    send_message(1, 1, response=response, webhook_url=settings.discord_webhook_url)

def lotto_check():
    auth_ctrl, settings = _setup_and_login()

    response = check_winning_lotto645(auth_ctrl)
    send_message(0, 0, response=response, webhook_url=settings.discord_webhook_url)

def win720_check():
    auth_ctrl, settings = _setup_and_login()

    response = check_winning_win720(auth_ctrl)
    send_message(0, 1, response=response, webhook_url=settings.discord_webhook_url)

def run():
    if len(sys.argv) < 2:
        print("Usage: python controller.py [buy|check]")
        return

    if sys.argv[1] == "buy":
        buy()
    elif sys.argv[1] == "check":
        check()
    elif sys.argv[1] == "buy_lotto":
        lotto_buy()
    elif sys.argv[1] == "buy_win720":
        win720_buy()
    elif sys.argv[1] == "check_lotto":
        lotto_check()
    elif sys.argv[1] == "check_win720":
        win720_check()
  

if __name__ == "__main__":
    try:
        run()
    except ConfigurationError as error:
        print(f"[설정 오류] {error}", file=sys.stderr)
        sys.exit(2)
