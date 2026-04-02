import traceback
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from datetime import datetime
from django.conf import settings

from account.models import User
from .utils import verify_otp, create_otp
from notification.email_utils import send_html_email

def login_verify_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('frontend:login')

    user = User.objects.filter(id=user_id).first()
    if not user:
        return redirect('frontend:login')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        if verify_otp(user, otp_input, otp_type='login'):
            auth_login(request, user)
            messages.success(request, "Logged in successfully via OTP.")
            return redirect('account:customer_dashboard')
        messages.error(request, "Invalid or expired OTP.")

    return render(request, 'otp/new/login_verify_otp.html', {"user": user})


def resend_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        messages.error(request, "Session expired. Please login again.")
        return redirect('account:login')

    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, "User not found. Please login again.")
        return redirect('account:login')

    try:
        otp_obj = create_otp(user, otp_type='login')
    except PermissionDenied:
        messages.error(
            request,
            "OTP resend limit reached. Please wait 10 minutes."
        )
        return redirect('otp:login_verify_otp')

    try:
        send_html_email(
            subject="Your Login OTP",
            to_email=[user.email],
            template_name="notification/emails/login_otp.html",
            context={
                    "user": user, 
                    "otp": otp_obj.code,
                    "site_name": settings.SITE_NAME,
                    "year": datetime.now().year,
                },
        )
        messages.success(request, "A new OTP has been sent to your email.")
    except Exception:
        print("\nEMAIL ERROR:")
        traceback.print_exc()
        print("\nLOGIN OTP (dev mode):", otp_obj.code)
        messages.info(request, f"OTP printed in console (dev): {otp_obj.code}")

    return redirect('otp:login_verify_otp')