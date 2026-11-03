"""Pricing rules. All amounts are integer cents."""
from money import div_round_half_up

TAX_RATE_BP = 750  # basis points: 7.5 percent
SHIPPING_CENTS = 499
FREE_SHIPPING_FROM = 5000
COUPONS = {"SAVE10": 10, "SAVE20": 20}  # percent off the subtotal


def line_total(unit_cents: int, qty: int) -> int:
    return unit_cents * qty


def discount_cents(subtotal: int, code) -> int:
    pct = COUPONS.get(code or "", 0)
    return div_round_half_up(subtotal * pct, 100)


def tax_cents(taxable: int) -> int:
    return div_round_half_up(taxable * TAX_RATE_BP, 10000)


def shipping_cents(discounted_subtotal: int) -> int:
    return 0 if discounted_subtotal >= FREE_SHIPPING_FROM else SHIPPING_CENTS


def price_order(lines: list, code=None) -> dict:
    """lines: [{"sku": str, "unit_cents": int, "qty": int}]. Every component of the price, in cents."""
    subtotal = sum(line_total(line["unit_cents"], line["qty"]) for line in lines)
    discount = discount_cents(subtotal, code)
    discounted = subtotal - discount
    tax = tax_cents(discounted)
    shipping = shipping_cents(discounted)
    return {
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "shipping": shipping,
        "total": discounted + tax + shipping,
    }