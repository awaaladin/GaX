from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Profile, BankAccount, Transaction, BillPayment, KYC, StripePayment

# User Registration
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user)
        BankAccount.objects.create(user=user)
        return user

# User Login
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        data['user'] = user
        return data

# User & Profile
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'dob', 'gender', 'is_frozen']

# Bank Account
class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ['account_number', 'balance', 'created_at']

# Deposit
class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    details = serializers.CharField(required=False)

# Withdrawal
class WithdrawalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    details = serializers.CharField(required=False)

# Transfer
class TransferSerializer(serializers.Serializer):
    to_account_number = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    details = serializers.CharField(required=False)

# Transaction
class TransactionSerializer(serializers.ModelSerializer):
    from_account = BankAccountSerializer()
    to_account = BankAccountSerializer()

    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'transaction_type', 'from_account', 'to_account', 'details', 'timestamp']

# Bill Payment
class BillPaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillPayment
        fields = ['amount', 'biller_name', 'account_number', 'service_type', 'reference']

class BillPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillPayment
        fields = '__all__'

# KYC Upload
class KYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYC
        fields = ['document_type', 'document']

# Stripe Payment
class StripeSessionCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

# Freeze Account
class AccountFreezeSerializer(serializers.Serializer):
    is_frozen = serializers.BooleanField()
