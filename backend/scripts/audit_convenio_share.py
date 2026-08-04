"""How the Parte MBC share closes the jan/fev convênio gap — and what it does NOT prove.

This is the evidence behind `dre.convenio_mbc_shares` (2026-08-04), which took the
convênio off the "needs a finance ruling" list. Read it before changing that rule.

The problem
-----------
`030.010.0110` posts the GROSS convênio for a lawyer; the share MBC actually bears is
written only in the lançamento's free text (`convenio_memo`). Finance does not maintain
that text: **`603,50 / 524,28` appears in ALL TWELVE months of 2025 and into Feb 2026**
while the posted plan changed twice underneath it (Oct 2025 EHF 1.795,86 -> 2.122,32).
So "ask Renata to fix the note" would have fixed one instance of a systemic problem.

What is genuinely VALIDATED
---------------------------
1. **The staleness test.** `plan_total = posted + convenio_extra_dl` holds to the centavo
   in mar–jul for BOTH lawyers (10 checks, nothing fitted) and fails exactly in jan/fev.
   That is a DB-only way to tell a current note from a leftover — no workbook, no ruling.
2. **EHF's posted is 2.122,30 in all seven months of 2026.** One plan all year, so any
   posted-proportional rule reproduces the mar+ Parte MBC (1.564,10) for jan/fev too.
3. **RB February's posted (3.427,58) is identical to mar–jul**, so its share is as solid
   as EHF's.

What is NOT validated — say this plainly
----------------------------------------
* The share is **exactly determined**: one free parameter and one observation per lawyer,
  so it is a *restatement* of the trusted month, not a confirmed law. EHF 0.73698346 and
  RB 0.73698936 agreeing to 5 decimals is suggestive but is not independent evidence, and
  no single shared constant hits both to the centavo (hence per-lawyer).
* **RB January 2026 is an EXTRAPOLATION.** Its posted was 2.355,73 vs 3.427,58 from
  February on — a real 1.071,85 plan change that the workbook does NOT track (it types
  2.526,09 in every month). Nothing in the DB or the book states RB's January share, so
  applying the ratio assumes the share held while the plan moved. That single number is
  an estimate we own, flagged in `DIFERENCAS_ACUMULADO_2026.md`.
* ⚠ An earlier draft of this claimed the ratio was "confirmed out-of-sample on 2025".
  **That was wrong.** The 2025 figure it matched (1.469,10) is the memo's *subtrahend*,
  a different quantity from the Parte MBC. Corrected here so nobody repeats it.

Run: cd backend && python -m scripts.audit_convenio_share
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORKBOOK = REPO / "reference" / "workbook" / "Fechamento MBC 06.2026.xlsx"
#: 'Base_Resultado Mensal_V2' per-área custo-equipe block headers, and month columns.
BLOCKS = (("Contencioso", 5), ("Econômico", 30), ("Arbitragem", 60))
BASE_COL = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8}
CONVENIO = "030.010.0110"


def _brl(v: float) -> str:
    s = f"{abs(v):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"{'-' if v < 0 else ''}{s}"


def main() -> None:
    import openpyxl
    from dotenv import load_dotenv

    load_dotenv(REPO / "backend" / ".env")
    from app.api.providers import get_budget_repo, get_snapshot_store
    from app.budget.models import annual_budget, monthly_budget
    from app.closing.dre import assemble_dre_sections, convenio_mbc_shares

    snaps = get_snapshot_store().snapshots_by_year(2026, client_id="mbc")
    entries = get_budget_repo().get_budget("mbc", 2026)
    ann = annual_budget(entries) if entries else {}
    shares = convenio_mbc_shares(snaps)

    print("§1 The staleness test: plan_total == posted + extra_dl ?")
    print(f"   {'mês':5}{'sigla':7}{'posted':>12}{'extra_dl':>12}{'plan':>12}{'memo ok':>9}")
    for m in sorted(snaps):
        posted = {
            r["sigla"]: r["valor"]
            for r in (snaps[m].get("custo_equipe_deriv") or [])
            if r.get("id_conta") == CONVENIO
        }
        extra = {r["sigla"]: r["valor"] for r in (snaps[m].get("convenio_extra_dl") or [])}
        for memo in snaps[m].get("convenio_memo") or []:
            sg = memo["sigla"]
            p, e = posted.get(sg), extra.get(sg)
            if p is None:
                continue
            ok = sg in shares and abs((memo.get("parsed_valor") or 0) / p - shares[sg]) < 1e-6
            print(
                f"   {m:<5}{sg:7}{_brl(p):>12}{_brl(e or 0):>12}"
                f"{_brl(round(p + (e or 0), 2)):>12}{'sim' if ok else 'NÃO':>9}"
            )

    print("\n§2 Shares learned from the months whose memo is CURRENT:")
    for sg, sh in sorted(shares.items()):
        print(f"   {sg}: {sh:.8f}")
    print("   (per lawyer, from that lawyer's own months — never a hardcoded constant)")

    wb = openpyxl.load_workbook(WORKBOOK, data_only=True)
    base = wb["Base_Resultado Mensal_V2"]

    print("\n§3 Effect on per-área Custo equipe (jan/fev are the only stale months):")
    print(f"   {'mês':5}{'área':14}{'antes':>13}{'depois':>13}{'planilha':>13}{'Δ depois':>12}")
    for m in (1, 2):
        kwargs = dict(
            snapshot=snaps[m],
            budget=monthly_budget(entries, month=m) if entries else None,
            budget_annual=ann or None,
            transfers=None,
            period_label=f"2026-{m:02d}",
            period_month=m,
            targets=None,
        )
        before = assemble_dre_sections(**kwargs)
        after = assemble_dre_sections(**kwargs, convenio_shares=shares)

        def ce(sec: dict, key: str) -> float:
            rows = sec[key]["rows"]
            return next(
                (r.get("Realizado", {}).get("value") or 0.0
                 for r in rows if r.get("key") == "custo_equipe"),
                0.0,
            )

        for label, row in BLOCKS:
            key = {"Contencioso": "contencioso", "Econômico": "economico",
                   "Arbitragem": "arbitragem"}[label]
            bk = float(base.cell(row, BASE_COL[m]).value or 0.0)
            a = ce(after, key)
            print(
                f"   {m:<5}{label:14}{_brl(ce(before, key)):>13}{_brl(a):>13}"
                f"{_brl(bk):>13}{_brl(round(a - bk, 2)):>12}"
            )

    print("\n§4 ⚠ RB January is the one EXTRAPOLATION — its plan really did change:")
    for m in sorted(snaps):
        p = next(
            (r["valor"] for r in (snaps[m].get("custo_equipe_deriv") or [])
             if r.get("id_conta") == CONVENIO and r.get("sigla") == "RB"),
            None,
        )
        if p is not None:
            print(f"   m{m} RB posted {_brl(p)}")
    print("   Jan 2.355,73 vs 3.427,58 from Feb on (Δ 1.071,85). The workbook types")
    print("   2.526,09 in EVERY month, so it does not track that change. Ours does, and")
    print("   the resulting RB-January share is assumed, not stated anywhere.")


if __name__ == "__main__":
    main()
