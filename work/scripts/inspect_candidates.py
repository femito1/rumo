"""Inspect the top candidate endpoints in detail."""
import json
from pathlib import Path

DUMPS = Path("/home/nandoravioli/bia4u/rumo/work/api_dumps")

CANDIDATES = [
    "FaturaViews",
    "FaturaRedacaoViews",
    "FaturaCasoViews",
    "AlocacaoRecebimentoFaturaClienteViews",
    "AlocacaoRecebimentoFaturaClienteJobViews",
    "AlocacaoRecebimentoTransferenciaClienteViews",
    "AlocacaoRecebimentoContratoViews",
    "RateioFaturaCasoViews",
    "RateioFaturaOriginalViews",
    "RateioFaturaProfissionalViews",
    "TributoViews",
    "OrcamentoViews",
    "MetaReceitaViews",
    "BusinessPlanCustoViews",
    "BusinessPlanCategoriaViews",
    "BusinessPlanConsolidadoProfissionalViews",
    "BusinessPlanProfissionalViews",
    "LancamentoViews",
    "LancamentoFinanceiroViews",
    "AdiantamentoViews",
    "PreFaturaViews",
    "AprovacaoDespesaViews",
    "PrestacaoContaViews",
    "PrestacaoContaInstitucionalViews",
    "PrestacaoContaEscritorioViews",
    "MovimentacaoFinanceiraViews",
    "SaldoFaturaViews",
    "CustoProfissionalViews",
    "CustoCategoriaViews",
    "BusinessPlanViews",
]

for name in CANDIDATES:
    p = DUMPS / f"{name}.json"
    if not p.exists():
        print(f"--- {name}: NOT DUMPED")
        continue
    try:
        j = json.loads(p.read_text())
    except Exception as e:
        print(f"--- {name}: parse error {e}")
        continue
    if not isinstance(j, dict):
        print(f"--- {name}: not a dict")
        continue
    if "_error" in j:
        print(f"--- {name}: ERROR {j.get('_error')}")
        continue
    rows = j.get("value", [])
    print(f"\n=== {name}  rows={len(rows)} ===")
    if rows:
        r = rows[0]
        for k, v in r.items():
            sv = str(v)
            if len(sv) > 90:
                sv = sv[:90] + "..."
            print(f"  {k}: {sv}")
