"""
API Views for Digital Banking and Payment Gateway
All REST API endpoints for production use
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction as db_transaction
from django.utils import timezone
from django.conf import settings
from django.shortcuts import get_object_or_404
from decimal import Decimal
import logging

from .models import (
    User, Profile, Wallet, BankAccount, Transaction,
    BillPayment, PaymentGateway, APIKey, WebhookLog, KYC
)
from .serializers import (
    UserSerializer, ProfileSerializer, WalletSerializer,
    BankAccountSerializer, TransactionSerializer,
    DepositSerializer, WithdrawalSerializer, TransferSerializer,
    BillPaymentSerializer, AirtimeSerializer, DataSerializer,
    TVSerializer, ElectricitySerializer,
    PaymentGatewaySerializer, InitiatePaymentSerializer,
    VerifyPaymentSerializer, APIKeySerializer,
    WebhookLogSerializer, KYCSerializer,
    SetTransactionPINSerializer
)
from .utils.payment import PaymentProcessor
from .utils.moniepoint import MoniepointAPI
from .utils.signature import SignatureVerifier
from .utils.bills import (
    AirtimeService, DataService, TVService, ElectricityService
)
from .permissions import IsOwnerOrReadOnly, IsMerchant, IsAPIKeyAuthenticated
from .throttling import UserRateThrottle, MerchantRateThrottle

logger = logging.getLogger(__name__)


# ==================== AUTHENTICATION ====================

class RegisterView(APIView):
    """User registration"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class SetTransactionPINView(APIView):
    """Set or update transaction PIN"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SetTransactionPINSerializer(data=request.data)
        if serializer.is_valid():
            pin = serializer.validated_data['pin']

            # Hash and save PIN
            request.user.transaction_pin = SignatureVerifier.hash_transaction_pin(pin)
            request.user.save()

            return Response({
                'message': 'Transaction PIN set successfully'
            })

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ==================== WALLET OPERATIONS ====================

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """Wallet viewset - Read only"""
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)


class DepositView(APIView):
    """Deposit funds to wallet"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        if serializer.is_valid():
            try:
                wallet = request.user.wallet
                amount = serializer.validated_data['amount']
                description = serializer.validated_data.get(
                    'description',
                    'Wallet deposit'
                )
                metadata = serializer.validated_data.get('metadata', {})

                # Process deposit
                txn = PaymentProcessor.credit_wallet(
                    wallet=wallet,
                    amount=amount,
                    description=description,
                    transaction_type='deposit',
                    metadata=metadata
                )

                return Response({
                    'success': True,
                    'transaction': TransactionSerializer(txn).data,
                    'wallet': WalletSerializer(wallet).data,
                    'message': 'Deposit successful'
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Deposit error: {e}")
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class WithdrawalView(APIView):
    """Withdraw funds to bank account"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = WithdrawalSerializer(data=request.data)
        if serializer.is_valid():
            try:
                wallet = request.user.wallet
                amount = serializer.validated_data['amount']
                bank_account_id = serializer.validated_data['bank_account_id']
                transaction_pin = serializer.validated_data['transaction_pin']

                # Get bank account
                bank_account = get_object_or_404(
                    BankAccount,
                    id=bank_account_id,
                    user=request.user
                )

                # Process withdrawal
                txn = PaymentProcessor.process_withdrawal(
                    wallet=wallet,
                    amount=amount,
                    bank_account=bank_account,
                    transaction_pin=transaction_pin
                )

                return Response({
                    'success': True,
                    'transaction': TransactionSerializer(txn).data,
                    'message': 'Withdrawal initiated. Pending approval.'
                }, status=status.HTTP_201_CREATED)

            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Withdrawal error: {e}")
                return Response({
                    'success': False,
                    'message': 'Withdrawal failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class TransferView(APIView):
    """Transfer funds to another wallet"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @db_transaction.atomic
    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        if serializer.is_valid():
            try:
                wallet = request.user.wallet
                amount = serializer.validated_data['amount']
                recipient_account = serializer.validated_data['recipient_account']
                transaction_pin = serializer.validated_data['transaction_pin']
                narration = serializer.validated_data.get('narration', 'Transfer')

                # Process transfer
                result = PaymentProcessor.process_transfer(
                    sender_wallet=wallet,
                    recipient_account=recipient_account,
                    amount=amount,
                    narration=narration,
                    transaction_pin=transaction_pin
                )

                return Response({
                    'success': True,
                    'transaction': TransactionSerializer(
                        result['debit_transaction']
                    ).data,
                    'message': result['message']
                }, status=status.HTTP_201_CREATED)

            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Transfer error: {e}")
                return Response({
                    'success': False,
                    'message': 'Transfer failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ==================== BILL PAYMENTS ====================

class AirtimeView(APIView):
    """Purchase airtime"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = AirtimeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = AirtimeService()
                result = service.purchase_airtime(
                    user=request.user,
                    wallet=request.user.wallet,
                    provider=serializer.validated_data['provider'],
                    phone_number=serializer.validated_data['phone_number'],
                    amount=serializer.validated_data['amount'],
                    transaction_pin=serializer.validated_data['transaction_pin']
                )

                return Response({
                    'success': True,
                    'bill_payment': BillPaymentSerializer(
                        result['bill_payment']
                    ).data,
                    'message': result['message']
                }, status=status.HTTP_201_CREATED)

            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Airtime purchase error: {e}")
                return Response({
                    'success': False,
                    'message': 'Airtime purchase failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class DataView(APIView):
    """Purchase data bundle"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = DataSerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = DataService()
                result = service.purchase_data(
                    user=request.user,
                    wallet=request.user.wallet,
                    provider=serializer.validated_data['provider'],
                    phone_number=serializer.validated_data['phone_number'],
                    plan_code=serializer.validated_data['plan_code'],
                    transaction_pin=serializer.validated_data['transaction_pin']
                )

                return Response({
                    'success': True,
                    'bill_payment': BillPaymentSerializer(
                        result['bill_payment']
                    ).data,
                    'message': result['message']
                }, status=status.HTTP_201_CREATED)

            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Data purchase error: {e}")
                return Response({
                    'success': False,
                    'message': 'Data purchase failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class TVView(APIView):
    """Purchase TV subscription"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = TVSerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = TVService()
                result = service.purchase_subscription(
                    user=request.user,
                    wallet=request.user.wallet,
                    provider=serializer.validated_data['provider'],
                    smartcard_number=serializer.validated_data['smartcard_number'],
                    plan_code=serializer.validated_data['plan_code'],
                    transaction_pin=serializer.validated_data['transaction_pin']
                )

                return Response({
                    'success': True,
                    'bill_payment': BillPaymentSerializer(
                        result['bill_payment']
                    ).data,
                    'message': result['message']
                }, status=status.HTTP_201_CREATED)

            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"TV subscription error: {e}")
                return Response({
                    'success': False,
                    'message': 'Subscription failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ElectricityView(APIView):
    """Purchase electricity"""
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = ElectricitySerializer(data=request.data)
        if serializer.is_valid():
            try:
                service = ElectricityService()
                result = service.purchase_electricity(
                    user=request.user,
                    wallet=request.user.wallet,
                    provider=serializer.validated_data['provider'],
                    meter_number=serializer.validated_data['meter_number'],
                    meter_type=serializer.validated_data['meter_type'],
                    amount=serializer.validated_data['amount'],
                    transaction_pin=serializer.validated_data['transaction_pin']
                )

                return Response({
                    'success': True,
                    'bill_payment': BillPaymentSerializer(
                        result['bill_payment']
                    ).data,
                    'token': result.get('token'),
                    'message': result['message']
                }, status=status.HTTP_201_CREATED)

            except ValueError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Electricity payment error: {e}")
                return Response({
                    'success': False,
                    'message': 'Payment failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ==================== PAYMENT GATEWAY ====================

class InitiatePaymentView(APIView):
    """Initiate payment for merchants"""
    permission_classes = [IsAPIKeyAuthenticated]
    throttle_classes = [MerchantRateThrottle]

    @db_transaction.atomic
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                merchant = request.user
                amount = serializer.validated_data['amount']
                email = serializer.validated_data['email']

                # Calculate fee
                fee = PaymentProcessor.calculate_payment_gateway_fee(amount)
                merchant_amount = amount - fee

                # Create payment gateway record
                payment = PaymentGateway.objects.create(
                    merchant=merchant,
                    customer_email=email,
                    customer_name=serializer.validated_data.get('customer_name'),
                    customer_phone=serializer.validated_data.get('customer_phone'),
                    amount=amount,
                    fee=fee,
                    merchant_amount=merchant_amount,
                    callback_url=serializer.validated_data.get('callback_url'),
                    metadata=serializer.validated_data.get('metadata', {}),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )

                # Generate payment URL
                payment_url = f"{settings.FRONTEND_URL}/pay/{payment.reference}"
                payment.payment_url = payment_url
                payment.save()

                logger.info(
                    f"Payment initiated: {payment.reference} - "
                    f"₦{amount} - {merchant.username}"
                )

                return Response({
                    'success': True,
                    'payment_url': payment_url,
                    'reference': payment.reference,
                    'amount': str(amount),
                    'fee': str(fee),
                    'merchant_amount': str(merchant_amount)
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                logger.error(f"Payment initiation error: {e}")
                return Response({
                    'success': False,
                    'message': 'Payment initiation failed'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class VerifyPaymentView(APIView):
    """Verify payment status"""
    permission_classes = [IsAPIKeyAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                reference = serializer.validated_data['reference']
                payment = get_object_or_404(
                    PaymentGateway,
                    reference=reference,
                    merchant=request.user
                )

                return Response({
                    'success': True,
                    'payment': PaymentGatewaySerializer(payment).data
                })

            except Exception as e:
                logger.error(f"Payment verification error: {e}")
                return Response({
                    'success': False,
                    'message': 'Verification failed'
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class PaymentStatusView(APIView):
    """Get payment status (public endpoint)"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, reference):
        try:
            payment = get_object_or_404(
                PaymentGateway,
                reference=reference
            )

            return Response({
                'reference': payment.reference,
                'amount': str(payment.amount),
                'status': payment.status,
                'paid_at': payment.paid_at
            })

        except Exception as e:
            return Response({
                'success': False,
                'message': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)


class MoniepointWebhookView(APIView):
    """Handle Moniepoint webhooks"""
    permission_classes = [permissions.AllowAny]

    @db_transaction.atomic
    def post(self, request):
        try:
            # Get signature from headers
            signature = request.headers.get('X-Moniepoint-Signature', '')

            # Log webhook
            webhook_log = WebhookLog.objects.create(
                source='moniepoint',
                event_type=request.data.get('eventType', 'unknown'),
                payload=request.data,
                signature=signature,
                ip_address=self.get_client_ip(request)
            )

            # Verify signature
            if not SignatureVerifier.verify_moniepoint_signature(
                request.data,
                signature
            ):
                webhook_log.status = 'invalid'
                webhook_log.error_message = 'Invalid signature'
                webhook_log.save()

                return Response({
                    'success': False,
                    'message': 'Invalid signature'
                }, status=status.HTTP_401_UNAUTHORIZED)

            webhook_log.is_verified = True
            webhook_log.status = 'processing'
            webhook_log.save()

            # Process webhook based on event type
            event_type = request.data.get('eventType')

            if event_type == 'SUCCESSFUL_TRANSACTION':
                self.handle_successful_transaction(request.data, webhook_log)
            elif event_type == 'FAILED_TRANSACTION':
                self.handle_failed_transaction(request.data, webhook_log)

            webhook_log.status = 'processed'
            webhook_log.processed_at = timezone.now()
            webhook_log.save()

            return Response({'success': True})

        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def handle_successful_transaction(self, payload, webhook_log):
        """Handle successful transaction webhook"""
        try:
            reference = payload.get('transactionReference')
            amount = Decimal(str(payload.get('amount', 0)))

            # Find payment
            payment = PaymentGateway.objects.filter(
                reference=reference
            ).first()

            if payment and payment.status == 'pending':
                # Update payment
                payment.status = 'successful'
                payment.paid_at = timezone.now()
                payment.save()

                # Credit merchant wallet
                merchant_wallet = payment.merchant.wallet
                txn = PaymentProcessor.credit_wallet(
                    wallet=merchant_wallet,
                    amount=payment.merchant_amount,
                    description=f"Payment: {reference}",
                    transaction_type='payment',
                    metadata={'payment_id': str(payment.id)}
                )

                payment.transaction = txn
                payment.save()

                webhook_log.transaction = txn
                webhook_log.save()

                logger.info(
                    f"Payment completed: {reference} - ₦{amount}"
                )

        except Exception as e:
            logger.error(f"Transaction handling error: {e}")
            raise

    def handle_failed_transaction(self, payload, webhook_log):
        """Handle failed transaction webhook"""
        try:
            reference = payload.get('transactionReference')

            payment = PaymentGateway.objects.filter(
                reference=reference
            ).first()

            if payment:
                payment.status = 'failed'
                payment.save()

                logger.info(f"Payment failed: {reference}")

        except Exception as e:
            logger.error(f"Failed transaction handling error: {e}")
            raise

    def get_client_ip(self, request):
        """Get client IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# ==================== TRANSACTIONS ====================

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Transaction viewset"""
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['transaction_type', 'status']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


# ==================== API KEYS ====================

class APIKeyViewSet(viewsets.ModelViewSet):
    """API key management for merchants"""
    serializer_class = APIKeySerializer
    permission_classes = [permissions.IsAuthenticated, IsMerchant]

    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
