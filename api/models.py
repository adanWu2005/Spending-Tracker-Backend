from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
import string

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plaid_access_token = models.CharField(max_length=500, blank=True, null=True)
    plaid_item_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_cursor = models.CharField(max_length=500, blank=True, null=True)
    # Consent fields
    data_consent_given = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    # Security tracking fields
    last_vulnerability_scan = models.DateTimeField(null=True, blank=True)
    last_access_review = models.DateTimeField(null=True, blank=True)
    last_patch_update = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class BankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plaid_account_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=50)  # checking, savings, credit, etc.
    subtype = models.CharField(max_length=50, blank=True, null=True)
    mask = models.CharField(max_length=10, blank=True, null=True)
    institution_name = models.CharField(max_length=200)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.institution_name}"

class SpendingCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#000000")  # Hex color code
    icon = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    plaid_transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    name = models.CharField(max_length=200)
    merchant_name = models.CharField(max_length=200, blank=True, null=True)
    category = models.ManyToManyField(SpendingCategory, blank=True)
    primary_category = models.ForeignKey(SpendingCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_transactions')
    pending = models.BooleanField(default=False)
    payment_channel = models.CharField(max_length=50, blank=True, null=True)
    transaction_type = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.name} - ${self.amount} - {self.date}"



class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = ''.join(random.choices(string.digits, k=6))
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired()

    class Meta:
        ordering = ['-created_at']

class DataRetentionPolicy(models.Model):
    """Model to track data retention and deletion policies"""
    policy_name = models.CharField(max_length=200, default="Data Retention and Deletion Policy")
    is_implemented = models.BooleanField(default=True)
    last_reviewed = models.DateTimeField(auto_now=True)
    next_review_date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Data Retention Policy - {'Active' if self.is_implemented else 'Inactive'}"

class AccessProvisioning(models.Model):
    """Model to track automated access de-provisioning"""
    feature_name = models.CharField(max_length=200, default="Automated Access De-provisioning")
    is_implemented = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Access De-provisioning - {'Active' if self.is_implemented else 'Inactive'}"

class ZeroTrustArchitecture(models.Model):
    """Model to track zero trust access architecture"""
    architecture_name = models.CharField(max_length=200, default="Zero Trust Access Architecture")
    is_implemented = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Zero Trust Architecture - {'Active' if self.is_implemented else 'Inactive'}"

class CentralizedIAM(models.Model):
    """Model to track centralized identity and access management"""
    iam_name = models.CharField(max_length=200, default="Centralized Identity and Access Management")
    is_implemented = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Centralized IAM - {'Active' if self.is_implemented else 'Inactive'}"
