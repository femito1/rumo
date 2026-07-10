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

from app.closing.verification import Targets, verified_value
from app.closing.workbook_layouts import (
    AMORTIZACAO_MENSAL,
    AREAS,
    BONUS_RESERVE_RATE,
    INSTITUCIONAL_SECTIONS,
    imposto_sobre_recebimento,
    institutional_030_section,
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


def _parse_custo_overrides(raw: dict[str, Any], cls: Any) -> dict[str, Any]:
    """Build ``{sigla -> LawyerOverride}`` from the snapshot override map.

    Each entry is either a number (treated as ``cap_total``) or an object with
    optional ``set_account`` (dict), ``add`` (number) and ``cap_total`` (number).
    See ``app.closing.custo_equipe_deriv.LawyerOverride``.
    """
    out: dict[str, Any] = {}
    for sigla, spec in raw.items():
        if isinstance(spec, (int, float)):
            out[str(sigla)] = cls(cap_total=float(spec))
            continue
        if isinstance(spec, dict):
            set_acct = {
                str(k): float(v) for k, v in (spec.get("set_account") or {}).items()
            }
            add = float(spec.get("add", 0.0) or 0.0)
            cap = spec.get("cap_total")
            out[str(sigla)] = cls(
                set_account=set_acct,
                add=add,
                cap_total=float(cap) if cap is not None else None,
            )
    return out


def _pct(numer: float, denom: float) -> float | None:
    if not denom:
        return None
    return round(numer / denom, 4)


def bonus_reserve(resultado_liquido: float) -> float:
    """Reserva de bônus = 10% do Resultado Líquido (client-confirmed 2026-07-10)."""
    return round(resultado_liquido * BONUS_RESERVE_RATE, 2)


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
    # Hand-built ledger (workbook Base_Resultado) per-area figures, when present.
    # Overrides the SISJURI ``custo_area`` aggregation and drives Comissão,
    # Despesas Equipe and the derived Despesa Institucional (rateio) so the area
    # tabs tie to the client dashboard. Empty when no ledger was imported.
    area_comissao: dict[str, float] = field(default_factory=dict)
    area_despesas_equipe: dict[str, float] = field(default_factory=dict)
    area_despesa_institucional: dict[str, float] = field(default_factory=dict)
    has_ledger: bool = False

    @classmethod
    def from_snapshot(cls, snap: dict[str, Any]) -> "RealizadoInputs":
        revenue = snap.get("revenue", {}) or {}
        despesas_rows = snap.get("despesas_conta", []) or []
        custo_area = snap.get("custo_area", []) or []
        receb_area = snap.get("recebimento_area", []) or []

        recebimento = float(revenue.get("recebimento_bruto", 0.0) or 0.0)
        faturamento = float(revenue.get("faturamento_bruto", 0.0) or 0.0)

        sec_map: dict[str, SectionBreakdown] = {}
        # The ledger tax accounts are kept only as an informational detail under
        # the Impostos block; the DRE Imposto LINE is 15% of Recebimento (see
        # ``imposto`` in the return below), per the client-confirmed rule.
        imposto_accounts: list[tuple[str, float]] = []
        custo_equipe_from_accounts = 0.0

        for row in despesas_rows:
            id_conta = str(row.get("id_conta", ""))
            total = float(row.get("total", 0.0) or 0.0)
            nome = str(row.get("nome_conta", "?"))
            if is_imposto(row):
                imposto_accounts.append((nome, round(total, 2)))
                continue
            if is_direct_team(id_conta):
                custo_equipe_from_accounts += total
                continue
            carveout = institutional_030_section(id_conta)
            if carveout is not None:
                sec = sec_map.setdefault(carveout, SectionBreakdown(carveout))
                sec.total = round(sec.total + total, 2)
                sec.accounts.append((nome, round(total, 2)))
                continue
            if is_indirect(id_conta):
                sec_name = section_for(row.get("nome_conta_pai"), id_conta)
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

        # Preferred: SISJURI-derived per-area Custo equipe (no manual ledger).
        # The extract emits ``custo_equipe_deriv`` (per-lawyer components) plus
        # ``rateio_grupo`` (CAD_RATEIO_GRUPO %s) and ``home_area`` (sigla->grupo).
        # When present it overrides the noisy ``custo_area`` aggregation. A small
        # per-lawyer ``custo_equipe_overrides`` map handles rare negotiated caps.
        deriv_rows = snap.get("custo_equipe_deriv") or []
        if deriv_rows:
            from app.closing.custo_equipe_deriv import (
                LawyerOverride,
                build_area_splits,
                derive_area_custo_equipe,
            )

            splits = build_area_splits(
                snap.get("rateio_grupo") or [],
                {
                    str(k): str(v)
                    for k, v in (snap.get("home_area") or {}).items()
                },
            )
            overrides = _parse_custo_overrides(
                snap.get("custo_equipe_overrides") or {}, LawyerOverride
            )
            # Combine per-lawyer rows with the "area-level" personal-debit lines
            # (Vale Refeição/Transporte on 500.010.<SIGLA>): those carry a sigla
            # too, so the fold routes them via the lawyer's home area/rateio just
            # like the 030.010.* components.
            all_rows = list(deriv_rows) + list(snap.get("custo_equipe_area") or [])
            derived = derive_area_custo_equipe(
                all_rows, splits, overrides=overrides
            )
            if any(derived.values()):
                area_custo = {a: round(v, 2) for a, v in derived.items()}
                custo_equipe = round(sum(area_custo.values()), 2)

        # Preferred: SISJURI-derived per-area Comissão (Participação Externa +
        # Interna). When the ``comissao_deriv`` block is present it replaces the
        # workbook ledger's per-area comissao (docs/SISJURI_QUERIES.md §12a).
        comissao_rows = snap.get("comissao_deriv")
        area_comissao_deriv: dict[str, float] | None = None
        if comissao_rows is not None:
            from app.closing.comissao_deriv import derive_area_comissao
            from app.closing.custo_equipe_deriv import build_area_splits

            com_splits = build_area_splits(
                snap.get("rateio_grupo") or [],
                {str(k): str(v) for k, v in (snap.get("home_area") or {}).items()},
            )
            area_comissao_deriv = derive_area_comissao(comissao_rows, com_splits)

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

        # Hand-built ledger (workbook Base_Resultado) overlay, when imported.
        # It supplies per-area Custo equipe / Comissão / Despesas Equipe (which
        # SISJURI cannot reproduce because of manual per-lawyer splits) and lets
        # us derive Despesa Institucional via the workbook rateio. When present,
        # its Custo equipe overrides the SISJURI ``custo_area`` per-area values.
        ledger = snap.get("ledger") or {}
        area_comissao: dict[str, float] = {}
        area_desp_equipe: dict[str, float] = {}
        area_desp_inst: dict[str, float] = {}
        has_ledger = bool(ledger)
        if has_ledger:
            from app.closing.ledger_import import (
                LedgerMonth,
                despesa_institucional_rateio,
            )

            lc = {a: float(v) for a, v in (ledger.get("custo_equipe") or {}).items()}
            area_comissao = {
                a: round(float(v), 2) for a, v in (ledger.get("comissao") or {}).items()
            }
            # SISJURI-derived comissão wins over the workbook ledger when present.
            if area_comissao_deriv is not None:
                area_comissao = {a: round(v, 2) for a, v in area_comissao_deriv.items()}
            area_desp_equipe = {
                a: round(float(v), 2)
                for a, v in (ledger.get("despesas_equipe") or {}).items()
            }
            lm = LedgerMonth(
                month=0,
                custo_equipe=lc,
                comissao=area_comissao,
                despesas_equipe=area_desp_equipe,
                despesa_institucional_total=float(
                    ledger.get("despesa_institucional_total", 0.0) or 0.0
                ),
            )
            area_desp_inst = despesa_institucional_rateio(lm)
            # Ledger per-area Custo equipe overrides the SISJURI aggregation
            # ONLY when the SISJURI-derived block is absent. The derived block
            # (custo_equipe_deriv) is authoritative when present.
            if lc and not deriv_rows:
                area_custo = {a: round(v, 2) for a, v in lc.items()}
                custo_equipe = round(sum(area_custo.values()), 2)

        # No workbook ledger but SISJURI comissão present: use the derived values.
        if not has_ledger and area_comissao_deriv is not None:
            area_comissao = {a: round(v, 2) for a, v in area_comissao_deriv.items()}

        return cls(
            recebimento=recebimento,
            faturamento=faturamento,
            custo_equipe=custo_equipe,
            despesas=despesas_total,
            imposto=imposto_sobre_recebimento(recebimento),
            sections=ordered,
            area_custo_equipe=area_custo,
            area_recebimento=area_receb,
            imposto_accounts=imposto_accounts,
            area_comissao=area_comissao,
            area_despesas_equipe=area_desp_equipe,
            area_despesa_institucional=area_desp_inst,
            has_ledger=has_ledger,
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
    section_key: str = "",
    targets: Targets | None = None,
) -> dict[str, Any]:
    # Hard rule: blank the Realizado if it disagrees with the workbook target.
    realizado = verified_value(realizado, section_key, key, targets)
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
    r: RealizadoInputs,
    orc: dict[str, float],
    targets: Targets | None = None,
    section_key: str = "institucional",
) -> list[dict[str, Any]]:
    """Block 1 (DRE) + block 3 (expense sections) of the Institucional tab."""
    od = OrcadoDerived.from_budget(orc)

    def dre(label: str, key: str, orcado: float | None, realizado: float | None,
            **kw: Any) -> dict[str, Any]:
        return _dre_row(label, key, orcado, realizado,
                        section_key=section_key, targets=targets, **kw)

    rows: list[dict[str, Any]] = [
        dre("Recebimento", RECEBIMENTO, orc.get(RECEBIMENTO), r.recebimento),
        dre("Custo equipe", CUSTO_EQUIPE, orc.get(CUSTO_EQUIPE), r.custo_equipe),
        dre("Despesas", DESPESAS, orc.get(DESPESAS), r.despesas),
        dre(
            "Resultado Bruto", RESULTADO_BRUTO, od.resultado_bruto, r.resultado_bruto,
            is_total=True, kind="subtotal",
        ),
        dre(
            "Margem Bruta", MARGEM_BRUTA, od.margem_bruta,
            _pct(r.resultado_bruto, r.recebimento),
            indent=1, kind="margin",
        ),
        dre("Imposto", IMPOSTO, orc.get(IMPOSTO), r.imposto),
        dre("Amortização", AMORTIZACAO, od.amortizacao, r.amortizacao),
        dre(
            "Resultado Liquido", RESULTADO_LIQUIDO, od.resultado_liquido,
            r.resultado_liquido,
            is_total=True, kind="subtotal",
        ),
        dre(
            "Margem Liquida", MARGEM_LIQUIDA, od.margem_liquida,
            _pct(r.resultado_liquido, r.recebimento), indent=1, kind="margin",
        ),
        dre("Reserva de Bônus", RESERVA_BONUS, od.reserva_bonus, r.reserva_bonus),
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
    targets: Targets | None = None,
    section_key: str = "",
) -> list[dict[str, Any]]:
    """Contencioso/Econômico/Arbitragem tab: Recebimento, Custo equipe, Comissão,
    Despesas Equipe, Despesa Institucional, Resultado Bruto (Orçado|Realizado|%).

    Recebimento realizado comes from SISJURI per-area (via CASO -> área
    jurídica, verified to the centavo vs the workbook, with Resumo_Recebidas
    cross-area transfers applied upstream); it is never hand-filled. Custo
    equipe, Comissão and Despesas Equipe come from the imported hand-ledger
    (workbook Base_Resultado) when present, and Despesa Institucional is then
    derived via the workbook rateio — ties the area tabs to the client
    dashboard. Without a ledger, Custo equipe falls back to the SISJURI
    ``custo_area`` aggregation and Comissão/Despesas Equipe/Despesa
    Institucional to manual entry (``man``); when absent they render blank.
    Resultado Bruto is computed once Recebimento is present."""
    man = man or {}
    custo = r.area_custo_equipe.get(area)
    # Recebimento is SISJURI-derived (CASO -> área jurídica) with Resumo_Recebidas
    # transfers already applied upstream; it is never hand-filled anymore.
    receb = r.area_recebimento.get(area)
    # When the hand-built ledger is imported it is authoritative for Comissão,
    # Despesas Equipe and the derived Despesa Institucional (rateio); it ties the
    # area tabs to the client dashboard. Manual entry only fills the gaps when no
    # ledger exists for the month (future-proof fallback).
    if r.has_ledger:
        comissao = r.area_comissao.get(area)
        desp_equipe = r.area_despesas_equipe.get(area)
        desp_inst = r.area_despesa_institucional.get(area)
    else:
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
    def dre(label: str, key: str, orcado: float | None, realizado: float | None,
            **kw: Any) -> dict[str, Any]:
        return _dre_row(label, key, orcado, realizado,
                        section_key=section_key, targets=targets, **kw)

    return [
        dre("Recebimento", RECEBIMENTO, orc.get(RECEBIMENTO), receb),
        dre("Custo equipe", CUSTO_EQUIPE, orc.get(CUSTO_EQUIPE), custo),
        dre("Comissão", COMISSAO, orc.get(COMISSAO), comissao),
        dre("Despesas Equipe", DESPESAS_EQUIPE, orc.get(DESPESAS_EQUIPE), desp_equipe),
        dre(
            "Despesa Institucional", DESPESA_INSTITUCIONAL,
            orc.get(DESPESA_INSTITUCIONAL), desp_inst,
        ),
        dre(
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
    targets: Targets | None = None,
) -> dict[str, dict[str, Any]]:
    """Return section payloads keyed by SectionKey.value (workbook-faithful).

    ``manual`` carries per-area Realizado inputs (per-area Recebimento etc.);
    ``transfers`` are Resumo_Recebidas cross-area recebimento reclassifications
    (``AreaTransfer``) that net onto the SISJURI-derived per-area base.
    ``targets`` is the workbook verification overlay: a Realizado cell that
    diverges from its target by more than R$0,01 is blanked (the hard rule)."""
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
        "rows": _institucional_rows(r, inst_orc, targets, "institucional"),
        "snapshot_missing": missing,
    }
    for area in AREAS:
        area_key = _AREA_SECTION[area]
        sections[area_key] = {
            "kind": "rich",
            "name": area,
            "columns": _DRE_COLUMNS,
            "rows": _area_rows(
                area, r, budget.get(area, {}), manual.get(area, {}),
                targets, area_key,
            ),
            "snapshot_missing": missing,
        }

    # Areas Sintetico: consolidated block + the three area blocks stacked.
    sint: list[dict[str, Any]] = [_section_header_row("RESULTADO INSTITUCIONAL")]
    sint.extend(_institucional_rows(r, inst_orc, targets, "institucional")[:10])
    for area in AREAS:
        sint.append(_section_header_row(f"RESULTADO {area.upper()}"))
        sint.extend(_area_rows(
            area, r, budget.get(area, {}), manual.get(area, {}),
            targets, _AREA_SECTION[area],
        ))
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
        assemble_faturas_analitico,
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
    sections["faturas_analitico"] = assemble_faturas_analitico(snapshot)
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
