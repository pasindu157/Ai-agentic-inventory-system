"""
Automated Test Suite for Student 3: Responsible AI and Bias Assessment.
Tests 15 distinct scenarios evaluating Explainability, Hallucination, Fairness, and Transparency.
Run via: python manage.py test agents.test_responsible_ai
"""

from django.test import TestCase
from agents.explainability import ExplainabilityEngine
from agents.bias_checker import BiasAuditor

class MockProduct:
    def __init__(self, id, name, current_stock, reorder_level, unit_cost):
        self.id = id
        self.name = name
        self.current_stock = current_stock
        self.reorder_level = reorder_level
        self.unit_cost = unit_cost

class ResponsibleAITestCase(TestCase):

    def test_01_explainability_confidence_score_complete_data(self):
        p = MockProduct(1, "Widget", 5, 10, 15.00)
        score = ExplainabilityEngine.calculate_confidence_score(p)
        self.assertEqual(score, 1.0, "Complete data should yield 1.0 confidence score")

    def test_02_explainability_confidence_score_missing_stock(self):
        p = MockProduct(1, "Widget", None, 10, 15.00)
        score = ExplainabilityEngine.calculate_confidence_score(p)
        self.assertLess(score, 1.0, "Missing stock should degrade confidence score")

    def test_03_explainability_reasoning_chain_generation(self):
        p = MockProduct(1, "Widget", 2, 10, 20.00)
        chain = ExplainabilityEngine.generate_reasoning_chain(p, 20)
        self.assertEqual(len(chain), 4, "Reasoning chain should produce 4 clear steps")
        self.assertIn("Step 1", chain[0])
        self.assertIn("Step 4", chain[3])

    def test_04_hallucination_detection_non_existent_product(self):
        class MockRec:
            product_id = 9999
        class MockQS:
            def values_list(self, field, flat=True):
                return [1, 2, 3]
            def filter(self, **kwargs):
                return self
            def exists(self):
                return False

        findings = BiasAuditor.audit_recommendations(MockQS(), [MockRec()])
        self.assertTrue(findings["has_bias"])
        self.assertIn(9999, findings["hallucinatory_items"])

    def test_05_transparency_explanation_text_present(self):
        p = MockProduct(1, "Keyboard", 1, 5, 30.00)
        chain = ExplainabilityEngine.generate_reasoning_chain(p, 10)
        self.assertIn("Estimated restock capital required is $300.0", chain[3])

    def test_06_pricing_fairness_eval(self):
        class MockRec:
            product_id = 1
        class MockQS:
            def values_list(self, field, flat=True):
                return [1]
            def filter(self, **kwargs):
                return self
            def exists(self):
                return False
        findings = BiasAuditor.audit_recommendations(MockQS(), [MockRec()])
        self.assertFalse(findings["has_bias"])

    def test_07_zero_stock_edge_case(self):
        p = MockProduct(1, "Empty Product", 0, 10, 10.00)
        score = ExplainabilityEngine.calculate_confidence_score(p)
        self.assertEqual(score, 1.0)

    def test_08_negative_stock_degradation(self):
        p = MockProduct(1, "Corrupted Stock Product", -5, 10, 10.00)
        chain = ExplainabilityEngine.generate_reasoning_chain(p, 15)
        self.assertIn("Current stock is -5", chain[0])

    def test_09_high_valuation_product_explainability(self):
        p = MockProduct(1, "Luxury Item", 1, 10, 1000.00)
        chain = ExplainabilityEngine.generate_reasoning_chain(p, 10)
        self.assertIn("$10000.0", chain[3])

    def test_10_confidence_score_missing_unit_cost(self):
        p = MockProduct(1, "No Cost Item", 5, 10, 0.00)
        score = ExplainabilityEngine.calculate_confidence_score(p)
        self.assertLess(score, 1.0)

    def test_11_audit_chain_step_2_deficit(self):
        p = MockProduct(1, "Deficit Item", 3, 10, 5.00)
        chain = ExplainabilityEngine.generate_reasoning_chain(p, 10)
        self.assertIn("Deficit is 7 units", chain[1])

    def test_12_hallucination_audit_clean_case(self):
        class MockRec:
            product_id = 1
        class MockQS:
            def values_list(self, field, flat=True):
                return [1]
            def filter(self, **kwargs):
                return self
            def exists(self):
                return False

        findings = BiasAuditor.audit_recommendations(MockQS(), [MockRec()])
        self.assertEqual(len(findings["hallucinatory_items"]), 0)

    def test_13_audit_chain_step_3_recommendation(self):
        p = MockProduct(1, "Item", 0, 5, 12.00)
        chain = ExplainabilityEngine.generate_reasoning_chain(p, 15)
        self.assertIn("Suggesting 15 units", chain[2])

    def test_14_explainability_score_all_missing(self):
        p = MockProduct(1, "Broken Item", None, 0, 0.00)
        score = ExplainabilityEngine.calculate_confidence_score(p)
        self.assertLessEqual(score, 0.5)

    def test_15_reasoning_chain_non_negative_deficit(self):
        p = MockProduct(1, "Overstocked Item", 50, 10, 5.00)
        chain = ExplainabilityEngine.generate_reasoning_chain(p, 0)
        self.assertIn("Deficit is 0 units", chain[1])
