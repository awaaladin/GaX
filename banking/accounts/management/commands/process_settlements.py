"""
Clear pending settlements
Process approved withdrawals and settlements
"""
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from banking.accounts.models import Transaction
from banking.accounts.utils.moniepoint import MoniepointAPI
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process pending settlements and approved withdrawals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of transactions to process'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        self.stdout.write(
            self.style.SUCCESS('Starting settlement processing')
        )

        # Get approved withdrawals
        pending_withdrawals = Transaction.objects.filter(
            transaction_type='withdrawal',
            status='pending',
            requires_approval=True
        ).select_related('user', 'wallet')[:limit]

        self.stdout.write(
            f'Found {pending_withdrawals.count()} pending withdrawals'
        )

        processed = 0
        failed = 0

        for withdrawal in pending_withdrawals:
            try:
                if not dry_run:
                    with db_transaction.atomic():
                        # Get bank account details from metadata
                        metadata = withdrawal.metadata
                        account_number = metadata.get('account_number')
                        bank_name = metadata.get('bank_name')
                        account_name = metadata.get('account_name')

                        if not all([account_number, bank_name, account_name]):
                            raise ValueError('Incomplete bank account details')

                        # Initiate transfer via Moniepoint
                        moniepoint = MoniepointAPI(environment='live')

                        result = moniepoint.initiate_transfer(
                            amount=withdrawal.amount,
                            account_number=account_number,
                            account_name=account_name,
                            bank_code=metadata.get('bank_code', ''),
                            narration=f'Withdrawal: {withdrawal.reference}',
                            reference=withdrawal.reference
                        )

                        if result.get('status'):
                            # Update transaction
                            withdrawal.status = 'processing'
                            withdrawal.external_reference = result.get(
                                'transactionReference'
                            )
                            withdrawal.save()

                            processed += 1

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Processed: {withdrawal.reference}'
                                )
                            )
                        else:
                            # Mark as failed
                            withdrawal.status = 'failed'
                            withdrawal.save()

                            failed += 1

                            self.stdout.write(
                                self.style.ERROR(
                                    f'Failed: {withdrawal.reference} - '
                                    f'{result.get("message")}'
                                )
                            )

            except Exception as e:
                logger.error(
                    f'Settlement error for {withdrawal.reference}: {e}'
                )
                self.stdout.write(
                    self.style.ERROR(
                        f'Error: {withdrawal.reference} - {str(e)}'
                    )
                )
                failed += 1

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSettlement processing complete:\n'
                    f'Processed: {processed}\n'
                    f'Failed: {failed}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Dry run complete (no changes made)')
            )
