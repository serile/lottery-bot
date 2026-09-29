"""Small, optional state store persisted by GitHub Actions on the bot-state branch."""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from typing import Any


STATE_DIRECTORY_ENV = "LOTTERY_STATE_DIR"


def _state_path(kind: str) -> Path | None:
    directory = os.getenv(STATE_DIRECTORY_ENV, "").strip()
    if not directory:
        return None
    return Path(directory) / f"{kind}.json"


def get_round(kind: str, round_no: str) -> dict[str, Any] | None:
    path = _state_path(kind)
    if path is None or not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        item = payload.get("rounds", {}).get(str(round_no))
        return item if isinstance(item, dict) else None
    except (OSError, json.JSONDecodeError):
        # State is an audit trail, not the source of truth for a real purchase.
        return None


def record_round(kind: str, round_no: str, status: str, *, source: str) -> None:
    path = _state_path(kind)
    if path is None:
        return

    payload: dict[str, Any] = {"rounds": {}}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("rounds"), dict):
                payload = loaded
        except (OSError, json.JSONDecodeError):
            # Start a new valid record rather than blocking a verified purchase.
            # Purchase history remains the source of truth.
            payload = {"rounds": {}}

    now = datetime.datetime.now(datetime.UTC).isoformat()
    payload["rounds"][str(round_no)] = {
        "status": status,
        "source": source,
        "recorded_at": now,
    }
    payload["updated_at"] = now

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
