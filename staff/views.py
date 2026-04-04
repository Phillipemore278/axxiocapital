import traceback
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

from .services import create_manual_snapshot
from .decorators import admin_staff_only
from account.models import User, KYC
from account.forms import AdminCustomerEditForm
from plan.models import Plan, OrderPlan
from plan.forms import PlanForm
from transaction.models import Transaction, Coin, Wallet
from transaction.forms import CoinForm, WalletForm
from notification.email_utils import send_html_email


@login_required
@admin_staff_only
def admin_dashboard_view(request):
    customers = User.objects.filter(is_staff=False).order_by('-date_joined')

    context = {
        "current_url": request.resolver_match.url_name,
        "customers": customers,
    }

    return render(request, 'staff/dashboard.html', context)


@login_required
@admin_staff_only
def admin_customer_detail_view(request, user_id):
    customer = get_object_or_404(User, id=user_id, is_staff=False)
    order_plan = OrderPlan.objects.filter(portfolio=customer.portfolio)
    order_plan_count = order_plan.count()

    context = {
        "current_url": request.resolver_match.url_name,
        "customer": customer,
        "order_plan":order_plan,
        "order_plan_count":order_plan_count
    }

    return render(request, 'staff/customer_detail.html', context)


@login_required
@admin_staff_only
def admin_edit_customer_view(request, user_id):
    customer = get_object_or_404(User, id=user_id, is_staff=False)

    if request.method == "POST":
        form = AdminCustomerEditForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            alert_msg = f"{customer.full_name}'s information is updated successfuly."
            messages.success(request,  alert_msg)
            return redirect("staff:admin_dashboard")
    else:
        form = AdminCustomerEditForm(instance=customer)

    context = {
        "current_url": request.resolver_match.url_name,
        "customer": customer,
        "form": form,
    }

    return render(request, "staff/edit_customer.html", context)


@login_required
@admin_staff_only
def admin_delete_customer_view(request, user_id):
    customer = get_object_or_404(User, id=user_id, is_staff=False)

    if request.method == "POST":
        full_name = customer.full_name
        customer.delete()
        messages.success(
            request,
            f"{full_name} has been deleted successfully."
        )
        return redirect("staff:admin_dashboard")

    context = {
        "current_url": request.resolver_match.url_name,
        "customer": customer,
    }

    return render(request, "staff/delete_customer.html", context)


@login_required
@admin_staff_only
def admin_plan_list_view(request):
    plans = Plan.objects.all().order_by('-created_at')

    context = {
        "current_url": request.resolver_match.url_name,
        "plans": plans,
    }
    return render(
        request,
        'staff/plan_list.html',
        context
    )


@login_required
@admin_staff_only
def admin_plan_create_view(request):
    if request.method == 'POST':
        form = PlanForm(request.POST)

        if form.is_valid():
            plan = form.save()
            messages.success(request, "Plan is Created successfully.")
            return redirect('staff:admin_plan_list')
        else:
            messages.error(request, "Please fix the errors below.")
            print("Form errors:", form.errors)
    else:
        form = PlanForm()

    context = {
        "current_url": request.resolver_match.url_name,
        "form": form,
    }
    return render(
        request,
        'staff/plan_form.html',
        context
    )


@login_required
@admin_staff_only
def admin_plan_edit_view(request, pk):
    plan = get_object_or_404(Plan, pk=pk)

    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan)

        if form.is_valid():
            form.save()
            messages.success(request, "Plan updated successfully.")
            return redirect('staff:admin_plan_list')
        else:
            messages.error(request, "Please fix the errors below.")
            print("Form errors:", form.errors)
    else:
        form = PlanForm(instance=plan)

    context = {
        "form": form,
        "plan": plan,
        "current_url": request.resolver_match.url_name,
    }
    return render(request, 'staff/plan_form.html', context)


@login_required
@admin_staff_only
def admin_plan_delete_view(request, pk):
    plan = get_object_or_404(Plan, pk=pk)

    if request.method == 'POST':
        plan.delete()
        messages.success(request, "plan is deleted successfully.")
        return redirect('staff:admin_plan_list')

    context = {
        "current_url": request.resolver_match.url_name,
        "plan": plan,
    }
    return render(
        request,
        'staff/plan_confirm_delete.html',
        context
    )


