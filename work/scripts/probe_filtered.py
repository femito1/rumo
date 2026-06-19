"""Probe key endpoints with date filters for 2025-01 and 2025-02 to verify data exists.

We try multiple OData filter syntaxes since the server is OData v3:
- AnoMes eq '2025-01'  (string field)
- DataAnoMes ge datetime'2025-01-01' and DataAnoMes lt datetime'2025-02-01'
- DataEmissao ge datetime'2025-01-01' and DataEmissao lt datetime'2025-02-01'
- DataRecebimento ge ... and DataRecebimento lt ...

Strategy: for each candidate endpoint with a date column, fetch rows for Jan 2025
and Feb 2025 with $top=200 (capped) and dump them.
"""
import json
import sys
import time
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth

BASE = "https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV"
session = requests.Session()
session.auth = HTTPBasicAuth("integracao", "RumoTech1!")
session.headers.update({"Accept": "application/json"})

OUT = Path("/home/nandoravioli/bia4u/rumo/work/api_dumps_filtered")
OUT.mkdir(parents=True, exist_ok=True)

# (endpoint, [filter_attempts])
TARGETS = [
    ("FaturaViews", [
        "DataEmissao ge datetime'2025-01-01' and DataEmissao lt datetime'2025-03-01'",
    ]),
    ("FaturaRedacaoViews", [
        "DataEmissao ge datetime'2025-01-01' and DataEmissao lt datetime'2025-03-01'",
    ]),
    ("AlocacaoRecebimentoFaturaClienteJobViews", [
        "DataRecebimento ge datetime'2025-01-01' and DataRecebimento lt datetime'2025-03-01'",
    ]),
    ("AlocacaoRecebimentoFaturaClienteViews", [
        "DataRecebimento ge datetime'2025-01-01' and DataRecebimento lt datetime'2025-03-01'",
    ]),
    ("RateioFaturaCasoViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
        "DataAnoMes ge datetime'2025-01-01' and DataAnoMes lt datetime'2025-03-01'",
    ]),
    ("RateioFaturaOriginalViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
    ]),
    ("RateioFaturaProfissionalViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
    ]),
    ("TributoViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
    ]),
    ("OrcamentoViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
    ]),
    ("MetaReceitaViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
    ]),
    ("AdiantamentoViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
    ]),
    ("AprovacaoDespesaViews", [
        "Data ge datetime'2025-01-01' and Data lt datetime'2025-03-01'",
    ]),
    ("PreFaturaViews", [
        "DataEmissao ge datetime'2025-01-01' and DataEmissao lt datetime'2025-03-01'",
    ]),
    ("SaldoFaturaViews", [
        "Data ge datetime'2025-01-01' and Data lt datetime'2025-03-01'",
    ]),
    ("PosicaoFinanceiraResultadoFaturamentoViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
    ]),
    ("PosicaoFinanceiraResultadoRecebimentoViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
    ]),
    ("PosicaoFinanceiraDespesaIncorridaViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
    ]),
    ("PosicaoFinanceiraResumoDespesaViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
    ]),
    ("PosicaoFinanceiraResumoProfissionalViews", [
        "AnoMes eq '2025-01'", "AnoMes eq '2025-02'",
    ]),
]


def safe_name(s):
    return "".join(c if c.isalnum() else "_" for c in s)[:120]


def fetch(endpoint, filt, top=500):
    import urllib.parse as up
    url = f"{BASE}/{endpoint}?$filter={up.quote(filt, safe=' ')}&$top={top}"
    t0 = time.time()
    try:
        r = session.get(url, timeout=120)
    except Exception as e:
        return None, 0, 0, str(e)
    dt = time.time() - t0
    if r.status_code != 200:
        return r.status_code, len(r.content), dt, r.text[:300]
    try:
        j = r.json()
        n = len(j.get("value", []))
        # save dump
        fname = f"{endpoint}__{safe_name(filt)}.json"
        (OUT / fname).write_bytes(r.content)
        return r.status_code, len(r.content), dt, n
    except Exception as e:
        return r.status_code, len(r.content), dt, f"parse err {e}"


report = []
for endpoint, filters in TARGETS:
    for filt in filters:
        st, sz, dt, info = fetch(endpoint, filt)
        line = f"{endpoint:50s} | {filt[:55]:55s} | status={st} bytes={sz} t={dt:.1f}s -> {info}"
        print(line)
        report.append(line)
        time.sleep(0.2)

Path("/home/nandoravioli/bia4u/rumo/work/analysis/probe_filtered_report.txt").write_text("\n".join(report))
