"""
Admin panel views for managing the banking platform
Custom admin interface separate from Django admin
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    User, Transaction, BillPayment, PaymentGateway,
    WebhookLog, KYC, Wallet
)
from .serializers import (
    TransactionSerializer, BillPaymentSerializer,
    PaymentGatewaySerializer, WebhookLogSerializer,
    KYCSerializer, UserSerializer
)
from .permissions import IsAdmin
from .utils.payment import PaymentProcessor
import logging

logger = logging.getLogger(__name__)


class AdminDashboardView(viewsets.ViewSet):
    """Admin dashboard with statistics"""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get dashboard statistics"""
        # Date range
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Total statistics
        total_users = User.objects.count()
        total_merchants = User.objects.filter(user_type='merchant').count()
        
        total_transactions = Transaction.objects.aggregate(
            count=Count('id'),
            total_amount=Sum('amount')
        )

        # Today's statistics
        today_transactions = Transaction.objects.filter(
            created_at__date=today
        ).aggregate(
            count=Count('id'),
            total_amount=Sum('amount')
        )

        # This week's statistics
        week_transactions = Transaction.objects.filter(
            created_at__date__gte=week_ago
        ).aggregate(
            count=Count('id'),
            total_amount=Sum('amount')
        )

        # Revenue (from fees)
        total_revenue = Transaction.objects.aggregate(
            total_fees=Sum('fee')
        )

        # Pending approvals
        pending_withdrawals = Transaction.objects.filter(
            transaction_type='withdrawal',
            status='pending',
            requires_approval=True
        ).count()

        pending_kyc = KYC.objects.filter(status='pending').count()

        # Bill payments breakdown
        bill_payments_stats = BillPayment.objects.values(
            'bill_type'
        ).annotate(
            count=Count('id'),
            total=Sum('amount')
        )

        # Payment gateway statistics
        gateway_stats = PaymentGateway.objects.aggregate(
            total=Count('id'),
            successful=Count('id', filter=Q(status='successful')),
            pending=Count('id', filter=Q(status='pending')),
            failed=Count('id', filter=Q(status='failed'))
        )

        # Top users by transaction volume
        top_users = User.objects.annotate(
            transaction_count=Count('transactions'),
            total_spent=Sum('transactions__amount')
        ).order_by('-total_spent')[:10]

        return Response({
            'users': {
                'total': total_users,
                'merchants': total_merchants,
                'regular': total_users - total_merchants
            },
            'transactions': {
                'total_count': total_transactions['count'] or 0,
                'total_amount': str(total_transactions['total_amount'] or 0),
                'today_count': today_transactions['count'] or 0,
                'today_amount': str(today_transactions['total_amount'] or 0),
                'week_count': week_transactions['count'] or 0,
                'week_amount': str(week_transactions['total_amount'] or 0)
            },
            'revenue': {
                'total_fees': str(total_revenue['total_fees'] or 0)
            },
            'pending': {
                'withdrawals': pending_withdrawals,
                'kyc': pending_kyc
            },
            'bill_payments': list(bill_payments_stats),
            'payment_gateway': gateway_stats,
            'top_users': UserSerializer(top_users, many=True).data
        })


