from django.utils import timezone
from datetime import timedelta
import math
from inventory.models import Product, SalesRecord

class ExecutorAgent:
    def analyze_product(self, product_identifier):
        try:
            # 1. Fetch product by exact SKU or fuzzy name match
            product = Product.objects.filter(sku__iexact=product_identifier).first()
            if not product:
                product = Product.objects.filter(name__icontains=product_identifier).first()
            if not product:
                return None, "Product not found"
        except Exception as e:
            return None, str(e)
            
        # 2. Get SalesRecords for last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_sales = SalesRecord.objects.filter(product=product, sale_date__gte=thirty_days_ago)
        
        total_quantity_sold = sum(sale.quantity_sold for sale in recent_sales)
        average_daily_sales = round(total_quantity_sold / 30.0, 2)
        
        # 3. Calculate metrics
        current_stock = product.current_stock
        reorder_threshold = product.reorder_level
        
        if product.default_supplier:
            supplier_details = {
                "name": product.default_supplier.name,
                "email": product.default_supplier.contact_email,
                "lead_time_days": product.default_supplier.lead_time_days
            }
            lead_time_days = product.default_supplier.lead_time_days
        else:
            supplier_details = None
            lead_time_days = 7
            
        if average_daily_sales == 0:
            days_until_stockout = float('inf')
        else:
            days_until_stockout = round(current_stock / average_daily_sales, 1)
            
        if days_until_stockout <= lead_time_days:
            reorder_status = "URGENT_REORDER"
        elif current_stock <= reorder_threshold:
            reorder_status = "REORDER_SOON"
        else:
            reorder_status = "OPTIMAL"
            
        # Optional: recommended buffer size (e.g. 30 days worth of sales)
        target_buffer = average_daily_sales * 30
        shortfall = target_buffer - current_stock
        if shortfall > 0:
            recommended_reorder_quantity = math.ceil(shortfall / 10.0) * 10
        else:
            recommended_reorder_quantity = 0
            
        result = {
            "product_name": product.name,
            "sku": product.sku,
            "current_stock": current_stock,
            "average_daily_sales": average_daily_sales,
            "days_until_stockout": days_until_stockout,
            "reorder_threshold": reorder_threshold,
            "lead_time_days": lead_time_days,
            "reorder_status": reorder_status,
            "recommended_reorder_quantity": recommended_reorder_quantity,
            "supplier_details": supplier_details
        }
        
        return result, None
