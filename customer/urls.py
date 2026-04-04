from django.urls import path

from . import views

app_name = 'customer'

urlpatterns = [
    path('dashboard/', views.customer_dashboard_view, name='customer_dashboard'),
    path('active-plans/', views.active_plan_list_view, name='active_plan_list'),
    path('plan-list/', views.all_plans_view, name='all_plans'),
    path('settings-and-security/', views.settings_security, name='settings_security'),
    path('wallet/', views.wallet_view, name='wallet'),

    # plan
    path('activate-plan/<plan_id>/', views.activate_plan_view, name='activate_plan'),

    # order
    path('orderplan-detail/<order_id>/', views.orderplan_detail_view, name='orderplan_detail'),
    path('liquidate-plan/<order_id>/', views.liquidate_plan_view, name='liquidate_plan'),

    # transaction
    path('deposit/', views.customer_deposit_view, name='customer_deposit'),
    path('user/withdraw/', views.customer_withdraw_view, name='customer_withdraw'),
    path("wallet/get/", views.get_wallet, name="get_wallet"),

    # kyc
    path('verify-kyc/', views.verify_kyc_view, name='verify_kyc'),

    # auth
    path('change_password/', views.change_password, name='change_password'),
    
]