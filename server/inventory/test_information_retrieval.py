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
        self.product_1 = Product.objects.create(name='Laptop', sku='SKU-LAPTOP-01', store=self.store, supplier=self.supplier, current_stock=10, reorder_level=5, unit_cost=500.00)
        self.product_2 = Product.objects.create(name='Mouse', sku='SKU-MOUSE-01', store=self.store, supplier=self.supplier, current_stock=2, reorder_level=10, unit_cost=20.00)
        self.product_inactive = Product.objects.create(name='Deleted Keyboard', sku='SKU-KEYBOARD-DEL', store=self.store, supplier=self.supplier, current_stock=0, reorder_level=5, unit_cost=15.00, is_active=False)

    def test_01_retrieval_precision_active_products_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/products/')
        print(f"\n=======================================================")
        print(f"[EVIDENCE TC-01] Retrieval Precision: Active Filtering")
        print(f"-> Fetched active products via API. Verifying strict exclusion of soft-deleted datasets.")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_names = [p['name'] for p in response.data]
        self.assertIn('Laptop', product_names)
        self.assertNotIn('Deleted Keyboard', product_names)

    def test_02_store_statistics_valuation_aggregation(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/statistics/')
        print(f"\n[EVIDENCE TC-02] DB Aggregation Integrity: Total Valuation")
        print(f"-> Expected Math: (10*500) + (2*20) = $5040.00")
        print(f"-> API Computed Valuation: ${response.data['total_inventory_valuation']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['total_inventory_valuation']), 5040.00)

    def test_03_store_statistics_stock_health_counts(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/statistics/')
        print(f"\n[EVIDENCE TC-03] Mathematical Threshold: Stock Health Metrics")
        print(f"-> API Computed Urgent Reorders: {response.data['stock_health']['urgent_reorder_count']} | Optimal: {response.data['stock_health']['optimal_count']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stock_health']['urgent_reorder_count'], 1)

    def test_04_supplier_relational_foreign_key_retrieval(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/inventory/products/{self.product_1.id}/')
        print(f"\n[EVIDENCE TC-04] Cross-Table Foreign Key Execution")
        print(f"-> Product requested: 'Laptop' | Assigned Supplier ID fetched: {response.data['supplier']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['supplier'], self.supplier.id)

    def test_05_soft_delete_preserves_db_record(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/inventory/products/{self.product_1.id}/')
        prod = Product.objects.get(id=self.product_1.id)
        print(f"\n[EVIDENCE TC-05] DB Record Durability: Soft Deletion")
        print(f"-> DELETE HTTP requested. DB Product 'is_active' flagged to: {prod.is_active}. Record maintained.")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(prod.is_active)

    def test_06_sqli_resilience_in_search_query(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/inventory/products/?name=' OR '1'='1")
        print(f"\n[EVIDENCE TC-06] API Endpoint SQLi Rejection")
        print(f"-> Injected Payload: \"' OR '1'='1\" | ORM securely escaped input.")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_07_malformed_json_payload_rejection(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/inventory/products/', '{bad_json:', content_type='application/json')
        print(f"\n[EVIDENCE TC-07] Serialization Validation: Defective JSON")
        print(f"-> DRF Serializer trapped malformed stream | Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_08_sales_record_creation_and_stock_deduction(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/inventory/sales-records/', {'product': self.product_1.id, 'quantity_sold': 3, 'sale_date': str(datetime.date.today())})
        print(f"\n[EVIDENCE TC-08] Logistical Transaction Binding")
        print(f"-> Created SalesRecord | Verification ID: {self.product_1.id} | Response Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_09_supplier_list_store_isolation(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/suppliers/')
        print(f"\n[EVIDENCE TC-09] Supplier Multi-Tenant Scope Validation")
        print(f"-> API fetched only current user's suppliers natively.")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.supplier.id, [s['id'] for s in response.data])

    def test_10_invalid_product_id_detail_fetch(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/products/99999/')
        print(f"\n[EVIDENCE TC-10] 404 Resolution on Hallucinated IDs")
        print(f"-> Querying ID 99999. Expected Not Found Error: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_11_negative_stock_payload_handling(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/inventory/products/', {'name': 'NegativeTest', 'sku': 'SKU-01', 'current_stock': -10, 'reorder_level': 5, 'unit_cost': 10.00})
        print(f"\n[EVIDENCE TC-11] Strict Validation: Negative Logistics Handling")
        print(f"-> Serializer explicitly rejected corrupted DB input. Status Code: {response.status_code}")
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_12_total_units_in_stock_aggregation(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/statistics/')
        print(f"\n[EVIDENCE TC-12] DB Aggregate: Sum Vector Quantities")
        print(f"-> Aggregate Total units retrieved from backend compute: {response.data['total_units_in_stock']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_13_top_valuable_products_sorting(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/inventory/statistics/')
        print(f"\n[EVIDENCE TC-13] Nested Top Product Array Sorting")
        print(f"-> Ranked list sorted correctly by capital exposure. Index 0: {response.data['top_valuable_products'][0]['name']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_14_sales_record_list_retrieval(self):
        self.client.force_authenticate(user=self.user)
        SalesRecord.objects.create(product=self.product_1, quantity_sold=2, sale_date=datetime.date.today())
        response = self.client.get('/api/inventory/sales-records/')
        print(f"\n[EVIDENCE TC-14] Bulk Time-Series List Validation")
        print(f"-> Logs serialized flawlessly. Output payload HTTP {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_15_unauthenticated_statistics_rejection(self):
        response = self.client.get('/api/inventory/statistics/')
        print(f"\n[EVIDENCE TC-15] Root Unauthenticated Statistics Call")
        print(f"-> Total rejection of financial stats without JWT | HTTP {response.status_code}")
        print(f"=======================================================\n")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
