from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Supplier, Product, SalesRecord
from .serializers import SupplierSerializer, ProductSerializer, SalesRecordSerializer

class TenantModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return self.queryset.all()
        if hasattr(user, 'store'):
            return self.queryset.filter(store=user.store)
        return self.queryset.none()
        
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'store') and user.role != 'ADMIN':
            serializer.save(store=user.store)
        else:
            serializer.save()

class SupplierViewSet(TenantModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

class ProductViewSet(TenantModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class SalesRecordViewSet(TenantModelViewSet):
    queryset = SalesRecord.objects.all()
    serializer_class = SalesRecordSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return self.queryset.all()
        if hasattr(user, 'store'):
            return self.queryset.filter(product__store=user.store)
        return self.queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'store') and user.role != 'ADMIN':
            product = serializer.validated_data.get('product')
            if product.store != user.store:
                raise PermissionDenied("Product doesn't belong to your store.")
        serializer.save()
