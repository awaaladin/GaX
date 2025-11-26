"""
Bill Payment Services
Airtime, Data, TV, and Electricity payment integrations
"""
import logging
import requests
from decimal import Decimal
from django.conf import settings
from django.db import transaction as db_transaction
from ..models import BillPayment, Transaction
from .payment import PaymentProcessor

logger = logging.getLogger(__name__)


class BillPaymentService:
    """Base class for bill payment services"""

    def __init__(self):
        """Initialize bill payment service"""
        # You would configure actual API credentials here
        self.api_url = getattr(
            settings,
            'BILL_PAYMENT_API_URL',
            'https://api.example.com'
        )
        self.api_key = getattr(settings, 'BILL_PAYMENT_API_KEY', '')

    def _make_request(self, endpoint, data):
        """Make API request to bill payment provider"""
        url = f"{self.api_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        try:
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Bill payment API error: {e}")
            return {
                'status': False,
                'message': str(e)
            }


class AirtimeService(BillPaymentService):
    """Airtime purchase service"""

    PROVIDER_CODES = {
        'mtn': 'MTN',
        'glo': 'GLO',
        'airtel': 'AIRTEL',
        '9mobile': '9MOBILE'
    }

    @db_transaction.atomic
    def purchase_airtime(self, user, wallet, provider, phone_number,
                         amount, transaction_pin):
        """
        Purchase airtime

        Args:
            user: User making purchase
            wallet: User's wallet
            provider: Network provider
            phone_number: Phone number to recharge
            amount: Airtime amount
            transaction_pin: Transaction PIN

        Returns:
            dict: Purchase result
        """
        try:
            # Verify transaction PIN
            if not PaymentProcessor.verify_transaction_pin(
                user,
                transaction_pin
            ):
                raise ValueError("Invalid transaction PIN")

            # Validate amount
            if amount < Decimal('50.00') or amount > Decimal('10000.00'):
                raise ValueError(
                    "Amount must be between ₦50 and ₦10,000"
                )

            # Debit wallet
            debit_txn = PaymentProcessor.debit_wallet(
                wallet=wallet,
                amount=amount,
                fee=Decimal('0.00'),
                description=f"Airtime purchase - {provider.upper()}",
                transaction_type='airtime',
                metadata={
                    'provider': provider,
                    'phone_number': phone_number
                }
            )

            # Call external API
            api_response = self._make_request('/airtime/purchase', {
                'provider': self.PROVIDER_CODES.get(provider, provider),
                'phone_number': phone_number,
                'amount': float(amount),
                'reference': debit_txn.reference
            })

            # Create bill payment record
            bill_payment = BillPayment.objects.create(
                user=user,
                transaction=debit_txn,
                bill_type='airtime',
                provider=provider,
                amount=amount,
                phone_number=phone_number,
                status='completed' if api_response.get('status') else 'failed',
                response_data=api_response
            )

            # Update transaction if failed
            if not api_response.get('status'):
                debit_txn.status = 'failed'
                debit_txn.save()

                # Reverse transaction
                PaymentProcessor.reverse_transaction(
                    debit_txn,
                    'Airtime purchase failed'
                )

                raise ValueError(
                    api_response.get('message', 'Airtime purchase failed')
                )

            logger.info(
                f"Airtime purchase: {phone_number} - "
                f"{provider} - ₦{amount}"
            )

            return {
                'success': True,
                'transaction': debit_txn,
                'bill_payment': bill_payment,
                'message': 'Airtime purchase successful'
            }

        except Exception as e:
            logger.error(f"Airtime purchase error: {e}")
            raise


