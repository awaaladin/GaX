"""
Django signals for automatic wallet and transaction operations
Integrated with Paystack for virtual account creation
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction as db_transaction
from .models import User, Wallet, Profile, Transaction
from .utils.paystack import get_paystack_client
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_wallet_and_profile(sender, instance, created, **kwargs):
    """
    Automatically create wallet, profile, and Paystack virtual account when user is created
    """
    if created:
        try:
            with db_transaction.atomic():
                # Create wallet
                if not hasattr(instance, 'wallet'):
                    wallet = Wallet.objects.create(user=instance)
                    logger.info(f"Wallet created for user: {instance.username}")
                    
                    # Create Paystack virtual account
                    try:
                        paystack = get_paystack_client()
                        result = paystack.create_dedicated_account(
                            customer_email=instance.email,
                            customer_name=instance.get_full_name(),
                            customer_phone=instance.phone_number or '+2348000000000',
                            preferred_bank='wema-bank'
                        )
                        
                        if result.get('status'):
                            data = result.get('data', {})
                            # Update wallet with Paystack virtual account details
                            wallet.metadata = {
                                'paystack_customer': data.get('customer', {}),
                                'paystack_account': {
                                    'account_name': data.get('account_name'),
                                    'account_number': data.get('account_number'),
                                    'bank_name': data.get('bank', {}).get('name'),
                                    'bank_slug': data.get('bank', {}).get('slug'),
                                }
                            }
                            wallet.save(update_fields=['metadata'])
                            logger.info(
                                f"Paystack virtual account created: "
                                f"{data.get('account_number')} for {instance.username}"
                            )
                        else:
                            logger.warning(
                                f"Paystack virtual account creation failed for {instance.username}: "
                                f"{result.get('message')}"
                            )
                    except Exception as e:
                        logger.error(f"Error creating Paystack virtual account: {e}")

                # Create profile
                if not hasattr(instance, 'profile'):
                    Profile.objects.create(
                        user=instance,
                        name=f"{instance.first_name} {instance.last_name}",
                        phone_number=instance.phone_number
                    )
                    logger.info(f"Profile created for user: {instance.username}")

        except Exception as e:
            logger.error(f"Error creating wallet/profile for user {instance.username}: {e}")


@receiver(post_save, sender=Transaction)
def log_transaction(sender, instance, created, **kwargs):
    """
    Log transaction after creation
    """
    if created:
        logger.info(
            f"Transaction created: {instance.reference} - "
            f"{instance.transaction_type} - ₦{instance.amount} - "
            f"{instance.status}"
        )


@receiver(post_save, sender=Transaction)
def handle_transaction_approval(sender, instance, **kwargs):
    """
    Handle transaction when approved
    """
    if instance.requires_approval and instance.approved_by and not instance.completed_at:
        try:
            # Update transaction status
            if instance.status == 'pending':
                instance.status = 'processing'
                instance.save(update_fields=['status'])

                logger.info(
                    f"Transaction approved: {instance.reference} by "
                    f"{instance.approved_by.username}"
                )

        except Exception as e:
            logger.error(f"Error handling transaction approval: {e}")