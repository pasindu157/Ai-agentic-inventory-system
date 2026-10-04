"""
Automated Test Suite for Student 2: Privacy and Data Leakage Assessment.
Tests 15 distinct security scenarios evaluating Authentication, Multi-Tenancy, Authorization, and Data Isolation.
Run via: python manage.py test users.test_privacy_security
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import CustomUser, Store, AuditLog
from inventory.models import Product

class PrivacyAndSecurityTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        
        # Store A Owner
        self.user_a = CustomUser.objects.create_user(username='owner_a', password='StrongPassword123!', role='STORE_OWNER')
        self.store_a = Store.objects.create(name='Store A', owner=self.user_a, subscription_plan='STARTER', is_active=True)
        
        # Store B Owner
        self.user_b = CustomUser.objects.create_user(username='owner_b', password='StrongPassword123!', role='STORE_OWNER')
        self.store_b = Store.objects.create(name='Store B', owner=self.user_b, subscription_plan='PRO', is_active=True)

        # Admin User
        self.admin_user = CustomUser.objects.create_superuser(username='admin_user', password='StrongPassword123!', email='admin@test.com')

        # Product in Store A
        self.product_a = Product.objects.create(name='Store A Product', sku='SKU-STORE-A', store=self.store_a, current_stock=10, reorder_level=5, unit_cost=20.00)
        
        # Product in Store B
        self.product_b = Product.objects.create(name='Store B Product', sku='SKU-STORE-B', store=self.store_b, current_stock=15, reorder_level=5, unit_cost=30.00)

    def test_01_unauthenticated_api_rejection(self):
        response = self.client.get('/api/inventory/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_02_invalid_jwt_token_tampering(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_tampered_token_string')
        response = self.client.get('/api/inventory/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_03_cross_tenant_product_isolation_idor(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/inventory/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_ids = [p['id'] for p in response.data]
        self.assertIn(self.product_a.id, product_ids)
        self.assertNotIn(self.product_b.id, product_ids)

    def test_04_cross_tenant_direct_product_access_blocked(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f'/api/inventory/products/{self.product_b.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_05_suspended_store_api_access_blocked(self):
        self.store_a.is_active = False
        self.store_a.save()
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/inventory/products/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_06_store_owner_cannot_call_admin_overview(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/users/admin/overview/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_07_store_owner_cannot_toggle_store_active(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/users/admin/toggle-store-active/', {'store_id': self.store_b.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_08_starter_plan_product_limit_enforced(self):
        self.client.force_authenticate(user=self.user_a)
        # Create 4 more products (Total 5 = Limit for Starter)
        for i in range(4):
            Product.objects.create(name=f'P{i}', sku=f'SKU-LIMIT-{i}', store=self.store_a, current_stock=1, reorder_level=1, unit_cost=10)
        
        # 6th product attempt
        response = self.client.post('/api/inventory/products/', {
            'name': '6th Product',
            'sku': 'SKU-LIMIT-6TH',
            'current_stock': 5,
            'reorder_level': 2,
            'unit_cost': 15.00
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_09_sensitive_user_info_no_password_leak(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data)

    def test_10_audit_log_created_on_registration(self):
        response = self.client.post('/api/users/register/', {
            'username': 'new_user_testing',
            'password': 'StrongPassword123!',
            'email': 'new@test.com',
            'store_name': 'New Testing Store'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AuditLog.objects.filter(action='USER_REGISTERED').exists())

    def test_11_audit_log_created_on_store_suspension(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/users/admin/toggle-store-active/', {'store_id': self.store_a.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(action='STORE_SUSPENDED').exists())

    def test_12_audit_log_created_on_plan_upgrade(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/users/upgrade-plan/', {'plan': 'PRO'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(action='PLAN_UPGRADED').exists())

    def test_13_admin_privilege_access_granted(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/users/admin/overview/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_14_audit_logs_endpoint_admin_only(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/users/admin/audit-logs/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_15_audit_logs_endpoint_accessible_by_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/users/admin/audit-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
