"""Daily sales report in the store's local time."""
from datetime import timedelta, timezone


def store_offset() -> timedelta:
    """Offset of the store's local time from UTC."""
    return timedelta(hours=5, minutes=30)


def local_date(created_at):
    return (created_at.astimezone(timezone.utc) + store_offset()).date()


def daily_report(orders: list) -> dict:
    """Order count and revenue (cents) per local date."""
    report = {}
    for order in orders:
        if order["status"] == "cancelled":
            continue
        key = local_date(order["created_at"]).isoformat()
        day = report.setdefault(key, {"orders": 0, "revenue_cents": 0})
        day["orders"] += 1
        day["revenue_cents"] += order["pricing"]["total"]
    return report