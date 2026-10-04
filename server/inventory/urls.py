from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupplierViewSet, ProductViewSet, SalesRecordViewSet, StoreStatisticsView

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet)
router.register(r'products', ProductViewSet)
router.register(r'sales-records', SalesRecordViewSet)

urlpatterns = [
    path('statistics/', StoreStatisticsView.as_view(), name='store-statistics'),
    path('', include(router.urls)),
]
