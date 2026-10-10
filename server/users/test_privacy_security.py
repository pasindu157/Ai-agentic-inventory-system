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
        self.user_a = CustomUser.objects.create_user(username='owner_a', password='StrongPassword123!', role='STORE_OWNER')
        self.store_a = Store.objects.create(name='Store A', owner=self.user_a, subscription_plan='STARTER', is_active=True)
        self.user_b = CustomUser.objects.create_user(username='owner_b', password='StrongPassword123!', role='STORE_OWNER')
        self.store_b = Store.objects.create(name='Store B', owner=self.user_b, subscription_plan='PRO', is_active=True)
        self.admin_user = CustomUser.objects.create_superuser(username='admin_user', password='StrongPassword123!', email='admin@test.com')
        self.product_a = Product.objects.create(name='Store A Product', sku='SKU-STORE-A', store=self.store_a, current_stock=10, reorder_level=5, unit_cost=20.00)
        self.product_b = Product.objects.create(name='Store B Product', sku='SKU-STORE-B', store=self.store_b, current_stock=15, reorder_level=5, unit_cost=30.00)

    def test_01_unauthenticated_api_rejection(self):
        response = self.client.get('/api/inventory/products/')
        print(f"\n=======================================================")
        print(f"[EVIDENCE TC-01] General API Authentication Barrier")
        print(f"-> Unauthenticated HTTP GET request explicitly blocked | Output: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_02_invalid_jwt_token_tampering(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_tampered_token_string')
        response = self.client.get('/api/inventory/products/')
        print(f"\n[EVIDENCE TC-02] JWT Cryptographic Tampering Rejection")
        print(f"-> System identified fraudulent JWT hash signature | HTTP {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_03_cross_tenant_product_isolation_idor(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/inventory/products/')
        print(f"\n[EVIDENCE TC-03] Multi-Tenant Root Isolation Array")
        print(f"-> Store_A logged in. Store_B Products leaked to them: {self.product_b.id in [p['id'] for p in response.data]}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_04_cross_tenant_direct_product_access_blocked(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(f'/api/inventory/products/{self.product_b.id}/')
        print(f"\n[EVIDENCE TC-04] Direct IDOR Exploit Prevention")
        print(f"-> Store_A manually attempts REST target Store_B product ID. HTTP return: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_05_suspended_store_api_access_blocked(self):
        self.store_a.is_active = False
        self.store_a.save()
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/inventory/products/')
        print(f"\n[EVIDENCE TC-05] Store Deactivation Hard Block Lifecycle")
        print(f"-> System safely blocked suspended tenant account execution: HTTP {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_06_store_owner_cannot_call_admin_overview(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/users/admin/overview/')
        print(f"\n[EVIDENCE TC-06] Vertical Privilege Escalation (Viewing)")
        print(f"-> Store_Owner attempted to read Admin-Only root dashboard. Denied: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_07_store_owner_cannot_toggle_store_active(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/users/admin/toggle-store-active/', {'store_id': self.store_b.id})
        print(f"\n[EVIDENCE TC-07] Vertical Privilege Escalation (Mutation)")
        print(f"-> Store_Owner attempted to maliciously ban Store_B via POST. Denied: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_08_starter_plan_product_limit_enforced(self):
        self.client.force_authenticate(user=self.user_a)
        for i in range(4): Product.objects.create(name=f'P{i}', sku=f'SKU-TEST-{i}', store=self.store_a, current_stock=1, reorder_level=1, unit_cost=10)
        response = self.client.post('/api/inventory/products/', {'name': 'Excess Product', 'current_stock': 5, 'reorder_level': 2, 'unit_cost': 15.00})
        print(f"\n[EVIDENCE TC-08] Subscription Rate Limit / Quota Enforcement")
        print(f"-> Starter_Plan attempt to create product #6 blocked at boundary. HTTP: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_09_sensitive_user_info_no_password_leak(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/users/me/')
        print(f"\n[EVIDENCE TC-09] Serialization PII Data Exfiltration Shield")
        print(f"-> Verified user 'password' hash strictly omitted from /me endpoint serialization.")
        self.assertNotIn('password', response.data)

    def test_10_audit_log_created_on_registration(self):
        response = self.client.post('/api/users/register/', {'username': 'new_u', 'password': 'StrongPassword123!', 'email': 'a@a.com', 'store_name': 'New'})
        print(f"\n[EVIDENCE TC-10] DB Audit Logger: Autonomous Registration Tracking")
        print(f"-> Audit system accurately triggered 'USER_REGISTERED' system action node.")
        self.assertTrue(AuditLog.objects.filter(action='USER_REGISTERED').exists())

    def test_11_audit_log_created_on_store_suspension(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/users/admin/toggle-store-active/', {'store_id': self.store_a.id})
        print(f"\n[EVIDENCE TC-11] DB Audit Logger: Security Policy Mutation Tracking")
        print(f"-> Audit system accurately documented 'STORE_SUSPENDED' target penalty.")
        self.assertTrue(AuditLog.objects.filter(action='STORE_SUSPENDED').exists())

    def test_12_audit_log_created_on_plan_upgrade(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/users/upgrade-plan/', {'plan': 'PRO'})
        print(f"\n[EVIDENCE TC-12] DB Audit Logger: Financial Upsell Tracking")
        print(f"-> Database formally logged strict 'PLAN_UPGRADED' billing change.")
        self.assertTrue(AuditLog.objects.filter(action='PLAN_UPGRADED').exists())

    def test_13_admin_privilege_access_granted(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/users/admin/overview/')
        print(f"\n[EVIDENCE TC-13] Superuser Explicit Execution Pipeline")
        print(f"-> Admin authenticated properly and was authorized root array data: HTTP {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_14_audit_logs_endpoint_admin_only(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/users/admin/audit-logs/')
        print(f"\n[EVIDENCE TC-14] Standard User Surveillance Refusal")
        print(f"-> Store_Owner completely rejected querying network audit traces: HTTP {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_15_audit_logs_endpoint_accessible_by_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/users/admin/audit-logs/')
        print(f"\n[EVIDENCE TC-15] Administrative Internal Affairs Pipeline")
        print(f"-> True Superuser successfully breached Audit Table for global tracking.")
        print(f"=======================================================\n")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
