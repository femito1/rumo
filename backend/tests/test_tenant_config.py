# backend/tests/test_tenant_config.py
"""Per-client accounting shape (áreas, account overrides, rates).

The load-bearing property is the FIRST test: MBC's row carries an empty
``provider_config``, so the defaults must reproduce the hardcoded constants exactly.
Everything else in this file is about a second client actually being expressible.
"""
import pytest

from app.closing.workbook_layouts import AREAS, match_area, section_for
from app.tenancy.tenant_config import DEFAULT_TENANT, TenantConfig


def test_the_default_config_reproduces_MBC_exactly():
    """An empty provider_config must behave like the old constants — MBC's live row is
    exactly that, so any divergence here is a production change."""
    cfg = TenantConfig.from_provider_config({})
    assert cfg.area_labels == AREAS == ("Contencioso", "Econômico", "Arbitragem")
    assert cfg.account_overrides == {}
    assert cfg.amortizacao_mensal is None  # falls back to the worksheet default
    assert cfg.bonus_reserve_rate is None


@pytest.mark.parametrize(
    "grupo,expected",
    [
        # The real spellings SISJURI emits, including the dropped-space variants.
        ("Equipe Contencioso", "Contencioso"),
        ("EquipeContencioso", "Contencioso"),
        ("Equipe Direito Econômico", "Econômico"),
        ("EquipeDireito Econômico", "Econômico"),
        ("Equipe DireitoEconômico", "Econômico"),
        ("Arbitragem", "Arbitragem"),
        ("EquipeAmbiental", "Arbitragem"),  # client-confirmed: Ambiental → Arbitragem
        ("Compliance", "Arbitragem"),
    ],
)
def test_default_matching_agrees_with_the_old_function(grupo, expected):
    """Same answer as `match_area`, for every spelling seen in a live snapshot."""
    hits = [a for a in DEFAULT_TENANT.area_labels if DEFAULT_TENANT.match_area(grupo, a)]
    assert hits == [expected]
    assert [a for a in AREAS if match_area(grupo, a)] == [expected]


def test_a_grupo_must_resolve_to_exactly_one_area():
    """⚠ Three loops in dre.py ADD over every matching área, so an ambiguous name would
    book the same money twice. 'equipecontencioso' contains 'econ', which is why
    Econômico is anchored on 'econô'/'econo'."""
    for grupo in ("EquipeContencioso", "Equipe Contencioso", "equipecontencioso"):
        hits = [a for a in DEFAULT_TENANT.area_labels if DEFAULT_TENANT.match_area(grupo, a)]
        assert hits == ["Contencioso"], f"{grupo} matched {hits}"


def test_nao_alocados_is_never_an_area():
    for a in DEFAULT_TENANT.area_labels:
        assert DEFAULT_TENANT.match_area("Não Alocados", a) is False
        assert match_area("Não Alocados", a) is False


def test_a_second_client_can_declare_its_own_areas():
    cfg = TenantConfig.from_provider_config(
        {
            "areas": [
                {"label": "Tributário", "match": ["tribut", "fiscal"]},
                {"label": "Trabalhista", "match": ["trabalh"]},
            ]
        }
    )
    assert cfg.area_labels == ("Tributário", "Trabalhista")
    assert cfg.match_area("Equipe Fiscal", "Tributário") is True
    assert cfg.match_area("Equipe Trabalhista", "Trabalhista") is True
    # MBC's áreas mean nothing to this client.
    assert cfg.match_area("Equipe Contencioso", "Tributário") is False


def test_an_area_without_an_explicit_matcher_falls_back_to_its_label():
    """The simple case: a client whose grupo names already equal its área labels needs
    to type the label once, not twice."""
    cfg = TenantConfig.from_provider_config({"areas": [{"label": "Societário"}]})
    assert cfg.match_area("Equipe Societário", "Societário") is True
    assert cfg.match_area("Equipe Tributário", "Societário") is False


def test_account_overrides_layer_over_the_builtin_map():
    """A second client shares most of the SISJURI tree, so it names only its exceptions.
    Nothing is replaced wholesale — that would mean re-declaring hundreds of accounts."""
    cfg = TenantConfig.from_provider_config({"accounts": {"020.060.0040": "Administrativas"}})
    # The override wins for the named account...
    assert section_for("Seguros", "020.060.0040", cfg) == "Administrativas"
    # ...and MBC's default still applies to it without the override...
    assert section_for("Seguros", "020.060.0040", DEFAULT_TENANT) == "Ocupação"
    # ...while every other account is untouched by the override.
    assert section_for("Vale Refeição", "020.080.0050", cfg) == section_for(
        "Vale Refeição", "020.080.0050", DEFAULT_TENANT
    )


def test_rates_are_overridable_but_default_to_MBC():
    cfg = TenantConfig.from_provider_config(
        {"amortizacao_mensal": 1234.5, "bonus_reserve_rate": 0.15}
    )
    assert cfg.amortizacao_mensal == 1234.5
    assert cfg.bonus_reserve_rate == 0.15


def test_a_malformed_config_falls_back_instead_of_exploding():
    """provider_config is hand-edited JSON in a jsonb column. A typo must not take the
    closing down — it degrades to MBC's defaults."""
    for bad in ({"areas": "Contencioso"}, {"areas": []}, {"accounts": []},
                {"amortizacao_mensal": "oito mil"}, None):
        cfg = TenantConfig.from_provider_config(bad)
        assert cfg.area_labels == AREAS
        assert cfg.account_overrides == {}
