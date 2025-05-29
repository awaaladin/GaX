from django.urls import path
from .views import (
    RegisterView, LoginView, ProfileView, DashboardView,
    DepositView, WithdrawalView, TransferView, BillPaymentView,
    KYCUploadView, StripeSessionCreateView, AccountFreezeView,
    TransactionHistoryView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='api-register'),
    path('login/', LoginView.as_view(), name='api-login'),
    path('profile/', ProfileView.as_view(), name='api-profile'),
    path('dashboard/', DashboardView.as_view(), name='api-dashboard'),
    path('deposit/', DepositView.as_view(), name='api-deposit'),
    path('withdraw/', WithdrawalView.as_view(), name='api-withdraw'),
    path('transfer/', TransferView.as_view(), name='api-transfer'),
    path('pay-bill/', BillPaymentView.as_view(), name='api-bill-payment'),
    path('kyc/', KYCUploadView.as_view(), name='api-kyc-upload'),
    path('stripe-session/', StripeSessionCreateView.as_view(), name='api-stripe-session'),
    path('freeze-account/', AccountFreezeView.as_view(), name='api-freeze-account'),
    path('transactions/', TransactionHistoryView.as_view(), name='api-transaction-history'),
]
