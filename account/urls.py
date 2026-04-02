from django.urls import path
from . import views

app_name = 'account'
urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('account-created/', views.account_created_view, name='account_created'),
    path("verify-email/<uidb64>/<token>/", views.verify_email,
        name="verify_email",),
        path('resend-verification/', views.resend_verification_view, name='resend_verification'),
    path('login/', views.EmailLoginView.as_view(), name='login'),
]