from django.contrib import admin
from .models import Supplier, Product, SalesRecord

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'contact_email', 'lead_time_days')
    list_filter = ('store',)
    search_fields = ('name', 'store__name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'store', 'current_stock', 'reorder_level', 'unit_cost')
    list_filter = ('store',)
    search_fields = ('name', 'sku', 'store__name')

@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_sold', 'sale_date')
    list_filter = ('sale_date', 'product__store')
    search_fields = ('product__name',)
