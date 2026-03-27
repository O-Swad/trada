"""Persistence helpers for saving and loading trade-off studies as JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage"
STORAGE_FILE = STORAGE_DIR / "tradeoff_state.json"


def load_tradeoff_state() -> dict[str, Any] | None:
    """Load persisted trade-off data if it exists."""

    if not STORAGE_FILE.exists():
        return None
    try:
        return json.loads(STORAGE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_tradeoff_state(payload: dict[str, Any]) -> None:
    """Persist the current trade-off state as JSON."""

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def empty_study_library() -> dict[str, Any]:
    """Create an empty study library payload."""

    return {
        "version": 2,
        "active_study_id": "",
        "studies": [],
    }


def load_study_library() -> dict[str, Any] | None:
    """Load a study library, preserving compatibility with legacy single-study files."""

    payload = load_tradeoff_state()
    if payload is None:
        return None
    if "studies" in payload:
        payload.setdefault("version", 2)
        payload.setdefault("active_study_id", "")
        return payload
    return {
        "version": 2,
        "active_study_id": "study_legacy",
        "studies": [
            {
                "id": "study_legacy",
                "name": str(payload.get("project_name", "Recovered Study")),
                "description": str(payload.get("project_description", "")),
                "updated_at": "",
                "payload": payload,
                "result_snapshot": {},
            }
        ],
    }


def save_study_library(payload: dict[str, Any]) -> None:
    """Persist the study library as JSON."""

    save_tradeoff_state(payload)
