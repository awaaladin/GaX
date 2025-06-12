from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserRegistrationForm
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.decorators import login_required
from .models import BankAccount, Transaction, StripePayment
from .forms import DepositForm, WithdrawForm, TransferForm
from .forms import BillPaymentForm
from .models import BillPayment
from .models import KYC
from .forms import KYCUploadForm
from django.db.models import Q
from .forms import TransactionFilterForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from decimal import Decimal
from .forms import ProfileUpdateForm
from .models import Profile, User
from django.contrib import messages
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import json
from django.utils import timezone
import logging
from django.contrib.auth import login as auth_login
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import login
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import jwt
from datetime import datetime, timedelta

# Registration and Login
class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

class LoginView(views.APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response({'message': 'Login successful'})

# Profile and Dashboard
class ProfileView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

class DashboardView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = user.profile
        bank_account = BankAccount.objects.filter(user=user).first()
        transactions = Transaction.objects.filter(user=user).order_by('-timestamp')[:5]
        data = {
            "user": UserSerializer(user).data,
            "profile": ProfileSerializer(profile).data,
            "bank_account": BankAccountSerializer(bank_account).data,
            "recent_transactions": TransactionSerializer(transactions, many=True).data,
            "services": ["deposit", "withdraw", "transfer", "bills", "kyc", "stripe"]
        }
        return Response(data)

# Deposit, Withdrawal, Transfer
class DepositView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']
        details = serializer.validated_data.get('details', '')
        account = request.user.bankaccount
        account.balance += amount
        account.save()
        Transaction.objects.create(user=request.user, amount=amount, transaction_type='deposit',
                                   from_account=account, to_account=account, details=details)
        return Response({'message': 'Deposit successful'})

class WithdrawalView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']
        details = serializer.validated_data.get('details', '')
        account = request.user.bankaccount
        if account.balance < amount:
            return Response({'error': 'Insufficient funds'}, status=400)
        account.balance -= amount
        account.save()
        Transaction.objects.create(user=request.user, amount=amount, transaction_type='withdrawal',
                                   from_account=account, to_account=account, details=details)
        return Response({'message': 'Withdrawal successful'})

class TransferView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        to_account_number = serializer.validated_data['to_account_number']
        amount = serializer.validated_data['amount']
        details = serializer.validated_data.get('details', '')
        from_account = request.user.bankaccount
        to_account = BankAccount.find_by_account_number(to_account_number)
        if from_account.balance < amount:
            return Response({'error': 'Insufficient funds'}, status=400)
        from_account.balance -= amount
        to_account.balance += amount
        from_account.save()
        to_account.save()
        Transaction.objects.create(user=request.user, amount=amount, transaction_type='transfer',
                                   from_account=from_account, to_account=to_account, details=details)
        return Response({'message': 'Transfer successful'})

# Bill Payment
class BillPaymentView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BillPaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = request.user.bankaccount
        if account.balance < serializer.validated_data['amount']:
            return Response({'error': 'Insufficient balance'}, status=400)
        account.balance -= serializer.validated_data['amount']
        account.save()
        BillPayment.objects.create(user=request.user, account=account, **serializer.validated_data)
        return Response({'message': 'Bill payment successful'})

# KYC Upload
class KYCUploadView(generics.CreateAPIView):
    serializer_class = KYCSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Stripe Payment Session
class StripeSessionCreateView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StripeSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']
        StripePayment.objects.create(user=request.user, amount=amount, status='initiated')
        return Response({'message': f'Stripe session for ₦{amount} created (simulation)'})

# Freeze Account
class AccountFreezeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AccountFreezeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_frozen = serializer.validated_data['is_frozen']
        profile = request.user.profile
        profile.is_frozen = is_frozen
        profile.save()
        return Response({'message': f'Account {"frozen" if is_frozen else "unfrozen"}'})

# Transaction History
class TransactionHistoryView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(user=user).order_by('-timestamp')

# Set up logging
logger = logging.getLogger(__name__)

# Set Stripe API key globally for this module
stripe.api_key = settings.STRIPE_SECRET_KEY

class LoginView(DjangoLoginView):
    template_name = 'accounts/login.html' 

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create associated Profile and BankAccount
            profile, created = Profile.objects.get_or_create(user=user)
            bank_account, created = BankAccount.objects.get_or_create(user=user)
            
            # Auto-login the user after registration
            auth_login(request, user)
            
            messages.success(request, 'Registration successful. Welcome to your dashboard!')
            return redirect('dashboard')
        else:
            # Display specific form errors to the user
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_name = form.fields[field].label or field.replace('_', ' ').title()
                        messages.error(request, f"{field_name}: {error}")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})



