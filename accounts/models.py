from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import re

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, blank=False, null=False)  # Make required
    account_number = models.CharField(max_length=15, unique=True, blank=True, null=True)  # Add account_number
    address = models.CharField(max_length=255, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.username

    def clean_phone_number(self):
        """Clean and format phone number to Nigerian standard"""
        if not self.phone_number:
            return None

        cleaned = re.sub(r'\D', '', self.phone_number)

        if cleaned.startswith('234') and len(cleaned) == 13:
            cleaned = '0' + cleaned[3:]
        elif len(cleaned) == 10 and not cleaned.startswith('0'):
            cleaned = '0' + cleaned
        elif len(cleaned) == 11 and cleaned.startswith('0'):
            pass

        return cleaned if len(cleaned) == 11 and cleaned.startswith('0') else None

    def save(self, *args, **kwargs):
        # Set account_number to phone_number without the first zero
        cleaned_phone = self.clean_phone_number()
        if cleaned_phone:
            self.phone_number = cleaned_phone
            if cleaned_phone.startswith('0'):
                self.account_number = cleaned_phone[1:]
            else:
                self.account_number = cleaned_phone
        if not self.address and hasattr(self, '_address'):
            self.address = self._address
        super().save(*args, **kwargs)


# Profile model - this was missing!
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    middle_name = models.CharField(max_length=30, blank=True, null=True)
    phone_code = models.CharField(max_length=5, default='+234')
    phone = models.CharField(max_length=20, blank=True, null=True)
    alt_phone = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    bvn = models.CharField(max_length=11, blank=True, null=True)
    nin = models.CharField(max_length=11, blank=True, null=True)
    next_of_kin_name = models.CharField(max_length=150, blank=True, null=True)
    next_of_kin_phone_code = models.CharField(max_length=5, default='+234')
    next_of_kin_phone = models.CharField(max_length=20, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # For compatibility
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# BankAccount model
class BankAccount(models.Model):
    ACCOUNT_TYPES = (
        ('checking', 'Checking'),
        ('savings', 'Savings'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=15, unique=True, blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='savings')
    balance = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    is_frozen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.account_number and self.user:
            cleaned_phone = self.user.clean_phone_number()
            self.account_number = cleaned_phone or self.user.phone_number
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.account_number}"

    @classmethod
    def find_by_account_number(cls, account_number):
        cleaned = re.sub(r'\D', '', account_number)
        search_numbers = [cleaned]

        if cleaned.startswith('234') and len(cleaned) == 13:
            search_numbers.append('0' + cleaned[3:])
        elif len(cleaned) == 10:
            search_numbers.append('0' + cleaned)
            search_numbers.append('234' + cleaned)
        elif len(cleaned) == 11 and cleaned.startswith('0'):
            search_numbers.append('234' + cleaned[1:])
            search_numbers.append(cleaned[1:])

        for number in search_numbers:
            try:
                return cls.objects.get(account_number=number)
            except cls.DoesNotExist:
                continue

        return None


# Transaction model
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('funding', 'Wallet Funding'),
        ('airtime', 'Airtime Purchase'),
        ('data', 'Data Purchase'),
        ('tv', 'TV Subscription'),
        ('electricity', 'Electricity Payment'),
        ('bill_payment', 'Bill Payment'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    from_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_transactions')
    to_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, null=True, blank=True, related_name='received_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=255, unique=True, editable=False)
    is_approved = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type.title()} - ₦{self.amount}"


# BillPayment model
class BillPayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    biller_name = models.CharField(max_length=100)
    bill_number = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.biller_name} - ₦{self.amount}"


# KYC model
class KYC(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    id_document = models.FileField(upload_to='kyc_docs/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"KYC for {self.user.username} - {self.status}"


# Stripe Payment Model
class StripePayment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_session_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Stripe Payment - {self.user.username} - ₦{self.amount}"


# Signal handlers
@receiver(post_save, sender=User)
def create_user_profile_and_account(sender, instance, created, **kwargs):
    if created:
        cleaned_phone = instance.clean_phone_number()

        Profile.objects.get_or_create(
            user=instance,
            defaults={
                'phone_number': cleaned_phone or instance.phone_number,
                'phone': cleaned_phone or instance.phone_number,
                'balance': 0.00,
                'name': instance.full_name
            }
        )

        BankAccount.objects.get_or_create(
            user=instance,
            defaults={
                'account_number': cleaned_phone or instance.phone_number,
                'account_type': 'savings',
                'balance': 0.00
            }
        )


@receiver(post_save, sender=User)
def save_user_profile_and_account(sender, instance, **kwargs):
    cleaned_phone = instance.clean_phone_number()
    try:
        profile = instance.profile
        if cleaned_phone and profile.phone_number != cleaned_phone:
            profile.phone_number = cleaned_phone
            profile.phone = cleaned_phone
            profile.save()
    except Profile.DoesNotExist:
        pass

    try:
        account = instance.bankaccount
        if cleaned_phone and account.account_number != cleaned_phone:
            account.account_number = cleaned_phone
            account.save()
    except BankAccount.DoesNotExist:
        pass