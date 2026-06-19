"""Try to reproduce the BASE 'Receita de honorários' values:
- Jan 2025: 279,821.07
- Feb 2025: 319,233.58

We try several aggregation hypotheses on FaturaViews:
  H1: sum of ValorHonorarios where DataEmissao in month and Situacao != 'C' (cancelled)
  H2: sum of ValorHonorarios where Situacao == 'R' (recebida) and DataEmissao in month
  H3: sum of (ValorHonorarios - ValorDesconto)
  H4: sum of ValorDespesasTributaveis + ValorHonorarios
  H5: by data de recebimento (using AlocacaoRecebimento*)

Also we already have the ground-truth FATURAS sheet from the workbook with sums:
  Jan: 227,933.47 (Valor Líquido)
  Feb: 287,269.76 (Valor Líquido)
The doc said BASE != FATURAS — so probably revenue is by emission month
of paid (recebida) invoices, or by AlocacaoRecebimento date.
"""
import json
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

D = Path("/home/nandoravioli/bia4u/rumo/work/api_dumps_filtered")

def load(name):
    p = D / name
    return json.loads(p.read_text())["value"]

def parse_date(v):
    if not v: return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except Exception:
        return None

def month_key(v):
    d = parse_date(v)
    return d.strftime("%Y-%m") if d else None


print("="*70)
print("FATURAS Jan/Feb 2025 (server data, by DataEmissao)")
print("="*70)
faturas = load("FaturaViews__DataEmissao_ge_datetimeoffset_2025_01_01T00_00_00Z__and_DataEmissao_lt_datetimeoffset_2025_03_01T00_00_00Z___ALL.json")
print(f"Total faturas: {len(faturas)}")
sit_counts = Counter(f.get("Situacao") for f in faturas)
print(f"Situacao distribution: {sit_counts}")
tipo_counts = Counter(f.get("Tipo") for f in faturas)
print(f"Tipo distribution: {tipo_counts}")

# Group by month + situacao + tipo
groups = defaultdict(lambda: {"n":0, "sum_hon":0, "sum_desc":0, "sum_desp":0, "sum_desp_trib":0})
for f in faturas:
    mk = month_key(f.get("DataEmissao"))
    s = f.get("Situacao")
    t = f.get("Tipo")
    g = groups[(mk, s, t)]
    g["n"] += 1
    g["sum_hon"] += float(f.get("ValorHonorarios") or 0)
    g["sum_desc"] += float(f.get("ValorDesconto") or 0)
    g["sum_desp"] += float(f.get("ValorDespesas") or 0)
    g["sum_desp_trib"] += float(f.get("ValorDespesasTributaveis") or 0)

print(f"\n{'Month':10s} {'Sit':3s} {'Tipo':4s} {'N':>4s} {'Sum_Hon':>14s} {'Sum_Desc':>10s} {'Sum_Desp':>10s} {'Net':>14s}")
for k in sorted(groups.keys()):
    mk, s, t = k
    g = groups[k]
    net = g["sum_hon"] - g["sum_desc"]
    print(f"{mk!s:10s} {s!s:3s} {t!s:4s} {g['n']:>4d} {g['sum_hon']:>14,.2f} {g['sum_desc']:>10,.2f} {g['sum_desp']:>10,.2f} {net:>14,.2f}")

# Aggregate per month, all situacoes except C
print("\n--- Sums by month (Situacao != C, Tipo=F) ---")
TARGETS = {"2025-01": 279821.07, "2025-02": 319233.58}
for mk in ("2025-01", "2025-02"):
    rows = [f for f in faturas if month_key(f.get("DataEmissao"))==mk and f.get("Situacao")!="C" and f.get("Tipo")=="F"]
    s_hon = sum(float(f.get("ValorHonorarios") or 0) for f in rows)
    s_net = sum(float(f.get("ValorHonorarios") or 0) - float(f.get("ValorDesconto") or 0) for f in rows)
    s_desp_trib = sum(float(f.get("ValorDespesasTributaveis") or 0) for f in rows)
    print(f"{mk} n={len(rows):>3d}  hon={s_hon:>12,.2f}  net={s_net:>12,.2f}  desp_trib={s_desp_trib:>10,.2f}  TARGET={TARGETS[mk]:>12,.2f}  diff_hon={s_hon-TARGETS[mk]:+,.2f}")

# Try by Tipo F or R (Recebida)
print("\n--- All Tipo (F=Fatura R=Recebimento) and Situacao R only ---")
for mk in ("2025-01", "2025-02"):
    rows = [f for f in faturas if month_key(f.get("DataEmissao"))==mk and f.get("Situacao")=="R"]
    s_hon = sum(float(f.get("ValorHonorarios") or 0) for f in rows)
    print(f"  {mk} Situacao=R n={len(rows)} sum_hon={s_hon:,.2f}")

