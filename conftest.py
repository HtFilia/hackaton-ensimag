"""Root conftest — filters pytest tests to the registered team only.

If a .team file exists (written by `make register`) or the HACKATHON_TEAM
environment variable is set, only the matching team's parametrized tests are
collected.  Without any filter all teams are tested (admin / CI use-case).
"""
from __future__ import annotations

import os
from pathlib import Path


def _active_team() -> str | None:
    team = os.environ.get("HACKATHON_TEAM", "").strip()
    if team:
        return team
    p = Path(".team")
    if p.exists():
        return p.read_text().strip() or None
    return None


def pytest_collection_modifyitems(items: list) -> None:
    team = _active_team()
    if not team:
        return

    filtered = []
    for item in items:
        if hasattr(item, "callspec") and "team" in item.callspec.params:
            if item.callspec.params["team"] == team:
                filtered.append(item)
        else:
            filtered.append(item)

    items[:] = filtered
