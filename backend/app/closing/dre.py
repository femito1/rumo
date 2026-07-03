# backend/app/closing/dre.py
"""Assemble the workbook's DRE views faithfully (Orçado x Realizado).

Mirrors `Copy of Fechamento MBC 02.2026.xlsx`. Vocabulary and structure come
from `workbook_layouts.py`. Base of the Institucional DRE is **Recebimento**
(cash received), matching the workbook — not Faturamento.

All values are recomputed from clean sources (SISJURI snapshot + manual budget);
the workbook itself carries #REF! errors so we never copy its cells.

Row shape for rich DRE tabs: each row exposes the display columns first
(``Linha``, then value columns) followed by metadata (``key``, ``indent``,
``is_total``, ``kind``) that the frontend's ``rowKeys`` slice ignores.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.closing.workbook_layouts import (
    AMORTIZACAO_MENSAL,
    AREAS,
    BONUS_RESERVE_RATE,
    INSTITUCIONAL_SECTIONS,
    is_direct_team,
    is_imposto,
    is_indirect,
    match_area,
    section_for,
)

# --- canonical line keys (stable; shared with budget + frontend) -------------
RECEBIMENTO = "recebimento"
FATURAMENTO = "faturamento"
CUSTO_EQUIPE = "custo_equipe"
DESPESAS = "despesas"
RESULTADO_BRUTO = "resultado_bruto"
MARGEM_BRUTA = "margem_bruta"
IMPOSTO = "imposto"
AMORTIZACAO = "amortizacao"
RESULTADO_LIQUIDO = "resultado_liquido"
MARGEM_LIQUIDA = "margem_liquida"
RESERVA_BONUS = "reserva_bonus"
COMISSAO = "comissao"
DESPESAS_EQUIPE = "despesas_equipe"
DESPESA_INSTITUCIONAL = "despesa_institucional"


def _pct(numer: float, denom: float) -> float | None:
    if not denom:
        return None
    return round(numer / denom, 4)


def bonus_reserve(net_margin_value: float) -> float:
    """Reserva de bônus = fixed rate x margem líquida (finance-confirmed)."""
    return round(net_margin_value * BONUS_RESERVE_RATE, 2)


@dataclass
class OrcadoDerived:
    """Budgeted derived lines, computed from the base Orçado inputs the same way
    Realizado derives from SISJURI. Present only when the base budget rows exist,
    so the Orçado column mirrors Realizado instead of showing a placeholder."""

    resultado_bruto: float | None = None
    margem_bruta: float | None = None
    amortizacao: float | None = None
    resultado_liquido: float | None = None
    margem_liquida: float | None = None
    reserva_bonus: float | None = None

    @classmethod
    def from_budget(cls, orc: dict[str, float]) -> "OrcadoDerived":
        receb = orc.get(RECEBIMENTO)
        custo = orc.get(CUSTO_EQUIPE)
        desp = orc.get(DESPESAS)
        imposto = orc.get(IMPOSTO)
        # Only derive when the whole base is budgeted; a partial budget would
        # produce misleading totals, so we leave those lines blank instead.
        if None in (receb, custo, desp):
            return cls()
        assert receb is not None and custo is not None and desp is not None
        rb = round(receb - custo - desp, 2)
        amort = orc.get(AMORTIZACAO, AMORTIZACAO_MENSAL)
        rl: float | None = None
        rbonus: float | None = None
        if imposto is not None:
            rl = round(rb - imposto - amort, 2)
            rbonus = bonus_reserve(rl)
        return cls(
            resultado_bruto=rb,
            margem_bruta=_pct(rb, receb),
            amortizacao=amort,
            resultado_liquido=rl,
            margem_liquida=_pct(rl, receb) if rl is not None else None,
            reserva_bonus=rbonus,
        )


@dataclass
class SectionBreakdown:
    """One institutional section subtotal + its sub-accounts."""

    name: str
    total: float = 0.0
    accounts: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class RealizadoInputs:
    """Clean realizado inputs for one competence month (workbook vocabulary)."""

    recebimento: float
    faturamento: float
    custo_equipe: float
    despesas: float
    imposto: float
    amortizacao: float = AMORTIZACAO_MENSAL
    sections: list[SectionBreakdown] = field(default_factory=list)
    area_custo_equipe: dict[str, float] = field(default_factory=dict)
    area_recebimento: dict[str, float] = field(default_factory=dict)
    imposto_accounts: list[tuple[str, float]] = field(default_factory=list)

    @classmethod
    def from_snapshot(cls, snap: dict[str, Any]) -> "RealizadoInputs":
        revenue = snap.get("revenue", {}) or {}
        despesas_rows = snap.get("despesas_conta", []) or []
        custo_area = snap.get("custo_area", []) or []
        receb_area = snap.get("recebimento_area", []) or []

        recebimento = float(revenue.get("recebimento_bruto", 0.0) or 0.0)
        faturamento = float(revenue.get("faturamento_bruto", 0.0) or 0.0)

        sec_map: dict[str, SectionBreakdown] = {}
        imposto_total = 0.0
        imposto_accounts: list[tuple[str, float]] = []
        custo_equipe_from_accounts = 0.0

        for row in despesas_rows:
            id_conta = str(row.get("id_conta", ""))
            total = float(row.get("total", 0.0) or 0.0)
            nome = str(row.get("nome_conta", "?"))
            if is_imposto(row):
                imposto_total += total
                imposto_accounts.append((nome, round(total, 2)))
                continue
            if is_direct_team(id_conta):
                custo_equipe_from_accounts += total
                continue
            if is_indirect(id_conta):
                sec_name = section_for(row.get("nome_conta_pai"))
                sec = sec_map.setdefault(sec_name, SectionBreakdown(sec_name))
                sec.total = round(sec.total + total, 2)
                sec.accounts.append((nome, round(total, 2)))

        ordered: list[SectionBreakdown] = []
        for name in INSTITUCIONAL_SECTIONS:
            if name in sec_map:
                ordered.append(sec_map.pop(name))
            else:
                ordered.append(SectionBreakdown(name, 0.0, []))
        ordered.extend(sec_map.values())

        despesas_total = round(sum(s.total for s in ordered), 2)

        area_custo: dict[str, float] = {}
        for a in custo_area:
            for area in AREAS:
                if match_area(str(a.get("area", "")), area):
                    area_custo[area] = round(
                        area_custo.get(area, 0.0) + float(a.get("total", 0.0) or 0.0), 2
                    )
        custo_equipe = (
            round(sum(area_custo.values()), 2)
            if area_custo
            else round(custo_equipe_from_accounts, 2)
        )

        # Per-area recebimento: SISJURI splits the sacred receipt total by
        # CASO -> área jurídica. Names vary ("Direito Econômico", "Arbitragem
        # MV"); fold them onto the workbook's three areas via ``match_area``.
        area_receb: dict[str, float] = {}
        for a in receb_area:
            for area in AREAS:
                if match_area(str(a.get("area", "")), area):
                    area_receb[area] = round(
                        area_receb.get(area, 0.0) + float(a.get("total", 0.0) or 0.0), 2
                    )

        return cls(
            recebimento=recebimento,
            faturamento=faturamento,
            custo_equipe=custo_equipe,
            despesas=despesas_total,
            imposto=round(imposto_total, 2),
            sections=ordered,
            area_custo_equipe=area_custo,
            area_recebimento=area_receb,
            imposto_accounts=imposto_accounts,
        )

    @classmethod
    def empty(cls) -> "RealizadoInputs":
        return cls(
            recebimento=0.0,
            faturamento=0.0,
            custo_equipe=0.0,
            despesas=0.0,
            imposto=0.0,
            sections=[SectionBreakdown(n, 0.0, []) for n in INSTITUCIONAL_SECTIONS],
        )

    @property
    def resultado_bruto(self) -> float:
        return round(self.recebimento - self.custo_equipe - self.despesas, 2)

    @property
    def resultado_liquido(self) -> float:
        return round(self.resultado_bruto - self.imposto - self.amortizacao, 2)

    @property
    def reserva_bonus(self) -> float:
        return bonus_reserve(self.resultado_liquido)


# --- rich-tab helpers --------------------------------------------------------
_DRE_COLUMNS = ["Linha", "Orçado", "Realizado", "Desvio %"]


def _dre_row(
    label: str,
    key: str,
    orcado: float | None,
    realizado: float | None,
    *,
    indent: int = 0,
    is_total: bool = False,
    kind: str = "amount",
) -> dict[str, Any]:
    desvio = None
    if kind != "margin" and orcado is not None and realizado is not None:
        desvio = _pct(realizado, orcado)
    return {
        "Linha": label,
        "Orçado": {"value": orcado, "source": "orcado"},
        "Realizado": {"value": realizado, "source": "realizado"},
        "Desvio %": desvio,
        "key": key,
        "indent": indent,
        "is_total": is_total,
        "kind": kind,
    }


def _institucional_rows(
    r: RealizadoInputs, orc: dict[str, float]
) -> list[dict[str, Any]]:
    """Block 1 (DRE) + block 3 (expense sections) of the Institucional tab."""
    od = OrcadoDerived.from_budget(orc)
    rows: list[dict[str, Any]] = [
        _dre_row("Recebimento", RECEBIMENTO, orc.get(RECEBIMENTO), r.recebimento),
        _dre_row("Custo equipe", CUSTO_EQUIPE, orc.get(CUSTO_EQUIPE), r.custo_equipe),
        _dre_row("Despesas", DESPESAS, orc.get(DESPESAS), r.despesas),
        _dre_row(
            "Resultado Bruto", RESULTADO_BRUTO, od.resultado_bruto, r.resultado_bruto,
            is_total=True, kind="subtotal",
        ),
        _dre_row(
            "Margem Bruta", MARGEM_BRUTA, od.margem_bruta,
            _pct(r.resultado_bruto, r.recebimento),
            indent=1, kind="margin",
        ),
        _dre_row("Imposto", IMPOSTO, orc.get(IMPOSTO), r.imposto),
        _dre_row("Amortização", AMORTIZACAO, od.amortizacao, r.amortizacao),
        _dre_row(
            "Resultado Liquido", RESULTADO_LIQUIDO, od.resultado_liquido,
            r.resultado_liquido,
            is_total=True, kind="subtotal",
        ),
        _dre_row(
            "Margem Liquida", MARGEM_LIQUIDA, od.margem_liquida,
            _pct(r.resultado_liquido, r.recebimento), indent=1, kind="margin",
        ),
        _dre_row("Reserva de Bônus", RESERVA_BONUS, od.reserva_bonus, r.reserva_bonus),
    ]
    # Block 3: expense sections + indented sub-accounts, % of recebimento.
    rows.append(_section_header_row("DESPESAS POR SEÇÃO"))
    for sec in r.sections:
        rows.append(
            {
                "Linha": sec.name,
                "Orçado": {"value": None, "source": "orcado"},
                "Realizado": {"value": sec.total, "source": "realizado"},
                "Desvio %": _pct(sec.total, r.recebimento),
                "key": f"sec::{sec.name}",
                "indent": 0,
                "is_total": True,
                "kind": "section_total",
            }
        )
        for nome, val in sec.accounts:
            rows.append(
                {
                    "Linha": nome,
                    "Orçado": {"value": None, "source": "orcado"},
                    "Realizado": {"value": val, "source": "realizado"},
                    "Desvio %": None,
                    "key": f"acct::{sec.name}::{nome}",
                    "indent": 1,
                    "is_total": False,
                    "kind": "amount",
                }
            )
    return rows


def _section_header_row(title: str) -> dict[str, Any]:
    return {
        "Linha": title,
        "Orçado": None,
        "Realizado": None,
        "Desvio %": None,
        "key": f"hdr::{title}",
        "indent": 0,
        "is_total": True,
        "kind": "header",
    }


def _area_rows(
    area: str,
    r: RealizadoInputs,
    orc: dict[str, float],
    man: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Contencioso/Econômico/Arbitragem tab: Recebimento, Custo equipe, Comissão,
    Despesas Equipe, Despesa Institucional, Resultado Bruto (Orçado|Realizado|%).

    Custo equipe and Recebimento realizado both come from SISJURI per-area
    (Recebimento via CASO -> área jurídica, verified to the centavo vs the
    workbook). A manual per-area actual still overrides the SISJURI value
    (later-overrides-earlier), e.g. once the Resumo_Recebidas cross-area
    transfers are applied. Comissão, Despesas Equipe and Despesa Institucional
    remain manual (``man``). When absent they render blank; Resultado Bruto is
    computed once Recebimento is present."""
    man = man or {}
    custo = r.area_custo_equipe.get(area)
    receb = man.get(RECEBIMENTO, r.area_recebimento.get(area))
    comissao = man.get(COMISSAO)
    desp_equipe = man.get(DESPESAS_EQUIPE)
    desp_inst = man.get(DESPESA_INSTITUCIONAL)
    resultado: float | None = None
    if receb is not None:
        resultado = round(
            receb - (custo or 0.0) - (comissao or 0.0)
            - (desp_equipe or 0.0) - (desp_inst or 0.0),
            2,
        )
    return [
        _dre_row("Recebimento", RECEBIMENTO, orc.get(RECEBIMENTO), receb),
        _dre_row("Custo equipe", CUSTO_EQUIPE, orc.get(CUSTO_EQUIPE), custo),
        _dre_row("Comissão", COMISSAO, orc.get(COMISSAO), comissao),
        _dre_row("Despesas Equipe", DESPESAS_EQUIPE, orc.get(DESPESAS_EQUIPE), desp_equipe),
        _dre_row(
            "Despesa Institucional", DESPESA_INSTITUCIONAL,
            orc.get(DESPESA_INSTITUCIONAL), desp_inst,
        ),
        _dre_row(
            "Resultado Bruto", RESULTADO_BRUTO, None, resultado,
            is_total=True, kind="subtotal",
        ),
    ]