@login_required
def dashboard(request):
    services = [
        {"name": "Deposit", "icon": "fa-download", "url": "deposit"},
        {"name": "Withdraw", "icon": "fa-upload", "url": "withdraw"},
        {"name": "Transfer", "icon": "fa-exchange-alt", "url": "transfer"},
        {"name": "Bill Pay", "icon": "fa-bolt", "url": "bill_payment"},
        {"name": "KYC", "icon": "fa-id-card", "url": "kyc_upload"},
        {"name": "Transactions", "icon": "fa-history", "url": "transaction_history"},
        {"name": "Freeze Cards", "icon": "fa-snowflake", "url": "manage_cards"},
    ]

    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')[:5]
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Get or create bank account
    bank_account, created = BankAccount.objects.get_or_create(user=request.user)

    # Check for Stripe success/cancel messages
    if request.GET.get('success'):
        messages.success(request, 'Payment successful! Your wallet has been funded.')
    elif request.GET.get('canceled'):
        messages.info(request, 'Payment was canceled.')

    context = {
        'services': services,
        'transactions': transactions,
        'profile': profile,
        'bank_account': bank_account,
        'user': request.user,
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    bank_account, created = BankAccount.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {
        'profile': profile, 
        'bank_account': bank_account
    })

def sync_balances(user):
    """Ensure profile and bank account balances are in sync"""
    try:
        profile = user.profile
        bank_account = user.bankaccount
        
        # Use bank account as the source of truth
        if profile.balance != bank_account.balance:
            profile.balance = bank_account.balance
            profile.save()
    except (Profile.DoesNotExist, BankAccount.DoesNotExist):
        pass

@login_required
def deposit_view(request):
    form = DepositForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        account = form.cleaned_data['account']
        amount = form.cleaned_data['amount']
        
        # Update account balance
        account.balance += amount
        account.save()
        
        # Update profile balance
        profile = request.user.profile
        profile.balance += amount
        profile.save()
        
        Transaction.objects.create(
            user=request.user,
            to_account=account, 
            transaction_type='deposit', 
            amount=amount,
            details='Manual deposit'
        )
        messages.success(request, f'Successfully deposited ₦{amount}')
        return redirect('dashboard')
    return render(request, 'accounts/transaction_form.html', {'form': form, 'title': 'Deposit'})

@login_required
def withdraw_view(request):
    form = WithdrawForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        account = form.cleaned_data['account']
        amount = form.cleaned_data['amount']
        if amount <= account.balance:
            # Update account balance
            account.balance -= amount
            account.save()
            
            # Update profile balance
            profile = request.user.profile
            profile.balance -= amount
            profile.save()
            
            Transaction.objects.create(
                user=request.user,
                from_account=account, 
                transaction_type='withdrawal', 
                amount=amount,
                details='Manual withdrawal'
            )
            messages.success(request, f'Successfully withdrew ₦{amount}')
            return redirect('dashboard')
        else:
            messages.error(request, 'Insufficient balance')
    return render(request, 'accounts/withdraw.html', {'form': form, 'title': 'Withdraw'})

@login_required
def transfer_view(request):
    form = TransferForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        from_account = form.cleaned_data['from_account']
        to_account_number = form.cleaned_data['to_account_number']  # Changed from to_account
        amount = form.cleaned_data['amount']
        
        # Find recipient account by phone number
        to_account = BankAccount.find_by_account_number(to_account_number)
        if not to_account:
            messages.error(request, 'Recipient account not found')
            return render(request, 'accounts/transfer.html', {'form': form, 'title': 'Transfer'})
        
        if from_account == to_account:
            messages.error(request, 'Cannot transfer to the same account')
            return render(request, 'accounts/transfer.html', {'form': form, 'title': 'Transfer'})
        
        if amount <= from_account.balance:
            # Update balances
            from_account.balance -= amount
            to_account.balance += amount
            from_account.save()
            to_account.save()
            
            # Update profile balances
            sender_profile = from_account.user.profile
            sender_profile.balance -= amount
            sender_profile.save()
            
            receiver_profile = to_account.user.profile
            receiver_profile.balance += amount
            receiver_profile.save()
            
            Transaction.objects.create(
                user=request.user,
                from_account=from_account, 
                to_account=to_account,
                transaction_type='transfer', 
                amount=amount,
                details=f'Transfer to {to_account.account_number}'
            )
            messages.success(request, f'Successfully transferred ₦{amount} to {to_account.account_number}')
            return redirect('dashboard')
        else:
            messages.error(request, 'Insufficient balance')
    return render(request, 'accounts/transfer.html', {'form': form, 'title': 'Transfer'})

