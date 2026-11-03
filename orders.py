"""Order lifecycle: create, ship, cancel."""
import itertools
from datetime import datetime, timezone

from inventory import Inventory, OutOfStock
from pricing import price_order

CATALOG = {"widget": 1500, "gadget": 2500, "gizmo": 4000, "gasket": 1295}  # unit price in cents


class OrderError(Exception):
    pass


class OrderBook:
    def __init__(self, inventory: Inventory):
        self.inventory = inventory
        self.orders = {}
        self._ids = itertools.count(1)

    def create(self, items: list, code=None, created_at=None) -> dict:
        """items: [{"sku": str, "qty": int}]"""
        if not items:
            raise OrderError("an order needs at least one item")
        lines = []
        for item in items:
            if item["sku"] not in CATALOG:
                raise OrderError(f"unknown sku: {item['sku']}")
            lines.append({"sku": item["sku"], "unit_cents": CATALOG[item["sku"]], "qty": item["qty"]})
        reserved = []
        try:
            for line in lines:
                self.inventory.reserve(line["sku"], line["qty"])
                reserved.append(line)
        except (OutOfStock, ValueError):
            for done in reserved:
                self.inventory.release(done["sku"], done["qty"])
            raise
        stamp = created_at or datetime.now(timezone.utc)
        order = {
            "id": next(self._ids),
            "status": "pending",
            "lines": lines,
            "code": code,
            "pricing": price_order(lines, code),
            "created_at": stamp,
        }
        self.orders[order["id"]] = order
        return order

    def ship(self, order_id: int) -> dict:
        order = self.orders.get(order_id)
        if order is None:
            raise OrderError(f"order {order_id} not found")
        if order["status"] == "pending":
            order["status"] = "shipped"
            return order
        raise OrderError(f"order {order_id} is {order['status']} and cannot be shipped")

    def cancel(self, order_id: int) -> dict:
        order = self.orders.get(order_id)
        if order is None:
            raise OrderError(f"order {order_id} not found")
        if order["status"] != "pending":
            raise OrderError(f"order {order_id} is {order['status']} and cannot be cancelled")
        for line in order["lines"]:
            self.inventory.release(line["sku"], line["qty"])
        order["status"] = "cancelled"
        order["refund_cents"] = order["pricing"]["total"]
        return order