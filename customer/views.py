from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, F, Q
from decimal import Decimal
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash
import json
from django.db.models.functions import TruncDate
from datetime import datetime

from .models import Portfolio
from .forms import KYCForm
from account.models import KYC
# from account.forms import BootstrapPasswordChangeForm, VIPRequestForm
from account.forms import BootstrapPasswordChangeForm
from plan.models import Plan, OrderPlan, OrderPlanItem
from transaction.forms import CustomerTransactionForm
# from copytrade.models import CopyRelationship
from transaction.models import Coin, Wallet

@login_required
def customer_dashboard_view(request):
    portfolio = Portfolio.objects.get(user=request.user)

    totals = OrderPlan.objects.filter(
        portfolio=portfolio,
        status=OrderPlan.STATUS_ACTIVE,
    ).aggregate(
        non_mirrored=Sum('principal_amount', filter=Q(is_mirrowed=False)),
        active_earnings=Sum(
            F('current_value') - F('principal_amount'),
            filter=Q(is_mirrowed=False)
        ),
    )

    non_mirrored_total = totals['non_mirrored'] or 0
    active_earnings = totals['active_earnings'] or 0

    # All active plans for this portfolio (mirrored or not)
    all_active_plans = OrderPlan.objects.filter(
        portfolio=portfolio,
        status=OrderPlan.STATUS_ACTIVE
    ).select_related("plan")

    context = {
        "current_url": request.resolver_match.url_name,
        "portfolio": portfolio,
        "non_mirrored_total": non_mirrored_total,
        "active_plans": all_active_plans[:3],
        "active_plans_count": all_active_plans.count(),
        "active_earnings": active_earnings,
    }
    return render(request, "customer/dashboard.html", context)


@login_required
def active_plan_list_view(request):
    portfolio = request.user.portfolio
    active_plans = OrderPlan.objects.filter(portfolio=portfolio)

    return render(
        request,
        "customer/active_plan_list.html",
        {
            "active_plans": active_plans,
            "portfolio": portfolio
        }
    )


@login_required
def all_plans_view(request):
    plans = Plan.objects.all()
    context = {
        "current_url": request.resolver_match.url_name,
        "plans": plans,
    }
    return render(request, "customer/all_plans.html", context)


