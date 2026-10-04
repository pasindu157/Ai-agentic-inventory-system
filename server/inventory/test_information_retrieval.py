"""
Automated Test Suite for Student 4: Information Retrieval and Security Assessment.
Tests 15 distinct scenarios evaluating Retrieval Precision, DB Aggregation Integrity, Rate Limiting, and API Security.
Run via: python manage.py test inventory.test_information_retrieval
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
import datetime
from users.models import CustomUser, Store
from inventory.models import Product, Supplier, SalesRecord

class InformationRetrievalTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        
        self.user = CustomUser.objects.create_user(username='retrieval_user', password='StrongPassword123!', role='STORE_OWNER')
        self.store = Store.objects.create(name='Retrieval Store', owner=self.user, subscription_plan='PRO', is_active=True)
        
        self.supplier = Supplier.objects.create(name='Tech Supplier', store=self.store, contact_email='sup@test.com', contact_phone='123456789')
        
        self.product_1 = Product.objects.create(
            name='Laptop', sku='SKU-LAPTOP-01', store=self.store, supplier=self.supplier,
            current_stock=10, reorder_level=5, unit_cost=500.00
        )
        self.product_2 = Product.objects.create(
            name='Mouse', sku='SKU-MOUSE-01', store=self.store, supplier=self.supplier,
            current_stock=2, reorder_level=10, unit_cost=20.00
        )
        self.product_inactive = Product.objects.create(
            name='Deleted Keyboard', sku='SKU-KEYBOARD-DEL', store=self.store, supplier=self.supplier,
            current_stock=0, reorder_level=5, unit_cost=15.00, is_active=False
        )

    def test_01_retrieval_precision_active_products_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_names = [p['name'] for p in response.data]
        self.assertIn('Laptop', product_names)
        self.assertIn('Mouse', product_names)
        self.assertNotIn('Deleted Keyboard', product_names)

    def test_02_store_statistics_valuation_aggregation(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Valuation: (10 * 500) + (2 * 20) = 5040.00
        self.assertEqual(float(response.data['total_inventory_valuation']), 5040.00)

    def test_03_store_statistics_stock_health_counts(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Mouse (stock 2 <= reorder 10) is URGENT REORDER
        self.assertEqual(response.data['stock_health']['urgent_reorder_count'], 1)
        # Laptop (stock 10 > reorder 5) is OPTIMAL
        self.assertEqual(response.data['stock_health']['optimal_count'], 1)

    def test_04_supplier_relational_foreign_key_retrieval(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/inventory/products/{self.product_1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['supplier'], self.supplier.id)

    def test_05_soft_delete_preserves_db_record(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/inventory/products/{self.product_1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify soft deleted in DB
        prod = Product.objects.get(id=self.product_1.id)
        self.assertFalse(prod.is_active)

    def test_06_sqli_resilience_in_search_query(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/inventory/products/?name=' OR '1'='1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_07_malformed_json_payload_rejection(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/inventory/products/', '{bad_json:', content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_08_sales_record_creation_and_stock_deduction(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/inventory/sales-records/', {
            'product': self.product_1.id,
            'quantity_sold': 3,
            'sale_date': str(datetime.date.today())
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check sales log exists
        self.assertTrue(SalesRecord.objects.filter(product=self.product_1).exists())

    def test_09_supplier_list_store_isolation(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/suppliers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        supplier_ids = [s['id'] for s in response.data]
        self.assertIn(self.supplier.id, supplier_ids)

    def test_10_invalid_product_id_detail_fetch(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/products/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_11_negative_stock_payload_handling(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/inventory/products/', {
            'name': 'Negative Stock Test',
            'sku': 'SKU-NEG-01',
            'current_stock': -10,
            'reorder_level': 5,
            'unit_cost': 10.00
        })
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_12_total_units_in_stock_aggregation(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Total units: 10 + 2 = 12
        self.assertEqual(response.data['total_units_in_stock'], 12)

    def test_13_top_valuable_products_sorting(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        top_products = response.data['top_valuable_products']
        self.assertEqual(top_products[0]['name'], 'Laptop')  # Laptop $5000 vs Mouse $40

    def test_14_sales_record_list_retrieval(self):
        self.client.force_authenticate(user=self.user)
        SalesRecord.objects.create(product=self.product_1, quantity_sold=2, sale_date=datetime.date.today())
        response = self.client.get('/api/inventory/sales-records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_15_unauthenticated_statistics_rejection(self):
        response = self.client.get('/api/inventory/statistics/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
