from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import UserRegistrationSerializer, UserSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

class UserProfileView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class UpgradePlanView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        plan = request.data.get('plan')
        valid_plans = ['STARTER', 'PRO', 'ENTERPRISE']
        if plan not in valid_plans:
            return Response({'error': f'Invalid plan choice. Choose from {valid_plans}'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        if not hasattr(user, 'store'):
            return Response({'error': 'User does not own a store'}, status=status.HTTP_400_BAD_REQUEST)
        
        store = user.store
        store.subscription_plan = plan
        store.save()
        
        from .serializers import StoreSerializer
        return Response({
            'message': f'Subscription successfully updated to {plan}',
            'store': StoreSerializer(store).data
        }, status=status.HTTP_200_OK)

class AdminPlatformOverviewView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        if not (user.is_superuser or user.role == 'ADMIN'):
            return Response({'error': 'Permission denied. Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        
        from .models import Store
        from inventory.models import Product

        total_stores = Store.objects.count()
        total_active_products = Product.objects.filter(is_active=True).count()
        
        starter_count = Store.objects.filter(subscription_plan='STARTER').count()
        pro_count = Store.objects.filter(subscription_plan='PRO').count()
        enterprise_count = Store.objects.filter(subscription_plan='ENTERPRISE').count()
        
        mrr = (pro_count * 29) + (enterprise_count * 79)

        stores_qs = Store.objects.select_related('owner').all()
        stores_data = []
        for store in stores_qs:
            p_count = Product.objects.filter(store=store, is_active=True).count()
            stores_data.append({
                'id': store.id,
                'name': store.name,
                'owner_id': store.owner.id,
                'owner_username': store.owner.username,
                'owner_email': store.owner.email,
                'subscription_plan': store.subscription_plan,
                'created_at': store.created_at,
                'active_products_count': p_count
            })

        return Response({
            'kpis': {
                'total_stores': total_stores,
                'total_active_products': total_active_products,
                'starter_count': starter_count,
                'pro_count': pro_count,
                'enterprise_count': enterprise_count,
                'mrr': mrr
            },
            'stores': stores_data
        }, status=status.HTTP_200_OK)

class AdminChangeStorePlanView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        if not (user.is_superuser or user.role == 'ADMIN'):
            return Response({'error': 'Permission denied. Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
        
        from .models import Store
        store_id = request.data.get('store_id')
        plan = request.data.get('plan')
        
        valid_plans = ['STARTER', 'PRO', 'ENTERPRISE']
        if plan not in valid_plans:
            return Response({'error': f'Invalid plan choice. Choose from {valid_plans}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response({'error': 'Store not found'}, status=status.HTTP_404_NOT_FOUND)

        store.subscription_plan = plan
        store.save()

        return Response({
            'message': f"Store '{store.name}' subscription updated to {plan}",
            'store_id': store.id,
            'new_plan': store.subscription_plan
        }, status=status.HTTP_200_OK)
