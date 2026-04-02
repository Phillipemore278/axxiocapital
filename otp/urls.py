from django.urls import path
from . import views

app_name = 'otp'

urlpatterns = [
    path('login-verify/', views.login_verify_otp_view, name='login_verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
]
