"""HTTP API for the billing service."""
import json
import logging
import os
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from inventory import Inventory, OutOfStock
from orders import OrderBook, OrderError
from reports import daily_report


class JsonFmt(logging.Formatter):
    def format(self, record):
        data = {
            "ts": round(time.time(), 3),
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        data.update(getattr(record, "ctx", {}))
        if record.exc_info:
            data["trace"] = self.formatException(record.exc_info)
        return json.dumps(data)


log = logging.getLogger("billing")
log.setLevel(logging.INFO)
_handler = logging.FileHandler(os.getenv("LOG_FILE", "logs.jsonl"), encoding="utf-8")
_handler.setFormatter(JsonFmt())
log.addHandler(_handler)

app = FastAPI()
INITIAL_STOCK = {"widget": 10, "gadget": 5, "gizmo": 2, "gasket": 20}
BOOK = OrderBook(Inventory(INITIAL_STOCK))


def reset_state():
    global BOOK
    BOOK = OrderBook(Inventory(INITIAL_STOCK))


class Item(BaseModel):
    sku: str
    qty: int


class NewOrder(BaseModel):
    items: list[Item]
    code: str | None = None


@app.middleware("http")
async def trace(request: Request, call_next):
    rid = uuid.uuid4().hex[:8]
    try:
        resp = await call_next(request)
    except Exception:
        log.exception(
            "unhandled exception",
            extra={"ctx": {"request_id": rid, "method": request.method, "path": request.url.path}},
        )
        return JSONResponse({"error": "internal"}, status_code=500)
    log.info(
        "request",
        extra={"ctx": {"request_id": rid, "method": request.method, "path": request.url.path, "status": resp.status_code}},
    )
    return resp


@app.post("/orders")
def create_order(body: NewOrder):
    items = [i.model_dump() for i in body.items]
    try:
        order = BOOK.create(items, body.code)
    except OutOfStock as e:
        log.warning("order_rejected", extra={"ctx": {"reason": str(e), "items": items}})
        raise HTTPException(409, str(e))
    except OrderError as e:
        raise HTTPException(400, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    log.info(
        "order_created",
        extra={"ctx": {
            "order_id": order["id"],
            "code": body.code,
            "pricing": order["pricing"],
            "stock_after": {line["sku"]: BOOK.inventory.available(line["sku"]) for line in order["lines"]},
        }},
    )
    return order


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    order = BOOK.orders.get(order_id)
    if order is None:
        raise HTTPException(404, f"order {order_id} not found")
    return order


@app.post("/orders/{order_id}/ship")
def ship_order(order_id: int):
    try:
        order = BOOK.ship(order_id)
    except OrderError as e:
        raise HTTPException(404 if "not found" in str(e) else 409, str(e))
    log.info("order_shipped", extra={"ctx": {"order_id": order_id}})
    return order


@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int):
    before = BOOK.orders.get(order_id, {}).get("status")
    try:
        order = BOOK.cancel(order_id)
    except OrderError as e:
        raise HTTPException(404 if "not found" in str(e) else 409, str(e))
    skus = sorted({line["sku"] for line in order["lines"]})
    log.info(
        "order_cancelled",
        extra={"ctx": {
            "order_id": order_id,
            "status_before": before,
            "refund_cents": order["refund_cents"],
            "units": sum(line["qty"] for line in order["lines"]),
            "stock_after": {sku: BOOK.inventory.available(sku) for sku in skus},
        }},
    )
    return order


@app.get("/stock/{sku}")
def stock(sku: str):
    available = BOOK.inventory.available(sku)
    log.info("stock_query", extra={"ctx": {"sku": sku, "available": available}})
    return {"sku": sku, "available": available}


@app.get("/reports/daily")
def report():
    orders = list(BOOK.orders.values())
    result = daily_report(orders)
    log.info(
        "daily_report",
        extra={"ctx": {
            "days": sorted(result),
            "report_orders": sum(day["orders"] for day in result.values()),
            "book_orders": len(orders),
            "book_cancelled": sum(1 for o in orders if o["status"] == "cancelled"),
        }},
    )
    return result