_AREA_SECTION = {"Contencioso": "contencioso", "Econômico": "economico", "Arbitragem": "arbitragem"}


def assemble_dre_sections(
    *,
    snapshot: dict[str, Any] | None,
    budget: dict[str, dict[str, float]] | None,
    period_label: str,
    manual: dict[str, dict[str, float]] | None = None,
    transfers: list[Any] | None = None,
    period_month: int | None = None,
) -> dict[str, dict[str, Any]]:
    """Return section payloads keyed by SectionKey.value (workbook-faithful).

    ``manual`` carries per-area Realizado inputs (per-area Recebimento etc.);
    ``transfers`` are Resumo_Recebidas cross-area recebimento reclassifications
    (``AreaTransfer``) that net onto the SISJURI-derived per-area base."""
    r = RealizadoInputs.from_snapshot(snapshot) if snapshot is not None else RealizadoInputs.empty()
    missing = snapshot is None
    budget = budget or {}
    manual = manual or {}

    # Overlay Resumo_Recebidas transfers onto the SISJURI per-area recebimento
    # base (value conserved; sums back to the sacred total).
    if transfers:
        from app.manual.transfers import apply_to_base

        r.area_recebimento = apply_to_base(r.area_recebimento, transfers)
    inst_orc = budget.get("institucional", {})

    sections: dict[str, dict[str, Any]] = {}
    sections["institucional"] = {
        "kind": "rich",
        "name": "Institucional",
        "columns": _DRE_COLUMNS,
        "rows": _institucional_rows(r, inst_orc),
        "snapshot_missing": missing,
    }
    for area in AREAS:
        sections[_AREA_SECTION[area]] = {
            "kind": "rich",
            "name": area,
            "columns": _DRE_COLUMNS,
            "rows": _area_rows(area, r, budget.get(area, {}), manual.get(area, {})),
            "snapshot_missing": missing,
        }

    # Areas Sintetico: consolidated block + the three area blocks stacked.
    sint: list[dict[str, Any]] = [_section_header_row("RESULTADO INSTITUCIONAL")]
    sint.extend(_institucional_rows(r, inst_orc)[:10])  # DRE lines only
    for area in AREAS:
        sint.append(_section_header_row(f"RESULTADO {area.upper()}"))
        sint.extend(_area_rows(area, r, budget.get(area, {}), manual.get(area, {})))
    sections["areas_sintetico"] = {
        "kind": "rich",
        "name": "Areas Sintetico atualizado",
        "columns": _DRE_COLUMNS,
        "rows": sint,
        "snapshot_missing": missing,
    }

    from app.closing.secondary_tabs import (
        assemble_amortizacao,
        assemble_dre_2026,
        assemble_fluxo_consolidado,
        assemble_institucional_ano,
        assemble_meta,
        assemble_rateio_mensal,
    )

    sections["amortizacao"] = assemble_amortizacao()
    sections["rateio_mensal"] = assemble_rateio_mensal(snapshot, period_label)
    sections["dre_2026"] = assemble_dre_2026(budget)
    sections["institucional_ano"] = assemble_institucional_ano(
        snapshot, budget, period_label
    )
    sections["fluxo_consolidado"] = assemble_fluxo_consolidado(
        snapshot, manual, period_label
    )
    sections["base_resultado"] = {
        "kind": "rich",
        "name": "Base_Resultado Mensal",
        "columns": ["Linha", "Valor"],
        "rows": _base_resultado_rows(snapshot, r),
        "snapshot_missing": missing,
    }

    # Meta goal-tracking dashboard: annual recebimento goal (8.060.000) vs the
    # competence month's realized recebimento.
    month = period_month
    if month is None:
        low = period_label.lower()
        for idx, mes in enumerate(_MESES_PT, start=1):
            if mes in low:
                month = idx
                break
    sections["meta_dashboard"] = assemble_meta(
        budget,
        month=month,
        recebimento_realizado=r.recebimento if not missing else None,
    )
    return sections


