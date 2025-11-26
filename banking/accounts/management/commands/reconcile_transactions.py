"""
Reconcile failed transactions
Check and update status of pending/failed transactions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from banking.accounts.models import Transaction, PaymentGateway
from banking.accounts.utils.moniepoint import MoniepointAPI
from banking.accounts.utils.payment import PaymentProcessor
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reconcile failed or pending transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Check transactions from last N hours (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting reconciliation for last {hours} hours'
            )
        )

        # Get cutoff time
        cutoff_time = timezone.now() - timedelta(hours=hours)

        # Reconcile transactions
        pending_txns = Transaction.objects.filter(
            status__in=['pending', 'processing'],
            created_at__gte=cutoff_time
        )

        self.stdout.write(
            f'Found {pending_txns.count()} pending transactions'
        )

        reconciled = 0
        failed = 0

        for txn in pending_txns:
            try:
                if txn.external_reference:
                    # Query external API
                    moniepoint = MoniepointAPI()
                    result = moniepoint.verify_transaction(
                        txn.external_reference
                    )

                    if result.get('status'):
                        status = result.get('transactionStatus', '')

                        if not dry_run:
                            if status == 'SUCCESSFUL':
                                txn.status = 'completed'
                                txn.completed_at = timezone.now()
                                txn.save()
                                reconciled += 1

                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'Reconciled: {txn.reference}'
                                    )
                                )
                            elif status == 'FAILED':
                                txn.status = 'failed'
                                txn.save()

                                # Reverse if needed
                                if txn.transaction_type in [
                                    'withdrawal',
                                    'transfer'
                                ]:
                                    PaymentProcessor.reverse_transaction(
                                        txn,
                                        'Failed transaction reversal'
                                    )

                                failed += 1
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'Failed: {txn.reference}'
                                    )
                                )

            except Exception as e:
                logger.error(f'Reconciliation error for {txn.reference}: {e}')
                self.stdout.write(
                    self.style.ERROR(
                        f'Error: {txn.reference} - {str(e)}'
                    )
                )

        # Reconcile payment gateway transactions
        pending_payments = PaymentGateway.objects.filter(
            status='pending',
            created_at__gte=cutoff_time
        )

        self.stdout.write(
            f'Found {pending_payments.count()} pending payments'
        )

        for payment in pending_payments:
            try:
                # Check if payment is abandoned (older than 1 hour)
                if payment.created_at < timezone.now() - timedelta(hours=1):
                    if not dry_run:
                        payment.status = 'abandoned'
                        payment.save()

                        self.stdout.write(
                            self.style.WARNING(
                                f'Abandoned: {payment.reference}'
                            )
                        )

            except Exception as e:
                logger.error(
                    f'Payment reconciliation error for '
                    f'{payment.reference}: {e}'
                )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nReconciliation complete:\n'
                    f'Reconciled: {reconciled}\n'
                    f'Failed: {failed}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Dry run complete (no changes made)')
            )
