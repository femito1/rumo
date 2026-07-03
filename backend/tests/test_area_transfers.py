# backend/tests/test_area_transfers.py
"""Cross-area recebimento transfers (Resumo_Recebidas overlay).

The SISJURI base per-area recebimento is auto-derived (CASO -> área jurídica).
On top of it, finance records manual reclassifications that move received cash
between areas (and commission splits). These are structured deltas, verified to
reproduce the workbook's per-area Receita rows for Fev 2026 exactly.
"""
import pytest

from app.manual.transfers import AreaTransfer, apply_to_base, net_deltas


def test_net_deltas_conserve_total():
    # A transfer moves value from origem to destino; the net over all areas is 0.
    transfers = [
        AreaTransfer("mbc", "2026-02", "Arbitragem", "Contencioso", 4362.575),
        AreaTransfer("mbc", "2026-02", "Arbitragem", "Contencioso", 1034.5535),
        AreaTransfer("mbc", "2026-02", "Arbitragem", "Econômico", 1034.5535),
    ]
    deltas = net_deltas(transfers)
    assert sum(deltas.values()) == pytest.approx(0.0, abs=0.01)
    assert deltas["Contencioso"] == pytest.approx(5397.1285, abs=0.01)
    assert deltas["Econômico"] == pytest.approx(1034.5535, abs=0.01)
    assert deltas["Arbitragem"] == pytest.approx(-6431.682, abs=0.01)


def test_apply_to_base_reproduces_workbook_feb():
    # SISJURI base (verified to the centavo) + Fev transfers == workbook Receita.
    base = {
        "Contencioso": 133202.74,
        "Econômico": 117626.71,
        "Arbitragem": 68404.13,
    }
    transfers = [
        AreaTransfer("mbc", "2026-02", "Arbitragem", "Contencioso", 4362.575),
        AreaTransfer("mbc", "2026-02", "Arbitragem", "Contencioso", 1034.5535),
        AreaTransfer("mbc", "2026-02", "Arbitragem", "Econômico", 1034.5535),
    ]
    result = apply_to_base(base, transfers)
    # Workbook G36/G54/G72 (using rounded 133203/117627/68404 base):
    assert result["Contencioso"] == pytest.approx(138599.87, abs=0.5)
    assert result["Econômico"] == pytest.approx(118661.26, abs=0.5)
    assert result["Arbitragem"] == pytest.approx(61972.45, abs=0.5)


def test_apply_to_base_is_noop_without_transfers():
    base = {"Contencioso": 100.0, "Econômico": 50.0, "Arbitragem": 25.0}
    assert apply_to_base(base, []) == base
