from django.urls import path

from . import views

app_name = 'account'

urlpatterns = [
    path('dashboard/', views.customer_dashboard_view, name='customer_dashboard'),
    
]