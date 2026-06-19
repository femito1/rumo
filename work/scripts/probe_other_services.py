"""Enumerate the entity sets of the other OData services we found."""
import json
import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path

session = requests.Session()
session.auth = HTTPBasicAuth("integracao", "RumoTech1!")
session.headers.update({"Accept": "application/json"})

SERVICES = [
    "ODataConsultivo",
    "ODataContratos",
    "ODataCriminal",
    "ODataCivel",
    "ODataTrabalhista",
    "ODataTributario",
]

OUT = Path("/home/nandoravioli/bia4u/rumo/work/api_dumps_other_services")
OUT.mkdir(parents=True, exist_ok=True)

ANALYSIS = Path("/home/nandoravioli/bia4u/rumo/work/analysis")

for svc in SERVICES:
    base = f"https://legaldesk.mbclaw.com.br/API/v1/{svc}"
    print(f"\n=== {svc} ===")
    # catalog
    r = session.get(f"{base}/", timeout=30)
    if r.status_code != 200:
        print(f"  catalog: {r.status_code}")
        continue
    cat = r.json()
    sets = [v["name"] for v in cat.get("value", [])]
    print(f"  EntitySets: {len(sets)}")
    (OUT / f"{svc}_catalog.json").write_text(json.dumps(cat, indent=2, ensure_ascii=False))
    # metadata
    rm = session.get(f"{base}/$metadata", timeout=60)
    if rm.status_code == 200:
        (OUT / f"{svc}_metadata.xml").write_bytes(rm.content)
    # are these the SAME entity sets as ODataGERALADV?
    geral_sets = {e["set"] for e in json.loads((ANALYSIS/"entities.json").read_text())}
    new_sets = set(sets) - geral_sets
    print(f"  New (not in ODataGERALADV): {len(new_sets)}")
    if new_sets:
        for n in sorted(new_sets)[:20]:
            print(f"    + {n}")
