import pytest
from fastapi.testclient import TestClient

import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def fresh_state():
    app_module.reset_state()


def test_create_and_get_order():
    r = client.post("/orders", json={"items": [{"sku": "widget", "qty": 2}]})
    assert r.status_code == 200
    assert r.json()["pricing"]["total"] == 3724
    got = client.get("/orders/1")
    assert got.status_code == 200
    assert got.json()["status"] == "pending"


def test_out_of_stock_returns_409():
    r = client.post("/orders", json={"items": [{"sku": "gizmo", "qty": 3}]})
    assert r.status_code == 409


def test_unknown_sku_returns_400():
    r = client.post("/orders", json={"items": [{"sku": "nope", "qty": 1}]})
    assert r.status_code == 400


def test_cancel_unknown_order_returns_404():
    assert client.post("/orders/99/cancel").status_code == 404


def test_stock_endpoint():
    r = client.get("/stock/widget")
    assert r.status_code == 200
    assert r.json() == {"sku": "widget", "available": 10}