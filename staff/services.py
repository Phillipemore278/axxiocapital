# app/services.py
from decimal import Decimal, ROUND_HALF_EVEN
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from plan.models import OrderPlan, OrderPlanItem, TransactionLog

def create_manual_snapshot(order_id, percent, actor=None, reason=None):
    """
    Create a new OrderPlanItem with given percent (positive or negative).
    """
    snapshot_date = timezone.now()
    

    with transaction.atomic():
        order = OrderPlan.objects.select_for_update().get(pk=order_id)
        before_value = order.current_value

        delta = (order.principal_amount * (percent / Decimal('100'))).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_EVEN
        )

        item = OrderPlanItem.objects.create(
            order_plan=order,
            snapshot_at=snapshot_date,
            delta_amount=delta,
            percent_applied=percent,
        )

        # recompute cumulative
        total_delta = order.items.aggregate(total=Sum('delta_amount'))['total'] or Decimal('0.00')
        cumulative = (order.principal_amount + total_delta).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        item.cumulative_amount = cumulative
        item.save(update_fields=['cumulative_amount'])

        order.current_value = cumulative
        order.save(update_fields=['current_value'])

        TransactionLog.objects.create(
            order_plan=order,
            before_value=before_value,
            change_amount=delta,
            after_value=order.current_value,
            reason=reason or f"Manual snapshot ({percent}%)",
            created_by=actor
        )

    return item
