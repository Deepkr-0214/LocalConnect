from datetime import date, timedelta
from django.db.models import Sum, Avg
from core.models import Order


class DjangoOrderFilters:
    """Centralized order filtering logic for financial calculations using Django ORM."""

    COMPLETED_STATUS = 'Completed'

    @staticmethod
    def calculate_total_earnings(vendor_id):
        result = Order.objects.filter(
            vendor_id=vendor_id,
            status=DjangoOrderFilters.COMPLETED_STATUS
        ).aggregate(total=Sum('total'))['total']
        return float(result) if result else 0.0

    @staticmethod
    def calculate_today_earnings(vendor_id):
        today = date.today()
        result = Order.objects.filter(
            vendor_id=vendor_id,
            status=DjangoOrderFilters.COMPLETED_STATUS,
            created_at__date=today
        ).aggregate(total=Sum('total'))['total']
        return float(result) if result else 0.0

    @staticmethod
    def calculate_week_earnings(vendor_id):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        result = Order.objects.filter(
            vendor_id=vendor_id,
            status=DjangoOrderFilters.COMPLETED_STATUS,
            created_at__date__gte=week_start
        ).aggregate(total=Sum('total'))['total']
        return float(result) if result else 0.0

    @staticmethod
    def calculate_month_earnings(vendor_id):
        today = date.today()
        month_start = today.replace(day=1)
        result = Order.objects.filter(
            vendor_id=vendor_id,
            status=DjangoOrderFilters.COMPLETED_STATUS,
            created_at__date__gte=month_start
        ).aggregate(total=Sum('total'))['total']
        return float(result) if result else 0.0

    @staticmethod
    def get_completed_orders_count(vendor_id):
        return Order.objects.filter(
            vendor_id=vendor_id,
            status=DjangoOrderFilters.COMPLETED_STATUS
        ).count()

    @staticmethod
    def calculate_average_order_value(vendor_id):
        result = Order.objects.filter(
            vendor_id=vendor_id,
            status=DjangoOrderFilters.COMPLETED_STATUS
        ).aggregate(avg=Avg('total'))['avg']
        return float(result) if result else 0.0

    @staticmethod
    def get_earnings_chart_data(vendor_id, days=7):
        today = date.today()
        chart_labels = []
        chart_values = []

        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            chart_labels.append(day.strftime('%d %b'))

            day_earnings = Order.objects.filter(
                vendor_id=vendor_id,
                status=DjangoOrderFilters.COMPLETED_STATUS,
                created_at__date=day
            ).aggregate(total=Sum('total'))['total']
            chart_values.append(float(day_earnings) if day_earnings else 0.0)

        return chart_labels, chart_values
