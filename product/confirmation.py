"""Human-in-the-loop confirmation for live travel searches.

The base project sends a parsed request directly to transport tools.  This
module adds a product safety layer: users see the route, date, modes, and
ranking preferences before any live MCP search is executed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping


MODE_LABELS = {
    "flight": "Flights",
    "train": "Trains",
    "bus": "Buses",
}


@dataclass(frozen=True)
class UserPreferences:
    """User-controlled constraints used to explain and rank results."""

    priority: str = "balanced"
    max_budget_eur: float | None = None
    max_changes: int | None = None

    def __post_init__(self) -> None:
        allowed = {"balanced", "cheapest", "fastest", "fewest_changes"}
        if self.priority not in allowed:
            raise ValueError(f"priority must be one of {sorted(allowed)}")
        if self.max_budget_eur is not None and self.max_budget_eur <= 0:
            raise ValueError("max_budget_eur must be positive")
        if self.max_changes is not None and self.max_changes < 0:
            raise ValueError("max_changes cannot be negative")


@dataclass(frozen=True)
class SearchPlan:
    """A structured preview of the action that awaits user approval."""

    original_query: str
    origin: str
    destination: str
    departure_date: date
    modes: tuple[str, ...]
    preferences: UserPreferences

    def to_markdown(self) -> str:
        mode_text = ", ".join(MODE_LABELS.get(mode, mode) for mode in self.modes)
        constraints = [f"Priority: **{self.preferences.priority.replace('_', ' ')}**"]
        if self.preferences.max_budget_eur is not None:
            constraints.append(f"Budget: **EUR {self.preferences.max_budget_eur:.0f}**")
        if self.preferences.max_changes is not None:
            constraints.append(f"Maximum changes: **{self.preferences.max_changes}**")
        return (
            "### Confirm live search\n"
            f"- Route: **{self.origin} → {self.destination}**\n"
            f"- Departure: **{self.departure_date.isoformat()}**\n"
            f"- Search: **{mode_text}**\n"
            f"- {' · '.join(constraints)}\n\n"
            "No transport provider will be queried until you confirm."
        )


def build_search_plan(
    original_query: str,
    parsed: Mapping[str, object],
    preferences: UserPreferences | None = None,
) -> SearchPlan:
    """Turn the fast-path parser output into a user-reviewable plan."""

    mode = str(parsed["mode"])
    modes = ("flight", "train", "bus") if mode == "plan" else (mode,)
    departure_date = parsed["date"]
    if not isinstance(departure_date, date):
        raise TypeError("parsed date must be datetime.date")
    return SearchPlan(
        original_query=original_query,
        origin=str(parsed["from"]),
        destination=str(parsed["to"]),
        departure_date=departure_date,
        modes=modes,
        preferences=preferences or UserPreferences(),
    )
