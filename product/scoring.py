"""Transparent preference-based scoring for comparable travel options."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .confirmation import UserPreferences


@dataclass(frozen=True)
class TravelOption:
    label: str
    price_eur: float
    duration_minutes: int
    changes: int = 0
    carbon_kg: float | None = None

    def __post_init__(self) -> None:
        if self.price_eur < 0 or self.duration_minutes <= 0 or self.changes < 0:
            raise ValueError("travel option values must be non-negative")


WEIGHTS = {
    "balanced": (0.35, 0.35, 0.20, 0.10),
    "cheapest": (0.65, 0.15, 0.15, 0.05),
    "fastest": (0.15, 0.65, 0.15, 0.05),
    "fewest_changes": (0.15, 0.20, 0.60, 0.05),
}


def score_option(option: TravelOption, preferences: UserPreferences) -> float:
    """Return a 0-100 score with an intentionally explainable formula."""

    if preferences.max_budget_eur is not None and option.price_eur > preferences.max_budget_eur:
        return 0.0
    if preferences.max_changes is not None and option.changes > preferences.max_changes:
        return 0.0

    price_score = 1 / (1 + option.price_eur / 100)
    duration_score = 1 / (1 + option.duration_minutes / 180)
    change_score = 1 / (1 + option.changes)
    carbon_score = 0.5 if option.carbon_kg is None else 1 / (1 + option.carbon_kg / 50)
    weights = WEIGHTS[preferences.priority]
    score = sum(
        weight * component
        for weight, component in zip(
            weights,
            (price_score, duration_score, change_score, carbon_score),
        )
    )
    return round(score * 100, 1)


def rank_options(
    options: Iterable[TravelOption], preferences: UserPreferences
) -> list[tuple[TravelOption, float]]:
    """Rank options and keep filtered-out choices at the bottom."""

    scored = [(option, score_option(option, preferences)) for option in options]
    return sorted(scored, key=lambda item: (-item[1], item[0].price_eur))
