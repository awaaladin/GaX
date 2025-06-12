from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import DepositForm, WithdrawForm, TransferForm
from .models import Transaction

@login_required
def deposit_view(request):
    form = DepositForm(request.user, request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            account = form.cleaned_data['account']
            amount = form.cleaned_data['amount']
            account.balance += amount
            account.save()
            Transaction.objects.create(to_account=account, transaction_type='deposit', amount=amount)
            return redirect('dashboard')
        # If POST but not valid, fall through to render with errors
    # Always render the form for GET or invalid POST
    return render(request, 'accounts/transaction_form.html', {'form': form, 'title': 'Deposit'})

@login_required
def withdraw_view(request):
    form = WithdrawForm(request.user, request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            account = form.cleaned_data['account']
            amount = form.cleaned_data['amount']
            if amount <= account.balance:
                account.balance -= amount
                account.save()
                Transaction.objects.create(from_account=account, transaction_type='withdrawal', amount=amount)
                return redirect('dashboard')
        # If POST but not valid, fall through to render with errors
    # Always render the form for GET or invalid POST
    return render(request, 'accounts/withdraw.html', {'form': form, 'title': 'Withdraw'})

@login_required
def transfer_view(request):
    form = TransferForm(request.user, request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            from_account = form.cleaned_data['from_account']
            to_account = form.cleaned_data['to_account']
            amount = form.cleaned_data['amount']
            if amount <= from_account.balance:
                from_account.balance -= amount
                to_account.balance += amount
                from_account.save()
                to_account.save()
                Transaction.objects.create(
                    from_account=from_account, to_account=to_account,
                    transaction_type='transfer', amount=amount
                )
                return redirect('dashboard')
        # If POST but not valid, fall through to render with errors
    # Always render the form for GET or invalid POST
    return render(request, 'accounts/transfer.html', {'form': form, 'title': 'Transfer'})