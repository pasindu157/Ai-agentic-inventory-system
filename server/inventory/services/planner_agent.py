import os
import requests
from google import genai
from google.genai import types
from django.conf import settings

class PlannerAgent:
    def __init__(self):
        api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.getenv('GEMINI_API_KEY')
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.5-flash'
        self.last_executor_data = {}
        
        self.system_instruction = (
            "You are an expert supply chain advisor. "
            "You must use the fetch_product_inventory_analysis tool to verify stock and analytical trends before giving advice. "
            "Provide clear, numbers-backed explanations of current stock, daily sales velocity, estimated days until stockout. "
            "Never guess inventory numbers. Offer concrete reorder advice based purely on the tool's data."
        )

    def handle_query(self, user_message: str) -> dict:
        
        def fetch_product_inventory_analysis(product_name: str) -> dict:
            """Fetches deterministically calculated inventory statistics and reorder metrics from the executor agent."""
            try:
                response = requests.post(
                    'http://127.0.0.1:8000/api/executor/analyze/',
                    json={"product": product_name}
                )
                if response.status_code == 200:
                    data = response.json()
                    self.last_executor_data = data
                    return data
                elif response.status_code == 404:
                    return {"error": "Product not found out of available inventory."}
                else:
                    return {"error": f"Failed with status code {response.status_code}"}
            except Exception as e:
                return {"error": str(e)}

        chat = self.client.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.3,
            )
        )
        
        try:
            response = chat.send_message(
                user_message,
                config=types.GenerateContentConfig(
                    tools=[fetch_product_inventory_analysis]
                )
            )
            
            return {
                "response": response.text,
                "status": "success",
                "executor_data": self.last_executor_data if self.last_executor_data else None
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
