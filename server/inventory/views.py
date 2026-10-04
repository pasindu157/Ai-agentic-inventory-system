from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Sum
from .models import Supplier, Product, SalesRecord
from .serializers import SupplierSerializer, ProductSerializer, SalesRecordSerializer

class TenantModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        qs = self.queryset
        if hasattr(self.model, 'is_active'):
            qs = qs.filter(is_active=True)
            
        if user.role == 'ADMIN':
            return qs.all()
        if hasattr(user, 'store'):
            return qs.filter(store=user.store)
        return qs.none()
        
    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'store') and user.role != 'ADMIN':
            serializer.save(store=user.store)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        if hasattr(instance, 'is_active'):
            instance.is_active = False
            instance.save()
        else:
            instance.delete()

class SupplierViewSet(TenantModelViewSet):
    model = Supplier
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

class ProductViewSet(TenantModelViewSet):
    model = Product
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'store') and user.role != 'ADMIN':
            store = user.store
            if store.subscription_plan == 'STARTER':
                active_count = Product.objects.filter(store=store, is_active=True).count()
                if active_count >= 5:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError({"detail": "Starter plan limit reached. You can only manage up to 5 active products on the Starter plan. Upgrade to Pro for unlimited products."})
            serializer.save(store=store)
        else:
            serializer.save()

class SalesRecordViewSet(TenantModelViewSet):
    queryset = SalesRecord.objects.all()
    serializer_class = SalesRecordSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return SalesRecord.objects.all()
        if hasattr(user, 'store'):
            return SalesRecord.objects.filter(product__store=user.store)
        return SalesRecord.objects.none()

class StoreStatisticsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        if not hasattr(user, 'store'):
            return Response({"error": "No store associated with this user."}, status=status.HTTP_400_BAD_REQUEST)
        
        store = user.store
        active_products = Product.objects.filter(store=store, is_active=True)
        
        total_products_count = active_products.count()
        total_units_in_stock = active_products.aggregate(total=Sum('current_stock'))['total'] or 0
        
        total_valuation = 0.0
        urgent_reorder_count = 0
        low_stock_count = 0
        optimal_count = 0
        
        top_valuable_products = []
        
        for p in active_products:
            stock = float(p.current_stock)
            cost = float(p.unit_cost)
            reorder = float(p.reorder_level)
            p_val = stock * cost
            total_valuation += p_val
            
            if stock <= reorder:
                urgent_reorder_count += 1
            elif stock <= (reorder * 1.5):
                low_stock_count += 1
            else:
                optimal_count += 1
                
            top_valuable_products.append({
                'id': p.id,
                'sku': p.sku,
                'name': p.name,
                'current_stock': p.current_stock,
                'reorder_level': p.reorder_level,
                'unit_cost': float(p.unit_cost),
                'total_value': round(p_val, 2)
            })
            
        top_valuable_products.sort(key=lambda x: x['total_value'], reverse=True)
        top_5_valuable = top_valuable_products[:5]
        
        avg_unit_cost = round(total_valuation / total_units_in_stock, 2) if total_units_in_stock > 0 else 0.0

        return Response({
            'total_products_count': total_products_count,
            'total_units_in_stock': total_units_in_stock,
            'total_valuation': round(total_valuation, 2),
            'avg_unit_cost': avg_unit_cost,
            'health': {
                'urgent_reorder_count': urgent_reorder_count,
                'low_stock_count': low_stock_count,
                'optimal_count': optimal_count,
                'urgent_pct': round((urgent_reorder_count / total_products_count * 100), 1) if total_products_count > 0 else 0,
                'low_pct': round((low_stock_count / total_products_count * 100), 1) if total_products_count > 0 else 0,
                'optimal_pct': round((optimal_count / total_products_count * 100), 1) if total_products_count > 0 else 0,
            },
            'top_valuable_products': top_5_valuable
        }, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'store') and user.role != 'ADMIN':
            product = serializer.validated_data.get('product')
            if product.store != user.store:
                raise PermissionDenied("Product doesn't belong to your store.")
        serializer.save()
