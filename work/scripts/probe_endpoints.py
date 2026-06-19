"""Probe every OData entity set with $top=5 to capture a small sample.

Strategy:
- For each set, request `?$top=5&$format=json` first.
- Save raw response to work/api_dumps/<set>.json with metadata wrapper.
- Track http status, byte size, item count, error if any.
- Concurrency: small thread pool (6 workers) with politeness delay.
- Idempotent: skip files that already exist non-empty unless --force.

We intentionally do NOT try date filters yet; first pass is just discovery.
"""
import argparse
import concurrent.futures as cf
import json
import sys
import time
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth

BASE = "https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV"
USER, PASS = "integracao", "RumoTech1!"
DUMPS = Path("/home/nandoravioli/bia4u/rumo/work/api_dumps")
ENTITIES = Path("/home/nandoravioli/bia4u/rumo/work/analysis/entities.json")
INDEX = Path("/home/nandoravioli/bia4u/rumo/work/analysis/probe_index.tsv")

DUMPS.mkdir(parents=True, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument("--workers", type=int, default=6)
ap.add_argument("--top", type=int, default=5)
ap.add_argument("--timeout", type=int, default=60)
ap.add_argument("--force", action="store_true")
ap.add_argument("--limit", type=int, default=0, help="if >0, only probe first N sets (for testing)")
args = ap.parse_args()

sets = json.loads(ENTITIES.read_text())
if args.limit:
    sets = sets[: args.limit]

session = requests.Session()
session.auth = HTTPBasicAuth(USER, PASS)
session.headers.update({"Accept": "application/json"})


def probe(es):
    name = es["set"]
    out_path = DUMPS / f"{name}.json"
    meta_path = DUMPS / f"{name}.meta.json"
    if not args.force and out_path.exists() and out_path.stat().st_size > 0:
        try:
            j = json.loads(out_path.read_text())
            return name, "skip", out_path.stat().st_size, len(j.get("value", [])) if isinstance(j, dict) else 0, ""
        except Exception:
            pass
    url = f"{BASE}/{name}?$top={args.top}"
    t0 = time.time()
    try:
        r = session.get(url, timeout=args.timeout)
    except Exception as e:
        meta_path.write_text(json.dumps({"url": url, "error": str(e)}))
        return name, "ERR", 0, 0, str(e)[:200]
    elapsed = time.time() - t0
    meta = {
        "url": url,
        "status": r.status_code,
        "elapsed_s": round(elapsed, 3),
        "content_type": r.headers.get("Content-Type", ""),
        "bytes": len(r.content),
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    if r.status_code != 200:
        out_path.write_text(json.dumps({"_error": r.status_code, "body": r.text[:4000]}, ensure_ascii=False))
        return name, str(r.status_code), len(r.content), 0, r.text[:120]
    # store raw text
    out_path.write_bytes(r.content)
    try:
        j = r.json()
        n = len(j.get("value", [])) if isinstance(j, dict) else 0
    except Exception as e:
        n = -1
    return name, "200", len(r.content), n, ""


rows = []
errs = 0
with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
    futs = {ex.submit(probe, s): s for s in sets}
    for i, fut in enumerate(cf.as_completed(futs), 1):
        name, status, size, n, err = fut.result()
        rows.append((name, status, size, n, err))
        if status not in ("200", "skip"):
            errs += 1
        if i % 25 == 0 or i == len(futs):
            print(f"[{i}/{len(futs)}] last={name} status={status} bytes={size} items={n} errs={errs}")

with open(INDEX, "w", encoding="utf-8") as f:
    f.write("set\tstatus\tbytes\titems\terror\n")
    for r in rows:
        f.write("\t".join(str(x) for x in r) + "\n")

print(f"Done. Errors: {errs}/{len(rows)}")
