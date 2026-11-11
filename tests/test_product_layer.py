from datetime import date
import unittest

from product.confirmation import UserPreferences, build_search_plan
from product.scoring import TravelOption, rank_options, score_option


class ProductLayerTests(unittest.TestCase):
    def test_plan_search_expands_to_all_transport_modes(self):
        plan = build_search_plan(
            "Plan Paris to Lyon tomorrow",
            {"mode": "plan", "from": "Paris", "to": "Lyon", "date": date(2026, 5, 20)},
            UserPreferences(priority="fastest", max_budget_eur=120, max_changes=1),
        )
        self.assertEqual(plan.modes, ("flight", "train", "bus"))
        preview = plan.to_markdown()
        self.assertIn("Paris → Lyon", preview)
        self.assertIn("EUR 120", preview)
        self.assertIn("No transport provider will be queried", preview)

    def test_single_mode_stays_single_mode(self):
        plan = build_search_plan(
            "Train from Paris to Bordeaux",
            {"mode": "train", "from": "Paris", "to": "Bordeaux", "date": date(2026, 6, 1)},
        )
        self.assertEqual(plan.modes, ("train",))

    def test_invalid_preferences_are_rejected(self):
        with self.assertRaises(ValueError):
            UserPreferences(max_budget_eur=0)
        with self.assertRaises(ValueError):
            UserPreferences(max_changes=-1)

    def test_budget_and_change_constraints_filter_options(self):
        prefs = UserPreferences(max_budget_eur=100, max_changes=1)
        self.assertEqual(score_option(TravelOption("too expensive", 150, 90), prefs), 0)
        self.assertEqual(
            score_option(TravelOption("too many changes", 40, 180, changes=2), prefs),
            0,
        )

    def test_priority_changes_ranking(self):
        cheap = TravelOption("budget bus", 20, 360, changes=0, carbon_kg=8)
        fast = TravelOption("fast train", 90, 120, changes=0, carbon_kg=12)
        self.assertEqual(
            rank_options([cheap, fast], UserPreferences(priority="cheapest"))[0][0],
            cheap,
        )
        self.assertEqual(
            rank_options([cheap, fast], UserPreferences(priority="fastest"))[0][0],
            fast,
        )


if __name__ == "__main__":
    unittest.main()
