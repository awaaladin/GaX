"""
Payment processing utilities
Handle wallet operations, transaction processing, and fees
Integrated with Paystack for virtual accounts and transfers
"""
import logging
from decimal import Decimal
from django.db import transaction as db_transaction
from django.db.models import F
from django.utils import timezone
from django.conf import settings
from ..models import Wallet, Transaction, PaymentGateway
from .signature import SignatureVerifier
from .paystack import get_paystack_client

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """Process payments and wallet operations"""

    # Fee configuration (can be moved to database/settings)
    TRANSFER_FEE = Decimal('10.00')
    WITHDRAWAL_FEE = Decimal('50.00')
    PAYMENT_GATEWAY_FEE_PERCENTAGE = Decimal('1.5')  # 1.5%
    PAYMENT_GATEWAY_CAP = Decimal('2000.00')

    @staticmethod
    def calculate_transfer_fee(amount):
        """Calculate transfer fee"""
        if amount <= Decimal('5000.00'):
            return Decimal('10.00')
        elif amount <= Decimal('50000.00'):
            return Decimal('25.00')
        else:
            return Decimal('50.00')

    @staticmethod
    def calculate_withdrawal_fee(amount):
        """Calculate withdrawal fee"""
        return PaymentProcessor.WITHDRAWAL_FEE

    @staticmethod
    def calculate_payment_gateway_fee(amount):
        """Calculate payment gateway fee"""
        fee = (amount * PaymentProcessor.PAYMENT_GATEWAY_FEE_PERCENTAGE) / 100

        if fee > PaymentProcessor.PAYMENT_GATEWAY_CAP:
            fee = PaymentProcessor.PAYMENT_GATEWAY_CAP

        return fee.quantize(Decimal('0.01'))

    @staticmethod
    @db_transaction.atomic
    def credit_wallet(wallet, amount, description, transaction_type='deposit',
                      metadata=None):
        """
        Credit wallet with amount

        Args:
            wallet: Wallet instance
            amount: Amount to credit
            description: Transaction description
            transaction_type: Type of transaction
            metadata: Additional metadata

        Returns:
            Transaction: Created transaction
        """
        try:
            # Validate amount
            if amount <= 0:
                raise ValueError("Amount must be greater than zero")

            # Get balance before
            balance_before = wallet.balance

            # Update wallet balance using F() to prevent race conditions
            Wallet.objects.filter(id=wallet.id).update(
                balance=F('balance') + amount,
                ledger_balance=F('ledger_balance') + amount,
                updated_at=timezone.now()
            )

            # Refresh wallet
            wallet.refresh_from_db()
            balance_after = wallet.balance

            # Create transaction record
            txn = Transaction.objects.create(
                user=wallet.user,
                wallet=wallet,
                transaction_type=transaction_type,
                amount=amount,
                fee=Decimal('0.00'),
                total_amount=amount,
                status='completed',
                description=description,
                metadata=metadata or {},
                balance_before=balance_before,
                balance_after=balance_after,
                completed_at=timezone.now()
            )

            logger.info(
                f"Wallet credited: {wallet.account_number} - "
                f"₦{amount} - {txn.reference}"
            )

            return txn

        except Exception as e:
            logger.error(f"Credit wallet error: {e}")
            raise

    @staticmethod
    @db_transaction.atomic
    def debit_wallet(wallet, amount, fee, description, transaction_type,
                     metadata=None, recipient_account=None,
                     recipient_name=None, recipient_bank=None):
        """
        Debit wallet with amount

        Args:
            wallet: Wallet instance
            amount: Amount to debit
            fee: Transaction fee
            description: Transaction description
            transaction_type: Type of transaction
            metadata: Additional metadata
            recipient_account: Recipient account number
            recipient_name: Recipient name
            recipient_bank: Recipient bank

        Returns:
            Transaction: Created transaction
        """
        try:
            # Validate amount
            if amount <= 0:
                raise ValueError("Amount must be greater than zero")

            total_amount = amount + fee

            # Check sufficient balance
            if wallet.balance < total_amount:
                raise ValueError("Insufficient balance")

            # Check if wallet is frozen
            if wallet.is_frozen:
                raise ValueError("Wallet is frozen")

            # Get balance before
            balance_before = wallet.balance

            # Update wallet balance using F() to prevent race conditions
            Wallet.objects.filter(id=wallet.id).update(
                balance=F('balance') - total_amount,
                ledger_balance=F('ledger_balance') - total_amount,
                updated_at=timezone.now()
            )

            # Refresh wallet
            wallet.refresh_from_db()
            balance_after = wallet.balance

            # Create transaction record
            txn = Transaction.objects.create(
                user=wallet.user,
                wallet=wallet,
                transaction_type=transaction_type,
                amount=amount,
                fee=fee,
                total_amount=total_amount,
                status='completed',
                description=description,
                metadata=metadata or {},
                recipient_account=recipient_account,
                recipient_name=recipient_name,
                recipient_bank=recipient_bank,
                balance_before=balance_before,
                balance_after=balance_after,
                completed_at=timezone.now()
            )

            logger.info(
                f"Wallet debited: {wallet.account_number} - "
                f"₦{total_amount} - {txn.reference}"
            )

            return txn

        except Exception as e:
            logger.error(f"Debit wallet error: {e}")
            raise

    @staticmethod
    @db_transaction.atomic
    def process_transfer(sender_wallet, recipient_account, amount,
                         narration, transaction_pin):
        """
        Process wallet-to-wallet transfer

        Args:
            sender_wallet: Sender's wallet
            recipient_account: Recipient account number
            amount: Amount to transfer
            narration: Transfer description
            transaction_pin: Sender's transaction PIN

        Returns:
            dict: Transfer result with transactions
        """
        try:
            # Verify transaction PIN
            if not SignatureVerifier.verify_transaction_pin(
                transaction_pin,
                sender_wallet.user.transaction_pin
            ):
                raise ValueError("Invalid transaction PIN")

            # Find recipient wallet
            try:
                recipient_wallet = Wallet.objects.get(
                    account_number=recipient_account,
                    is_active=True
                )
            except Wallet.DoesNotExist:
                raise ValueError("Recipient account not found")

            # Check self-transfer
            if sender_wallet.id == recipient_wallet.id:
                raise ValueError("Cannot transfer to same account")

            # Calculate fee
            fee = PaymentProcessor.calculate_transfer_fee(amount)

            # Debit sender
            debit_txn = PaymentProcessor.debit_wallet(
                wallet=sender_wallet,
                amount=amount,
                fee=fee,
                description=f"Transfer to {recipient_wallet.account_number}",
                transaction_type='transfer',
                metadata={'narration': narration},
                recipient_account=recipient_wallet.account_number,
                recipient_name=recipient_wallet.user.get_full_name(),
                recipient_bank='GAX Bank'
            )

            # Credit recipient
            credit_txn = PaymentProcessor.credit_wallet(
                wallet=recipient_wallet,
                amount=amount,
                description=f"Transfer from {sender_wallet.account_number}",
                transaction_type='deposit',
                metadata={
                    'narration': narration,
                    'sender_reference': debit_txn.reference
                }
            )

            logger.info(
                f"Transfer completed: {sender_wallet.account_number} -> "
                f"{recipient_wallet.account_number} - ₦{amount}"
            )

            return {
                'success': True,
                'debit_transaction': debit_txn,
                'credit_transaction': credit_txn,
                'fee': fee,
                'message': 'Transfer successful'
            }

        except Exception as e:
            logger.error(f"Transfer error: {e}")
            raise

    @staticmethod
    def verify_transaction_pin(user, pin):
        """
        Verify user's transaction PIN

        Args:
            user: User instance
            pin: Plain text PIN

        Returns:
            bool: True if PIN is valid
        """
        if not user.transaction_pin:
            return False

        return SignatureVerifier.verify_transaction_pin(
            pin,
            user.transaction_pin
        )

    @staticmethod
    @db_transaction.atomic
    def process_withdrawal(wallet, amount, bank_account, transaction_pin):
        """
        Process withdrawal to external bank account

        Args:
            wallet: User's wallet
            amount: Amount to withdraw
            bank_account: BankAccount instance
            transaction_pin: Transaction PIN

        Returns:
            Transaction: Created transaction (pending)
        """
        try:
            # Verify PIN
            if not PaymentProcessor.verify_transaction_pin(
                wallet.user,
                transaction_pin
            ):
                raise ValueError("Invalid transaction PIN")

            # Calculate fee
            fee = PaymentProcessor.calculate_withdrawal_fee(amount)
            total_amount = amount + fee

            # Check balance
            if wallet.balance < total_amount:
                raise ValueError("Insufficient balance")

            # Get balance before
            balance_before = wallet.balance

            # Deduct from wallet (mark as pending)
            Wallet.objects.filter(id=wallet.id).update(
                balance=F('balance') - total_amount,
                updated_at=timezone.now()
            )

            wallet.refresh_from_db()
            balance_after = wallet.balance

            # Create transaction (pending admin approval)
            txn = Transaction.objects.create(
                user=wallet.user,
                wallet=wallet,
                transaction_type='withdrawal',
                amount=amount,
                fee=fee,
                total_amount=total_amount,
                status='pending',
                description=f"Withdrawal to {bank_account.bank_name}",
                metadata={
                    'bank_account_id': str(bank_account.id),
                    'account_number': bank_account.account_number,
                    'bank_name': bank_account.bank_name,
                    'account_name': bank_account.account_name
                },
                recipient_account=bank_account.account_number,
                recipient_name=bank_account.account_name,
                recipient_bank=bank_account.bank_name,
                balance_before=balance_before,
                balance_after=balance_after,
                requires_approval=True
            )

            logger.info(
                f"Withdrawal initiated: {wallet.account_number} - "
                f"₦{amount} - {txn.reference}"
            )

            return txn

        except Exception as e:
            logger.error(f"Withdrawal error: {e}")
            raise

    @staticmethod
    @db_transaction.atomic
    def reverse_transaction(transaction, reason):
        """
        Reverse a transaction

        Args:
            transaction: Transaction to reverse
            reason: Reason for reversal

        Returns:
            Transaction: Reversal transaction
        """
        try:
            if transaction.status == 'reversed':
                raise ValueError("Transaction already reversed")

            if transaction.status not in ['completed', 'failed']:
                raise ValueError("Cannot reverse transaction in this state")

            wallet = transaction.wallet

            # Credit back the total amount
            reversal_txn = PaymentProcessor.credit_wallet(
                wallet=wallet,
                amount=transaction.total_amount,
                description=f"Reversal: {transaction.reference}",
                transaction_type='refund',
                metadata={
                    'original_reference': transaction.reference,
                    'reason': reason
                }
            )

            # Update original transaction
            transaction.status = 'reversed'
            transaction.save()

            logger.info(
                f"Transaction reversed: {transaction.reference} - "
                f"₦{transaction.total_amount}"
            )

            return reversal_txn

        except Exception as e:
            logger.error(f"Reversal error: {e}")
            raise
