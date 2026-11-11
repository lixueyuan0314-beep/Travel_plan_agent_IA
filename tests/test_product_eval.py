import unittest

from eval.product_eval import build_summary, evaluate_cases, load_cases


class ProductEvaluationTests(unittest.TestCase):
    def test_offline_scenario_set_has_no_regressions(self):
        results = evaluate_cases(load_cases())
        failures = [result for result in results if not result.passed]
        self.assertEqual(failures, [])

    def test_safety_metrics_are_reported(self):
        summary = build_summary(evaluate_cases(load_cases()))
        self.assertGreaterEqual(summary["total"], 30)
        self.assertEqual(summary["false_confirmations"], 0)
        self.assertEqual(summary["missed_confirmations"], 0)
        self.assertEqual(summary["categories"]["provider_recovery"], {"passed": 6, "total": 6})


if __name__ == "__main__":
    unittest.main()
