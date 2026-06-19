"""Round 2 of filtered probes:
- Use datetimeoffset literal for DateTimeOffset properties.
- Pull more rows where the first attempt returned exactly 500 (server cap).
"""
import json
import time
import urllib.parse as up
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth

BASE = "https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV"
session = requests.Session()
session.auth = HTTPBasicAuth("integracao", "RumoTech1!")
session.headers.update({"Accept": "application/json"})

OUT = Path("/home/nandoravioli/bia4u/rumo/work/api_dumps_filtered")
OUT.mkdir(parents=True, exist_ok=True)


def safe_name(s):
    return "".join(c if c.isalnum() else "_" for c in s)[:120]


def fetch_all(endpoint, filt, page=500, max_pages=20):
    """Page through results using $skip until <page rows are returned."""
    all_rows = []
    skip = 0
    for i in range(max_pages):
        url = f"{BASE}/{endpoint}?$filter={up.quote(filt, safe=' ')}&$top={page}&$skip={skip}"
        t0 = time.time()
        r = session.get(url, timeout=120)
        dt = time.time() - t0
        if r.status_code != 200:
            return None, r.status_code, r.text[:300]
        j = r.json()
        rows = j.get("value", [])
        all_rows.extend(rows)
        print(f"  [{endpoint}] skip={skip} -> {len(rows)} rows ({dt:.1f}s)")
        if len(rows) < page:
            break
        skip += page
        time.sleep(0.2)
    fname = f"{endpoint}__{safe_name(filt)}__ALL.json"
    (OUT / fname).write_text(json.dumps({"value": all_rows}, ensure_ascii=False))
    return len(all_rows), 200, None


# DateTimeOffset filters
DT_TARGETS = [
    ("FaturaViews", "DataEmissao", "DateTimeOffset"),
    ("FaturaRedacaoViews", "DataEmissao", "DateTimeOffset"),
    ("AlocacaoRecebimentoFaturaClienteJobViews", "DataRecebimento", "DateTime"),
    ("AlocacaoRecebimentoFaturaClienteViews", "DataRecebimento", "DateTime"),
    ("AprovacaoDespesaViews", "Data", "DateTimeOffset"),
    ("PreFaturaViews", "DataEmissao", "DateTimeOffset"),
    ("SaldoFaturaViews", "Data", "DateTimeOffset"),
]

for endpoint, field, typ in DT_TARGETS:
    if typ == "DateTimeOffset":
        filt = f"{field} ge datetimeoffset'2025-01-01T00:00:00Z' and {field} lt datetimeoffset'2025-03-01T00:00:00Z'"
    else:
        filt = f"{field} ge datetime'2025-01-01' and {field} lt datetime'2025-03-01'"
    print(f"\n>>> {endpoint} (filter on {field})")
    n, st, err = fetch_all(endpoint, filt)
    print(f"  total={n} status={st} err={err}")

# Also re-pull capped ones
PAGINATE = [
    ("PosicaoFinanceiraResumoProfissionalViews", "AnoMes eq '2025-01'"),
    ("PosicaoFinanceiraResumoProfissionalViews", "AnoMes eq '2025-02'"),
]
for endpoint, filt in PAGINATE:
    print(f"\n>>> {endpoint} {filt}")
    n, st, err = fetch_all(endpoint, filt)
    print(f"  total={n} status={st}")