# transaction
@login_required
@admin_staff_only
@transaction.atomic
def admin_deposit_requests_view(request):
    deposits = (
        Transaction.objects
        .select_related('portfolio', 'portfolio__user')
        .filter(transaction_type='DEPOSIT', status='PENDING')
        .order_by('-timestamp')
    )

    if request.method == "POST":
        transaction_id = request.POST.get("transaction_id")
        action = request.POST.get("action")

        deposit = get_object_or_404(
            Transaction,
            id=transaction_id,
            transaction_type='DEPOSIT',
            status='PENDING'
        )

        portfolio = deposit.portfolio

        if action == "approve":
            portfolio.cash_balance += deposit.amount
            portfolio.save(update_fields=['cash_balance'])

            deposit.status = 'SUCCESSFUL'
            deposit.balance = portfolio.cash_balance
            deposit.save(update_fields=['status', 'balance'])

            messages.success(
                request,
                f"Deposit of {deposit.amount} approved successfully."
            )

        elif action == "decline":
            deposit.status = 'FAILED'
            deposit.save(update_fields=['status'])

            messages.error(
                request,
                f"Deposit of {deposit.amount} was declined."
            )

        return redirect('staff:admin_deposit_requests')

    return render(
        request,
        "staff/deposit_requests.html",
        {
            "deposits": deposits,
            "current_url": request.resolver_match.url_name,
        }
    )


@login_required
@admin_staff_only
@transaction.atomic
def admin_withdraw_requests_view(request):
    withdrawals = (
        Transaction.objects
        .select_related('portfolio', 'portfolio__user')
        .filter(transaction_type='WITHDRAW', status='PENDING')
        .order_by('-timestamp')
    )

    if request.method == "POST":
        transaction_id = request.POST.get("transaction_id")
        action = request.POST.get("action")

        withdraw = get_object_or_404(
            Transaction,
            id=transaction_id,
            transaction_type='WITHDRAW',
            status='PENDING'
        )

        portfolio = withdraw.portfolio

        if action == "approve":
            # Funds already deducted at request time
            withdraw.status = 'SUCCESSFUL'
            withdraw.save(update_fields=['status'])

            messages.success(
                request,
                f"Withdrawal of {withdraw.amount} approved successfully."
            )

        elif action == "decline":
            # Refund the reserved funds
            portfolio.cash_balance += withdraw.amount
            portfolio.save(update_fields=['cash_balance'])

            withdraw.status = 'FAILED'
            withdraw.balance = portfolio.cash_balance
            withdraw.save(update_fields=['status', 'balance'])

            messages.warning(
                request,
                f"Withdrawal of {withdraw.amount} was successfully declined and funds were returned to owner's poprtfolio balance."
            )

        return redirect('staff:admin_withdraw_requests')

    return render(
        request,
        "staff/withdraw_requests.html",
        {
            "withdrawals": withdrawals,
            "current_url": request.resolver_match.url_name,
        }
    )


@login_required
@admin_staff_only
def admin_kyc_list_view(request):
    kycs = (
        KYC.objects
        .select_related('portfolio__user')
        .filter(status__in=[KYC.STATUS_PENDING, KYC.STATUS_REJECTED ])
        .order_by('-submitted_at')
    )

    context = {
        "current_url": request.resolver_match.url_name,
        "kycs": kycs,
    }

    return render(request, 'staff/kyc_list.html', context)


@login_required
@admin_staff_only
def admin_kyc_review_view(request, kyc_id):
    kyc = get_object_or_404(
        KYC.objects.select_related('portfolio__user'),
        id=kyc_id
    )

    if request.method == "POST":
        action = request.POST.get("action")
        user = kyc.portfolio.user

        if action == "approve":
            kyc.status = KYC.STATUS_VERIFIED
            kyc.reviewed_at = timezone.now()
            kyc.rejection_reason = ""
            kyc.save()
            try:
                send_html_email(
                    subject="Your Identity Verification Has Been Approved",
                    to_email=[user.email],
                    template_name="notification/emails/kyc_approved.html",
                    context={
                        "user": user, 
                        "site_name": settings.SITE_NAME,
                    },
                )

                messages.success(
                    request,
                    f"KYC approved for {user.email}."
                )
            except Exception:
                # If SMTP not configured, just print OTP
                print("\nEMAIL ERROR:")
                traceback.print_exc()
            return redirect('staff:admin_kyc_list')

        elif action == "reject":
            reason = request.POST.get("rejection_reason", "").strip()

            if not reason:
                messages.error(request, "Rejection reason is required.")
            else:
                kyc.status = KYC.STATUS_REJECTED
                kyc.reviewed_at = timezone.now()
                kyc.rejection_reason = reason
                kyc.save()

                try:
                    send_html_email(
                        subject="Update on Your Verification Request",
                        to_email=[user.email],
                        template_name="notification/emails/kyc_rejected.html",
                        context={
                            "user": user, 
                            "site_name": settings.SITE_NAME,
                            "reason": reason,
                        },
                    )
                    messages.success(
                        request,
                        f"KYC rejected for {user.email}."
                    )
                except Exception:
                    # If SMTP not configured, just print OTP
                    print("\nEMAIL ERROR:")
                    traceback.print_exc()
                return redirect('staff:admin_kyc_list')

    context = {
        "current_url": request.resolver_match.url_name,
        "kyc": kyc,
    }

    return render(request, 'staff/kyc_review.html', context)


