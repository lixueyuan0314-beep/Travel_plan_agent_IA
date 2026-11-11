import unittest

from product.resilience import execute_with_recovery, normalize_provider_payload


VALID_PAYLOAD = [
    {
        "label": "Train · direct",
        "price_eur": 68,
        "duration_minutes": 155,
        "changes": 0,
        "carbon_kg": 12,
    }
]


class ResilienceTests(unittest.TestCase):
    def test_timeout_then_success_is_recovered(self):
        events = iter([TimeoutError(), VALID_PAYLOAD])

        def operation():
            event = next(events)
            if isinstance(event, Exception):
                raise event
            return event

        result = execute_with_recovery(operation)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.attempts, 2)
        self.assertTrue(result.recovered)

    def test_repeated_timeout_fails_safely(self):
        result = execute_with_recovery(lambda: (_ for _ in ()).throw(TimeoutError()))
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.reason, "timeout")

    def test_empty_results_have_actionable_fallback(self):
        result = execute_with_recovery(lambda: [])
        self.assertEqual(result.status, "no_results")
        self.assertIn("Adjust", result.user_message)

    def test_malformed_payload_is_not_displayed(self):
        result = execute_with_recovery(lambda: {"unexpected": "shape"})
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.reason, "malformed_payload")
        self.assertEqual(result.options, ())

    def test_payload_is_normalized_to_shared_schema(self):
        options = normalize_provider_payload(VALID_PAYLOAD)
        self.assertEqual(options[0].label, "Train · direct")
        self.assertEqual(options[0].duration_minutes, 155)


if __name__ == "__main__":
    unittest.main()
