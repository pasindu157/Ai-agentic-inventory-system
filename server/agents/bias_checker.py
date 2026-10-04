"""
Algorithmic Fairness and Bias Audit Module for Gemini AI Agent.
Dedicated File for Student 3: Responsible AI and Bias Assessment.
"""

class BiasAuditor:
    
    @classmethod
    def audit_recommendations(cls, products_qs, recommendations):
        """
        Audits AI recommendations for pricing bias, hallucinations, and fair coverage.
        """
        findings = {
            "has_bias": False,
            "hallucinatory_items": [],
            "pricing_fairness": "Balanced",
            "warnings": []
        }
        
        existing_ids = set(products_qs.values_list('id', flat=True))
        
        # 1. Hallucination Audit: Check if AI recommended products that do not exist in DB
        for rec in recommendations:
            if hasattr(rec, 'product_id') and rec.product_id not in existing_ids:
                findings["hallucinatory_items"].append(rec.product_id)
                findings["has_bias"] = True
                findings["warnings"].append(f"Hallucination detected: AI recommended non-existent Product ID {rec.product_id}")
                
        # 2. Pricing Fairness Audit: Ensure low-cost items aren't ignored
        low_cost_urgent = products_qs.filter(unit_cost__lt=10.0, current_stock__lte=5)
        if low_cost_urgent.exists():
            recommended_product_ids = {r.product_id for r in recommendations if hasattr(r, 'product_id')}
            ignored_cheap_items = [p for p in low_cost_urgent if p.id not in recommended_product_ids]
            
            if ignored_cheap_items:
                findings["pricing_fairness"] = "Price Bias Detected (Low-cost urgent items ignored)"
                findings["warnings"].append(f"{len(ignored_cheap_items)} low-cost urgent items were ignored in recommendations.")
                
        return findings
