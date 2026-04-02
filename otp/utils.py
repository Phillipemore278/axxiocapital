import random
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import PermissionDenied

from .models import OTP

MAX_OTP_PER_WINDOW = 3
OTP_WINDOW_MINUTES = 10

def can_send_otp(user, otp_type):
    """
    Check if user can receive another OTP within the time window.
    """
    window_start = timezone.now() - timedelta(minutes=OTP_WINDOW_MINUTES)

    recent_count = OTP.objects.filter(
        user=user,
        otp_type=otp_type,
        created_at__gte=window_start
    ).count()

    return recent_count < MAX_OTP_PER_WINDOW

def generate_otp_code(length=6):
    """Generate a numeric OTP of given length."""
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

def create_otp(user, otp_type):
    if not can_send_otp(user, otp_type):
        raise PermissionDenied("OTP resend limit exceeded")
    
    # Invalidate previous unused OTPs
    OTP.objects.filter(
        user=user,
        otp_type=otp_type,
        is_used=False
    ).update(is_used=True)

    code = generate_otp_code()
    return OTP.objects.create(user=user, code=code, otp_type=otp_type)

def verify_otp(user, code, otp_type):
    """Verify OTP code, mark used if valid."""
    otp_obj = OTP.objects.filter(user=user, code=code, otp_type=otp_type, is_used=False).first()
    if not otp_obj or otp_obj.is_expired():
        return False
    otp_obj.mark_used()
    return True


