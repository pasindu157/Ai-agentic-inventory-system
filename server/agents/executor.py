from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from inventory.models import Product, SalesRecord

class ExecutorAgent:
    def __init__(self, store):
        self.store = store
        self.days_to_analyze = 30
        self.today = timezone.now().date()
        self.analysis_start_date = self.today - timedelta(days=self.days_to_analyze)

    def analyze_inventory(self):
        """
        Analyzes all products in the store mathematically.
        Returns a structured dictionary of reports that the Planner Agent (Gemini) can quickly parse.
        """
        products = Product.objects.filter(store=self.store, is_active=True)
        report = []

        for product in products:
            # Aggregate sales over the last 30 days
            sales = SalesRecord.objects.filter(
                product=product,
                sale_date__gte=self.analysis_start_date
            ).aggregate(total_sold=Sum('quantity_sold'))['total_sold'] or 0

            # Calculate Velocity (Items sold per day)
            velocity = sales / self.days_to_analyze
            
            # Predict Days of Stock Remaining
            days_of_stock_left = float('inf')
            if velocity > 0:
                days_of_stock_left = product.current_stock / velocity

            # Determine Raw Status mathematically based on business logic
            status = 'OPTIMAL'
            
            supplier_lead_time = product.supplier.lead_time_days if product.supplier else 0
            
            # Anomaly 1: Hard Limit - Stock is literally below the owner's defined reorder threshold!
            if product.current_stock <= product.reorder_level:
                status = 'URGENT_REORDER'
                
            # Anomaly 2: Math Projection - We are selling so fast we will run out before supplier restocks us
            elif days_of_stock_left <= (supplier_lead_time + 2) and velocity > 0:
                status = 'URGENT_REORDER'
            
            # Anomaly 3: Dead stock - velocity is super low but we have huge stock above reorder limits
            elif velocity < 0.2 and product.current_stock > (product.reorder_level * 2):
                status = 'OVERSTOCK'

            report.append({
                "product_id": product.id,
                "product_name": product.name,
                "supplier_name": product.supplier.name if product.supplier else 'Unknown',
                "current_stock": product.current_stock,
                "reorder_level": product.reorder_level,
                "supplier_lead_time_days": supplier_lead_time,
                "sales_last_30_days": sales,
                "velocity_per_day": round(velocity, 2),
                "estimated_days_of_stock_left": round(days_of_stock_left, 1) if days_of_stock_left != float('inf') else 'Infinite',
                "raw_status": status
            })

        return report
