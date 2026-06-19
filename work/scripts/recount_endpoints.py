"""Re-probe every endpoint with $inlinecount=allpages&$top=1 to get true row counts."""
import concurrent.futures as cf
import json
import time
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth

BASE = "https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV"
ENTITIES = Path("/home/nandoravioli/bia4u/rumo/work/analysis/entities.json")
OUT = Path("/home/nandoravioli/bia4u/rumo/work/analysis/true_counts.tsv")

session = requests.Session()
session.auth = HTTPBasicAuth("integracao", "RumoTech1!")
session.headers.update({"Accept": "application/json"})

sets = json.loads(ENTITIES.read_text())


def count(es):
    name = es["set"]
    url = f"{BASE}/{name}?$inlinecount=allpages&$top=1"
    try:
        r = session.get(url, timeout=60)
    except Exception as e:
        return name, "ERR", str(e)[:120], 0
    if r.status_code != 200:
        return name, str(r.status_code), r.text[:120], 0
    try:
        j = r.json()
        c = j.get("odata.count")
        n_rows = len(j.get("value", []))
        return name, "200", c, n_rows
    except Exception as e:
        return name, "PARSE", str(e), 0


rows = []
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(count, s): s for s in sets}
    for i, fut in enumerate(cf.as_completed(futs), 1):
        rows.append(fut.result())
        if i % 50 == 0 or i == len(futs):
            print(f"[{i}/{len(futs)}] last={rows[-1][0]} count={rows[-1][2]}")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("set\tstatus\ttotal_count\tn_rows_returned\n")
    for r in rows:
        f.write("\t".join(str(x) for x in r) + "\n")

# stats
counts = []
for r in rows:
    if r[1] == "200":
        try:
            c = int(r[2])
            counts.append((r[0], c))
        except (TypeError, ValueError):
            pass
print(f"\nWith count: {len(counts)}")
print(f"Empty (count=0): {sum(1 for _,c in counts if c==0)}")
print(f"Non-empty: {sum(1 for _,c in counts if c>0)}")
print(f"Top 30 by count:")
for n,c in sorted(counts, key=lambda x:-x[1])[:30]:
    print(f"  {n:60s}  {c:>10,}")
