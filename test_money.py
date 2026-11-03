from money import div_round_half_up, format_money


def test_div_round_half_up():
    assert div_round_half_up(14, 10) == 1
    assert div_round_half_up(15, 10) == 2
    assert div_round_half_up(16, 10) == 2
    assert div_round_half_up(0, 100) == 0


def test_format_money():
    assert format_money(1999) == "19.99"
    assert format_money(5) == "0.05"
    assert format_money(-250) == "-2.50"