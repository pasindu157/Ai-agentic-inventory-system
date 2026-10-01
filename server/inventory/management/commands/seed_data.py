import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import Store
from django.contrib.auth import get_user_model
from inventory.models import Supplier, Product, SalesRecord

class Command(BaseCommand):
    help = 'Seeds the database with realistic inventory and sales data for all stores.'

    def handle(self, *args, **kwargs):
        stores = list(Store.objects.all())
        
        # Fallback: if no stores exist, create a dummy one for the superuser
        if not stores:
            User = get_user_model()
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR("No users exist in the system. Create an account first!"))
                return
            store = Store.objects.create(name="AI MegaStore Demo", owner=user)
            self.stdout.write(self.style.WARNING(f"No store found. Auto-created '{store.name}' for user {user.username}."))
            stores = [store]

        for store in stores:
            self.stdout.write(f"Seeding data for store: {store.name}")
            
            # 1. Create Suppliers
            suppliers_data = [
                {"name": "Global Tech Logistics", "email": "contact@globaltech.com", "phone": "555-0101", "lead": 5},
                {"name": "Fresh Foods Co", "email": "orders@freshfoods.com", "phone": "555-0202", "lead": 2},
                {"name": "Office Supplies Direct", "email": "sales@officedirect.com", "phone": "555-0303", "lead": 7},
            ]
            
            suppliers = []
            for data in suppliers_data:
                sup, created = Supplier.objects.get_or_create(
                    store=store, name=data["name"],
                    defaults={"contact_email": data["email"], "contact_phone": data["phone"], "lead_time_days": data["lead"]}
                )
                suppliers.append(sup)

            # 2. Create Products with specific anomalies for the AI to find
            product_profiles = [
                # Fast seller (Needs reorder - high sales, low stock)
                {"name": "Wireless Earbuds", "sku": "WE-001", "sup": 0, "stock": 15, "reorder": 50, "cost": 25.00, "velocity": "HIGH"},
                {"name": "Organic Avocados (Pack)", "sku": "OA-002", "sup": 1, "stock": 5, "reorder": 20, "cost": 6.50, "velocity": "HIGH"},
                
                # Overstocked (Dead stock - low sales, huge stock)
                {"name": "2024 Desk Calendar", "sku": "DC-003", "sup": 2, "stock": 500, "reorder": 50, "cost": 4.00, "velocity": "LOW"},
                {"name": "Wired Basic Mouse", "sku": "WM-004", "sup": 0, "stock": 200, "reorder": 30, "cost": 8.00, "velocity": "LOW"},
                
                # Optimal (Stable sales, medium stock)
                {"name": "Notepad A4", "sku": "NP-005", "sup": 2, "stock": 100, "reorder": 40, "cost": 2.50, "velocity": "MEDIUM"},
                {"name": "Coffee Beans (1kg)", "sku": "CB-006", "sup": 1, "stock": 60, "reorder": 30, "cost": 15.00, "velocity": "MEDIUM"},
            ]

            today = timezone.now().date()
            
            for p_data in product_profiles:
                prod, created = Product.objects.get_or_create(
                    store=store, sku=p_data["sku"],
                    defaults={
                        "name": p_data["name"],
                        "supplier": suppliers[p_data["sup"]],
                        "current_stock": p_data["stock"],
                        "reorder_level": p_data["reorder"],
                        "unit_cost": p_data["cost"],
                        "description": f"Quality {p_data['name']} stocked properly."
                    }
                )
                if not created:
                    # Update stock if it already existed
                    prod.current_stock = p_data["stock"]
                    prod.save()
                
                # 3. Create historical sales data (last 30 days)
                SalesRecord.objects.filter(product=prod).delete() # Reset
                
                for i in range(30):
                    date = today - timedelta(days=i)
                    
                    if p_data["velocity"] == "HIGH":
                        qt = random.randint(5, 15)
                    elif p_data["velocity"] == "LOW":
                        qt = random.randint(0, 1) if random.random() > 0.6 else 0
                    else: # MEDIUM
                        qt = random.randint(2, 5)
                        
                    if qt > 0:
                        SalesRecord.objects.create(
                            product=prod,
                            quantity_sold=qt,
                            sale_date=date
                        )

            self.stdout.write(self.style.SUCCESS(f"Successfully seeded complex anomalies for store: {store.name}"))
