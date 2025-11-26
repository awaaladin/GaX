"""
Moniepoint API Integration
Complete wrapper for Moniepoint payment gateway API
"""
import requests
import hashlib
import hmac
import json
import logging
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)


class MoniepointAPI:
    """Moniepoint API wrapper with production and sandbox support"""

    def __init__(self, environment='sandbox'):
        """Initialize Moniepoint API client"""
        self.environment = environment

        if environment == 'live':
            self.base_url = settings.MONIEPOINT_LIVE_BASE_URL
            self.api_key = settings.MONIEPOINT_LIVE_API_KEY
            self.secret_key = settings.MONIEPOINT_LIVE_SECRET_KEY
            self.contract_code = settings.MONIEPOINT_LIVE_CONTRACT_CODE
        else:
            self.base_url = settings.MONIEPOINT_SANDBOX_BASE_URL
            self.api_key = settings.MONIEPOINT_SANDBOX_API_KEY
            self.secret_key = settings.MONIEPOINT_SANDBOX_SECRET_KEY
            self.contract_code = settings.MONIEPOINT_SANDBOX_CONTRACT_CODE

        self.timeout = 30

    def _generate_signature(self, payload):
        """Generate HMAC signature for request authentication"""
        message = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        return signature

    def _get_headers(self, signature=None):
        """Get request headers"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }
        if signature:
            headers['Signature'] = signature
        return headers

    def _make_request(
        self,
        method,
        endpoint,
        data=None,
        sign_request=True
    ):
        """Make HTTP request to Moniepoint API"""
        url = f"{self.base_url}{endpoint}"

        signature = None
        if sign_request and data:
            signature = self._generate_signature(data)

        headers = self._get_headers(signature)

        try:
            if method.upper() == 'GET':
                response = requests.get(
                    url,
                    headers=headers,
                    params=data,
                    timeout=self.timeout
                )
            elif method.upper() == 'POST':
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            logger.info(
                f"Moniepoint API Request: {method} {url} - "
                f"Status: {response.status_code}"
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"Moniepoint API timeout: {url}")
            return {
                'status': False,
                'message': 'Request timeout',
                'error': 'TIMEOUT'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Moniepoint API error: {str(e)}")
            return {
                'status': False,
                'message': str(e),
                'error': 'REQUEST_FAILED'
            }

    def create_virtual_account(
        self,
        account_reference,
        account_name,
        customer_email,
        customer_name,
        bvn=None
    ):
        """
        Create a virtual account for a customer

        Args:
            account_reference: Unique reference for the account
            account_name: Name to appear on the account
            customer_email: Customer email address
            customer_name: Customer full name
            bvn: Bank Verification Number (optional)

        Returns:
            dict: API response with account details
        """
        endpoint = '/api/v1/disbursements/virtual-account'
        payload = {
            'accountReference': account_reference,
            'accountName': account_name,
            'currencyCode': 'NGN',
            'contractCode': self.contract_code,
            'customerEmail': customer_email,
            'customerName': customer_name,
            'getAllAvailableBanks': True
        }

        if bvn:
            payload['bvn'] = bvn

        return self._make_request('POST', endpoint, payload)

    def verify_transaction(self, transaction_reference):
        """
        Verify a transaction by reference

        Args:
            transaction_reference: Transaction reference to verify

        Returns:
            dict: Transaction status and details
        """
        endpoint = f'/api/v1/merchant/transactions/query'
        payload = {
            'transactionReference': transaction_reference
        }

        return self._make_request('POST', endpoint, payload)

    def initiate_transfer(
        self,
        amount,
        account_number,
        account_name,
        bank_code,
        narration,
        reference
    ):
        """
        Initiate a bank transfer

        Args:
            amount: Amount to transfer
            account_number: Recipient account number
            account_name: Recipient account name
            bank_code: Recipient bank code
            narration: Transfer description
            reference: Unique transaction reference

        Returns:
            dict: Transfer response
        """
        endpoint = '/api/v1/disbursements/single'
        payload = {
            'amount': float(amount),
            'reference': reference,
            'narration': narration,
            'bankCode': bank_code,
            'accountNumber': account_number,
            'accountName': account_name,
            'currency': 'NGN'
        }

        return self._make_request('POST', endpoint, payload)

    def get_account_balance(self, account_number):
        """
        Get virtual account balance

        Args:
            account_number: Virtual account number

        Returns:
            dict: Account balance details
        """
        endpoint = f'/api/v1/disbursements/wallet-balance'
        payload = {
            'accountNumber': account_number
        }

        return self._make_request('GET', endpoint, payload)

    def verify_bank_account(self, account_number, bank_code):
        """
        Verify a bank account number

        Args:
            account_number: Account number to verify
            bank_code: Bank code

        Returns:
            dict: Account name and details
        """
        endpoint = '/api/v1/disbursements/account-lookup'
        payload = {
            'accountNumber': account_number,
            'bankCode': bank_code
        }

        return self._make_request('POST', endpoint, payload)

    def get_banks(self):
        """
        Get list of all supported banks

        Returns:
            dict: List of banks with codes
        """
        endpoint = '/api/v1/disbursements/banks'
        return self._make_request('GET', endpoint)

    def requery_transaction(self, transaction_reference):
        """
        Requery a failed or pending transaction

        Args:
            transaction_reference: Transaction reference

        Returns:
            dict: Updated transaction status
        """
        return self.verify_transaction(transaction_reference)

    def verify_webhook_signature(self, payload, signature):
        """
        Verify webhook signature

        Args:
            payload: Webhook payload
            signature: Signature from webhook headers

        Returns:
            bool: True if signature is valid
        """
        try:
            expected_signature = self._generate_signature(payload)
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False

    def get_transaction_history(
        self,
        start_date=None,
        end_date=None,
        page=1,
        size=50
    ):
        """
        Get transaction history

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            page: Page number
            size: Records per page

        Returns:
            dict: Transaction history
        """
        endpoint = '/api/v1/merchant/transactions'
        payload = {
            'page': page,
            'size': size
        }

        if start_date:
            payload['startDate'] = start_date
        if end_date:
            payload['endDate'] = end_date

        return self._make_request('GET', endpoint, payload)

    def initiate_bulk_transfer(self, transfers):
        """
        Initiate bulk transfers

        Args:
            transfers: List of transfer dictionaries

        Returns:
            dict: Bulk transfer response
        """
        endpoint = '/api/v1/disbursements/bulk'
        payload = {
            'batchReference': f"BATCH-{datetime.now().timestamp()}",
            'transfers': transfers
        }

        return self._make_request('POST', endpoint, payload)

    def reserve_account(
        self,
        account_reference,
        account_name,
        customer_email
    ):
        """
        Reserve a dedicated virtual account

        Args:
            account_reference: Unique reference
            account_name: Account name
            customer_email: Customer email

        Returns:
            dict: Reserved account details
        """
        endpoint = '/api/v1/disbursements/reserve-account'
        payload = {
            'accountReference': account_reference,
            'accountName': account_name,
            'currencyCode': 'NGN',
            'contractCode': self.contract_code,
            'customerEmail': customer_email,
        }

        return self._make_request('POST', endpoint, payload)


class MoniepointEncryption:
    """Handle encryption for sensitive Moniepoint data"""

    def __init__(self):
        """Initialize encryption"""
        self.key = self._get_encryption_key()
        self.cipher = Fernet(self.key)

    def _get_encryption_key(self):
        """Generate or retrieve encryption key"""
        password = settings.SECRET_KEY.encode()
        salt = b'moniepoint_salt_v1'  # Should be stored securely

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def encrypt(self, data):
        """Encrypt sensitive data"""
        try:
            if isinstance(data, str):
                data = data.encode()
            encrypted = self.cipher.encrypt(data)
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise

    def decrypt(self, encrypted_data):
        """Decrypt sensitive data"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
