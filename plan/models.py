# app/models.py
from decimal import Decimal, ROUND_HALF_EVEN
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from datetime import timedelta

class Plan(models.Model):

    class PlanType(models.TextChoices):
        REGULAR = "REGULAR", "Regular"
        GOLD = "GOLD", "Gold"
        DIAMOND = "DIAMOND", "Diamond"
        PLATINIUM = "PLATINIUM", "Platinium"

    name = models.CharField(max_length=200)

    plantype = models.CharField(
        max_length=30,
        choices=PlanType.choices,
        default=PlanType.REGULAR
    )

    percent_increment = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        help_text="Daily percent (e.g., 0.5000 for 0.5%)"
    )

    duration_days = models.PositiveIntegerField(null=True, blank=True)

    min_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )

    short_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="A brief summary of the product (max 255 characters)."
    )
    long_description = models.TextField(
        blank=True,
        null=True,
        help_text="A detailed description of the product."
    )

    # image = models.ImageField(
    #     upload_to="plan_img/",
    #     blank=True,
    #     null=True
    # )

    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_plantype_display()} ({self.percent_increment}%)"

class OrderPlan(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_PAUSED, 'Paused'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    portfolio = models.ForeignKey('customer.Portfolio', on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    principal_amount = models.DecimalField(max_digits=20, decimal_places=2)
    current_value = models.DecimalField(max_digits=20, decimal_places=2)
    start_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    is_mirrowed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'start_at']),
        ]

    def __str__(self):
        return f"OrderPlan #{self.pk} - {self.portfolio.user} - {self.plan.name}"

    def recompute_current_value(self):
        """Recompute current_value as principal + sum of all delta_amounts from items."""
        total_delta = self.items.aggregate(total=models.Sum('delta_amount'))['total'] or Decimal('0.00')
        new_value = (self.principal_amount + total_delta).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        self.current_value = new_value
        self.save(update_fields=['current_value'])
        return self.current_value
    
    def get_pnl(self):
        """
        Profit & Loss = current_value - principal_amount
        """
        pnl = (self.current_value - self.principal_amount).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_EVEN
        )
        return pnl

    def get_roi(self):
        """
        ROI (%) = (PnL / principal_amount) * 100
        """
        if self.principal_amount == 0:
            return Decimal('0.00')

        roi = ((self.current_value - self.principal_amount) / self.principal_amount) * Decimal('100')
        return roi.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
    
    @property
    def progress_percent(self):
        if not self.plan.duration_days:
            return 0

        start = self.start_at
        end = start + timedelta(days=self.plan.duration_days)
        now = timezone.now()

        total_duration = (end - start).total_seconds()
        elapsed = (now - start).total_seconds()

        progress = (elapsed / total_duration) * 100 if total_duration > 0 else 0
        progress = max(0, min(progress, 100))

        return round(progress)
    
    @property
    def end_date(self):
        if not self.plan.duration_days:
            return None
        return self.start_at + timedelta(days=self.plan.duration_days)
    
    @property
    def days_remaining(self):
        if not self.plan.duration_days:
            return 0

        end = self.start_at + timedelta(days=self.plan.duration_days)
        remaining = end - timezone.now()
        return max(remaining.days, 0)


class OrderPlanItem(models.Model):
    order_plan = models.ForeignKey(OrderPlan, on_delete=models.CASCADE, related_name='items')
    snapshot_at = models.DateTimeField()
    delta_amount = models.DecimalField(max_digits=20, decimal_places=2)
    percent_applied = models.DecimalField(max_digits=6, decimal_places=4)
    cumulative_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # unique_together = ('order_plan', 'snapshot_at')
        indexes = [
            models.Index(fields=['order_plan', 'snapshot_at']),
        ]

    def __str__(self):
        return f"Snapshot {self.snapshot_at} for OrderPlan {self.order_plan_id}"


class TransactionLog(models.Model):
    order_plan = models.ForeignKey(OrderPlan, on_delete=models.CASCADE, related_name='transactions')
    before_value = models.DecimalField(max_digits=20, decimal_places=2)
    change_amount = models.DecimalField(max_digits=20, decimal_places=2)
    after_value = models.DecimalField(max_digits=20, decimal_places=2)
    reason = models.CharField(max_length=255)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['order_plan', 'created_at']),
        ]

    def __str__(self):
        return f"Txn for OrderPlan {self.order_plan_id} at {self.created_at}"