@login_required
def settings_security(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    # password_form = BootstrapPasswordChangeForm(portfolio.user)

    context = {
        "current_url": request.resolver_match.url_name,
        'portfolio': portfolio,
        # "password_form":password_form,
    }
    return render(request, "customer/settings_security.html", context)


@login_required
def wallet_view(request):
    portfolio = request.user.portfolio

    totals = OrderPlan.objects.filter(
        portfolio=portfolio
    ).aggregate(
        non_mirrored=Sum('principal_amount', filter=Q(is_mirrowed=False)),
        mirrored=Sum('principal_amount', filter=Q(is_mirrowed=True))
    )

    non_mirrored_total = totals['non_mirrored'] or 0
    mirrored_total = totals['mirrored'] or 0

    # transactions = portfolio.transactions.all()

    return render(request, "customer/wallet.html", {
        "current_url": "wallet",
        "portfolio": portfolio,
        "non_mirrored_total": non_mirrored_total,
        "mirrored_total": mirrored_total,
        # "transactions": transactions,
    })


# plan side
@login_required
def activate_plan_view(request, plan_id):
    portfolio = request.user.portfolio
    plan = get_object_or_404(Plan, id=plan_id)

    if request.method == "POST":
        allocated_cash = Decimal(request.POST.get("allocated_cash", "0"))

        if allocated_cash < plan.min_amount: 
            messages.error(request, f"Minimum amount for this plan is ${plan.min_amount}.") 
            return redirect('customer:activate_plan', plan_id=plan.pk)
        
        if allocated_cash > portfolio.cash_balance:
            messages.error(
                request,
                "Allocated cash exceeds your available cash balance."
            )
            return redirect('customer:activate_plan', plan_id=plan.pk)
        
        # 1️⃣ Deduct allocated cash from follower only once
        portfolio.cash_balance -= allocated_cash
        portfolio.save(update_fields=['cash_balance'])

        order = OrderPlan.objects.create( 
            portfolio=portfolio, 
            plan=plan, 
            principal_amount=allocated_cash, 
            current_value=allocated_cash, 
            start_at=timezone.now(), 
            status=OrderPlan.STATUS_ACTIVE, 
        )

        messages.success(request, f"'{plan.name}' activated with ${allocated_cash}.") 
        return redirect('customer:customer_dashboard')

    return render(
        request,
        "customer/activate_plan.html",
        {
            "plan": plan,
            "portfolio": portfolio
        }
    )


@login_required
def orderplan_detail_view(request, order_id):
    portfolio = request.user.portfolio
    order = get_object_or_404(OrderPlan, pk=order_id, portfolio=portfolio) 
    
    snapshots_qs = order.items.order_by('snapshot_at')

    # -------- Pagination --------
    paginator = Paginator(snapshots_qs, 10)  # Show 10 snapshots per page
    page_number = request.GET.get('page')
    snapshots = paginator.get_page(page_number)

    # -------- Chart Data (Optional: Use ALL snapshots or only current page) --------
    # If you want chart to show ALL data:
    all_snapshots = snapshots_qs

    labels = [item.snapshot_at.strftime("%Y-%m-%d") for item in all_snapshots]
    values = [float(item.cumulative_amount or order.principal_amount) for item in all_snapshots]

    context = { 
        'order': order, 
        'snapshots': snapshots,   # paginated snapshots
        'labels': labels,
        'values': values,
    }

    return render(
        request,
        "customer/order_plan_detail.html",
        context
    )


# transaction part
@login_required
@transaction.atomic
def customer_deposit_view(request):
    portfolio = request.user.portfolio
    deposit_transactions = portfolio.transactions.filter(
        transaction_type='DEPOSIT'
    )
    coins = Coin.objects.all()

    if request.method == "POST":
        form = CustomerTransactionForm(request.POST, transaction_type="DEPOSIT")

        if form.is_valid():
            trans = form.save(commit=False)
            trans.transaction_type = 'DEPOSIT'
            trans.portfolio = portfolio
            trans.balance = portfolio.cash_balance

            # ✅ Get the coin from POST (from your <select id="coin-select">)
            coin_id = request.POST.get("coin")  # this will work
            print(coin_id)
            if coin_id:
                try:
                    trans.coin = Coin.objects.get(id=coin_id)
                except Coin.DoesNotExist:
                    print('didnot work')
                    form.add_error(None, "Selected coin does not exist.")
                    return render(request, "your_template.html", {"form": form, "coins": coins})
            print('returned none')
            trans.save()

            messages.success(request, "Your deposit request has been received and is currently being processed.")
            return redirect('customer:customer_deposit')
        else:
            # 🔥 THIS shows you exactly why the form is invalid
            messages.error(request, "An error occurred while processing your request. Please try again or contact support if the issue persists.")
            print("FORM ERRORS:", form.errors)
            print("NON FIELD ERRORS:", form.non_field_errors())
    else:
        form = CustomerTransactionForm()

    return render(
        request,
        "customer/transactions/customer_deposit.html",
        {
            "form": form,
            "transactions": deposit_transactions,
            "coins": coins
        }
    )


@login_required
@transaction.atomic
def customer_withdraw_view(request):
    portfolio = request.user.portfolio

    # Only fetch withdraw transactions once
    withdraw_transactions = portfolio.transactions.filter(
        transaction_type='WITHDRAW'
    )

    # Pending withdraws and total in a single query
    pending_withdraw_sum = withdraw_transactions.filter(
        status='PENDING'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    if request.method == "POST":
        form = CustomerTransactionForm(request.POST, transaction_type="WITHDRAW")

        if form.is_valid():
            trans = form.save(commit=False)
            trans.transaction_type = 'WITHDRAW'
            trans.portfolio = portfolio

            # Check if balance is sufficient
            if portfolio.cash_balance < trans.amount:
                messages.error(
                    request,
                    "You don't have enough cash balance to complete this withdrawal."
                )
            else:

                if not portfolio.is_kyc_verified:
                    messages.info(
                        request,
                        "You must complete identity verification (KYC) before making a withdrawal."
                    )
                    return redirect('customer:verify_kyc')
                # Deduct from balance and save
                portfolio.cash_balance -= trans.amount
                portfolio.save()

                trans.balance = portfolio.cash_balance
                trans.save()
                messages.success(
                    request,
                    "Your withdrawal request has been submitted successfully and is pending processing."
                )
                return redirect('customer:customer_withdraw')

    else:
        form = CustomerTransactionForm()

    return render(
        request,
        "customer/transactions/customer_withdraw.html",
        {
            "form": form,
            "transactions": withdraw_transactions,
            "portfolio": portfolio,
            "pending_withdraw_sum": pending_withdraw_sum,
        }
    )


# fetching crypto for deposit
from django.http import JsonResponse
def get_wallet(request):

    coin_id = request.GET.get("coin")

    wallet = Wallet.objects.filter(coin_id=coin_id).first()

    if wallet:
        data = {
            "wallet": wallet.wallet_address,
            "qr": wallet.qr_code.url if wallet.qr_code else ""
        }
    else:
        data = {}

    return JsonResponse(data)


@login_required
def verify_kyc_view(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)

    # Get or create KYC record
    kyc, created = KYC.objects.get_or_create(portfolio=portfolio)

    # If already verified, block resubmission
    if kyc.is_verified:
        messages.info(request, "Your identity has already been verified.")
        return redirect('customer:customer_dashboard')

    if request.method == "POST":
        form = KYCForm(request.POST, request.FILES, instance=kyc)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your KYC documents have been submitted successfully and are pending verification."
            )
            return redirect('customer:verify_kyc')
    else:
        form = KYCForm(instance=kyc)

    return render(
        request,
        'customer/verify_kyc.html',
        {
            'form': form,
            'kyc': kyc,
            'portfolio': portfolio,
            'current_url': request.resolver_match.url_name,
        }
    )
