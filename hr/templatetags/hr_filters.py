from django import template
from datetime import date

register = template.Library()


@register.filter
def months_since(date_value):
    """Calculate the number of months between a given date and today."""
    if not date_value:
        return 0
    today = date.today()
    months = (today.year - date_value.year) * 12 + (today.month - date_value.month)
    return months


@register.filter
def clearance_alert_needed(separation_record):
    """Check if clearance alert is needed (3+ months since leaving and clearance pending)."""
    if not separation_record or not separation_record.last_working_date:
        return False
    if separation_record.clearance_status == 'completed':
        return False
    months = months_since(separation_record.last_working_date)
    return months >= 3
