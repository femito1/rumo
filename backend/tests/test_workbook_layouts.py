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
    is_comissao_account,
    is_direct_team,
    is_imposto,
    match_area,
    section_for,
)


def test_comissao_not_misread_as_imposto():
    # "Participação Interna (comissões)" must NOT match the tax filter just because
    # "iss" is a substring of "comissões". Comissão is derived separately
    # (comissao_deriv), so it must be excluded from both the imposto and the
    # institutional-expense classification.
    row = {
        "nome_conta": "Participação Interna (comissões)",
        "nome_conta_pai": "Custos com Pessoal Técnico",
        "id_conta": "030.010.0120",
    }
    assert is_imposto(row) is False
    assert is_comissao_account("030.010.0120") is True
    assert is_comissao_account("030.010.0080") is True
    assert is_comissao_account("020.110.0010") is True
    assert is_comissao_account("030.010.0010") is False


def test_imposto_still_matches_real_taxes():
    assert is_imposto({"nome_conta": "ISS", "nome_conta_pai": "Impostos"}) is True
    assert is_imposto({"nome_conta": "INSS - Jurídico", "nome_conta_pai": "x"}) is True
    assert is_imposto({"nome_conta": "PIS", "nome_conta_pai": "Impostos"}) is True


def test_iss_juridico_is_team_cost_not_imposto():
    # 030.010.0160 "ISS" (jurídico, TRIMESTRAL) is booked by the workbook INSIDE
    # per-area Custo equipe ("ISS Trimestral", Base_Resultado rows 25/54/79), NOT
    # in the Impostos block. It posts only at quarter-ends (Jan/Apr/Jul/Oct), so
    # May — the reconciliation month — was zero and never exercised this path.
    # It must be treated as team cost, never as a tax (which would drop it, since
    # the DRE Imposto line is 15% of recebimento, not a sum of tax accounts).
    row = {
        "nome_conta": "ISS",
        "nome_conta_pai": "Custos com Pessoal Técnico",
        "id_conta": "030.010.0160",
    }
    assert is_imposto(row) is False
    assert is_direct_team("030.010.0160") is True
    assert institutional_030_section("030.010.0160") is None
    # The FGTS-ADM reclass and real 050/300 taxes are unaffected.
    assert is_imposto({"nome_conta": "FGTS", "id_conta": "020.050.0060"}) is True


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


def test_whitespace_variant_grupo_names_match_exactly_one_area():
    """SISJURI emits the SAME grupo with inconsistent spacing (observed live in the
    2026 Jan–Jun snapshots): ``EquipeContencioso`` (m2), ``Equipe DireitoEconômico``
    (m4/m5), ``EquipeDireito Econômico`` (m5), ``EquipeAmbiental`` (m5).

    ``EquipeContencioso`` is the dangerous one: dropping the space splices an
    ``"econ"`` out of ``"equipE-CONtencioso"``, so the old substring test matched
    BOTH Contencioso and Econômico. ``_grupo_to_area`` takes the first hit in
    ``AREAS`` and only landed right because Contencioso happens to precede
    Econômico in that tuple — but ``dre.py`` has three loops that ADD over every
    matching area, so an ambiguous name is double-counted into two áreas there.
    That is exactly the cross-área leak shape the client suspected, so pin it:
    every name must resolve to exactly ONE área.
    """
    variants = {
        "EquipeContencioso": "Contencioso",
        "Equipe Contencioso": "Contencioso",
        "Equipe DireitoEconômico": "Econômico",
        "EquipeDireito Econômico": "Econômico",
        "Equipe Direito Econômico": "Econômico",
        "EquipeAmbiental": "Arbitragem",
        "Equipe Ambiental": "Arbitragem",
    }
    for name, expected in variants.items():
        hits = [a for a in ("Contencioso", "Econômico", "Arbitragem") if match_area(name, a)]
        assert hits == [expected], f"{name!r} matched {hits}, expected exactly [{expected!r}]"


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


def test_investimentos_040_030_is_mapped_per_account_not_by_prefix():
    """``040.030.*`` is a MIXED bucket — only ``0010`` is Consultoria.

    A blanket ``040.030.`` → Consultoria prefix rule sent June's 429,00 "Móveis e
    Utensílios" (a pressure washer) into Consultoria Adm. e Financeira. The plano de
    contas has three children under 040.030.0000 "Investimentos":
        0010 Consultoria        → Consultoria (workbook H111, 14.705,80 ✓)
        0020 Móveis e Utensílios → Despesas Gerais, as "Material de Escritório"
                                   (workbook H105 = 468,40, of which 429,00 is this)
        0030 Reforma            → Despesas Gerais ("Manutenção do Escritório")

    Renata (2026-07-29) on 0020: "não tinha uma categoria específica então a gente
    entendeu que era material de escritório. Sendo um bem de escritório é uma despesa
    institucional que seria rateada, não de uma área específica." And on 0030:
    "Manutenção de escritório despesas gerais" — while noting the manutenção-vs-
    melhoria line is genuinely thin ("uma reforma de melhora é um investimento"), to
    be settled with Adriana. Both stay INSIDE Despesa Institucional either way, so
    they are rateized; only the family label is at stake.
    """
    assert section_for("Investimentos", "040.030.0010") == "Consultoria"
    assert section_for("Investimentos", "040.030.0020") == "Despesas Gerais"
    assert section_for("Investimentos", "040.030.0030") == "Despesas Gerais"
    # The sibling 040.* families keep their existing prefix behaviour.
    assert section_for("Marketing", "040.010.0090") == "Consultoria"
    assert section_for("Informática", "040.040.0010") == "Informática"
    assert section_for("Biblioteca", "040.050.0010") == "Gestão do Conhecimento"


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
