from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import calendar


def distribute_percentage_by_month(total_percentage, start_date, end_date):
    total_percentage = Decimal(str(total_percentage))
    total_days = (end_date - start_date).days + 1
    daily_percent = total_percentage / Decimal(total_days)

    results = []
    cumulative = Decimal("0")
    current = start_date

    while current <= end_date:
        year = current.year
        month = current.month

        month_start = date(year, month, 1)
        month_end = date(year, month, calendar.monthrange(year, month)[1])

        period_start = max(start_date, month_start)
        period_end = min(end_date, month_end)

        days = (period_end - period_start).days + 1

        monthly_percent = (daily_percent * days).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        cumulative += monthly_percent

        results.append({
            "year": year,
            "month": month,
            "days": days,
            "percent": monthly_percent,
            "cumulative": cumulative
        })

        current = month_end + timedelta(days=1)

    return results