class AdminTransactionViewSet(viewsets.ModelViewSet):
    """Admin transaction management"""
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ['status', 'transaction_type', 'user']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_queryset(self):
        return Transaction.objects.all().select_related('user', 'wallet')

    @action(detail=True, methods=['post'])
    def approve_withdrawal(self, request, pk=None):
        """Approve a pending withdrawal"""
        transaction = self.get_object()

        if transaction.transaction_type != 'withdrawal':
            return Response({
                'success': False,
                'message': 'Not a withdrawal transaction'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not transaction.requires_approval:
            return Response({
                'success': False,
                'message': 'Transaction does not require approval'
            }, status=status.HTTP_400_BAD_REQUEST)

        if transaction.status != 'pending':
            return Response({
                'success': False,
                'message': 'Transaction is not pending'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Approve transaction
            transaction.approved_by = request.user
            transaction.approved_at = timezone.now()
            transaction.status = 'processing'
            transaction.save()

            logger.info(
                f"Withdrawal approved: {transaction.reference} by "
                f"{request.user.username}"
            )

            return Response({
                'success': True,
                'message': 'Withdrawal approved',
                'transaction': TransactionSerializer(transaction).data
            })

        except Exception as e:
            logger.error(f"Approval error: {e}")
            return Response({
                'success': False,
                'message': 'Approval failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def reject_withdrawal(self, request, pk=None):
        """Reject a pending withdrawal and reverse funds"""
        transaction = self.get_object()

        if transaction.transaction_type != 'withdrawal':
            return Response({
                'success': False,
                'message': 'Not a withdrawal transaction'
            }, status=status.HTTP_400_BAD_REQUEST)

        if transaction.status != 'pending':
            return Response({
                'success': False,
                'message': 'Transaction is not pending'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            reason = request.data.get('reason', 'Rejected by admin')

            # Reverse the transaction
            reversal = PaymentProcessor.reverse_transaction(
                transaction,
                reason
            )

            logger.info(
                f"Withdrawal rejected: {transaction.reference} by "
                f"{request.user.username}"
            )

            return Response({
                'success': True,
                'message': 'Withdrawal rejected and reversed',
                'reversal': TransactionSerializer(reversal).data
            })

        except Exception as e:
            logger.error(f"Rejection error: {e}")
            return Response({
                'success': False,
                'message': 'Rejection failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminBillPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin bill payment management"""
    serializer_class = BillPaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ['bill_type', 'provider', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        return BillPayment.objects.all().select_related('user', 'transaction')


class AdminPaymentGatewayViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin payment gateway management"""
    serializer_class = PaymentGatewaySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ['status', 'merchant']
    ordering = ['-created_at']

    def get_queryset(self):
        return PaymentGateway.objects.all().select_related('merchant')


class AdminWebhookLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin webhook log viewing"""
    serializer_class = WebhookLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ['source', 'status', 'event_type']
    ordering = ['-created_at']

    def get_queryset(self):
        return WebhookLog.objects.all()


class AdminKYCViewSet(viewsets.ModelViewSet):
    """Admin KYC management"""
    serializer_class = KYCSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ['status']
    ordering = ['-submitted_at']

    def get_queryset(self):
        return KYC.objects.all().select_related('user')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve KYC"""
        kyc = self.get_object()

        if kyc.status != 'pending':
            return Response({
                'success': False,
                'message': 'KYC is not pending'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            kyc.status = 'approved'
            kyc.reviewed_by = request.user
            kyc.reviewed_at = timezone.now()
            kyc.save()

            # Update user verification status
            user = kyc.user
            user.is_verified = True
            user.save()

            logger.info(
                f"KYC approved for user: {user.username} by "
                f"{request.user.username}"
            )

            return Response({
                'success': True,
                'message': 'KYC approved',
                'kyc': KYCSerializer(kyc).data
            })

        except Exception as e:
            logger.error(f"KYC approval error: {e}")
            return Response({
                'success': False,
                'message': 'Approval failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject KYC"""
        kyc = self.get_object()

        if kyc.status != 'pending':
            return Response({
                'success': False,
                'message': 'KYC is not pending'
            }, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason', '')
        if not reason:
            return Response({
                'success': False,
                'message': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            kyc.status = 'rejected'
            kyc.rejection_reason = reason
            kyc.reviewed_by = request.user
            kyc.reviewed_at = timezone.now()
            kyc.save()

            logger.info(
                f"KYC rejected for user: {kyc.user.username} by "
                f"{request.user.username}"
            )

            return Response({
                'success': True,
                'message': 'KYC rejected',
                'kyc': KYCSerializer(kyc).data
            })

        except Exception as e:
            logger.error(f"KYC rejection error: {e}")
            return Response({
                'success': False,
                'message': 'Rejection failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminUserViewSet(viewsets.ModelViewSet):
    """Admin user management"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ['user_type', 'is_verified', 'is_active']
    ordering = ['-created_at']

    def get_queryset(self):
        return User.objects.all()

    @action(detail=True, methods=['post'])
    def freeze_wallet(self, request, pk=None):
        """Freeze user's wallet"""
        user = self.get_object()

        try:
            wallet = user.wallet
            wallet.is_frozen = True
            wallet.save()

            logger.warning(
                f"Wallet frozen for user: {user.username} by "
                f"{request.user.username}"
            )

            return Response({
                'success': True,
                'message': 'Wallet frozen'
            })

        except Exception as e:
            logger.error(f"Wallet freeze error: {e}")
            return Response({
                'success': False,
                'message': 'Operation failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def unfreeze_wallet(self, request, pk=None):
        """Unfreeze user's wallet"""
        user = self.get_object()

        try:
            wallet = user.wallet
            wallet.is_frozen = False
            wallet.save()

            logger.info(
                f"Wallet unfrozen for user: {user.username} by "
                f"{request.user.username}"
            )

            return Response({
                'success': True,
                'message': 'Wallet unfrozen'
            })

        except Exception as e:
            logger.error(f"Wallet unfreeze error: {e}")
            return Response({
                'success': False,
                'message': 'Operation failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
