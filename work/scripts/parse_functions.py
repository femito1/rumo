"""Parse FunctionImport definitions from $metadata.xml.

In OData v3 a FunctionImport is an RPC-style endpoint:
  GET /BASE/FunctionName?param1=value1&param2=value2

These are often the *real* business endpoints (e.g. GetReceitaByPeriodo)
while EntitySets are mostly raw views. The Postman collection only had
GETs of EntitySets, so we never even tried these.
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

META = Path("/home/nandoravioli/bia4u/rumo/work/api_dumps/_metadata.xml")
OUT = Path("/home/nandoravioli/bia4u/rumo/work/analysis/functions.json")
OUT_TSV = Path("/home/nandoravioli/bia4u/rumo/work/analysis/functions.tsv")

tree = ET.parse(META)
root = tree.getroot()
edm_ns = None
for child in root.iter():
    if child.tag.endswith("}Schema"):
        edm_ns = child.tag.split("}")[0].lstrip("{")
        break

functions = []
for fi in root.iter(f"{{{edm_ns}}}FunctionImport"):
    name = fi.attrib.get("Name")
    return_type = fi.attrib.get("ReturnType", "")
    method = fi.attrib.get("m:HttpMethod", "")
    if not method:
        # try without prefix
        for k, v in fi.attrib.items():
            if k.endswith("HttpMethod"):
                method = v
                break
    is_collection = fi.attrib.get("EntitySet") or "Collection" in return_type
    params = []
    for p in fi.findall(f"{{{edm_ns}}}Parameter"):
        params.append({
            "name": p.attrib.get("Name"),
            "type": p.attrib.get("Type"),
            "nullable": p.attrib.get("Nullable", "true"),
            "mode": p.attrib.get("Mode", "In"),
        })
    functions.append({
        "name": name,
        "method": method or "GET",
        "return_type": return_type,
        "entity_set": fi.attrib.get("EntitySet"),
        "params": params,
    })

OUT.write_text(json.dumps(functions, indent=2, ensure_ascii=False))

with open(OUT_TSV, "w", encoding="utf-8") as f:
    f.write("name\tmethod\treturn_type\tentity_set\tn_params\tparams\n")
    for fn in functions:
        params = ", ".join(f"{p['name']}:{p['type']}" for p in fn["params"])
        f.write(f"{fn['name']}\t{fn['method']}\t{fn['return_type']}\t{fn['entity_set'] or ''}\t{len(fn['params'])}\t{params}\n")

print(f"Total FunctionImports: {len(functions)}")
print(f"GET: {sum(1 for f in functions if f['method'] in ('GET','') )}")
print(f"POST: {sum(1 for f in functions if f['method']=='POST')}")
# methods histogram
from collections import Counter
print("Method dist:", Counter(f['method'] for f in functions))

# Find functions with date-like params and revenue-like names
candidates = []
for fn in functions:
    pname = fn["name"].lower()
    if any(k in pname for k in ("receit","fatura","recebim","despes","custo","pagto","pagament","baixa","balanc","tribut","imposto","movimentacao","prestaca","lancament","financeir","bp","caixa","entrada","saida","rateio","amortiz","conta","orcam","planejam")):
        candidates.append(fn)
print(f"\nName-filtered candidates: {len(candidates)}")
for fn in candidates[:30]:
    pnames = [p["name"] for p in fn["params"]]
    print(f"  {fn['name']}({', '.join(pnames)}) -> {fn['return_type']}")
