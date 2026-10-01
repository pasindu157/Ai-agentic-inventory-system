import os
from openai import OpenAI
from inventory.models import Product
from .models import AIRecommendation
from .executor import ExecutorAgent

class PlannerAgent:
    def __init__(self, store):
        self.store = store
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key if api_key else "dummy_key",
        )
        # Using OpenRouter's routing to Google Gemini
        self.model_name = "google/gemini-2.5-flash"

    def generate_recommendations(self):
        # 1. Run deterministic Executor Agent
        executor = ExecutorAgent(self.store)
        math_reports = executor.analyze_inventory()

        recommendations_created = 0

        # 2. Iterate through anomalies and generate AI text
        for item in math_reports:
            if item['raw_status'] == 'OPTIMAL':
                continue  # Skip healthy items to save API calls
                
            prompt = f"""
            You are an expert retail inventory manager. Analyze this math report for a product and give the store owner 2-3 sentences of highly actionable advice. Be professional.
            
            Product Name: {item['product_name']}
            Current Stock: {item['current_stock']}
            Mathematics Status: {item['raw_status']} 
            Velocity (Sales/Day): {item['velocity_per_day']}
            Days of stock left: {item['estimated_days_of_stock_left']}
            Supplier Lead Time: {item['supplier_lead_time_days']} days
            
            Explain why this is an issue and exactly what the owner should do. Do not use formatting like markdown asterisks, just plain text.
            """
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=250
                )
                explanation = response.choices[0].message.content.replace('*', '').strip()
                
                product = Product.objects.get(id=item['product_id'])
                
                # Save interpretation directly to DB for the frontend to read
                AIRecommendation.objects.create(
                    store=self.store,
                    product=product,
                    recommendation_type=item['raw_status'],
                    explanation=explanation,
                    recommended_order_quantity=item['reorder_level'] if item['raw_status'] == 'URGENT_REORDER' else 0
                )
                recommendations_created += 1
            except Exception as e:
                print(f"Failed to generate for {item['product_name']}: {e}")
                
        return recommendations_created
