"""Replays a scripted traffic scenario against the billing app, in-process.

Usage: python traffic.py inc_201
Logs go to the file named by the LOG_FILE environment variable.
"""
import sys
from datetime import datetime, timezone

from fastapi.testclient import TestClient

import app as app_module


def order(c, items, code=None):
    return c.post("/orders", json={"items": items, "code": code})


def inc_201(c):
    order(c, [{"sku": "gizmo", "qty": 1}, {"sku": "gadget", "qty": 2}], "SAVE10")
    order(c, [{"sku": "widget", "qty": 1}])


def inc_202(c):
    order(c, [{"sku": "gadget", "qty": 2}])
    order(c, [{"sku": "widget", "qty": 3}])


def inc_203(c):
    order(c, [{"sku": "gasket", "qty": 1}], "SAVE10")
    order(c, [{"sku": "gasket", "qty": 3}], "SAVE10")


def inc_204(c):
    c.get("/stock/gizmo")
    order(c, [{"sku": "gizmo", "qty": 2}])
    order(c, [{"sku": "gizmo", "qty": 1}])


def inc_205(c):
    c.get("/stock/widget")
    order(c, [{"sku": "widget", "qty": 4}])
    c.post("/orders/1/cancel")
    c.get("/stock/widget")


def inc_206(c):
    order(c, [{"sku": "widget", "qty": 2}, {"sku": "gizmo", "qty": 3}])
    c.get("/stock/widget")
    c.get("/stock/gizmo")
    order(c, [{"sku": "widget", "qty": 1}])


def inc_207(c):
    order(c, [{"sku": "widget", "qty": 1}])
    order(c, [{"sku": "gadget", "qty": 1}])
    c.post("/orders/2/cancel")
    c.get("/reports/daily")


def inc_208(c):
    order(c, [{"sku": "widget", "qty": 1}])
    c.get("/reports/daily")


def inc_209(c):
    app_module.BOOK.create([{"sku": "widget", "qty": 1}], created_at=datetime(2026, 1, 1, 18, 45, tzinfo=timezone.utc))
    app_module.BOOK.create([{"sku": "gadget", "qty": 1}], created_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc))
    c.get("/reports/daily")


def inc_210(c):
    order(c, [{"sku": "widget", "qty": 1}])
    c.post("/orders/1/ship")
    c.post("/orders/1/cancel")


SCENARIOS = {f.__name__: f for f in (inc_201, inc_202, inc_203, inc_204, inc_205,
                                     inc_206, inc_207, inc_208, inc_209, inc_210)}

if __name__ == "__main__":
    name = sys.argv[1]
    app_module.reset_state()
    SCENARIOS[name](TestClient(app_module.app))
    print(f"replayed {name}")