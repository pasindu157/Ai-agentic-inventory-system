from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AIRecommendation
from .serializers import AIRecommendationSerializer
from .planner import PlannerAgent

class AIRecommendationViewSet(viewsets.ModelViewSet):
    serializer_class = AIRecommendationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'ADMIN':
            return AIRecommendation.objects.all()
        if hasattr(user, 'store'):
            return AIRecommendation.objects.filter(store=user.store)
        return AIRecommendation.objects.none()

    # Create a dynamic REST endpoint: POST /api/agents/recommendations/generate/
    @action(detail=False, methods=['post'])
    def generate(self, request):
        user = request.user
        if not hasattr(user, 'store'):
            return Response({"error": "No store associated with this user."}, status=400)
            
        if user.role != 'ADMIN' and user.store.subscription_plan != 'ENTERPRISE':
            return Response({"error": "AI Insights are exclusive to the Enterprise AI Plan. Please upgrade your subscription to unlock Gemini."}, status=403)

        planner = PlannerAgent(user.store)
        
        # Erase outdated recommendations to keep the user's dashboard completely fresh and uncluttered
        AIRecommendation.objects.filter(store=user.store).delete()
        
        try:
            created = planner.generate_recommendations()
            return Response({
                "message": f"Successfully generated {created} new anomaly recommendations.",
                "created": created
            }, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['post'])
    def ask(self, request):
        user = request.user
        if not hasattr(user, 'store'):
            return Response({"error": "No store associated with this user."}, status=400)
            
        if user.role != 'ADMIN' and user.store.subscription_plan != 'ENTERPRISE':
            return Response({"error": "Gemini AI Analyst Chat is exclusive to the Enterprise AI Plan. Please upgrade your subscription."}, status=403)

        question = request.data.get('question')
        if not question:
            return Response({"error": "Question is absolutely required."}, status=400)
            
        planner = PlannerAgent(user.store)
        try:
            answer = planner.ask_question(question)
            return Response({"answer": answer}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
