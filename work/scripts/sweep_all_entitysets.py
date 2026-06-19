"""Exhaustive authenticated sweep of EVERY OData entity set.

For each entity set in the service `$metadata`, issue `?$top=1` and record
whether it returns rows and which fields are populated. Threaded for speed.
Writes a JSON summary so we never have to guess view names again.
"""
from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "work/scripts")
from web_login import ROOT, login

SERVICE = "ODataGERALADV"


def get_entity_sets(session) -> list[str]:
    md = session.get(
        f"{ROOT}/API/v1/{SERVICE}/$metadata", timeout=120,
        headers={"Accept": "application/xml"},
    ).text
    return sorted(set(re.findall(r'<EntitySet Name="([^"]+)"', md)))


def probe(session, ent: str) -> dict:
    url = f"{ROOT}/API/v1/{SERVICE}/{ent}?$top=1"
    try:
        r = session.get(url, timeout=45, headers={"Accept": "application/json"})
    except Exception as ex:  # noqa: BLE001
        return {"set": ent, "status": "ERR", "rows": 0, "err": str(ex)[:60]}
    if r.status_code != 200:
        return {"set": ent, "status": r.status_code, "rows": 0,
                "err": r.text[:60].replace("\n", " ")}
    try:
        v = r.json().get("value", [])
    except Exception:  # noqa: BLE001
        return {"set": ent, "status": 200, "rows": 0, "err": "non-json"}
    if not v:
        return {"set": ent, "status": 200, "rows": 0, "fields": []}
    fields = [k for k, val in v[0].items() if val not in (None, "")]
    return {"set": ent, "status": 200, "rows": len(v), "fields": fields}


def main() -> None:
    session = login("integracao", "RumoTech1!")
    sets = get_entity_sets(session)
    print(f"total entity sets: {len(sets)}", flush=True)

    results: list[dict] = []
    done = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(probe, session, e): e for e in sets}
        for fut in futures:
            pass
        for fut in __import__("concurrent.futures").futures.as_completed(futures):
            results.append(fut.result())
            done += 1
            if done % 50 == 0:
                print(f"  ...{done}/{len(sets)}", flush=True)

    results.sort(key=lambda d: d["set"])
    has_data = [r for r in results if r.get("rows", 0) > 0 and r["status"] == 200]
    empty = [r for r in results if r.get("rows", 0) == 0 and r["status"] == 200]
    errors = [r for r in results if r["status"] != 200]

    out = {"service": SERVICE, "total": len(sets),
           "has_data": len(has_data), "empty": len(empty), "errors": len(errors),
           "results": results}
    with open("work/data/entityset_sweep.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"\nHAS_DATA={len(has_data)} EMPTY={len(empty)} ERRORS={len(errors)}", flush=True)
    print("\n=== entity sets WITH data ===", flush=True)
    for r in has_data:
        print(f"  {r['set']} (fields={len(r.get('fields', []))})", flush=True)
    print("SWEEP_COMPLETE", flush=True)


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"elapsed {time.time() - t0:.0f}s", flush=True)
