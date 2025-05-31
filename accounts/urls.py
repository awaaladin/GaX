from django.urls import path, include # Import include
from . import views
from .views import register, LoginView
from django.contrib.auth import views as auth_views
from .views import RegisterView, LoginView, ProfileView,DashboardView,ProfileView,DepositView,WithdrawalView,TransferView,BillPaymentView,KYCUploadView,StripeSessionCreateView,AccountFreezeView,TransactionHistoryView



urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # This makes accounts/ the dashboard
    path('dashboard/', views.dashboard, name='dashboard'),  # Keep this for compatibility
    path('register/', views.register, name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('transfer/', views.transfer_view, name='transfer'),
    path('bill-payment/', views.bill_payment_view, name='bill_payment'),
    path('kyc-upload/', views.kyc_upload_view, name='kyc_upload'),
    path('manage-cards/', views.manage_cards, name='manage_cards'),
    path('transaction-history/', views.transaction_history_view, name='transaction_history'),
    path('approve-transactions/', views.approve_transactions_view, name='approve_transactions'),
    path('buy-airtime/', views.airtime_view, name='buy_airtime'),
    path('buy-data/', views.buy_data, name='buy_data'),
    path('create-stripe-session/', views.create_stripe_session, name='create_stripe_session'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),

    # Include API URLs from the accounts app
    # This line ensures that paths defined in api_urls.py (like 'dashboard/')
    # are accessible under the 'api/accounts/' prefix.
    path('api/accounts/', include('accounts.api_urls')), # ADD THIS LINE
]
