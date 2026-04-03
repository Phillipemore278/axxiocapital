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
]