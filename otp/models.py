from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class OTP(models.Model):
    OTP_TYPE_CHOICES = [
        ('login', 'Login'),
        ('password_reset', 'Password Reset'),
        ('email_verify', 'Email Verification'),
        ('2fa', 'Two-Factor Auth'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=50, choices=OTP_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'otp_type']),
        ]

    def is_expired(self):
        expiry_minutes = {
            'login': 10,
            'password_reset': 15,
            'email_verify': 24*60,
            '2fa': 5,
        }.get(self.otp_type, 10)
        return timezone.now() > self.created_at + timezone.timedelta(minutes=expiry_minutes)

    def mark_used(self):
        self.is_used = True
        self.save()

    # def mark_used(self):
    #     self.delete()

    def __str__(self):
        return f"{self.otp_type.upper()} OTP for {self.user.email}"