#: Lowercase PT month stems for parsing a period label into a month index.
_MESES_PT = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


# --- Base_Resultado Mensal (hierarchical monthly ledger) ---------------------
_AREA_ORDER = ("Contencioso", "Econômico", "Arbitragem")


def _base_resultado_rows(
    snap: dict[str, Any] | None, r: RealizadoInputs
) -> list[dict[str, Any]]:
    """Faithful Base_Resultado: Movimentação (Recebimento) + per-area Custo
    equipe (with per-lawyer sub-rows) + institutional sections/sub-accounts +
    Impostos. One 'Valor' column for the competence month."""

    def row(label: str, valor: float | None, *, indent: int = 0,
            is_total: bool = False, kind: str = "amount",
            key: str = "") -> dict[str, Any]:
        return {
            "Linha": label,
            "Valor": {"value": valor, "source": "realizado"} if valor is not None else None,
            "indent": indent,
            "is_total": is_total,
            "kind": kind,
            "key": key or label,
        }

    rows: list[dict[str, Any]] = []
    rows.append(row("Movimentação de Entrada", r.recebimento, is_total=True, kind="section_total", key="mov_entrada"))
    rows.append(row("Receita de honorários", r.recebimento, indent=1, key="receita_hon"))

    # Per-area Custo equipe with per-lawyer sub-rows.
    prof = (snap or {}).get("custo_equipe_prof", []) or []
    by_area: dict[str, dict[str, list[tuple[str, float]]]] = {}
    lump: list[tuple[str, float]] = []
    for p in prof:
        area = p.get("area")
        sigla = p.get("sigla")
        nome = str(p.get("nome_conta", "?"))
        valor = float(p.get("valor", 0.0) or 0.0)
        if not sigla or not area:
            lump.append((nome, valor))
            continue
        norm = next((a for a in _AREA_ORDER if match_area(str(area), a)), None) or str(area)
        by_area.setdefault(norm, {}).setdefault(sigla, []).append((nome, valor))

    for area in _AREA_ORDER:
        people = by_area.get(area, {})
        area_total = round(sum(v for pers in people.values() for _, v in pers), 2)
        rows.append(row(f"Custo equipe - {area}", area_total, is_total=True,
                        kind="section_total", key=f"custo_{area}"))
        for sigla in sorted(people):
            for nome, valor in people[sigla]:
                rows.append(row(f"{sigla} - {nome}", valor, indent=1,
                                key=f"prof::{area}::{sigla}::{nome}"))

    if lump:
        lump_total = round(sum(v for _, v in lump), 2)
        rows.append(row("Distribuição Mensal Fixa (rateio sócios)", lump_total,
                        is_total=True, kind="section_total", key="distrib_fixa"))
        for nome, valor in lump:
            rows.append(row(nome, valor, indent=1, key=f"lump::{nome}"))

    # Institutional expense sections + sub-accounts.
    for sec in r.sections:
        rows.append(row(sec.name, sec.total, is_total=True, kind="section_total",
                        key=f"sec::{sec.name}"))
        for nome, valor in sec.accounts:
            rows.append(row(nome, valor, indent=1, key=f"acct::{sec.name}::{nome}"))

    # Impostos block.
    rows.append(row("Impostos", r.imposto, is_total=True, kind="section_total", key="impostos"))
    for nome, valor in r.imposto_accounts:
        rows.append(row(nome, valor, indent=1, key=f"imp::{nome}"))

    # Distribuição de Lucros extras (discretionary profit distributions). These
    # are exceptional, finance-entered amounts (no clean SISJURI rule): team
    # bonus, extraordinary/excess partner distributions, MV excess, Cacione
    # pass-through. Values come from the snapshot's optional 'distribuicao_extras'
    # map when present; otherwise each line renders blank ('ainda não temos').
    extras = (snap or {}).get("distribuicao_extras", {}) or {}
    extra_lines: tuple[tuple[str, str], ...] = (
        ("Bônus equipe", "bonus_equipe"),
        ("DL excedente dos sócios", "dl_excedente_socios"),
        ("DL Extraordinária", "dl_extraordinaria"),
        ("DL excedente MV", "dl_excedente_mv"),
        ("Repasse Cacione", "repasse_cacione"),
    )
    present = [
        (label, float(extras[k]))
        for label, k in extra_lines
        if extras.get(k) is not None
    ]
    block_total = round(sum(v for _, v in present), 2) if present else None
    rows.append(row("Distribuição de Lucros extras", block_total, is_total=True,
                    kind="section_total", key="distrib_extras"))
    for label, k in extra_lines:
        val = extras.get(k)
        rows.append(row(label, float(val) if val is not None else None,
                        indent=1, key=f"extra::{k}"))

    return rows


def assemble_base_resultado(
    snapshot: dict[str, Any] | None, period_label: str
) -> dict[str, Any]:
    r = RealizadoInputs.from_snapshot(snapshot) if snapshot is not None else RealizadoInputs.empty()
    return {
        "kind": "rich",
        "name": "Base_Resultado Mensal",
        "columns": ["Linha", "Valor"],
        "rows": _base_resultado_rows(snapshot, r),
        "snapshot_missing": snapshot is None,
    }