class DataService(BillPaymentService):
    """Data bundle purchase service"""

    # Example data plans (replace with actual plans from API)
    DATA_PLANS = {
        'mtn': {
            'MTN-1GB-30': {'name': '1GB - 30 Days', 'amount': Decimal('500')},
            'MTN-2GB-30': {'name': '2GB - 30 Days', 'amount': Decimal('1000')},
            'MTN-5GB-30': {'name': '5GB - 30 Days', 'amount': Decimal('2000')},
        },
        'glo': {
            'GLO-1GB-30': {'name': '1GB - 30 Days', 'amount': Decimal('500')},
            'GLO-2GB-30': {'name': '2GB - 30 Days', 'amount': Decimal('1000')},
        },
        'airtel': {
            'AIRTEL-1GB-30': {'name': '1GB - 30 Days', 'amount': Decimal('500')},
        },
        '9mobile': {
            '9MOB-1GB-30': {'name': '1GB - 30 Days', 'amount': Decimal('500')},
        }
    }

    @db_transaction.atomic
    def purchase_data(self, user, wallet, provider, phone_number,
                      plan_code, transaction_pin):
        """
        Purchase data bundle

        Args:
            user: User making purchase
            wallet: User's wallet
            provider: Network provider
            phone_number: Phone number
            plan_code: Data plan code
            transaction_pin: Transaction PIN

        Returns:
            dict: Purchase result
        """
        try:
            # Verify PIN
            if not PaymentProcessor.verify_transaction_pin(
                user,
                transaction_pin
            ):
                raise ValueError("Invalid transaction PIN")

            # Get plan details
            plans = self.DATA_PLANS.get(provider, {})
            plan = plans.get(plan_code)

            if not plan:
                raise ValueError("Invalid data plan")

            amount = plan['amount']

            # Debit wallet
            debit_txn = PaymentProcessor.debit_wallet(
                wallet=wallet,
                amount=amount,
                fee=Decimal('0.00'),
                description=f"Data purchase - {plan['name']}",
                transaction_type='data',
                metadata={
                    'provider': provider,
                    'phone_number': phone_number,
                    'plan_code': plan_code,
                    'plan_name': plan['name']
                }
            )

            # Call external API
            api_response = self._make_request('/data/purchase', {
                'provider': provider,
                'phone_number': phone_number,
                'plan_code': plan_code,
                'reference': debit_txn.reference
            })

            # Create bill payment record
            bill_payment = BillPayment.objects.create(
                user=user,
                transaction=debit_txn,
                bill_type='data',
                provider=provider,
                amount=amount,
                phone_number=phone_number,
                status='completed' if api_response.get('status') else 'failed',
                response_data=api_response
            )

            if not api_response.get('status'):
                debit_txn.status = 'failed'
                debit_txn.save()

                PaymentProcessor.reverse_transaction(
                    debit_txn,
                    'Data purchase failed'
                )

                raise ValueError(
                    api_response.get('message', 'Data purchase failed')
                )

            logger.info(
                f"Data purchase: {phone_number} - "
                f"{plan['name']} - ₦{amount}"
            )

            return {
                'success': True,
                'transaction': debit_txn,
                'bill_payment': bill_payment,
                'message': 'Data purchase successful'
            }

        except Exception as e:
            logger.error(f"Data purchase error: {e}")
            raise


class TVService(BillPaymentService):
    """TV subscription service (DSTV, GOtv, Startimes)"""

    TV_PLANS = {
        'dstv': {
            'DSTV-COMPACT': {'name': 'Compact', 'amount': Decimal('10500')},
            'DSTV-PREMIUM': {'name': 'Premium', 'amount': Decimal('24500')},
        },
        'gotv': {
            'GOTV-MAX': {'name': 'Max', 'amount': Decimal('4850')},
            'GOTV-JOLLI': {'name': 'Jolli', 'amount': Decimal('3300')},
        },
        'startimes': {
            'STAR-CLASSIC': {'name': 'Classic', 'amount': Decimal('2600')},
        }
    }

    def validate_smartcard(self, provider, smartcard_number):
        """Validate smartcard number and get customer name"""
        api_response = self._make_request('/tv/validate', {
            'provider': provider,
            'smartcard_number': smartcard_number
        })

        return api_response

    @db_transaction.atomic
    def purchase_subscription(self, user, wallet, provider,
                              smartcard_number, plan_code,
                              transaction_pin):
        """
        Purchase TV subscription

        Args:
            user: User making purchase
            wallet: User's wallet
            provider: TV provider
            smartcard_number: Smartcard number
            plan_code: Subscription plan code
            transaction_pin: Transaction PIN

        Returns:
            dict: Purchase result
        """
        try:
            # Verify PIN
            if not PaymentProcessor.verify_transaction_pin(
                user,
                transaction_pin
            ):
                raise ValueError("Invalid transaction PIN")

            # Validate smartcard
            validation = self.validate_smartcard(provider, smartcard_number)
            if not validation.get('status'):
                raise ValueError("Invalid smartcard number")

            customer_name = validation.get('customer_name', 'N/A')

            # Get plan details
            plans = self.TV_PLANS.get(provider, {})
            plan = plans.get(plan_code)

            if not plan:
                raise ValueError("Invalid subscription plan")

            amount = plan['amount']

            # Debit wallet
            debit_txn = PaymentProcessor.debit_wallet(
                wallet=wallet,
                amount=amount,
                fee=Decimal('100.00'),  # Service fee
                description=f"TV Subscription - {provider.upper()}",
                transaction_type='tv',
                metadata={
                    'provider': provider,
                    'smartcard_number': smartcard_number,
                    'plan_code': plan_code,
                    'plan_name': plan['name'],
                    'customer_name': customer_name
                }
            )

            # Call external API
            api_response = self._make_request('/tv/subscribe', {
                'provider': provider,
                'smartcard_number': smartcard_number,
                'plan_code': plan_code,
                'reference': debit_txn.reference
            })

            # Create bill payment record
            bill_payment = BillPayment.objects.create(
                user=user,
                transaction=debit_txn,
                bill_type='tv',
                provider=provider,
                amount=amount,
                smartcard_number=smartcard_number,
                customer_name=customer_name,
                status='completed' if api_response.get('status') else 'failed',
                response_data=api_response
            )

            if not api_response.get('status'):
                debit_txn.status = 'failed'
                debit_txn.save()

                PaymentProcessor.reverse_transaction(
                    debit_txn,
                    'TV subscription failed'
                )

                raise ValueError(
                    api_response.get('message', 'Subscription failed')
                )

            logger.info(
                f"TV subscription: {smartcard_number} - "
                f"{provider} - ₦{amount}"
            )

            return {
                'success': True,
                'transaction': debit_txn,
                'bill_payment': bill_payment,
                'message': 'Subscription successful'
            }

        except Exception as e:
            logger.error(f"TV subscription error: {e}")
            raise


