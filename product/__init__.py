"""Product-layer utilities for the travel agent."""

from .confirmation import SearchPlan, UserPreferences, build_search_plan
from .scoring import TravelOption, rank_options, score_option

__all__ = [
    "SearchPlan",
    "TravelOption",
    "UserPreferences",
    "build_search_plan",
    "rank_options",
    "score_option",
]
