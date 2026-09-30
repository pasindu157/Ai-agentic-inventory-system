import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from inventory.models import Supplier, Product, SalesRecord, PurchaseOrder


class Command(BaseCommand):
    help = 'Seeds database with realistic mock data for inventory, suppliers, and sales history.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding database...'))

        # Clear existing data to avoid duplicates on re-runs
        SalesRecord.objects.all().delete()
        PurchaseOrder.objects.all().delete()
        Product.objects.all().delete()
        Supplier.objects.all().delete()

        # 1. Create Suppliers
        suppliers_data = [
            {'name': 'AudioMax Inc.', 'contact_email': 'support@audiomax.com', 'lead_time_days': 4},
            {'name': 'TechSupplies Co.', 'contact_email': 'sales@techsupplies.com', 'lead_time_days': 5},
            {'name': 'Global Electronics Ltd.', 'contact_email': 'orders@globalelectronics.com', 'lead_time_days': 7},
        ]

        supplier_objs = {}
        for s_data in suppliers_data:
            supplier = Supplier.objects.create(**s_data)
            supplier_objs[supplier.name] = supplier
            self.stdout.write(self.style.SUCCESS(f'Created Supplier: {supplier.name}'))

        # 2. Create Products
        products_data = [
            {
                'name': 'Wireless Headphones',
                'sku': 'WH-1001',
                'category': 'Audio',
                'current_stock': 50,
                'reorder_level': 20,
                'unit_cost': 45.00,
                'unit_price': 89.99,
                'default_supplier': supplier_objs['AudioMax Inc.'],
                'avg_daily_sales': 8,
            },
            {
                'name': 'Mechanical Gaming Keyboard',
                'sku': 'KB-2002',
                'category': 'Peripherals',
                'current_stock': 35,
                'reorder_level': 15,
                'unit_cost': 30.00,
                'unit_price': 64.99,
                'default_supplier': supplier_objs['TechSupplies Co.'],
                'avg_daily_sales': 5,
            },
            {
                'name': 'Ergonomic Wireless Mouse',
                'sku': 'MS-3003',
                'category': 'Peripherals',
                'current_stock': 12,
                'reorder_level': 25,
                'unit_cost': 15.00,
                'unit_price': 34.99,
                'default_supplier': supplier_objs['TechSupplies Co.'],
                'avg_daily_sales': 6,
            },
            {
                'name': '4K Ultra HD Monitor 27"',
                'sku': 'MN-4004',
                'category': 'Displays',
                'current_stock': 18,
                'reorder_level': 10,
                'unit_cost': 180.00,
                'unit_price': 299.99,
                'default_supplier': supplier_objs['Global Electronics Ltd.'],
                'avg_daily_sales': 3,
            },
            {
                'name': 'USB-C Docking Station',
                'sku': 'DK-5005',
                'category': 'Accessories',
                'current_stock': 40,
                'reorder_level': 15,
                'unit_cost': 40.00,
                'unit_price': 79.99,
                'default_supplier': supplier_objs['Global Electronics Ltd.'],
                'avg_daily_sales': 4,
            },
            {
                'name': 'Noise-Cancelling Earbuds',
                'sku': 'EB-6006',
                'category': 'Audio',
                'current_stock': 8,
                'reorder_level': 20,
                'unit_cost': 50.00,
                'unit_price': 119.99,
                'default_supplier': supplier_objs['AudioMax Inc.'],
                'avg_daily_sales': 7,
            },
            {
                'name': 'HD Webcam 1080p',
                'sku': 'WC-7007',
                'category': 'Accessories',
                'current_stock': 60,
                'reorder_level': 15,
                'unit_cost': 22.00,
                'unit_price': 49.99,
                'default_supplier': supplier_objs['TechSupplies Co.'],
                'avg_daily_sales': 4,
            },
        ]

        product_objs = []
        for p_data in products_data:
            avg_daily_sales = p_data.pop('avg_daily_sales')
            product = Product.objects.create(**p_data)
            product_objs.append((product, avg_daily_sales))
            self.stdout.write(self.style.SUCCESS(f'Created Product: {product.name} (Stock: {product.current_stock})'))

        # 3. Create 30 days of daily historical sales data
        today = date.today()
        random.seed(42)  # For reproducible realistic data

        sales_records_to_create = []
        for product, avg_sales in product_objs:
            for day_offset in range(30, 0, -1):
                sale_date = today - timedelta(days=day_offset)
                # Vary daily sales around average (e.g., +/- 2 units, min 0)
                qty_sold = max(0, int(random.gauss(avg_sales, 1.5)))
                if qty_sold > 0:
                    total_price = round(qty_sold * float(product.unit_price), 2)
                    sales_records_to_create.append(
                        SalesRecord(
                            product=product,
                            quantity_sold=qty_sold,
                            sale_date=sale_date,
                            total_price=total_price,
                        )
                    )

        SalesRecord.objects.bulk_create(sales_records_to_create)
        self.stdout.write(self.style.SUCCESS(f'Created {len(sales_records_to_create)} historical sales records across 30 days.'))

        # 4. Create sample Purchase Orders
        po1 = PurchaseOrder.objects.create(
            product=product_objs[2][0],  # Ergonomic Wireless Mouse
            supplier=product_objs[2][0].default_supplier,
            quantity=50,
            status='PENDING'
        )
        self.stdout.write(self.style.SUCCESS(f'Created Purchase Order #{po1.id} for {po1.product.name}'))

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
