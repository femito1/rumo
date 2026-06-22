from app.closing.period import Period


def test_period_parse_and_labels():
    p = Period.parse("2026-05")
    assert p.ano_mes == "2026-05"
    assert p.label == "Maio 2026"
    assert p.column_letter == "G"
    assert p.date_start == "2026-05-01"
    assert p.date_end == "2026-06-01"


def test_period_december_rolls_year():
    p = Period.parse("2026-12")
    assert p.date_end == "2027-01-01"
