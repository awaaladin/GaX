from django.db import models
from django.conf import settings  
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
import secrets

# Custom user model
class User(AbstractUser):
    USER_TYPES = (
        ('user', 'User'),
        ('merchant', 'Merchant'),
        ('admin', 'Admin'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=15, unique=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='user')
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    transaction_pin = models.CharField(max_length=255, blank=True, null=True)  # Hashed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'users'


# Profile model
class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100)  
    phone_number = models.CharField(max_length=15, unique=True)  
    age = models.IntegerField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    bvn = models.CharField(max_length=11, blank=True, null=True, unique=True)
    nin = models.CharField(max_length=11, blank=True, null=True, unique=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        db_table = 'profiles'


# Wallet model - Core wallet system
class Wallet(models.Model):
    CURRENCY_CHOICES = (
        ('NGN', 'Nigerian Naira'),
        ('USD', 'US Dollar'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    account_number = models.CharField(max_length=10, unique=True, blank=True)
    balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    ledger_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NGN')
    is_active = models.BooleanField(default=True)
    is_frozen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            # Generate 10-digit account number
            self.account_number = '20' + str(uuid.uuid4().int)[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.account_number} - ₦{self.balance}"

    class Meta:
        db_table = 'wallets'


# BankAccount model - For linking external bank accounts
class BankAccount(models.Model):
    ACCOUNT_TYPES = (
        ('checking', 'Checking'),
        ('savings', 'Savings'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=10)
    account_number = models.CharField(max_length=10)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='savings')
    is_verified = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.bank_name} - {self.account_number}"

    class Meta:
        db_table = 'bank_accounts'
        unique_together = ('user', 'account_number', 'bank_code')


# Transaction model - All financial transactions
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('bill_payment', 'Bill Payment'),
        ('airtime', 'Airtime'),
        ('data', 'Data'),
        ('tv', 'TV Subscription'),
        ('electricity', 'Electricity'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    reference = models.CharField(max_length=255, unique=True, editable=False, db_index=True)
    external_reference = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    recipient_account = models.CharField(max_length=100, blank=True, null=True)
    recipient_name = models.CharField(max_length=255, blank=True, null=True)
    recipient_bank = models.CharField(max_length=100, blank=True, null=True)
    balance_before = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transactions')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"TXN-{uuid.uuid4().hex[:16].upper()}"
        if not self.total_amount:
            self.total_amount = self.amount + self.fee
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} - {self.transaction_type.title()} - ₦{self.amount}"

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]


# BillPayment model - All bill payments
class BillPayment(models.Model):
    BILL_TYPES = (
        ('airtime', 'Airtime'),
        ('data', 'Data'),
        ('tv', 'TV Subscription'),
        ('electricity', 'Electricity'),
    )
    
    PROVIDERS = (
        # Airtime/Data
        ('mtn', 'MTN'),
        ('glo', 'Glo'),
        ('airtel', 'Airtel'),
        ('9mobile', '9Mobile'),
        # TV
        ('dstv', 'DSTV'),
        ('gotv', 'GOtv'),
        ('startimes', 'Startimes'),
        # Electricity
        ('phed', 'PHED'),
        ('ikedc', 'IKEDC'),
        ('aedc', 'AEDC'),
        ('eedc', 'EEDC'),
        ('ekedc', 'EKEDC'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bill_payments')
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='bill_payment', null=True)
    bill_type = models.CharField(max_length=20, choices=BILL_TYPES)
    provider = models.CharField(max_length=50, choices=PROVIDERS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # For airtime/data
    smartcard_number = models.CharField(max_length=50, blank=True, null=True)  # For TV
    meter_number = models.CharField(max_length=50, blank=True, null=True)  # For electricity
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    reference = models.CharField(max_length=255, unique=True, editable=False)
    external_reference = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response_data = models.JSONField(default=dict, blank=True)
    token = models.TextField(blank=True, null=True)  # For electricity meter tokens
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"BILL-{uuid.uuid4().hex[:16].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bill_type} - {self.provider} - ₦{self.amount}"

    class Meta:
        db_table = 'bill_payments'
        ordering = ['-created_at']


# PaymentGateway model - For merchant integration
class PaymentGateway(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('abandoned', 'Abandoned'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gateway_payments')
    customer_email = models.EmailField()
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_phone = models.CharField(max_length=15, blank=True, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    merchant_amount = models.DecimalField(max_digits=15, decimal_places=2)  # Amount after fee
    currency = models.CharField(max_length=3, default='NGN')
    reference = models.CharField(max_length=255, unique=True, editable=False, db_index=True)
    payment_url = models.URLField(max_length=500, blank=True, null=True)
    callback_url = models.URLField(max_length=500, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='gateway_payment')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"PAY-{uuid.uuid4().hex[:20].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} - ₦{self.amount} - {self.status}"

    class Meta:
        db_table = 'payment_gateway'
        ordering = ['-created_at']


# APIKey model - For merchant authentication
class APIKey(models.Model):
    ENVIRONMENT_CHOICES = (
        ('test', 'Test'),
        ('live', 'Live'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    key = models.CharField(max_length=255, unique=True, editable=False, db_index=True)
    secret = models.CharField(max_length=255, editable=False)
    environment = models.CharField(max_length=10, choices=ENVIRONMENT_CHOICES, default='test')
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.key:
            env_prefix = 'sk_test' if self.environment == 'test' else 'sk_live'
            self.key = f"{env_prefix}_{secrets.token_urlsafe(32)}"
        if not self.secret:
            self.secret = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.key[:20]}..."

    class Meta:
        db_table = 'api_keys'
        ordering = ['-created_at']


# WebhookLog model - For logging all webhooks
class WebhookLog(models.Model):
    STATUS_CHOICES = (
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('invalid', 'Invalid Signature'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=50)  # moniepoint, paystack, etc.
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    signature = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='webhook_logs')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source} - {self.event_type} - {self.status}"

    class Meta:
        db_table = 'webhook_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['source', 'event_type']),
            models.Index(fields=['status']),
        ]


# KYC model
class KYC(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    DOCUMENT_TYPES = (
        ('nin', 'NIN'),
        ('drivers_license', "Driver's License"),
        ('voters_card', "Voter's Card"),
        ('international_passport', 'International Passport'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=50)
    id_document = models.FileField(upload_to='kyc_docs/')
    selfie = models.ImageField(upload_to='kyc_selfies/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='kyc_reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"KYC for {self.user.username} - {self.status}"

    class Meta:
        db_table = 'kyc'
