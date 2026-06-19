"""Hunt for exact values across ALL Edm.Decimal fields (not just Valor*).

Skip endpoints with 0 rows. Skip fields where filter syntax is not supported.
Avoid asking for round-number values that are likely false positives.
"""
import json
import urllib.parse as up
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth
import concurrent.futures as cf

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
        try: counts[parts[0]] = int(parts[2])
        except: counts[parts[0]] = 0

# distinctive workbook target values - skip integers and round numbers
TARGETS = {
    "Receita_Jan": 279821.07,
    "Receita_Feb": 319233.58,
    "Aluguel": 26384.63,
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
    "Amortizacao_Mensal": 8117.31,
    "Manut_Jardim_Jan": 836,
    "Manut_Jardim_Feb": 919.6,
    "OAB_CS": 936.2,
    "Material_Higiene_Jan": 995.49,
    "Material_Higiene_Feb": 263.89,
    "Reembolsaveis": 9762.54,
    "Eventos_Jan": 1171.71,
    "Eventos_Feb": 1166.75,
    "Custo_Total_Contencioso_Jan": 73576.315,
    "Custo_Total_Contencioso_Feb": 76342.345,
    "Custo_Total_Economico_Jan": 76041.035,
    "Custo_Total_Economico_Feb": 80276.745,
    "Custo_Total_Arbitragem_Jan": 62013.17,
    "Custo_Total_Arbitragem_Feb": 61794.34,
    "DespesasInst_Jan": 104973.54,
    "DespesasInst_Feb": 98454.78,
    "TotalSaidas_Jan": 316604.06,
    "TotalSaidas_Feb": 318368.21,
    "ImpostosTotal_Jan": 177678.92,
    "ImpostosTotal_Feb": 5641.82,
    "Telefonia_Total_Jan": 807.16,
}

# Build (endpoint, field) for ALL decimal fields where endpoint has data
queries = []
for e in ents:
    name = e["set"]
    if counts.get(name, 0) == 0:
        continue
    for p in e["properties"]:
        if p["type"] in ("Edm.Decimal", "Edm.Double", "Edm.Single"):
            queries.append((name, p["name"]))

print(f"(endpoint, decimal_field) pairs: {len(queries)}")

target_items = list(TARGETS.items())

def query_endpoint_field(endpoint, field, batch_targets):
    parts = []
    for label, v in batch_targets:
        parts.append(f"{field} eq {v}m")
    flt = " or ".join(parts)
    url = f"{BASE}/{endpoint}?$filter={up.quote(flt, safe=' ')}&$top=20"
    try:
        r = session.get(url, timeout=20)
    except Exception as e:
        return endpoint, field, [], f"ERR {e}"
    if r.status_code != 200:
        return endpoint, field, [], f"HTTP {r.status_code}"
    try:
        rows = r.json().get("value", [])
    except Exception:
        return endpoint, field, [], "PARSE ERR"
    matches = []
    for row in rows:
        v = row.get(field)
        if v is None: continue
        try: vf = float(v)
        except: continue
        for label, target in batch_targets:
            if abs(vf - float(target)) < 0.005:
                matches.append((label, target, row))
    return endpoint, field, matches, None


jobs = []
for endpoint, field in queries:
    for i in range(0, len(target_items), 12):
        jobs.append((endpoint, field, target_items[i:i+12]))

print(f"Queries to run: {len(jobs)}")

results = []
errors = 0
with cf.ThreadPoolExecutor(max_workers=10) as ex:
    futs = [ex.submit(query_endpoint_field, ep, fl, batch) for ep, fl, batch in jobs]
    for i, fut in enumerate(cf.as_completed(futs), 1):
        ep, fl, matches, err = fut.result()
        if err: errors += 1
        if matches: results.append((ep, fl, matches))
        if i % 200 == 0:
            print(f"[{i}/{len(jobs)}] hits={len(results)} errs={errors}")

# de-dup and report
out = []
for ep, field, matches in results:
    for label, target, row in matches:
        ctx = {}
        for k in ("Id","AnoMes","DataAnoMes","DataEmissao","DataInclusao","Data","Tipo","Descricao","Numero","ProfissionalSigla","CasoCodigo","ProfissionalPessoaNome","CasoAssunto","ClientePessoaNome","TipoDespesaDescricao","RazaoSocial"):
            if k in row:
                ctx[k] = row[k]
        out.append({"endpoint": ep, "field": field, "label": label, "target": target, "context": ctx})

Path("/home/nandoravioli/bia4u/rumo/work/analysis/value_hunt_v2_results.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str))
print(f"\nTotal positive hits: {len(out)} (errors: {errors})")
