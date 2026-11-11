"""Deterministic sample data for the key-free portfolio demo.

The generated options are intentionally labelled as simulated. They let a
reviewer experience confirmation, constraints, and explainable ranking without
API keys, network access, or claims that the prices are live.
"""
from __future__ import annotations

import hashlib

from .confirmation import SearchPlan
from .scoring import TravelOption


_MODE_PROFILES = {
    "flight": (118.0, 95, 0, 128.0),
    "train": (68.0, 155, 0, 12.0),
    "bus": (34.0, 310, 0, 8.0),
}


def generate_demo_options(plan: SearchPlan) -> list[TravelOption]:
    """Create stable sample options for the modes in a confirmed plan."""

    seed_text = f"{plan.origin}|{plan.destination}|{plan.departure_date.isoformat()}"
    digest = hashlib.sha256(seed_text.encode("utf-8")).digest()
    options: list[TravelOption] = []

    for index, mode in enumerate(plan.modes):
        price, duration, changes, carbon = _MODE_PROFILES[mode]
        jitter = digest[index] % 11
        label = mode.title()
        options.extend(
            [
                TravelOption(
                    label=f"{label} · direct",
                    price_eur=round(price + jitter, 2),
                    duration_minutes=duration + jitter * 2,
                    changes=changes,
                    carbon_kg=carbon,
                ),
                TravelOption(
                    label=f"{label} · value",
                    price_eur=round(price * 0.78 + jitter, 2),
                    duration_minutes=duration + 45 + jitter * 3,
                    changes=1,
                    carbon_kg=round(carbon * 0.92, 1),
                ),
            ]
        )
    return options
