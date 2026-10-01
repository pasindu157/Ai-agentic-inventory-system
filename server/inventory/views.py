from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from inventory.services.executor_agent import ExecutorAgent

@csrf_exempt
def analyze_product_endpoint(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_identifier = data.get('product')
            if not product_identifier:
                return JsonResponse({"error": "Missing 'product' in payload"}, status=400)
                
            agent = ExecutorAgent()
            result, error = agent.analyze_product(product_identifier)
            
            if error:
                return JsonResponse({"error": error}, status=404)
                
            return JsonResponse(result, status=200)
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

from inventory.services.planner_agent import PlannerAgent

@csrf_exempt
def planner_chat_endpoint(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message')
            if not user_message:
                return JsonResponse({"error": "Missing 'message' in payload"}, status=400)
                
            agent = PlannerAgent()
            result = agent.handle_query(user_message)
            
            if result.get("status") == "failed":
                return JsonResponse(result, status=500)
                
            return JsonResponse(result, status=200)
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
