"""
Responsible AI & Explainability (XAI) Engine for Gemini AI Agent.
Dedicated File for Student 3: Responsible AI and Bias Assessment.
"""

class ExplainabilityEngine:
    
    @classmethod
    def calculate_confidence_score(cls, product):
        """
        Calculates a transparent confidence score (0.00 - 1.00) based on stock data completeness.
        High confidence (0.90+) is awarded when current stock, reorder level, and unit cost are valid.
        """
        score = 1.0
        
        if getattr(product, 'current_stock', None) is None:
            score -= 0.3
        if getattr(product, 'reorder_level', None) is None or product.reorder_level <= 0:
            score -= 0.2
        if getattr(product, 'unit_cost', None) is None or product.unit_cost <= 0:
            score -= 0.1
            
        return max(0.0, round(score, 2))

    @classmethod
    def generate_reasoning_chain(cls, product, recommended_qty):
        """
        Generates step-by-step audit reasoning for transparent explainability (XAI).
        """
        current = product.current_stock
        reorder = product.reorder_level
        cost = float(product.unit_cost)
        
        steps = [
            f"Step 1 [Data Audit]: Current stock is {current} units vs Reorder Threshold of {reorder} units.",
            f"Step 2 [Deficit Calculation]: Deficit is {max(0, reorder - current)} units.",
            f"Step 3 [Reorder Recommendation]: Suggesting {recommended_qty} units to restore safety buffer.",
            f"Step 4 [Financial Impact]: Estimated restock capital required is ${round(recommended_qty * cost, 2)}."
        ]
        
        return steps
