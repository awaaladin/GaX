"""
Paystack Payment API Integration for GAX Banking
Handles virtual accounts, transfers, verifications, and webhooks
"""

import requests
import hashlib
import hmac
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)


class PaystackAPI:
    """
    Wrapper for Paystack Payment API
    Supports: Virtual Accounts, Transfers, Verification, Webhooks
    """

    def __init__(self):
        """Initialize Paystack API with live credentials"""
        self.base_url = settings.PAYSTACK_BASE_URL
        self.secret_key = settings.PAYSTACK_LIVE_SECRET_KEY
        self.public_key = settings.PAYSTACK_LIVE_PUBLIC_KEY

        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Paystack API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/transaction/initialize')
            data: Request payload

        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=data, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            result = response.json()

            logger.info(f"Paystack API {method} {endpoint}: {result.get('status')}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Paystack API error on {method} {endpoint}: {str(e)}")
            return {
                'status': False,
                'message': f'API request failed: {str(e)}'
            }

    # ==================== VIRTUAL ACCOUNTS ====================

    def create_dedicated_account(
        self,
        customer_email: str,
        customer_name: str,
        customer_phone: str,
        preferred_bank: str = 'wema-bank'
    ) -> Dict[str, Any]:
        """
        Create a dedicated virtual account for a customer

        Args:
            customer_email: Customer's email address
            customer_name: Customer's full name
            customer_phone: Customer's phone number
            preferred_bank: Bank slug (wema-bank, titan-paystack)

        Returns:
            {
                'status': True/False,
                'data': {
                    'account_name': 'Customer Name',
                    'account_number': '1234567890',
                    'bank': {
                        'name': 'Wema Bank',
                        'slug': 'wema-bank'
                    }
                }
            }
        """
        payload = {
            'email': customer_email,
            'first_name': customer_name.split()[0],
            'last_name': ' '.join(customer_name.split()[1:]) if len(customer_name.split()) > 1 else customer_name.split()[0],
            'phone': customer_phone,
            'preferred_bank': preferred_bank,
        }

        return self._make_request('POST', '/dedicated_account', payload)

    def list_dedicated_accounts(self, customer_email: str) -> Dict[str, Any]:
        """
        Get all dedicated accounts for a customer

        Args:
            customer_email: Customer's email

        Returns:
            List of dedicated accounts
        """
        params = {'email': customer_email}
        return self._make_request('GET', '/dedicated_account', params)

    # ==================== TRANSFERS ====================

    def initiate_transfer(
        self,
        amount: Decimal,
        recipient_code: str,
        reason: str = 'Payment',
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate a transfer to a recipient

        Args:
            amount: Transfer amount in Naira (will be converted to kobo)
            recipient_code: Paystack recipient code
            reason: Transfer description
            reference: Unique transaction reference

        Returns:
            Transfer initiation response
        """
        # Convert Naira to kobo (Paystack uses kobo)
        amount_in_kobo = int(amount * 100)

        payload = {
            'source': 'balance',
            'amount': amount_in_kobo,
            'recipient': recipient_code,
            'reason': reason,
        }

        if reference:
            payload['reference'] = reference

        return self._make_request('POST', '/transfer', payload)

    def create_transfer_recipient(
        self,
        account_number: str,
        bank_code: str,
        account_name: str
    ) -> Dict[str, Any]:
        """
        Create a transfer recipient

        Args:
            account_number: Recipient's account number
            bank_code: Bank code (e.g., '058' for GTBank)
            account_name: Account holder's name

        Returns:
            {
                'status': True/False,
                'data': {
                    'recipient_code': 'RCP_xxxxx',
                    'type': 'nuban'
                }
            }
        """
        payload = {
            'type': 'nuban',
            'name': account_name,
            'account_number': account_number,
            'bank_code': bank_code,
            'currency': 'NGN',
        }

        return self._make_request('POST', '/transferrecipient', payload)

    def verify_account_number(
        self,
        account_number: str,
        bank_code: str
    ) -> Dict[str, Any]:
        """
        Verify account number and get account name

        Args:
            account_number: Account number to verify
            bank_code: Bank code

        Returns:
            {
                'status': True/False,
                'data': {
                    'account_number': '1234567890',
                    'account_name': 'JOHN DOE'
                }
            }
        """
        params = {
            'account_number': account_number,
            'bank_code': bank_code,
        }

        return self._make_request('GET', '/bank/resolve', params)

    def list_banks(self) -> Dict[str, Any]:
        """
        Get list of Nigerian banks

        Returns:
            List of banks with codes
        """
        params = {
            'country': 'nigeria',
            'currency': 'NGN',
        }
        return self._make_request('GET', '/bank', params)

    # ==================== TRANSACTIONS ====================

    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Verify a transaction by reference

        Args:
            reference: Transaction reference

        Returns:
            Transaction details
        """
        return self._make_request('GET', f'/transaction/verify/{reference}')

    def initialize_transaction(
        self,
        email: str,
        amount: Decimal,
        callback_url: Optional[str] = None,
        reference: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Initialize a payment transaction

        Args:
            email: Customer's email
            amount: Amount in Naira (will be converted to kobo)
            callback_url: URL to redirect after payment
            reference: Unique transaction reference
            metadata: Additional transaction data

        Returns:
            {
                'status': True/False,
                'data': {
                    'authorization_url': 'https://checkout.paystack.com/...',
                    'access_code': 'xxxxx',
                    'reference': 'xxxxx'
                }
            }
        """
        amount_in_kobo = int(amount * 100)

        payload = {
            'email': email,
            'amount': amount_in_kobo,
        }

        if callback_url:
            payload['callback_url'] = callback_url
        if reference:
            payload['reference'] = reference
        if metadata:
            payload['metadata'] = metadata

        return self._make_request('POST', '/transaction/initialize', payload)

    # ==================== WEBHOOKS ====================

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Verify Paystack webhook signature

        Args:
            payload: Raw request body (bytes)
            signature: X-Paystack-Signature header value

        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    # ==================== BALANCE ====================

    def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance

        Returns:
            {
                'status': True/False,
                'data': [
                    {
                        'currency': 'NGN',
                        'balance': 1234567 (in kobo)
                    }
                ]
            }
        """
        return self._make_request('GET', '/balance')


# Convenience function
def get_paystack_client() -> PaystackAPI:
    """Get initialized Paystack API client"""
    return PaystackAPI()
