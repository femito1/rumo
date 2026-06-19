"""For each (endpoint, Valor* column) where the endpoint has data,
issue a $filter=Column eq <target> query for each known workbook target.

This brute-forces "is the value 26384.63 in any Valor field of any endpoint?"
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

ents = json.loads(Path("/home/nandoravioli/bia4u/rumo/work/analysis/entities.json").read_text())
counts = {}
with open("/home/nandoravioli/bia4u/rumo/work/analysis/true_counts.tsv") as f:
    next(f)
    for line in f:
        parts = line.rstrip("\n").split("\t")
        try:
            counts[parts[0]] = int(parts[2])
        except (ValueError, IndexError):
            counts[parts[0]] = 0

# Distinctive workbook targets (>50, >2 decimals, not round)
TARGETS = {
    "Receita_Jan": 279821.07,
    "Receita_Feb": 319233.58,
    "Aluguel": 26384.63,
    "Condominio": 4996,
    "Energia_Jan": 773.71,
    "Energia_Feb": 926.16,
    "IPTU_Feb": 6916.97,
    "Telefonia_Fixa": 65.29,
    "Limpeza": 3049.23,
    "Manutencao_AC": 919.76,
    "Internet": 741.87,
    "Consultoria_Adm": 14705.8,
    "Consultoria_Marketing": 6251.98,
    "Contabilidade_Jan": 9077.36,
    "Contabilidade_Feb": 7804.05,
    "COFINS_Jan": 185.68,
    "COFINS_Feb": 226.54,
    "CSLL_Jan": 43297.07,
    "FGTS_Jan": 480.64,
    "FGTS_Feb": 354.66,
    "INSS_Jan": 7466.34,
    "IRRF_Folha_Jan": 169.52,
    "IRRF_Trim_Jan": 123429.61,
    "ISS_3os": 228.69,
    "PIS_Jan": 40.3,
    "PIS_Feb": 49.13,
    "Convenio_Beatriz": 1269.46,
    "Convenio_Daniel": 1736.14,
    "Convenio_Isabel": 1564.08,
    "Convenio_Elisa": 2122.3,
    "Convenio_Ricardo_Jan": 2355.73,
    "Convenio_Ricardo_Feb": 3427.58,
    "Pro_Labore": 1621,
    "Pro_Labore_Aurelio": 810.5,
    "DataCenter_Oracle": 7478.66,
    "DL_Extraordinaria": 164477.34,
    "Bonus_Equipe": 101705.84,
    "Salario_ADM_Jan": 1683.06,
    "Salario_ADM_Feb": 3455.42,
    "Vale_Refeicao_Jan": 829.8,
    "Vale_Refeicao_Feb": 1014.2,
    "Seguro_RC": 2539.84,
    "Seguro_Locacao_Jan": 182.71,
    "Biblioteca": 692.37,
    "Suporte_Informatica_Jan": 4921.5,
    "Suporte_Informatica_Feb": 5427.47,
    "Licencas_Software_Jan": 9786.61,
    "Licencas_Software_Feb": 12193.48,
    "Comissao_Eco": 1500,
    "Amortizacao_Mensal": 8117.31,
}

# Build list: (endpoint, [valor_field_names])
queries = []
for e in ents:
    name = e["set"]
    if counts.get(name, 0) == 0:
        continue
    valor_fields = []
    for p in e["properties"]:
        if p["type"] == "Edm.Decimal" and ("Valor" in p["name"] or p["name"] in ("Total","Saldo","Custo")):
            valor_fields.append(p["name"])
    if valor_fields:
        queries.append((name, valor_fields))

print(f"Endpoints with data and Decimal Valor* columns: {len(queries)}")

# Each query: GET /{endpoint}?$filter=Field eq <value>&$top=3
# We don't want 50K queries. Strategy: use multi-OR per field per endpoint.
# Concretely, for each (endpoint, field), do:
#   $filter = (Field eq v1) or (Field eq v2) or ... &$top=5

found = []
attempted = 0
errors = 0

import concurrent.futures as cf

def query_endpoint_field(endpoint, field, batch_targets):
    parts = []
    for label, v in batch_targets:
        parts.append(f"{field} eq {v}m")  # Edm.Decimal literal
    flt = " or ".join(parts)
    url = f"{BASE}/{endpoint}?$filter={up.quote(flt, safe=' ')}&$top=20"
    try:
        r = session.get(url, timeout=30)
    except Exception as e:
        return endpoint, field, [], f"ERR {e}"
    if r.status_code != 200:
        return endpoint, field, [], f"HTTP {r.status_code} {r.text[:80]}"
    try:
        rows = r.json().get("value", [])
    except Exception:
        return endpoint, field, [], "PARSE ERR"
    matches = []
    for row in rows:
        v = row.get(field)
        if v is None: continue
        try:
            vf = float(v)
        except Exception:
            continue
        for label, target in batch_targets:
            if abs(vf - float(target)) < 0.005:
                matches.append((label, target, row))
    return endpoint, field, matches, None


# Run all queries with thread pool. Batch all targets per query.
target_items = list(TARGETS.items())
jobs = []
for endpoint, fields in queries:
    for field in fields:
        # Trim to top 12 targets per query to keep URL reasonable
        for i in range(0, len(target_items), 12):
            batch = target_items[i:i+12]
            jobs.append((endpoint, field, batch))

print(f"Total queries to run: {len(jobs)}")

results = []
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    futs = [ex.submit(query_endpoint_field, ep, fl, batch) for ep, fl, batch in jobs]
    for i, fut in enumerate(cf.as_completed(futs), 1):
        ep, fl, matches, err = fut.result()
        if err:
            errors += 1
        if matches:
            results.append((ep, fl, matches))
        if i % 100 == 0:
            print(f"[{i}/{len(jobs)}] hits={len(results)} errs={errors}")

print(f"\nFinished. Endpoint hits: {len(results)} | errors: {errors}")
out = []
for ep, field, matches in results:
    for label, target, row in matches:
        # extract a few useful fields for context
        ctx = {}
        for k in ("Id","AnoMes","DataAnoMes","DataEmissao","DataInclusao","Data","Tipo","Descricao","Numero","ProfissionalSigla","CasoCodigo","ProfissionalPessoaNome","CasoAssunto","ClientePessoaNome"):
            if k in row:
                ctx[k] = row[k]
        out.append({"endpoint": ep, "field": field, "label": label, "target": target, "context": ctx})

Path("/home/nandoravioli/bia4u/rumo/work/analysis/value_hunt_results.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str))
print(f"Total positive hits: {len(out)}")
# Print first 30
for r in out[:30]:
    print(f"  {r['label']:25s} {r['target']:>12,.2f}  in {r['endpoint']}.{r['field']}  ctx={r['context']}")
