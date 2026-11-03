"""Money helpers. All amounts are integer cents."""


def div_round_half_up(numerator: int, denominator: int) -> int:
    """Integer division rounded to the nearest whole number; exact halves round up (non-negative inputs)."""
    return (2 * numerator + denominator) // (2 * denominator)


def format_money(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"