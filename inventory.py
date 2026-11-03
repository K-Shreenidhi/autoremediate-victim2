"""Stock reservations."""


class OutOfStock(Exception):
    pass


class Inventory:
    def __init__(self, stock: dict):
        self._stock = dict(stock)

    def available(self, sku: str) -> int:
        return self._stock.get(sku, 0)

    def reserve(self, sku: str, qty: int) -> None:
        if qty < 1:
            raise ValueError("qty must be at least 1")
        if self.available(sku) < qty:
            raise OutOfStock(f"{sku}: wanted {qty}, have {self.available(sku)}")
        self._stock[sku] -= qty

    def release(self, sku: str, qty: int) -> None:
        self._stock[sku] = self.available(sku) + qty