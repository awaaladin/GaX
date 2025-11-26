"""
Purchase Service for GAX
Handles product purchases with escrow integration
"""

from django.db import transaction
from django.conf import settings
from decimal import Decimal
from accounts.models import User, Wallet, Transaction as TransactionModel
import uuid
import logging
import requests

logger = logging.getLogger(__name__)


class PurchaseService:
    """
    Service for handling product purchases
    Integrates with TRINITY escrow system
    """
    
    def __init__(self):
        self.trinity_url = settings.TRINITY_API_URL
        self.service_key = settings.SHARED_SERVICE_SECRET
    
    def _create_escrow(self, buyer_id, seller_id, amount, product_id, tx_ref):
        """
        Create escrow in TRINITY system
        """
        try:
            response = requests.post(
                f"{self.trinity_url}/api/escrow/create/",
                json={
                    'buyer_id': str(buyer_id),
                    'seller_id': str(seller_id),
                    'amount': str(amount),
                    'product_id': str(product_id),
                    'transaction_ref': tx_ref,
                    'auto_release_hours': settings.DEFAULT_ESCROW_AUTO_RELEASE_HOURS
                },
                headers={
                    'X-Service-Key': self.service_key,
                    'Content-Type': 'application/json'
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f'Escrow creation failed: {str(e)}')
            return None
    
    @transaction.atomic
    def process_purchase(self, buyer_id, seller_id, product_id, amount, use_escrow=True):
        """
        Process a product purchase
        
        Flow:
        1. Validate buyer and seller exist
        2. Check buyer has sufficient balance
        3. Deduct from buyer wallet (atomic)
        4. If use_escrow: Create escrow in TRINITY
        5. If not use_escrow: Credit seller immediately
        6. Create transaction record
        7. Sync to blockchain
        
        Args:
            buyer_id: UUID of buyer
            seller_id: UUID of seller
            product_id: UUID of product
            amount: Decimal amount
            use_escrow: Whether to use escrow (default: True)
        
        Returns:
            {
                'success': bool,
                'transaction_id': uuid,
                'reference': str,
                'escrow_id': uuid (if use_escrow),
                'status': 'completed|escrowed',
                'buyer_balance': Decimal
            }
        """
        try:
            # Get users and wallets with row-level lock
            buyer = User.objects.select_related('wallet').select_for_update().get(id=buyer_id)
            seller = User.objects.select_related('wallet').select_for_update().get(id=seller_id)
            
            buyer_wallet = buyer.wallet
            seller_wallet = seller.wallet
            
            amount = Decimal(str(amount))
            
            # Validate
            if buyer_id == seller_id:
                return {
                    'success': False,
                    'message': 'Cannot purchase from yourself'
                }
            
            if buyer_wallet.balance < amount:
                return {
                    'success': False,
                    'message': f'Insufficient balance. Required: ₦{amount}, Available: ₦{buyer_wallet.balance}'
                }
            
            # Generate transaction reference
            tx_ref = f'TXN-{timezone.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}'
            
            # Deduct from buyer wallet
            buyer_wallet.balance -= amount
            buyer_wallet.save(update_fields=['balance'])
            
            escrow_id = None
            status = 'completed'
            
            if use_escrow:
                # Create escrow
                escrow_result = self._create_escrow(
                    buyer_id, seller_id, amount, product_id, tx_ref
                )
                
                if escrow_result and escrow_result.get('success'):
                    escrow_id = escrow_result.get('escrow_id')
                    status = 'escrowed'
                else:
                    # Escrow creation failed, refund buyer
                    buyer_wallet.balance += amount
                    buyer_wallet.save(update_fields=['balance'])
                    return {
                        'success': False,
                        'message': 'Failed to create escrow. Payment refunded.'
                    }
            else:
                # Direct payment to seller
                seller_wallet.balance += amount
                seller_wallet.save(update_fields=['balance'])
            
            # Create transaction record
            tx = TransactionModel.objects.create(
                user=buyer,
                transaction_type='purchase',
                amount=amount,
                currency='NGN',
                status=status,
                reference=tx_ref,
                recipient=seller,
                description=f'Purchase of product {product_id}',
                metadata={
                    'buyer_id': str(buyer_id),
                    'seller_id': str(seller_id),
                    'product_id': str(product_id),
                    'escrow_id': str(escrow_id) if escrow_id else None,
                    'use_escrow': use_escrow
                }
            )
            
            logger.info(
                f'Purchase processed: buyer={buyer_id}, seller={seller_id}, '
                f'amount={amount}, escrow={use_escrow}, tx={tx.id}'
            )
            
            return {
                'success': True,
                'transaction_id': str(tx.id),
                'reference': tx_ref,
                'escrow_id': str(escrow_id) if escrow_id else None,
                'status': status,
                'buyer_balance': str(buyer_wallet.balance)
            }
            
        except User.DoesNotExist:
            logger.error(f'User not found: buyer={buyer_id} or seller={seller_id}')
            return {
                'success': False,
                'message': 'User not found'
            }
        except Exception as e:
            logger.error(f'Purchase error: {str(e)}')
            return {
                'success': False,
                'message': 'Purchase failed'
            }
    
    @transaction.atomic
    def release_escrow_funds(self, seller_id, amount, escrow_id, transaction_ref):
        """
        Release funds to seller when escrow is released
        Called by webhook from TRINITY
        """
        try:
            seller = User.objects.select_related('wallet').select_for_update().get(id=seller_id)
            seller_wallet = seller.wallet
            
            amount = Decimal(str(amount))
            
            # Credit seller wallet
            seller_wallet.balance += amount
            seller_wallet.save(update_fields=['balance'])
            
            # Update transaction status
            tx = TransactionModel.objects.get(reference=transaction_ref)
            tx.status = 'completed'
            tx.metadata['escrow_released'] = True
            tx.save(update_fields=['status', 'metadata'])
            
            logger.info(f'Escrow released: seller={seller_id}, amount={amount}, escrow={escrow_id}')
            
            return {
                'success': True,
                'message': 'Funds released to seller'
            }
        except Exception as e:
            logger.error(f'Escrow release error: {str(e)}')
            return {
                'success': False,
                'message': 'Failed to release funds'
            }


# Singleton instance
purchase_service = PurchaseService()
