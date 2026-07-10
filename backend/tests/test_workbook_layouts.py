# backend/tests/test_workbook_layouts.py
"""Lock the verified account -> workbook-family map.

These rules were reconciled to the centavo against Fechamento MBC 02.2026 and
05.2026 via FINANCE.VW_RESULTADO_MENSAL_DET (docs/HANDOFF_DRE_AUTOMATION.md,
Appendix B). They are keyed on the stable numeric CONTA3 codes, so a label change
upstream must not move them. If one of these assertions fails, the DRE
institutional block no longer matches the workbook — treat it as a bug.
"""
from app.closing.workbook_layouts import (
    institutional_030_section,
    is_direct_team,
    match_area,
    section_for,
)


def test_ambiental_folds_into_arbitragem():
    # Client-confirmed (2026-07-10): Ambiental soma com Arbitragem (same area).
    assert match_area("Equipe Ambiental", "Arbitragem") is True
    assert match_area("Arbitragem e Compliance", "Arbitragem") is True
    assert match_area("Equipe Ambiental", "Contencioso") is False
    assert match_area("Equipe Ambiental", "Econômico") is False


def test_nao_alocados_is_never_an_area():
    # "Não Alocados" is its own recebimento line, not a workbook area.
    for area in ("Contencioso", "Econômico", "Arbitragem"):
        assert match_area("Não Alocados", area) is False


def test_area_matching_basics():
    assert match_area("Equipe Contencioso", "Contencioso") is True
    assert match_area("Equipe Direito Econômico", "Econômico") is True
    assert match_area("Equipe Contencioso", "Econômico") is False


def test_cursos_treinamento_030_carveout():
    # 030.010.0180 is lifted OUT of Custo equipe into Gestão do Conhecimento.
    assert not is_direct_team("030.010.0180")
    assert institutional_030_section("030.010.0180") == "Gestão do Conhecimento"
    # Ordinary 030.* stays team cost.
    assert is_direct_team("030.010.0010")
    assert institutional_030_section("030.010.0010") is None


def test_conta3_overrides_win_over_parent_name():
    # Serviços de Terceiros (020.040.*) is split three ways in the workbook.
    assert section_for("Serviços de Terceiros", "020.040.0010") == "Informática"
    assert section_for("Serviços de Terceiros", "020.040.0030") == "Despesas Gerais"
    assert section_for("Serviços de Terceiros", "020.040.0050") == "Consultoria"
    assert section_for("Serviços de Terceiros", "020.040.0060") == "Informática"
    # Seguros moves into Ocupação as "Seguro Locação".
    assert section_for("Administrativas", "020.060.0040") == "Ocupação"
    # Manut. e Conservação leaves Ocupação for Despesas Gerais.
    assert section_for("Ocupação", "020.010.0050") == "Despesas Gerais"
    # Vale Refeição / Transporte (Benefícios) fold into Salários Administração.
    assert section_for("Benefícios", "020.080.0050") == "Salários Administração"
    assert section_for("Benefícios", "020.080.0060") == "Salários Administração"
    # Relacionamento Institucional and Eventos e Happy Hour -> Endomarketing (05 book).
    assert section_for("Despesas Gerais", "020.030.0150") == "Endomarketing"
    assert section_for("Investimento em Prospecção", "020.090.0040") == "Endomarketing"
    # Associações/Assinaturas STAY in Administrativas (not pulled to Despesas Área).
    assert section_for("Administrativas", "020.060.0020") == "Administrativas"
    assert section_for("Administrativas", "020.060.0010") == "Administrativas"


def test_prefix_rules():
    assert section_for("Financeiras", "020.070.0030") == "Administrativas"
    assert section_for("Investimentos", "040.010.0090") == "Consultoria"
    assert section_for("Investimentos", "040.030.0010") == "Consultoria"
    assert section_for("Investimentos", "040.040.0030") == "Informática"
    assert section_for("Investimentos", "040.050.0010") == "Gestão do Conhecimento"


def test_parent_name_fallback_when_no_code_rule():
    # Ordinary 020.040 leaves with no CONTA3 override keep the parent map result.
    assert section_for("Serviços de Terceiros", "020.040.9999") == "Consultoria"
    assert section_for("Ocupação", "020.010.0010") == "Ocupação"
    assert section_for("Telecomunicações", "020.020.0030") == "Telecomunicações"


def test_missing_parent_defaults_to_despesas_gerais():
    assert section_for(None, None) == "Despesas Gerais"
    assert section_for("", None) == "Despesas Gerais"
