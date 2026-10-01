from django.urls import path
from .views import analyze_product_endpoint, planner_chat_endpoint

urlpatterns = [
    path('api/executor/analyze/', analyze_product_endpoint, name='executor_analyze'),
    path('api/planner/chat/', planner_chat_endpoint, name='planner_chat'),
]
