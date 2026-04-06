from django.urls import path

from . import views

app_name = 'staff'

urlpatterns = [
    path('dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('customer/<int:user_id>/detail/',views.admin_customer_detail_view,
    name='admin_customer_detail'),
    path("customer/<int:user_id>/edit/", views.admin_edit_customer_view,
    name="admin_edit_customer"),
    path("customers/<int:user_id>/delete/", views.admin_delete_customer_view,
    name="admin_delete_customer"),

    path('plans/', views.admin_plan_list_view,name='admin_plan_list'),
    path('plan/create/', views.admin_plan_create_view,name='admin_plan_create'),
    path('plan/<int:pk>/edit/', views.admin_plan_edit_view,
    name='admin_plan_edit'),
    path('plan/<int:pk>/delete/', views.admin_plan_delete_view,
    name='admin_plan_delete'),

    path('pending-deposits/', views.admin_deposit_requests_view, name='admin_deposit_requests'),
    path('pending-withdrawals/', views.admin_withdraw_requests_view, name='admin_withdraw_requests'),

    path('kyc-list/', views.admin_kyc_list_view,name='admin_kyc_list'),
    path('kyc/<int:kyc_id>/review/', views.admin_kyc_review_view,
    name='admin_kyc_review'),

    # List all coins and wallets
    path('coins-wallets/', views.coin_wallet_list_view, name='admin_coin_wallet_list'),

    # Coin URLs
    path('coin/create/', views.coin_create_view, name='admin_coin_create'),
    path('coin/<int:pk>/edit/', views.coin_edit_view, name='admin_coin_edit'),

    # Wallet URLs
    path('wallet/create/', views.wallet_create_view, name='admin_wallet_create'),
    path('wallet/<int:pk>/edit/', views.wallet_edit_view, name='admin_wallet_edit'),
    path("wallet/<int:pk>/delete/",views.wallet_delete_view,name="wallet_delete"),

    path('snapshot-positive/<int:order_id>/', views.snapshot_positive_view,
    name='snapshot_positive'),
    path('snapshot-negative/<int:order_id>/', views.snapshot_negative_view,
    name='snapshot_negative'),

    path('sdeposit/', views.deposit_view, name='deposit'),
    path('swithdraw/', views.withdraw_view, name='withdraw'),
]