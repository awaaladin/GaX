"""
Premium Activation Service for GAX
Handles seller premium activation payments
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from accounts.models import User, Transaction as TransactionModel
import uuid
import logging

logger = logging.getLogger(__name__)


class PremiumService:
    """
    Service for handling premium activation
    This is a ONE-TIME payment to become a seller
    """
    
    def __init__(self):
        self.premium_fee = Decimal('5000.00')  # From settings
    
    @transaction.atomic
    def activate_premium(self, user_id):
        """
        Activate seller premium for a user
        
        Process:
        1. Validate user exists and doesn't have premium
        2. Check wallet balance
        3. Deduct premium fee from wallet
        4. Update user profile (is_seller_premium=True)
        5. Create transaction record
        6. Sync to blockchain (via webhook/signal)
        
        Returns:
            {
                'success': bool,
                'transaction_id': uuid,
                'reference': str,
                'message': str
            }
        """
        try:
            # Get user and wallet
            user = User.objects.select_for_update().get(id=user_id)
            wallet = user.wallet
            
            # Check if already has premium
            if user.user_type == 'merchant' or getattr(user, 'is_seller_premium', False):
                return {
                    'success': False,
                    'message': 'User already has seller premium'
                }
            
            # Check balance
            if wallet.balance < self.premium_fee:
                return {
                    'success': False,
                    'message': f'Insufficient balance. Required: ₦{self.premium_fee}, Available: ₦{wallet.balance}'
                }
            
            # Deduct from wallet
            wallet.balance -= self.premium_fee
            wallet.save(update_fields=['balance'])
            
            # Update user type
            user.user_type = 'merchant'  # Seller premium
            user.save(update_fields=['user_type'])
            
            # Create transaction record
            tx_reference = f'PREM-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}'
            tx = TransactionModel.objects.create(
                user=user,
                transaction_type='premium_activation',
                amount=self.premium_fee,
                currency='NGN',
                status='completed',
                reference=tx_reference,
                description='Seller Premium Activation (One-time fee)',
                metadata={
                    'user_id': str(user_id),
                    'premium_type': 'seller',
                    'fee': str(self.premium_fee)
                }
            )
            
            logger.info(f'Premium activated for user {user_id}, tx: {tx.id}')
            
            return {
                'success': True,
                'transaction_id': str(tx.id),
                'reference': tx_reference,
                'message': 'Seller Premium activated successfully'
            }
            
        except User.DoesNotExist:
            logger.error(f'User {user_id} not found')
            return {
                'success': False,
                'message': 'User not found'
            }
        except Exception as e:
            logger.error(f'Premium activation error: {str(e)}')
            return {
                'success': False,
                'message': 'Premium activation failed'
            }
    
    def check_premium_status(self, user_id):
        """
        Check if user has active seller premium
        """
        try:
            user = User.objects.get(id=user_id)
            has_premium = user.user_type == 'merchant'
            
            # Get premium activation transaction
            premium_tx = None
            if has_premium:
                premium_tx = TransactionModel.objects.filter(
                    user=user,
                    transaction_type='premium_activation',
                    status='completed'
                ).first()
            
            return {
                'user_id': str(user_id),
                'is_seller_premium': has_premium,
                'can_sell': has_premium,
                'premium_activated_at': premium_tx.created_at if premium_tx else None,
                'premium_fee': str(self.premium_fee)
            }
        except User.DoesNotExist:
            return {
                'user_id': str(user_id),
                'is_seller_premium': False,
                'can_sell': False
            }


# Singleton instance
premium_service = PremiumService()
