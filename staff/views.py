import traceback
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

# from .services import create_manual_snapshot
from .decorators import admin_staff_only
from account.models import User, KYC
from account.forms import AdminCustomerEditForm
from plan.models import Plan, OrderPlan
# from plan.forms import PlanForm
# from transaction.models import Transaction, Coin, Wallet
# from transaction.forms import CoinForm, WalletForm
# from notification.email_utils import send_html_email


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