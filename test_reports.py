from datetime import datetime, timezone

from reports import daily_report, local_date


def order(created_at, total=1000, status="pending"):
    return {"status": status, "created_at": created_at, "pricing": {"total": total}}


def utc(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


def test_order_after_local_midnight_belongs_to_next_day():
    # 18:45 UTC is 00:15 the next morning in the store's local time
    assert local_date(utc(2026, 1, 1, 18, 45)).isoformat() == "2026-01-02"


def test_order_before_local_midnight_stays_on_the_same_day():
    assert local_date(utc(2026, 1, 1, 18, 25)).isoformat() == "2026-01-01"


def test_daily_report_totals_per_local_day():
    orders = [
        order(utc(2026, 1, 1, 10, 0), 1000),
        order(utc(2026, 1, 1, 11, 0), 500),
        order(utc(2026, 1, 1, 19, 0), 700),
    ]
    assert daily_report(orders) == {
        "2026-01-01": {"orders": 2, "revenue_cents": 1500},
        "2026-01-02": {"orders": 1, "revenue_cents": 700},
    }


def test_cancelled_orders_are_not_counted():
    orders = [
        order(utc(2026, 1, 1, 10, 0), 1000),
        order(utc(2026, 1, 1, 10, 5), 900, status="cancelled"),
    ]
    assert daily_report(orders) == {"2026-01-01": {"orders": 1, "revenue_cents": 1000}}