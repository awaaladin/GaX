"""
Django signals for automatic wallet and transaction operations
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction as db_transaction
from .models import User, Wallet, Profile, Transaction
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_wallet_and_profile(sender, instance, created, **kwargs):
    """
    Automatically create wallet and profile when user is created
    """
    if created:
        try:
            with db_transaction.atomic():
                # Create wallet
                if not hasattr(instance, 'wallet'):
                    Wallet.objects.create(user=instance)
                    logger.info(f"Wallet created for user: {instance.username}")

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