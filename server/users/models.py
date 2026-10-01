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
    name = models.CharField(max_length=255)
    owner = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='store')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
