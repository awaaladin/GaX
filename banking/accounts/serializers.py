from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.db import transaction
from decimal import Decimal
from .models import (
    User, Profile, Wallet, BankAccount, Transaction,
    BillPayment, PaymentGateway, APIKey, WebhookLog, KYC
)
import re


class UserSerializer(serializers.ModelSerializer):
    """User serializer with password hashing"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'confirm_password',
            'phone_number', 'address', 'first_name', 'last_name',
            'user_type', 'is_verified', 'email_verified',
            'phone_verified', 'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']

    def validate_phone_number(self, value):
        """Validate Nigerian phone number"""
        if not re.match(r'^(\+234|234|0)[789][01]\d{8}$', value):
            raise serializers.ValidationError(
                "Invalid Nigerian phone number format"
            )
        return value

    def validate(self, attrs):
        """Validate password match"""
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({
                "password": "Passwords do not match"
            })
        return attrs

    def create(self, validated_data):
        """Create user with hashed password (wallet/profile created by signals)"""
        validated_data['password'] = make_password(
            validated_data['password']
        )
        user = User.objects.create(**validated_data)
        # Wallet and Profile are automatically created by signals
        return user


class ProfileSerializer(serializers.ModelSerializer):
    """Profile serializer"""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'username', 'name', 'phone_number', 'age', 'bio',
            'profile_picture', 'location', 'bvn', 'nin',
            'date_of_birth', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WalletSerializer(serializers.ModelSerializer):
    """Wallet serializer"""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Wallet
        fields = [
            'id', 'username', 'account_number', 'balance',
            'ledger_balance', 'currency', 'is_active', 'is_frozen',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'account_number', 'balance', 'ledger_balance',
            'created_at', 'updated_at'
        ]


class BankAccountSerializer(serializers.ModelSerializer):
    """Bank account serializer"""

    class Meta:
        model = BankAccount
        fields = [
            'id', 'bank_name', 'bank_code', 'account_number',
            'account_name', 'account_type', 'is_verified',
            'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']

    def validate_account_number(self, value):
        """Validate account number format"""
        if not re.match(r'^\d{10}$', value):
            raise serializers.ValidationError(
                "Account number must be 10 digits"
            )
        return value


class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer"""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'username', 'transaction_type', 'amount', 'fee',
            'total_amount', 'reference', 'external_reference', 'status',
            'description', 'metadata', 'recipient_account',
            'recipient_name', 'recipient_bank', 'balance_before',
            'balance_after', 'requires_approval', 'created_at',
            'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'reference', 'total_amount', 'status',
            'balance_before', 'balance_after', 'created_at',
            'updated_at', 'completed_at'
        ]


class DepositSerializer(serializers.Serializer):
    """Deposit serializer"""
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('100.00')
    )
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )
    metadata = serializers.JSONField(required=False)


class WithdrawalSerializer(serializers.Serializer):
    """Withdrawal serializer"""
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('100.00')
    )
    bank_account_id = serializers.UUIDField()
    transaction_pin = serializers.CharField(max_length=4)
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )

    def validate_transaction_pin(self, value):
        """Validate PIN format"""
        if not re.match(r'^\d{4}$', value):
            raise serializers.ValidationError("PIN must be 4 digits")
        return value


class TransferSerializer(serializers.Serializer):
    """Transfer serializer"""
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('100.00')
    )
    recipient_account = serializers.CharField(max_length=10)
    recipient_bank = serializers.CharField(max_length=100, required=False)
    transaction_pin = serializers.CharField(max_length=4)
    narration = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )

    def validate_transaction_pin(self, value):
        """Validate PIN format"""
        if not re.match(r'^\d{4}$', value):
            raise serializers.ValidationError("PIN must be 4 digits")
        return value

    def validate_recipient_account(self, value):
        """Validate account number"""
        if not re.match(r'^\d{10}$', value):
            raise serializers.ValidationError(
                "Account number must be 10 digits"
            )
        return value


class BillPaymentSerializer(serializers.ModelSerializer):
    """Bill payment serializer"""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = BillPayment
        fields = [
            'id', 'username', 'bill_type', 'provider', 'amount',
            'phone_number', 'smartcard_number', 'meter_number',
            'customer_name', 'reference', 'external_reference',
            'status', 'token', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reference', 'external_reference', 'status',
            'customer_name', 'token', 'created_at', 'updated_at'
        ]


class AirtimeSerializer(serializers.Serializer):
    """Airtime purchase serializer"""
    provider = serializers.ChoiceField(
        choices=['mtn', 'glo', 'airtel', '9mobile']
    )
    phone_number = serializers.CharField(max_length=15)
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('50.00'),
        max_value=Decimal('10000.00')
    )
    transaction_pin = serializers.CharField(max_length=4)

    def validate_phone_number(self, value):
        """Validate phone number"""
        if not re.match(r'^(\+234|234|0)[789][01]\d{8}$', value):
            raise serializers.ValidationError(
                "Invalid Nigerian phone number"
            )
        return value