print("\n="*40)
print("ALOCACAO RECEBIMENTO (AlocacaoRecebimentoFaturaClienteJobViews) - by DataRecebimento")
print("="*70)
# This was in the unfiltered dump - let's check if there's any data for 2025
import glob
for p in sorted((Path("/home/nandoravioli/bia4u/rumo/work/api_dumps")).glob("AlocacaoRecebimento*Views.json")):
    try:
        j = json.loads(p.read_text())
    except Exception:
        continue
    if not isinstance(j, dict) or "_error" in j:
        continue
    rows = j.get("value", [])
    if not rows:
        continue
    # Look for date fields
    sample = rows[0]
    date_keys = [k for k in sample if "Data" in k]
    if "DataRecebimento" in sample:
        print(f"  {p.stem}: {len(rows)} rows, has DataRecebimento")

# Print RateioFaturaCasoViews 2025-01 sum (AnoMes eq '2025-01' returned 106 rows)
print("\n="*40)
print("RateioFaturaCasoViews AnoMes eq '2025-01' / '2025-02'")
print("="*70)
for mk in ("2025-01", "2025-02"):
    fname = f"RateioFaturaCasoViews__AnoMes_eq__{mk.replace('-','_')}_.json"
    matches = list(D.glob(f"RateioFaturaCasoViews__*{mk.replace('-','_')}*.json"))
    if not matches:
        # search all
        matches = [p for p in D.glob("RateioFaturaCasoViews*") if mk.replace('-','_') in p.name]
    for m in matches:
        rows = json.loads(m.read_text()).get("value", [])
        s_fat = sum(float(r.get("FaturaValorHonorarios") or 0) for r in rows)
        s_rateado = sum(float(r.get("TotalRateado") or 0) for r in rows)
        s_faturado = sum(float(r.get("TotalFaturado") or 0) for r in rows)
        sit_counts = Counter(r.get("FaturaSituacao") for r in rows)
        print(f"  {m.name}: n={len(rows)}, sum_FaturaValorHonorarios={s_fat:,.2f}, sum_TotalFaturado={s_faturado:,.2f}, sum_TotalRateado={s_rateado:,.2f}, sit={sit_counts}")

# RateioFaturaOriginalViews
print("\nRateioFaturaOriginalViews AnoMes eq '2025-01' / '2025-02'")
for mk in ("2025-01", "2025-02"):
    matches = [p for p in D.glob("RateioFaturaOriginalViews*") if mk.replace('-','_') in p.name]
    for m in matches:
        rows = json.loads(m.read_text()).get("value", [])
        s_faturado = sum(float(r.get("ValorFaturado") or 0) for r in rows)
        s_trab = sum(float(r.get("ValorTrabalhado") or 0) for r in rows)
        s_hon = sum(float(r.get("FaturaValorHonorarios") or 0) for r in rows)
        sit_counts = Counter(r.get("FaturaSituacao") for r in rows)
        tipo_counts = Counter(r.get("FaturaTipo") for r in rows)
        print(f"  {m.name}: n={len(rows)}, ValorFaturado={s_faturado:,.2f}, ValorTrabalhado={s_trab:,.2f}, FaturaValorHonorarios={s_hon:,.2f}, sit={sit_counts}, tipo={tipo_counts}")

# Posicao financeira resultado faturamento
print("\nPosicaoFinanceiraResultadoFaturamentoViews AnoMes eq '2025-01' / '2025-02'")
for mk in ("2025-01", "2025-02"):
    matches = [p for p in D.glob("PosicaoFinanceiraResultadoFaturamentoViews*") if mk.replace('-','_') in p.name]
    for m in matches:
        rows = json.loads(m.read_text()).get("value", [])
        # show field stats: try Valor1..Valor9
        sums = {}
        for k in ("Valor1","Valor2","Valor3","Valor4","Valor5","Valor6","Valor7","Valor8","Valor9"):
            sums[k] = sum(float(r.get(k) or 0) for r in rows)
        print(f"  {m.name}: n={len(rows)} sums={sums}")
        if rows:
            print(f"    sample row keys: {list(rows[0].keys())[:30]}")

print("\nPosicaoFinanceiraResultadoRecebimentoViews AnoMes eq '2025-01' / '2025-02'")
for mk in ("2025-01", "2025-02"):
    matches = [p for p in D.glob("PosicaoFinanceiraResultadoRecebimentoViews*") if mk.replace('-','_') in p.name]
    for m in matches:
        rows = json.loads(m.read_text()).get("value", [])
        sums = {}
        for k in ("Valor1","Valor2","Valor3","Valor4","Valor5","Valor6","Valor7","Valor8","Valor9"):
            sums[k] = sum(float(r.get(k) or 0) for r in rows)
        print(f"  {m.name}: n={len(rows)} sums={sums}")
