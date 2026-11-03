import pytest

from inventory import Inventory, OutOfStock


def test_reserve_reduces_stock():
    inv = Inventory({"widget": 5})
    inv.reserve("widget", 2)
    assert inv.available("widget") == 3


def test_can_reserve_the_exact_remaining_stock():
    inv = Inventory({"widget": 3})
    inv.reserve("widget", 3)
    assert inv.available("widget") == 0


def test_cannot_reserve_more_than_available():
    inv = Inventory({"widget": 3})
    with pytest.raises(OutOfStock):
        inv.reserve("widget", 4)
    assert inv.available("widget") == 3


def test_release_returns_stock():
    inv = Inventory({"widget": 1})
    inv.release("widget", 4)
    assert inv.available("widget") == 5