# coin part
@login_required
@admin_staff_only
def coin_wallet_list_view(request):
    # Prefetch wallets for efficiency
    coins = Coin.objects.prefetch_related('wallets').all()

    context = {
        "current_url": request.resolver_match.url_name,
        "coins": coins,
    }
    return render(request, 'staff/coin_wallet_list.html', context)


@login_required
@admin_staff_only
def coin_create_view(request):
    if request.method == 'POST':
        form = CoinForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Coin created successfully.")
            return redirect('staff:admin_coin_wallet_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = CoinForm()

    return render(request, 'staff/coin_form.html', {
        "current_url": request.resolver_match.url_name,
        "form": form,
    })


@login_required
@admin_staff_only
def coin_edit_view(request, pk):
    coin = get_object_or_404(Coin, pk=pk)
    if request.method == 'POST':
        form = CoinForm(request.POST, request.FILES, instance=coin)
        if form.is_valid():
            form.save()
            messages.success(request, "Coin updated successfully.")
            return redirect('staff:admin_coin_wallet_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = CoinForm(instance=coin)

    return render(request, 'staff/coin_form.html', {
        "current_url": request.resolver_match.url_name,
        "form": form,
        "coin": coin,
    })


@login_required
@admin_staff_only
def wallet_create_view(request):
    if request.method == 'POST':
        form = WalletForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Wallet created successfully.")
            return redirect('staff:admin_coin_wallet_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = WalletForm()

    return render(request, 'staff/wallet_form.html', {
        "current_url": request.resolver_match.url_name,
        "form": form,
    })


@login_required
@admin_staff_only
def wallet_edit_view(request, pk):
    wallet = get_object_or_404(Wallet, pk=pk)
    if request.method == 'POST':
        form = WalletForm(request.POST, request.FILES, instance=wallet)
        if form.is_valid():
            form.save()
            messages.success(request, "Wallet updated successfully.")
            return redirect('staff:admin_coin_wallet_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = WalletForm(instance=wallet)

    return render(request, 'staff/wallet_form.html', {
        "current_url": request.resolver_match.url_name,
        "form": form,
        "wallet": wallet,
    })


@login_required
@admin_staff_only
def wallet_delete_view(request, pk):
    wallet = get_object_or_404(Wallet, pk=pk)

    if request.method == "POST":
        wallet.delete()
        messages.success(request, "Wallet deleted successfully.")
        return redirect('staff:admin_coin_wallet_list')

    return render(request, "staff/wallet_delete_confirm.html", {
        "current_url": request.resolver_match.url_name,
        "wallet": wallet,
    })


# snapshot
@login_required
@admin_staff_only
def snapshot_positive_view(request, order_id):
    order = get_object_or_404(OrderPlan, pk=order_id)
    item = create_manual_snapshot(order_id, order.monthly_percent,
                                  actor=request.user, reason="Staff positive toggle")
    messages.success(request, f"Positive snapshot created for {order.plan.name}: + ${item.delta_amount} gain added to the current value")
    return redirect('staff:admin_customer_detail', user_id=order.portfolio.user.id)


@login_required
@admin_staff_only
def snapshot_negative_view(request, order_id):
    order = get_object_or_404(OrderPlan, pk=order_id)
    percent = order.monthly_percent * Decimal('-1')
    item = create_manual_snapshot(order_id, percent,
                                  actor=request.user, reason="Staff negative toggle")
    messages.success(request, f"Negative snapshot created for {order.plan.name}: - ${item.delta_amount} remopved from the current value")
    return redirect('staff:admin_customer_detail', user_id=order.portfolio.user.id)