class ElectricityService(BillPaymentService):
    """Electricity payment service"""

    PROVIDERS = {
        'phed': 'Port Harcourt Electricity Distribution',
        'ikedc': 'Ikeja Electric',
        'aedc': 'Abuja Electricity Distribution',
        'eedc': 'Enugu Electricity Distribution',
        'ekedc': 'Eko Electricity Distribution'
    }

    def validate_meter(self, provider, meter_number, meter_type):
        """Validate meter number and get customer details"""
        api_response = self._make_request('/electricity/validate', {
            'provider': provider,
            'meter_number': meter_number,
            'meter_type': meter_type
        })

        return api_response

    @db_transaction.atomic
    def purchase_electricity(self, user, wallet, provider, meter_number,
                             meter_type, amount, transaction_pin):
        """
        Purchase electricity

        Args:
            user: User making purchase
            wallet: User's wallet
            provider: Electricity provider
            meter_number: Meter number
            meter_type: prepaid or postpaid
            amount: Amount to pay
            transaction_pin: Transaction PIN

        Returns:
            dict: Purchase result with token
        """
        try:
            # Verify PIN
            if not PaymentProcessor.verify_transaction_pin(
                user,
                transaction_pin
            ):
                raise ValueError("Invalid transaction PIN")

            # Validate meter
            validation = self.validate_meter(
                provider,
                meter_number,
                meter_type
            )
            if not validation.get('status'):
                raise ValueError("Invalid meter number")

            customer_name = validation.get('customer_name', 'N/A')

            # Validate amount
            if amount < Decimal('500.00'):
                raise ValueError("Minimum amount is ₦500")

            # Debit wallet
            service_fee = Decimal('100.00')
            debit_txn = PaymentProcessor.debit_wallet(
                wallet=wallet,
                amount=amount,
                fee=service_fee,
                description=f"Electricity - {provider.upper()}",
                transaction_type='electricity',
                metadata={
                    'provider': provider,
                    'meter_number': meter_number,
                    'meter_type': meter_type,
                    'customer_name': customer_name
                }
            )

            # Call external API
            api_response = self._make_request('/electricity/vend', {
                'provider': provider,
                'meter_number': meter_number,
                'meter_type': meter_type,
                'amount': float(amount),
                'reference': debit_txn.reference
            })

            token = api_response.get('token', '')

            # Create bill payment record
            bill_payment = BillPayment.objects.create(
                user=user,
                transaction=debit_txn,
                bill_type='electricity',
                provider=provider,
                amount=amount,
                meter_number=meter_number,
                customer_name=customer_name,
                token=token,
                status='completed' if api_response.get('status') else 'failed',
                response_data=api_response
            )

            if not api_response.get('status'):
                debit_txn.status = 'failed'
                debit_txn.save()

                PaymentProcessor.reverse_transaction(
                    debit_txn,
                    'Electricity payment failed'
                )

                raise ValueError(
                    api_response.get('message', 'Payment failed')
                )

            logger.info(
                f"Electricity payment: {meter_number} - "
                f"{provider} - ₦{amount}"
            )

            return {
                'success': True,
                'transaction': debit_txn,
                'bill_payment': bill_payment,
                'token': token,
                'message': 'Payment successful'
            }

        except Exception as e:
            logger.error(f"Electricity payment error: {e}")
            raise
