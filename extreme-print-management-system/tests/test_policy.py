import unittest

from epms.core import PrintCostPolicy
from epms.policy import anonymize_document_name, apply_pricing_rules, scrub_job_document


class PolicyTests(unittest.TestCase):
    def test_department_pricing_rule_applies(self):
        policy = apply_pricing_rules(
            base=PrintCostPolicy(bw_page_cents=10, color_page_cents=30, duplex_discount_percent=10),
            department="Students",
            rules=[{"department": "Students", "bw_multiplier_percent": 50, "color_multiplier_percent": 80, "is_active": True}],
        )
        self.assertEqual(policy.bw_page_cents, 5)
        self.assertEqual(policy.color_page_cents, 24)

    def test_anonymize_document_name(self):
        self.assertIn("redacted", anonymize_document_name("secret.pdf", job_id=9))

    def test_scrub_job_document(self):
        job = {"id": 3, "document_name": "payroll.xlsx"}
        redacted = scrub_job_document(job, enabled=True)
        self.assertNotEqual(redacted["document_name"], "payroll.xlsx")


if __name__ == "__main__":
    unittest.main()
