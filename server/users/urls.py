from django.urls import path
from .views import RegisterView, UserProfileView, LogoutView, UpgradePlanView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserProfileView.as_view(), name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('upgrade-plan/', UpgradePlanView.as_view(), name='upgrade-plan'),
]
