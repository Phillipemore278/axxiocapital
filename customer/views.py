from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from decimal import Decimal
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash
import json
from django.db.models.functions import TruncDate
from datetime import datetime

# from .models import Portfolio
# from .forms import KYCForm
# from account.models import KYC, VIPRequest
# from account.forms import BootstrapPasswordChangeForm, VIPRequestForm
# from plan.models import Plan, OrderPlan, OrderPlanItem
# from transaction.forms import CustomerTransactionForm
# from copytrade.models import CopyRelationship
# from transaction.models import Coin, Wallet

@login_required
def customer_dashboard_view(request):
    context = {}
    return render(request, "customer/dashboard.html", context)