"""
URL configuration for inventory_server project.
"""
from django.urls import path, include

urlpatterns = [
    path('', include('inventory.urls')),
    path('', include('users.urls')),
]
