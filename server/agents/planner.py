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
                # Throw this hard so the Django viewset catches it and sends the 500 alert to the UI!
                raise ValueError(f"Gemini API returned an error: {str(e)}")
                
        return recommendations_created

    def ask_question(self, question):
        from inventory.models import Product, SalesRecord
        from django.db.models import Sum
        from datetime import date, timedelta
        
        # 1. Gather live mathematical context of this exact owner's database
        products = Product.objects.filter(store=self.store, is_active=True)
        start_date = date.today() - timedelta(days=30)
        
        context = "Here is the exact live snapshot of the user's Inventory right now:\n"
        context += "(Note: Look closely at 'Units Sold Last 30 Days' to predict popularity and demand trends)\n"
        for p in products:
            # Aggregate total units sold in the last 30 days specifically for this product
            sales = SalesRecord.objects.filter(
                product=p,
                sale_date__gte=start_date
            ).aggregate(total_sold=Sum('quantity_sold'))['total_sold'] or 0
            
            context += f"- Product: {p.name} | SKU: {p.sku} | In Stock: {p.current_stock} | Reorder Tag: {p.reorder_level} | "
            context += f"Units Sold Last 30 Days: {sales} | Unit Cost: ${p.unit_cost}\n"
            
        prompt = f"""
        You are an elite, highly competent B2B SaaS Inventory Management AI Agent (Gemini Powered).
        The user (a Store Owner) has asked you a direct question about their specific store inventory data. 
        
        {context}
        
        USER QUESTION: "{question}"
        
        Answer their question precisely, factoring in the inventory data provided above. 
        Look at their stock values and cost logic to provide mathematically sound advice when applicable.
        Keep your answer concise, under 3 paragraphs. Be highly practical and strictly professional. 
        Do not hallucinate data that wasn't provided, and format your output in clean plain text.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Ad-hoc AI chat failed: {e}")
            raise ValueError(f"Gemini API returned an error: {str(e)}")
