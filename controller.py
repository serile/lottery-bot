import os
import sys
from dotenv import load_dotenv

import auth
import lotto645
import win720
import notification
import time
from config import ConfigurationError, Settings


def _setup_and_login():
    load_dotenv(override=True)
    settings = Settings.from_environment()

    auth_ctrl = auth.AuthController()
    auth_ctrl.login(settings.username, settings.password)

    return auth_ctrl, settings

def buy_lotto645(authCtrl: auth.AuthController, cnt: int, mode: str):
    lotto = lotto645.Lotto645()
    _mode = lotto645.Lotto645Mode[mode.upper()]
    response = lotto.buy_lotto645(authCtrl, cnt, _mode)
    response['balance'] = authCtrl.get_user_balance()
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
        response = check_winning_lotto645(auth_ctrl)
        send_message(0, 0, response=response, webhook_url=settings.discord_webhook_url)

    if settings.check_lotto645 and settings.check_win720:
        time.sleep(10)

    if settings.check_win720:
        response = check_winning_win720(auth_ctrl)
        send_message(0, 1, response=response, webhook_url=settings.discord_webhook_url)

def buy():
    auth_ctrl, settings = _setup_and_login()
    settings.validate_weekly_purchase()

    if settings.buy_lotto645:
        response = buy_lotto645(auth_ctrl, settings.lotto645_count, "AUTO")
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
