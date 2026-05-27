import unittest

from epms.core import PrintCostPolicy, calculate_job_cost, cents_to_money, evaluate_quota, money_to_cents


class CoreRulesTests(unittest.TestCase):
    def test_calculates_color_duplex_job_cost(self):
        cost = calculate_job_cost(
            pages=10,
            copies=2,
            color=True,
            duplex=True,
            policy=PrintCostPolicy(bw_page_cents=5, color_page_cents=30),
        )

        self.assertEqual(cost, 540)

    def test_rejects_invalid_page_count(self):
        with self.assertRaises(ValueError):
            calculate_job_cost(
                pages=0,
                copies=1,
                color=False,
                duplex=False,
                policy=PrintCostPolicy(bw_page_cents=5, color_page_cents=30),
            )

    def test_quota_allows_overdraft_within_limit(self):
        decision = evaluate_quota(balance_cents=100, overdraft_cents=50, cost_cents=125)

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.balance_after_cents, -25)

    def test_quota_holds_job_when_overdraft_exceeded(self):
        decision = evaluate_quota(balance_cents=100, overdraft_cents=10, cost_cents=125)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "Insufficient print quota")

    def test_money_formatting_round_trip(self):
        self.assertEqual(money_to_cents("12.345"), 1235)
        self.assertEqual(cents_to_money(-1235), "-12.35")


if __name__ == "__main__":
    unittest.main()
