from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AIRecommendation
from .serializers import AIRecommendationSerializer
from .planner import PlannerAgent
from .guardrails import AIGuardrail
from users.utils import log_audit_event

class AIRecommendationViewSet(viewsets.ModelViewSet):
    serializer_class = AIRecommendationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return AIRecommendation.objects.all()
        if hasattr(user, 'store'):
            return AIRecommendation.objects.filter(store=user.store)
        return AIRecommendation.objects.none()

    @action(detail=False, methods=['post'])
    def generate(self, request):
        user = request.user
        if not hasattr(user, 'store'):
            return Response({"error": "No store associated with this user."}, status=400)
            
        if user.role != 'ADMIN' and user.store.subscription_plan != 'ENTERPRISE':
            return Response({"error": "AI Insights are exclusive to the Enterprise AI Plan. Please upgrade your subscription to unlock Gemini."}, status=403)

        planner = PlannerAgent(user.store)
        AIRecommendation.objects.filter(store=user.store).delete()
        
        try:
            created = planner.generate_recommendations()
            log_audit_event(user, 'AI_RECOMMENDATIONS_GENERATED', f"Generated AI recommendations for store '{user.store.name}'", request)
            return Response({"status": "success", "count": len(created)})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def ask(self, request):
        user = request.user
        if not hasattr(user, 'store'):
            return Response({"error": "No store associated with this user."}, status=400)
            
        if user.role != 'ADMIN' and user.store.subscription_plan != 'ENTERPRISE':
            return Response({"error": "AI Analyst Chat is exclusive to the Enterprise AI Plan. Please upgrade your subscription to unlock Gemini."}, status=403)

        query = request.data.get('query') or request.data.get('question') or ''
        if not query.strip():
            return Response({"error": "Query cannot be empty."}, status=400)

        is_safe, violation_msg = AIGuardrail.inspect(query, user=user, request=request)
        if not is_safe:
            return Response({"error": violation_msg, "guardrail_triggered": True}, status=400)

        planner = PlannerAgent(user.store)
        try:
            answer = planner.ask_analyst(query)
            log_audit_event(user, 'AI_CHAT_QUERY', f"Query: {query[:100]}", request)
            return Response({"status": "success", "answer": answer})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
