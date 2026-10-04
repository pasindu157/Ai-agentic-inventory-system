from django.urls import path
from .views import (
    RegisterView, UserProfileView, LogoutView, UpgradePlanView,
    AdminPlatformOverviewView, AdminChangeStorePlanView, AdminToggleStoreActiveView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserProfileView.as_view(), name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('upgrade-plan/', UpgradePlanView.as_view(), name='upgrade-plan'),
    path('admin/overview/', AdminPlatformOverviewView.as_view(), name='admin-overview'),
    path('admin/change-store-plan/', AdminChangeStorePlanView.as_view(), name='admin-change-store-plan'),
    path('admin/toggle-store-active/', AdminToggleStoreActiveView.as_view(), name='admin-toggle-store-active'),
]
