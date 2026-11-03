from pricing import discount_cents, price_order, shipping_cents, tax_cents


def lines(unit_cents, qty=1):
    return [{"sku": "widget", "unit_cents": unit_cents, "qty": qty}]


def test_price_without_coupon():
    # subtotal 3000, tax 7.5 percent = 225, shipping 499
    assert price_order(lines(3000)) == {
        "subtotal": 3000, "discount": 0, "tax": 225, "shipping": 499, "total": 3724,
    }


def test_coupon_discount_applies_before_tax():
    # subtotal 10000, SAVE10 -> discount 1000, discounted 9000, tax 675, free shipping
    assert price_order(lines(10000), "SAVE10") == {
        "subtotal": 10000, "discount": 1000, "tax": 675, "shipping": 0, "total": 9675,
    }


def test_unknown_coupon_is_ignored():
    assert price_order(lines(3000), "BOGUS")["discount"] == 0


def test_free_shipping_at_threshold():
    assert shipping_cents(5000) == 0
    assert shipping_cents(4999) == 499
    assert shipping_cents(5001) == 0


def test_discount_rounds_half_up():
    # 10 percent of 105 cents is 10.5, which rounds up to 11
    assert discount_cents(105, "SAVE10") == 11
    assert discount_cents(104, "SAVE10") == 10


def test_tax_rounds_half_up():
    # 7.5 percent of 20 cents is 1.5, which rounds up to 2
    assert tax_cents(20) == 2
    assert tax_cents(19) == 1