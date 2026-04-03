from django.urls import path

from . import views

app_name = 'customer'

urlpatterns = [
    path('dashboard/', views.customer_dashboard_view, name='customer_dashboard'),
    path('active-plans/', views.active_plan_list_view, name='active_plan_list'),
    path('plan-list/', views.all_plans_view, name='all_plans'),
    path('settings-and-security/', views.settings_security, name='settings_security'),
    path('wallet/', views.wallet_view, name='wallet'),
    
]