@login_required
def bill_payment_view(request):
    if request.method == 'POST':
        form = BillPaymentForm(request.user, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            account = data['account']
            amount = data['amount']
            if account.balance >= amount:
                account.balance -= amount
                account.save()
                
                # Update profile balance
                profile = request.user.profile
                profile.balance -= amount
                profile.save()
                
                BillPayment.objects.create(
                    user=request.user,
                    account=account,
                    biller_name=data['biller_name'],
                    bill_number=data['bill_number'],
                    amount=amount
                )
                
                Transaction.objects.create(
                    user=request.user,
                    from_account=account,
                    transaction_type='bill_payment',
                    amount=amount,
                    details=f"{data['biller_name']} - {data['bill_number']}"
                )
                
                messages.success(request, "Bill paid successfully.")
                return redirect('dashboard')
            else:
                messages.error(request, "Insufficient balance.")
    else:
        form = BillPaymentForm(request.user)
    return render(request, 'accounts/bill_payment.html', {'form': form, 'title': 'Bill Payment'})

@login_required
def kyc_upload_view(request):
    try:
        kyc = request.user.kyc
    except KYC.DoesNotExist:
        kyc = None

    if request.method == 'POST':
        form = KYCUploadForm(request.POST, request.FILES, instance=kyc)
        if form.is_valid():
            kyc_obj = form.save(commit=False)
            kyc_obj.user = request.user
            kyc_obj.status = 'pending'
            kyc_obj.save()
            messages.success(request, "KYC document submitted successfully.")
            return redirect('dashboard')
    else:
        form = KYCUploadForm(instance=kyc)

    return render(request, 'accounts/kyc_upload.html', {'form': form, 'kyc': kyc})

@login_required
def manage_cards(request):
    accounts = BankAccount.objects.filter(user=request.user)
    if request.method == 'POST':
        for account in accounts:
            key = f"freeze_{account.id}"
            if key in request.POST:
                account.is_frozen = not account.is_frozen
                account.save()
        messages.success(request, "Card freeze settings updated.")
        return redirect('manage_cards')

    return render(request, 'accounts/manage_cards.html', {'accounts': accounts})

@login_required
def transaction_history_view(request):
    form = TransactionFilterForm(request.user, request.GET or None)
    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')

    if form.is_valid():
        if form.cleaned_data['account']:
            account = form.cleaned_data['account']
            transactions = transactions.filter(
                Q(from_account=account) | Q(to_account=account)
            )
        if form.cleaned_data['transaction_type']:
            transactions = transactions.filter(transaction_type=form.cleaned_data['transaction_type'])
        if form.cleaned_data['start_date']:
            transactions = transactions.filter(timestamp__date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data['end_date']:
            transactions = transactions.filter(timestamp__date__lte=form.cleaned_data['end_date'])

    return render(request, 'accounts/transaction_history.html', {
        'form': form,
        'transactions': transactions,
    })

@staff_member_required
def approve_transactions_view(request):
    pending_txns = Transaction.objects.filter(requires_approval=True, is_approved=False)

    if request.method == 'POST':
        txn_id = request.POST.get('txn_id')
        action = request.POST.get('action')
        txn = Transaction.objects.get(id=txn_id)

        if action == 'approve':
            txn.is_approved = True
            txn.save()
        elif action == 'reject':
            txn.delete()

        messages.success(request, "Transaction decision recorded.")
        return redirect('approve_transactions')

    return render(request, 'accounts/approve_transactions.html', {'transactions': pending_txns})

def process_service_payment(user, amount, service_type, details):
    """Process service payments (airtime, data, etc.)"""
    try:
        bank_account = user.bankaccount
        profile = user.profile
        
        if bank_account.balance >= amount:
            # Update balances
            bank_account.balance -= amount
            bank_account.save()
            
            profile.balance -= amount
            profile.save()
            
            # Create transaction record
            Transaction.objects.create(
                user=user, 
                from_account=bank_account,
                transaction_type=service_type, 
                amount=amount, 
                details=details
            )
            return True
    except (BankAccount.DoesNotExist, Profile.DoesNotExist):
        pass
    return False

@login_required
def airtime_view(request):
    if request.method == 'POST':
        network = request.POST.get('network')
        number = request.POST.get('number')
        amount = Decimal(request.POST.get('amount'))

        if process_service_payment(request.user, amount, 'airtime', f"{network} - {number}"):
            messages.success(request, 'Airtime purchase successful.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Insufficient balance.')

    return render(request, 'services/airtime.html')

@login_required
def buy_data(request):
    if request.method == 'POST':
        network = request.POST.get('network')
        number = request.POST.get('number')
        amount = Decimal(request.POST.get('amount'))

        if process_service_payment(request.user, amount, 'data', f"{network} - {number}"):
            messages.success(request, 'Data purchase successful.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Insufficient balance.')

    return render(request, 'services/data.html')

@login_required
def pay_electricity(request):
    if request.method == 'POST':
        disco = request.POST.get('disco')
        meter = request.POST.get('meter')
        amount = Decimal(request.POST.get('amount'))

        if process_service_payment(request.user, amount, 'electricity', f"{disco} - {meter}"):
            messages.success(request, 'Electricity payment successful.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Insufficient balance.')

    return render(request, 'services/electricity.html')

@login_required
def update_profile_picture(request):
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        profile = Profile.objects.get(user=request.user)
        profile.profile_picture = request.FILES['profile_picture']
        profile.save()
    return redirect('profile')

@login_required
def update_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    return render(request, 'accounts/update_profile.html', {'form': form})

@csrf_exempt
@login_required
def create_stripe_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        data = json.loads(request.body)
        amount = int(data.get('amount', 0))  # Amount in kobo
        
        if amount < 100:  # Less than ₦1.00
            return JsonResponse({'error': 'Amount must be at least ₦1.00'}, status=400)

        # Create Stripe session
        domain = request.build_absolute_uri('/').rstrip('/')
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'ngn',
                    'product_data': {'name': 'Wallet Funding'},
                    'unit_amount': amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{domain}/accounts/dashboard/?success=true',
            cancel_url=f'{domain}/accounts/dashboard/?canceled=true',
            metadata={
                'user_id': str(request.user.id),
                'amount_naira': str(amount / 100)  # Store amount in naira for reference
            }
        )

        # Create StripePayment record for tracking
        StripePayment.objects.create(
            user=request.user,
            stripe_session_id=session.id,
            amount=Decimal(str(amount / 100)),  # Convert kobo to naira
            status='pending'
        )

        logger.info(f"Stripe session created: {session.id} for user {request.user.username}")
        return JsonResponse({'sessionId': session.id})

    except Exception as e:
        logger.error(f"Stripe session creation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        return HttpResponse(status=400)

    logger.info(f" Stripe Event Received: {event['type']}")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session['id']
        user_id = session['metadata'].get('user_id')
        amount_naira = float(session['amount_total']) / 100  # Convert from kobo

        try:
            # Get user
            user = User.objects.get(id=user_id)

            # Update StripePayment record
            stripe_payment = StripePayment.objects.get(stripe_session_id=session_id)
            stripe_payment.status = 'completed'
            stripe_payment.completed_at = timezone.now()
            stripe_payment.save()

            # Get or create user's profile and bank account
            profile, _ = Profile.objects.get_or_create(user=user)
            bank_account, _ = BankAccount.objects.get_or_create(user=user)

            amount_decimal = Decimal(str(amount_naira))

            # Update balances
            profile.balance += amount_decimal
            profile.save()

            bank_account.balance += amount_decimal
            bank_account.save()

            # Create transaction record
            Transaction.objects.create(
                user=user,
                to_account=bank_account,
                transaction_type='funding',
                amount=amount_decimal,
                details='Stripe Wallet Funding'
            )

            logger.info(f"✅ Wallet funded: ₦{amount_naira} for user {user.username}")
            logger.info(f"✅ Profile balance: ₦{profile.balance}")
            logger.info(f"✅ Bank account balance: ₦{bank_account.balance}")

        except User.DoesNotExist:
            logger.error(f"❌ User ID {user_id} not found")
        except StripePayment.DoesNotExist:
            logger.error(f"❌ StripePayment record with session ID {session_id} not found")
        except Exception as e:
            logger.error(f"❌ Error processing payment: {str(e)}")

    return HttpResponse(status=200)

def login_view(request):
    if request.method == 'POST':
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }, settings.SECRET_KEY, algorithm='HS256')
        
        response = JsonResponse({'success': True})
        response.set_cookie(
            'django_api_token', 
            token, 
            max_age=86400,
            secure=True,
            samesite='None'
        )
        
        # Send token via postMessage
        response.content = f"""
            <script>
                window.parent.postMessage({{
                    type: 'token',
                    token: '{token}'
                }}, 'https://choropiaz-2.onrender.com');
            </script>
        """
        return response
    return render(request, 'accounts/login.html')
