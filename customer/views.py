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
from plan.models import Plan, OrderPlan, OrderPlanItem, TransactionLog
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

    # 2️⃣ Portfolio performance data for chart
    # Aggregate snapshots by date across all orders
    snapshots = (
        OrderPlanItem.objects.filter(order_plan__portfolio=portfolio)
        .annotate(date=TruncDate('snapshot_at'))
        .values('date')
        .annotate(total_value=Sum('cumulative_amount'))
        .order_by('date')
    )

    labels = [s['date'].strftime("%b %d") for s in snapshots]
    data = [float(s['total_value'] + portfolio.cash_balance) for s in snapshots]  # include cash if desired

     # --- Donut Chart Data ---
    allocation = (
        OrderPlan.objects.filter(
            portfolio=portfolio,
            status=OrderPlan.STATUS_ACTIVE
        )
        .values('plan__plantype')
        .annotate(total_allocated=Sum('principal_amount'))
        .order_by('plan__plantype')
    )

    # Prepare combined list of dicts for template
    allocation_items = [
        {
            'label': a['plan__plantype'].title(),
            'value': float(a['total_allocated']),
        }
        for a in allocation
    ]

    allocation_labels = [item['label'] for item in allocation_items]
    allocation_data = [item['value'] for item in allocation_items]
    allocation_total = sum(allocation_data)


    # Determine Largest / Lowest Allocation
    if allocation_items:
        largest_allocation = max(allocation_items, key=lambda x: x['value'])
        lowest_allocation = min(allocation_items, key=lambda x: x['value'])
    else:
        largest_allocation = lowest_allocation = None

    # Determine Best Performing (highest ROI among active plans)
    active_orders = OrderPlan.objects.filter(
        portfolio=portfolio,
        status=OrderPlan.STATUS_ACTIVE
    )
    best_performing = None
    best_roi = None
    if active_orders.exists():
        best_order = max(active_orders, key=lambda o: o.get_roi())
        best_performing = {
            'label': best_order.plan.name,
            'roi': best_order.get_roi()
        }

    # Optional: Simple Diversification Score
    num_plans = len(allocation_items)
    if num_plans <= 1:
        diversification = "Low"
    elif num_plans <= 3:
        diversification = "Moderate"
    else:
        diversification = "High"


    context = {
        "current_url": request.resolver_match.url_name,
        "portfolio": portfolio,
        "non_mirrored_total": non_mirrored_total,
        "active_plans": all_active_plans[:3],
        "active_plans_count": all_active_plans.count(),
        "active_earnings": active_earnings,
        'totals': totals,
        'chart_labels': labels,
        'chart_data': data,
        'allocation_items': allocation_items,
        'allocation_labels': allocation_labels,
        'allocation_data': allocation_data,
        'allocation_total': allocation_total,
        'largest_allocation': largest_allocation,
        'lowest_allocation': lowest_allocation,
        'best_performing': best_performing,
        'diversification': diversification,
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
        mirrored=Sum('current_value', filter=Q(is_mirrowed=False))
    )

    non_mirrored_total = totals['non_mirrored'] or 0
    mirrored_total = totals['mirrored'] or 0

    transactions = portfolio.transactions.all()

    return render(request, "customer/wallet.html", {
        "current_url": "wallet",
        "portfolio": portfolio,
        "non_mirrored_total": non_mirrored_total,
        "mirrored_total": mirrored_total,
        "transactions": transactions,
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
    snapshots_asc = order.items.order_by('-snapshot_at')

    # -------- Pagination --------
    paginator = Paginator(snapshots_asc, 10)  # Show 10 snapshots per page
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
        # 'snapshots_asc':snapshots_asc,
    }

    return render(
        request,
        "customer/order_plan_detail.html",
        context
    )


@login_required
def liquidate_plan_view(request, order_id):
    """
    Liquidate an OrderPlan:
    - Refund the current value to the user's cash balance
    - Delete the order plan
    - Log the transaction
    """
    order = get_object_or_404(OrderPlan, pk=order_id)
    portfolio = order.portfolio

    if request.method == "POST":
        with transaction.atomic():
            refunded_amount = order.current_value

            # 1️⃣ Add back to user's cash balance
            portfolio.cash_balance += refunded_amount
            portfolio.save(update_fields=['cash_balance'])

            # 2️⃣ Log the liquidation as a transaction
            TransactionLog.objects.create(
                order_plan=order,
                before_value=order.current_value,
                change_amount=refunded_amount,
                after_value=portfolio.cash_balance,
                reason=f"Liquidated '{order.plan.name}'",
                created_by=request.user
            )

            # 3️⃣ Delete the OrderPlan
            order.delete()

        messages.success(
            request,
            f"'{order.plan.name}' has been liquidated. ${refunded_amount} returned to your cash balance."
        )
        return redirect('customer:customer_dashboard')

    return render(
        request,
        "customer/liquidate_plan.html",
        {
            "order": order,
            "portfolio": portfolio
        }
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
