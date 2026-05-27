import unittest

from xig.policies import evaluate_predicate, Rule, default_rules


class PolicyTests(unittest.TestCase):
    def test_empty_predicate_matches(self):
        self.assertTrue(evaluate_predicate({}, {"a": 1}))

    def test_eq_predicate(self):
        self.assertTrue(evaluate_predicate({"label": "secret"}, {"label": "secret"}))
        self.assertFalse(evaluate_predicate({"label": "secret"}, {"label": "public"}))

    def test_all_of_combinator(self):
        pred = {"all_of": [{"bytes": {"gt": 100}}, {"path": {"startswith": "/media/"}}]}
        self.assertTrue(evaluate_predicate(pred, {"bytes": 500, "path": "/media/usb/x"}))
        self.assertFalse(evaluate_predicate(pred, {"bytes": 50, "path": "/media/usb/x"}))

    def test_any_of_combinator(self):
        pred = {"any_of": [{"path": {"endswith": ".enc"}}, {"path": {"endswith": ".locked"}}]}
        self.assertTrue(evaluate_predicate(pred, {"path": "x.locked"}))
        self.assertTrue(evaluate_predicate(pred, {"path": "x.enc"}))
        self.assertFalse(evaluate_predicate(pred, {"path": "x.txt"}))

    def test_regex_predicate(self):
        self.assertTrue(evaluate_predicate({"path": {"regex": r"^/media/"}}, {"path": "/media/usb"}))
        self.assertFalse(evaluate_predicate({"path": {"regex": r"^/etc/"}}, {"path": "/media/usb"}))

    def test_in_predicate(self):
        self.assertTrue(evaluate_predicate({"label": {"in": ["a", "b"]}}, {"label": "a"}))
        self.assertFalse(evaluate_predicate({"label": {"in": ["a", "b"]}}, {"label": "z"}))

    def test_unknown_operator_returns_false(self):
        self.assertFalse(evaluate_predicate({"bytes": {"weird": 1}}, {"bytes": 1}))

    def test_default_rules_validate(self):
        for rule in default_rules():
            rule.validate()

    def test_rule_validate_rejects_bad_severity(self):
        rule = Rule(
            id="X", name="x", kind="file.write", severity="ultra",
            risk_delta=1.0, mitre="T1059", when={},
        )
        with self.assertRaises(ValueError):
            rule.validate()


if __name__ == "__main__":
    unittest.main()
