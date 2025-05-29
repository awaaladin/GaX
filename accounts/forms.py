from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
import re
from .models import Profile, BankAccount, Transaction, KYC, BillPayment

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    # User model fields
    username = forms.CharField(max_length=150, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    middle_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)  # Add this to User model fields
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput, required=True)

    # Profile-related fields
    phone_code = forms.CharField(max_length=5, required=True, initial='+234', widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    alt_phone = forms.CharField(max_length=20, required=False)
    country = forms.ChoiceField(choices=[('nigeria', 'Nigeria'), ('ghana', 'Ghana'), ('kenya', 'Kenya'), ('uk', 'United Kingdom'), ('us', 'United States')], required=True)
    state = forms.CharField(max_length=100, required=True)
    city = forms.CharField(max_length=100, required=True)
    address = forms.CharField(max_length=255, required=True)
    postal_code = forms.CharField(max_length=20, required=False)

    # Identification numbers
    bvn = forms.CharField(max_length=11, required=False)
    nin = forms.CharField(max_length=11, required=False)

    # Next of kin
    next_of_kin_name = forms.CharField(max_length=150, required=True)
    next_of_kin_phone_code = forms.CharField(max_length=5, required=True, initial='+234', widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    next_of_kin_phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'middle_name', 'last_name', 'email', 'phone_number', 'password1', 'password2')

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone:
            raise ValidationError('Phone number is required.')

        # Remove all non-digit characters
        cleaned = re.sub(r'\D', '', phone)

        # Validate length and prefix depending on country code
        phone_code = self.cleaned_data.get('phone_code') or '+234'

        if phone_code == '+234':
            # Nigerian phone number validation
            if len(cleaned) not in [10, 11]:
                raise ValidationError('Phone number must be 10 or 11 digits for Nigeria.')
            if not cleaned.startswith(('7', '8', '9')):
                raise ValidationError('Nigerian phone number must start with 7, 8, or 9.')
        else:
            # Generic check for length between 7 and 15 digits
            if len(cleaned) < 7 or len(cleaned) > 15:
                raise ValidationError('Phone number must be between 7 and 15 digits.')

        # Check if phone number already exists in User model
        if User.objects.filter(phone_number=cleaned).exists():
            raise ValidationError('This phone number is already registered.')

        return cleaned

    def clean_alt_phone(self):
        phone = self.cleaned_data.get('alt_phone')
        if phone:
            cleaned = re.sub(r'\D', '', phone)
            if len(cleaned) < 7 or len(cleaned) > 15:
                raise ValidationError('Alternative phone number must be between 7 and 15 digits.')
            if not cleaned.isdigit():
                raise ValidationError('Alternative phone number must contain only digits.')
            return cleaned
        return ''

    def clean_next_of_kin_phone(self):
        phone = self.cleaned_data.get('next_of_kin_phone')
        if not phone:
            raise ValidationError('Next of kin phone number is required.')
        cleaned = re.sub(r'\D', '', phone)
        if len(cleaned) < 7 or len(cleaned) > 15:
            raise ValidationError('Next of kin phone number must be between 7 and 15 digits.')
        if not cleaned.isdigit():
            raise ValidationError('Next of kin phone number must contain only digits.')
        return cleaned

    def clean_bvn(self):
        bvn = self.cleaned_data.get('bvn')
        country = self.cleaned_data.get('country')

        if country == 'nigeria':
            if not bvn:
                raise ValidationError("BVN is required for Nigerian residents.")
            if len(bvn) != 11 or not bvn.isdigit():
                raise ValidationError("BVN must be exactly 11 digits.")
        return bvn or ''

    def clean_nin(self):
        nin = self.cleaned_data.get('nin')
        country = self.cleaned_data.get('country')
        
        # Only require NIN for Nigerian users
        if country == 'nigeria' and not nin:
            raise ValidationError("NIN is required for Nigerian residents.")
        
        if nin:
            if len(nin) != 11 or not nin.isdigit():
                raise ValidationError("NIN must be exactly 11 digits.")
        return nin or ''

    def clean_bvn(self):
        bvn = self.cleaned_data.get('bvn')
        country = self.cleaned_data.get('country')

        # Only require BVN for Nigerian users
        if country == 'nigeria' and not bvn:
            raise ValidationError("BVN is required for Nigerian residents.")
        
        if bvn:
            if len(bvn) != 11 or not bvn.isdigit():
                raise ValidationError("BVN must be exactly 11 digits.")
        return bvn or ''

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')
        if postal_code and not re.match(r'^[A-Za-z0-9\s\-]+$', postal_code):
            raise ValidationError('Postal code contains invalid characters.')
        return postal_code or ''

    def clean(self):
        cleaned_data = super().clean()
        # Additional cross-field validations if needed
        alt_phone = cleaned_data.get('alt_phone')
        phone_number = cleaned_data.get('phone_number')
        if alt_phone and phone_number and alt_phone == phone_number:
            self.add_error('alt_phone', 'Alternative phone number must be different from primary phone number.')
        return cleaned_data

    def save(self, commit=True):
        # Save the user with phone_number
        user = super().save(commit=False)
        user.phone_number = self.cleaned_data.get('phone_number')
        
        if commit:
            user.save()
            
            # Get or create profile
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Update profile fields
            profile.middle_name = self.cleaned_data.get('middle_name', '')
            profile.phone_code = self.cleaned_data.get('phone_code', '+234')
            profile.phone = self.cleaned_data.get('phone_number', '')
            profile.alt_phone = self.cleaned_data.get('alt_phone', '')
            profile.country = self.cleaned_data.get('country', '')
            profile.state = self.cleaned_data.get('state', '')
            profile.city = self.cleaned_data.get('city', '')
            profile.address = self.cleaned_data.get('address', '')
            profile.postal_code = self.cleaned_data.get('postal_code', '')
            profile.bvn = self.cleaned_data.get('bvn', '')
            profile.nin = self.cleaned_data.get('nin', '')
            profile.next_of_kin_name = self.cleaned_data.get('next_of_kin_name', '')
            profile.next_of_kin_phone_code = self.cleaned_data.get('next_of_kin_phone_code', '+234')
            profile.next_of_kin_phone = self.cleaned_data.get('next_of_kin_phone', '')
            
            profile.save()
            
        return user


class CustomLoginForm(forms.Form):
    """Custom login form that supports username or phone number"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Phone Number'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Try to authenticate with username first
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            
            # If that fails, try with phone number
            if self.user_cache is None:
                try:
                    # Look for user by phone number
                    user = User.objects.get(phone_number=username)
                    self.user_cache = authenticate(
                        self.request,
                        username=user.username,
                        password=password
                    )
                except User.DoesNotExist:
                    pass
            
            if self.user_cache is None:
                raise ValidationError('Invalid username/phone number or password')
            
        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    class Meta:
        model = Profile
        fields = ['middle_name', 'phone', 'alt_phone', 'age', 'bio', 'profile_picture', 'city', 'state', 'bvn']
        widgets = {
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Middle Name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'alt_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Alternative Phone Number'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 18,
                'max': 120
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State'
            }),
            'bvn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank Verification Number (11 digits)',
                'maxlength': 11
            })
        }

    def clean_bvn(self):
        bvn = self.cleaned_data.get('bvn')
        if bvn:
            if not bvn.isdigit() or len(bvn) != 11:
                raise ValidationError('BVN must be exactly 11 digits')
        return bvn


class DepositForm(forms.Form):
    """Form for making deposits"""
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'] = forms.ModelChoiceField(
            queryset=BankAccount.objects.filter(user=user),
            widget=forms.Select(attrs={'class': 'form-control'}),
            empty_label="Select Account"
        )
        self.fields['amount'] = forms.DecimalField(
            max_digits=12,
            decimal_places=2,
            min_value=Decimal('1.00'),
            widget=forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'step': '0.01',
                'min': '1.00'
            })
        )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount < Decimal('1.00'):
            raise ValidationError('Minimum deposit amount is ₦1.00')
        if amount and amount > Decimal('1000000.00'):
            raise ValidationError('Maximum deposit amount is ₦1,000,000.00')
        return amount


class WithdrawForm(forms.Form):
    """Form for making withdrawals"""
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['account'] = forms.ModelChoiceField(
            queryset=BankAccount.objects.filter(user=user),
            widget=forms.Select(attrs={'class': 'form-control'}),
            empty_label="Select Account"
        )
        self.fields['amount'] = forms.DecimalField(
            max_digits=12,
            decimal_places=2,
            min_value=Decimal('1.00'),
            widget=forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'step': '0.01',
                'min': '1.00'
            })
        )

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        amount = cleaned_data.get('amount')

        if account and amount:
            if amount > account.balance:
                raise ValidationError('Insufficient balance in selected account')
            if account.is_frozen:
                raise ValidationError('Cannot withdraw from frozen account')

        return cleaned_data


class TransferForm(forms.Form):
    """Form for making transfers"""
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['from_account'] = forms.ModelChoiceField(
            queryset=BankAccount.objects.filter(user=user),
            widget=forms.Select(attrs={'class': 'form-control'}),
            empty_label="Select Source Account",
            label="From Account"
        )
        self.fields['to_account_number'] = forms.CharField(
            max_length=15,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter recipient phone number'
            }),
            label="Recipient Phone Number"
        )
        self.fields['amount'] = forms.DecimalField(
            max_digits=12,
            decimal_places=2,
            min_value=Decimal('1.00'),
            widget=forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'step': '0.01',
                'min': '1.00'
            })
        )

    def clean_to_account_number(self):
        account_number = self.cleaned_data.get('to_account_number')
        if account_number:
            # Clean the phone number
            cleaned = re.sub(r'\D', '', account_number)
            
            # Validate format
            if len(cleaned) == 11 and cleaned.startswith('0'):
                pass
            elif len(cleaned) == 10:
                cleaned = '0' + cleaned
            elif len(cleaned) == 13 and cleaned.startswith('234'):
                cleaned = '0' + cleaned[3:]
            else:
                raise ValidationError('Please enter a valid phone number')
            
            return cleaned
        return account_number

    def clean(self):
        cleaned_data = super().clean()
        from_account = cleaned_data.get('from_account')
        to_account_number = cleaned_data.get('to_account_number')
        amount = cleaned_data.get('amount')

        if from_account and amount:
            if amount > from_account.balance:
                raise ValidationError('Insufficient balance in source account')
            if from_account.is_frozen:
                raise ValidationError('Cannot transfer from frozen account')

        if from_account and to_account_number:
            if from_account.account_number == to_account_number:
                raise ValidationError('Cannot transfer to the same account')

        return cleaned_data


class BillPaymentForm(forms.Form):
    """Form for bill payments"""
    BILLER_CHOICES = [
        ('', 'Select Biller'),
        ('EKEDC', 'Eko Electricity Distribution Company'),
        ('IKEDC', 'Ikeja Electric'),
        ('AEDC', 'Abuja Electricity Distribution Company'),
        ('PHED', 'Port Harcourt Electricity Distribution'),
        ('KEDCO', 'Kano Electricity Distribution Company'),
        ('DSTV', 'DSTV'),
        ('GOTV', 'GOTV'),
        ('Startimes', 'Startimes'),
        ('Smile', 'Smile Communications'),
        ('Spectranet', 'Spectranet'),
    ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['account'] = forms.ModelChoiceField(
            queryset=BankAccount.objects.filter(user=user),
            widget=forms.Select(attrs={'class': 'form-control'}),
            empty_label="Select Account"
        )
        self.fields['biller_name'] = forms.ChoiceField(
            choices=self.BILLER_CHOICES,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        self.fields['bill_number'] = forms.CharField(
            max_length=50,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter meter number / customer ID'
            })
        )
        self.fields['amount'] = forms.DecimalField(
            max_digits=10,
            decimal_places=2,
            min_value=Decimal('1.00'),
            widget=forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'step': '0.01',
                'min': '1.00'
            })
        )

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        amount = cleaned_data.get('amount')

        if account and amount:
            if amount > account.balance:
                raise ValidationError('Insufficient balance in selected account')
            if account.is_frozen:
                raise ValidationError('Cannot pay bills from frozen account')

        return cleaned_data


class KYCUploadForm(forms.ModelForm):
    """Form for KYC document upload"""
    class Meta:
        model = KYC
        fields = ['id_document']
        widgets = {
            'id_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
                'required': True
            })
        }

    def clean_id_document(self):
        document = self.cleaned_data.get('id_document')
        if document:
            # Check file size (max 5MB)
            if document.size > 5 * 1024 * 1024:
                raise ValidationError('File size must be less than 5MB')
            
            # Check file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            if document.content_type not in allowed_types:
                raise ValidationError('Only PDF, JPG, JPEG, and PNG files are allowed')
        
        return document


class TransactionFilterForm(forms.Form):
    """Form for filtering transactions"""
    TRANSACTION_TYPE_CHOICES = [
        ('', 'All Types'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('funding', 'Wallet Funding'),
        ('airtime', 'Airtime Purchase'),
        ('data', 'Data Purchase'),
        ('tv', 'TV Subscription'),
        ('electricity', 'Electricity Payment'),
        ('bill_payment', 'Bill Payment'),
    ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'] = forms.ModelChoiceField(
            queryset=BankAccount.objects.filter(user=user),
            required=False,
            widget=forms.Select(attrs={'class': 'form-control'}),
            empty_label="All Accounts"
        )
        self.fields['transaction_type'] = forms.ChoiceField(
            choices=self.TRANSACTION_TYPE_CHOICES,
            required=False,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        self.fields['start_date'] = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        )
        self.fields['end_date'] = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise ValidationError('Start date cannot be after end date')

        return cleaned_data


class AirtimeForm(forms.Form):
    """Form for airtime purchase"""
    NETWORK_CHOICES = [
        ('', 'Select Network'),
        ('MTN', 'MTN'),
        ('Airtel', 'Airtel'),
        ('Glo', 'Globacom'),
        ('9mobile', '9mobile'),
    ]

    network = forms.ChoiceField(
        choices=NETWORK_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=11,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number'
        })
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('50.00'),
        max_value=Decimal('10000.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount (₦50 - ₦10,000)',
            'step': '0.01',
            'min': '50.00',
            'max': '10000.00'
        })
    )

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            cleaned = re.sub(r'\D', '', phone)
            if len(cleaned) == 11 and cleaned.startswith('0'):
                return cleaned
            elif len(cleaned) == 10:
                return '0' + cleaned
            else:
                raise ValidationError('Please enter a valid Nigerian phone number')
        return phone


class DataForm(forms.Form):
    """Form for data purchase"""
    NETWORK_CHOICES = [
        ('', 'Select Network'),
        ('MTN', 'MTN'),
        ('Airtel', 'Airtel'),
        ('Glo', 'Globacom'),
        ('9mobile', '9mobile'),
    ]

    DATA_PLAN_CHOICES = [
        ('', 'Select Data Plan'),
        ('500MB', '500MB - ₦200'),
        ('1GB', '1GB - ₦350'),
        ('2GB', '2GB - ₦700'),
        ('5GB', '5GB - ₦1,500'),
        ('10GB', '10GB - ₦3,000'),
    ]

    network = forms.ChoiceField(
        choices=NETWORK_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=11,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number'
        })
    )
    data_plan = forms.ChoiceField(
        choices=DATA_PLAN_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            cleaned = re.sub(r'\D', '', phone)
            if len(cleaned) == 11 and cleaned.startswith('0'):
                return cleaned
            elif len(cleaned) == 10:
                return '0' + cleaned
            else:
                raise ValidationError('Please enter a valid Nigerian phone number')
        return phone


class ElectricityForm(forms.Form):
    """Form for electricity bill payment"""
    DISCO_CHOICES = [
        ('', 'Select Distribution Company'),
        ('EKEDC', 'Eko Electricity Distribution Company'),
        ('IKEDC', 'Ikeja Electric'),
        ('AEDC', 'Abuja Electricity Distribution Company'),
        ('PHED', 'Port Harcourt Electricity Distribution'),
        ('KEDCO', 'Kano Electricity Distribution Company'),
        ('EEDC', 'Enugu Electricity Distribution Company'),
    ]

    disco = forms.ChoiceField(
        choices=DISCO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Distribution Company"
    )
    meter_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter meter number'
        })
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('100.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount (minimum ₦100)',
            'step': '0.01',
            'min': '100.00'
        })
    )

    def clean_meter_number(self):
        meter = self.cleaned_data.get('meter_number')
        if meter and not meter.isdigit():
            raise ValidationError('Meter number should contain only digits')
        return meter