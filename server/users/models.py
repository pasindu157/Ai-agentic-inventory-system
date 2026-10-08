from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ADMIN = 'ADMIN'
    STORE_OWNER = 'STORE_OWNER'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (STORE_OWNER, 'Store Owner'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=STORE_OWNER)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Store(models.Model):
    STARTER = 'STARTER'
    PRO = 'PRO'
    ENTERPRISE = 'ENTERPRISE'
    PLAN_CHOICES = [
        (STARTER, 'Starter'),
        (PRO, 'Pro'),
        (ENTERPRISE, 'Enterprise'),
    ]

    name = models.CharField(max_length=255)
    owner = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='store')
    subscription_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=STARTER)
    is_active = models.BooleanField(default=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} [{self.get_subscription_plan_display()}]"
  

class AuditLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100)  # e.g., USER_LOGIN, PLAN_CHANGED, STORE_SUSPENDED, AI_QUERY_EXECUTED
    details = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {username} - {self.action}"
