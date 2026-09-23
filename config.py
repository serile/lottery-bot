"""Environment-based configuration for the lottery automation."""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Raised when a required setting is missing or unsafe."""


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("YOUR_"):
        raise ConfigurationError(f"{name} 환경 변수를 설정해 주세요.")
    return value


def _integer(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise ConfigurationError(f"{name}은(는) 정수여야 합니다: {raw!r}") from error
    if not minimum <= value <= maximum:
        raise ConfigurationError(f"{name}은(는) {minimum}~{maximum} 범위여야 합니다.")
    return value


def _boolean(name: str, default: bool) -> bool:
    raw = os.getenv(name, str(default)).strip().lower()
    values = {"true": True, "1": True, "yes": True, "false": False, "0": False, "no": False}
    if raw not in values:
        raise ConfigurationError(f"{name}은(는) true 또는 false여야 합니다.")
    return values[raw]


@dataclass(frozen=True)
class Settings:
    username: str
    password: str
    discord_webhook_url: str
    lotto645_count: int
    buy_lotto645: bool
    buy_win720: bool
    check_lotto645: bool
    check_win720: bool
    max_weekly_spend: int

    @classmethod
    def from_environment(cls) -> "Settings":
        # COUNT is retained as a compatibility fallback for existing forks.
        legacy_count = _integer("COUNT", 5, minimum=1, maximum=5)
        return cls(
            username=_required("USERNAME"),
            password=_required("PASSWORD"),
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL", "").strip(),
            lotto645_count=_integer("LOTTO645_COUNT", legacy_count, minimum=1, maximum=5),
            buy_lotto645=_boolean("BUY_LOTTO645", True),
            buy_win720=_boolean("BUY_WIN720", True),
            check_lotto645=_boolean("CHECK_LOTTO645", True),
            check_win720=_boolean("CHECK_WIN720", True),
            max_weekly_spend=_integer("MAX_WEEKLY_SPEND", 10_000, minimum=1_000, maximum=100_000),
        )

    def weekly_purchase_cost(self) -> int:
        return (self.lotto645_count * 1_000 if self.buy_lotto645 else 0) + (5_000 if self.buy_win720 else 0)

    def validate_weekly_purchase(self) -> None:
        cost = self.weekly_purchase_cost()
        if not cost:
            raise ConfigurationError("BUY_LOTTO645 또는 BUY_WIN720 중 하나는 true여야 합니다.")
        if cost > self.max_weekly_spend:
            raise ConfigurationError(
                f"예상 주간 구매액 {cost:,}원이 MAX_WEEKLY_SPEND {self.max_weekly_spend:,}원을 초과합니다."
            )

    def validate_single_purchase(self, cost: int, enabled: bool, name: str) -> None:
        if not enabled:
            raise ConfigurationError(f"{name} 구매가 비활성화되어 있습니다.")
        if cost > self.max_weekly_spend:
            raise ConfigurationError(
                f"예상 구매액 {cost:,}원이 MAX_WEEKLY_SPEND {self.max_weekly_spend:,}원을 초과합니다."
            )
