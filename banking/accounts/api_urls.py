"""
URL Configuration for Banking API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .api_views import (
    RegisterView, SetTransactionPINView,
    WalletViewSet, DepositView, WithdrawalView, TransferView,
    AirtimeView, DataView, TVView, ElectricityView,
    InitiatePaymentView, VerifyPaymentView, PaymentStatusView,
    MoniepointWebhookView,
    TransactionViewSet, APIKeyViewSet
)

# Create router
router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'api-keys', APIKeyViewSet, basename='apikey')

urlpatterns = [
    # Authentication
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/set-pin/', SetTransactionPINView.as_view(), name='set_pin'),

    # Wallet operations
    path('wallet/deposit/', DepositView.as_view(), name='deposit'),
    path('wallet/withdraw/', WithdrawalView.as_view(), name='withdraw'),
    path('wallet/transfer/', TransferView.as_view(), name='transfer'),

    # Bill payments
    path('bills/airtime/', AirtimeView.as_view(), name='airtime'),
    path('bills/data/', DataView.as_view(), name='data'),
    path('bills/tv/', TVView.as_view(), name='tv'),
    path('bills/electricity/', ElectricityView.as_view(), name='electricity'),

    # Payment Gateway (for merchants)
    path('payments/initiate/', InitiatePaymentView.as_view(), name='payment_initiate'),
    path('payments/verify/', VerifyPaymentView.as_view(), name='payment_verify'),
    path('payments/status/<str:reference>/', PaymentStatusView.as_view(), name='payment_status'),

    # Webhooks
    path('webhooks/moniepoint/', MoniepointWebhookView.as_view(), name='moniepoint_webhook'),

    # Router URLs
    path('', include(router.urls)),
]
