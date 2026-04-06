from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    nick_name = models.CharField(max_length=255)

    # Address fields
    address = models.TextField(null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    zipcode = models.CharField(max_length=20, null=True, blank=True)

    # Withdraw status choices
    WITHDRAW_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failing', 'Failing'),
    ]

    withdraw_status = models.CharField(
        max_length=10,
        choices=WITHDRAW_STATUS_CHOICES,
        default='pending'
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    def __str__(self):
        return self.email
    

class KYC(models.Model):
    # --------------------
    # Status choices
    # --------------------
    STATUS_NOT_SUBMITTED = 'NOT_SUBMITTED'
    STATUS_PENDING = 'PENDING'
    STATUS_VERIFIED = 'VERIFIED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (STATUS_NOT_SUBMITTED, 'Not Submitted'),
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    # --------------------
    # Relations
    # --------------------
    portfolio = models.OneToOneField(
        'customer.Portfolio',
        on_delete=models.CASCADE,
        related_name='kyc'
    )

    # --------------------
    # Personal Information
    # --------------------
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)

    # --------------------
    # Identity Document
    # --------------------
    DOCUMENT_PASSPORT = 'PASSPORT'
    DOCUMENT_NATIONAL_ID = 'NATIONAL_ID'
    DOCUMENT_DRIVER_LICENSE = 'DRIVERS_LICENSE'

    DOCUMENT_TYPE_CHOICES = [
        (DOCUMENT_PASSPORT, 'Passport'),
        (DOCUMENT_NATIONAL_ID, 'National ID'),
        (DOCUMENT_DRIVER_LICENSE, "Driver’s License"),
    ]

    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
        null=True,
        blank=True
    )
    document_number = models.CharField(max_length=100, null=True, blank=True)
    document_image = models.ImageField(
        upload_to='kyc/documents/',
        null=True,
        blank=True
    )

    # --------------------
    # Proof of Address
    # --------------------
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    address_proof = models.ImageField(
        upload_to='kyc/address/',
        null=True,
        blank=True
    )

    # --------------------
    # KYC Status
    # --------------------
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NOT_SUBMITTED
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --------------------
    # Helpers
    # --------------------
    def __str__(self):
        return f"KYC ({self.get_status_display()}) - {self.portfolio.user.email}"

    @property
    def is_verified(self):
        return self.status == self.STATUS_VERIFIED