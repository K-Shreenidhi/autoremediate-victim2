import pytest

from inventory import Inventory, OutOfStock
from orders import OrderBook, OrderError


def make_book():
    return OrderBook(Inventory({"widget": 10, "gadget": 5, "gizmo": 2, "gasket": 20}))


def test_create_reserves_stock():
    book = make_book()
    order = book.create([{"sku": "widget", "qty": 3}])
    assert order["status"] == "pending"
    assert order["pricing"]["subtotal"] == 4500
    assert book.inventory.available("widget") == 7


def test_create_sets_created_at():
    order = make_book().create([{"sku": "widget", "qty": 1}])
    assert order["created_at"] is not None


def test_unknown_sku_is_rejected():
    with pytest.raises(OrderError):
        make_book().create([{"sku": "nope", "qty": 1}])


def test_failed_order_does_not_leak_stock():
    book = make_book()
    with pytest.raises(OutOfStock):
        book.create([{"sku": "widget", "qty": 2}, {"sku": "gizmo", "qty": 3}])  # only 2 gizmos exist
    assert book.inventory.available("widget") == 10
    assert book.inventory.available("gizmo") == 2


def test_cancel_returns_every_unit_to_stock():
    book = make_book()
    order = book.create([{"sku": "widget", "qty": 4}])
    book.cancel(order["id"])
    assert book.inventory.available("widget") == 10


def test_cancel_refunds_what_was_paid():
    book = make_book()
    order = book.create([{"sku": "widget", "qty": 1}])
    cancelled = book.cancel(order["id"])
    assert cancelled["status"] == "cancelled"
    assert cancelled["refund_cents"] == order["pricing"]["total"]


def test_cannot_cancel_a_shipped_order():
    book = make_book()
    order = book.create([{"sku": "widget", "qty": 1}])
    book.ship(order["id"])
    with pytest.raises(OrderError):
        book.cancel(order["id"])
    assert book.orders[order["id"]]["status"] == "shipped"


def test_cannot_cancel_twice():
    book = make_book()
    order = book.create([{"sku": "widget", "qty": 1}])
    book.cancel(order["id"])
    with pytest.raises(OrderError):
        book.cancel(order["id"])


def test_cancel_unknown_order():
    with pytest.raises(OrderError):
        make_book().cancel(999)