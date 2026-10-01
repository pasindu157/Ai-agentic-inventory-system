from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import AIRecommendation
from .serializers import AIRecommendationSerializer

class AIRecommendationViewSet(viewsets.ModelViewSet):
    serializer_class = AIRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return AIRecommendation.objects.all()
        if hasattr(user, 'store'):
            return AIRecommendation.objects.filter(store=user.store)
        return AIRecommendation.objects.none()
        
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'store') and user.role != 'ADMIN':
            product = serializer.validated_data.get('product')
            if product and product.store != user.store:
                raise PermissionDenied("Product doesn't belong to your store.")
            serializer.save(store=user.store)
        else:
            serializer.save()
