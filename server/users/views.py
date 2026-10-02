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