class DataSerializer(serializers.Serializer):
    """Data purchase serializer"""
    provider = serializers.ChoiceField(
        choices=['mtn', 'glo', 'airtel', '9mobile']
    )
    phone_number = serializers.CharField(max_length=15)
    plan_code = serializers.CharField(max_length=50)
    transaction_pin = serializers.CharField(max_length=4)

    def validate_phone_number(self, value):
        """Validate phone number"""
        if not re.match(r'^(\+234|234|0)[789][01]\d{8}$', value):
            raise serializers.ValidationError(
                "Invalid Nigerian phone number"
            )
        return value


class TVSerializer(serializers.Serializer):
    """TV subscription serializer"""
    provider = serializers.ChoiceField(
        choices=['dstv', 'gotv', 'startimes']
    )
    smartcard_number = serializers.CharField(max_length=50)
    plan_code = serializers.CharField(max_length=50)
    transaction_pin = serializers.CharField(max_length=4)


class ElectricitySerializer(serializers.Serializer):
    """Electricity payment serializer"""
    provider = serializers.ChoiceField(
        choices=['phed', 'ikedc', 'aedc', 'eedc', 'ekedc']
    )
    meter_number = serializers.CharField(max_length=50)
    meter_type = serializers.ChoiceField(
        choices=['prepaid', 'postpaid']
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('500.00')
    )
    transaction_pin = serializers.CharField(max_length=4)


class PaymentGatewaySerializer(serializers.ModelSerializer):
    """Payment gateway serializer"""

    class Meta:
        model = PaymentGateway
        fields = [
            'id', 'customer_email', 'customer_name', 'customer_phone',
            'amount', 'fee', 'merchant_amount', 'currency', 'reference',
            'payment_url', 'callback_url', 'metadata', 'status',
            'paid_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'reference', 'fee', 'merchant_amount', 'payment_url',
            'status', 'paid_at', 'created_at'
        ]


class InitiatePaymentSerializer(serializers.Serializer):
    """Initiate payment serializer"""
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('100.00')
    )
    email = serializers.EmailField()
    customer_name = serializers.CharField(
        max_length=255,
        required=False
    )
    customer_phone = serializers.CharField(
        max_length=15,
        required=False
    )
    callback_url = serializers.URLField(required=False)
    metadata = serializers.JSONField(required=False)

    def validate_customer_phone(self, value):
        """Validate phone number if provided"""
        if value and not re.match(
            r'^(\+234|234|0)[789][01]\d{8}$',
            value
        ):
            raise serializers.ValidationError(
                "Invalid Nigerian phone number"
            )
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    """Verify payment serializer"""
    reference = serializers.CharField(max_length=255)


class APIKeySerializer(serializers.ModelSerializer):
    """API key serializer"""
    secret = serializers.CharField(read_only=True)

    class Meta:
        model = APIKey
        fields = [
            'id', 'key', 'secret', 'environment', 'is_active',
            'name', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'key', 'secret', 'created_at']


class WebhookLogSerializer(serializers.ModelSerializer):
    """Webhook log serializer"""

    class Meta:
        model = WebhookLog
        fields = [
            'id', 'source', 'event_type', 'payload', 'signature',
            'is_verified', 'status', 'response', 'error_message',
            'ip_address', 'created_at', 'processed_at'
        ]
        read_only_fields = fields


class KYCSerializer(serializers.ModelSerializer):
    """KYC serializer"""

    class Meta:
        model = KYC
        fields = [
            'id', 'document_type', 'document_number', 'id_document',
            'selfie', 'status', 'rejection_reason', 'submitted_at',
            'reviewed_at'
        ]
        read_only_fields = [
            'id', 'status', 'rejection_reason', 'submitted_at',
            'reviewed_at'
        ]

    def validate_document_number(self, value):
        """Validate document number format"""
        document_type = self.initial_data.get('document_type')

        if document_type == 'nin' and not re.match(r'^\d{11}$', value):
            raise serializers.ValidationError(
                "NIN must be 11 digits"
            )

        return value


class SetTransactionPINSerializer(serializers.Serializer):
    """Set transaction PIN serializer"""
    pin = serializers.CharField(max_length=4)
    confirm_pin = serializers.CharField(max_length=4)

    def validate_pin(self, value):
        """Validate PIN format"""
        if not re.match(r'^\d{4}$', value):
            raise serializers.ValidationError("PIN must be 4 digits")
        return value

    def validate(self, attrs):
        """Validate PIN match"""
        if attrs['pin'] != attrs['confirm_pin']:
            raise serializers.ValidationError({
                "pin": "PINs do not match"
            })
        return attrs
