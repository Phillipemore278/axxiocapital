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
# from .forms import KYCForm
# from account.models import KYC, VIPRequest
# from account.forms import BootstrapPasswordChangeForm, VIPRequestForm
from account.forms import BootstrapPasswordChangeForm
from plan.models import Plan, OrderPlan, OrderPlanItem
# from transaction.forms import CustomerTransactionForm
# from copytrade.models import CopyRelationship
# from transaction.models import Coin, Wallet

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
        "active_plans": all_active_plans,
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