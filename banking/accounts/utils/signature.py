"""
Signature verification utilities
Handle webhook signatures and API authentication
"""
import hashlib
import hmac
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class SignatureVerifier:
    """Verify signatures for webhooks and API requests"""

    @staticmethod
    def verify_moniepoint_signature(payload, signature, secret_key=None):
        """
        Verify Moniepoint webhook signature

        Args:
            payload: Webhook payload (dict or str)
            signature: Signature from webhook headers
            secret_key: Secret key (optional, uses settings if not provided)

        Returns:
            bool: True if signature is valid
        """
        try:
            if secret_key is None:
                secret_key = settings.MONIEPOINT_SANDBOX_SECRET_KEY

            # Convert payload to JSON string if dict
            if isinstance(payload, dict):
                message = json.dumps(payload, separators=(',', ':'))
            else:
                message = payload

            # Generate expected signature
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()

            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, signature)

            if not is_valid:
                logger.warning("Moniepoint signature verification failed")

            return is_valid

        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

    @staticmethod
    def verify_api_key_signature(payload, signature, api_secret):
        """
        Verify API key signature for merchant requests

        Args:
            payload: Request payload
            signature: Provided signature
            api_secret: Merchant API secret

        Returns:
            bool: True if signature is valid
        """
        try:
            if isinstance(payload, dict):
                message = json.dumps(payload, separators=(',', ':'))
            else:
                message = payload

            expected_signature = hmac.new(
                api_secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"API signature verification error: {e}")
            return False

    @staticmethod
    def generate_signature(payload, secret_key, algorithm='sha256'):
        """
        Generate signature for outgoing requests

        Args:
            payload: Request payload
            secret_key: Secret key
            algorithm: Hash algorithm (sha256, sha512)

        Returns:
            str: Generated signature
        """
        try:
            if isinstance(payload, dict):
                message = json.dumps(payload, separators=(',', ':'))
            else:
                message = payload

            hash_func = getattr(hashlib, algorithm)

            signature = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hash_func
            ).hexdigest()

            return signature

        except Exception as e:
            logger.error(f"Signature generation error: {e}")
            raise

    @staticmethod
    def verify_paystack_signature(payload, signature):
        """
        Verify Paystack webhook signature (for future integration)

        Args:
            payload: Webhook payload
            signature: Signature from webhook headers

        Returns:
            bool: True if signature is valid
        """
        try:
            secret_key = getattr(
                settings,
                'PAYSTACK_SECRET_KEY',
                ''
            )

            if isinstance(payload, dict):
                message = json.dumps(payload)
            else:
                message = payload

            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"Paystack signature verification error: {e}")
            return False

    @staticmethod
    def hash_transaction_pin(pin):
        """
        Hash transaction PIN

        Args:
            pin: Plain text PIN

        Returns:
            str: Hashed PIN
        """
        from django.contrib.auth.hashers import make_password
        return make_password(pin)

    @staticmethod
    def verify_transaction_pin(pin, hashed_pin):
        """
        Verify transaction PIN

        Args:
            pin: Plain text PIN
            hashed_pin: Hashed PIN from database

        Returns:
            bool: True if PIN matches
        """
        from django.contrib.auth.hashers import check_password
        return check_password(pin, hashed_pin)
