"""Round-2 numeric matcher: parse every JSON and look for any numeric value
within 0.5% (and abs<0.5) of each target. This catches rounded/scaled hits
that simple textual search misses.
"""
import json
from pathlib import Path

TARGETS = json.loads(Path("/home/nandoravioli/bia4u/rumo/work/analysis/manual_inputs.json").read_text())
DUMPS = [
    Path("/home/nandoravioli/bia4u/rumo/work/api_dumps"),
    Path("/home/nandoravioli/bia4u/rumo/work/api_dumps_filtered"),
]

# Build search list with distinctive non-trivial values
search = []
for t in TARGETS:
    for mk, key in (("jan_2025_value","jan"),("feb_2025_value","feb")):
        v = t.get(mk)
        if v in (None, "", 0): continue
        try:
            f = float(v)
        except: continue
        if abs(f) < 50: continue  # skip tiny values that match too easily
        search.append((f, t["label"], key, t["row"]))

print(f"distinctive search terms: {len(search)}")

def walk_numbers(obj, path=""):
    """Yield (path, number) for every numeric leaf in a JSON tree."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_numbers(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_numbers(v, f"{path}[{i}]")
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        yield path, obj
    elif isinstance(obj, str):
        # Try to parse strings that look like numbers (Edm.Decimal serialized as string in OData)
        try:
            f = float(obj)
            if obj.replace(".","").replace("-","").isdigit() or "." in obj:
                yield path, f
        except Exception:
            pass

# For each file, collect all numbers once, then test all targets
matches = {}
for direc in DUMPS:
    for p in sorted(direc.iterdir()):
        if p.suffix != ".json" or p.name.endswith(".meta.json"):
            continue
        try:
            j = json.loads(p.read_text())
        except Exception:
            continue
        nums = list(walk_numbers(j))
        for f, label, mk, row in search:
            for path, val in nums:
                if abs(val - f) < 0.005:
                    key = (row, label, mk, f)
                    matches.setdefault(key, []).append((p.name, path, val))

# Build report
out_lines = ["row\tlabel\tmonth\ttarget_value\tn_hits\tbest_hits"]
hit_keys = set()
for (row,label,mk,f), hits in matches.items():
    hit_keys.add((row,label,mk,f))
    # dedupe by file -> keep up to 4 unique files
    seen=set()
    best=[]
    for fn,p,v in hits:
        if fn in seen: continue
        seen.add(fn)
        best.append(f"{fn}::{p}={v}")
        if len(best)>=4: break
    out_lines.append(f"{row}\t{label}\t{mk}\t{f}\t{len(hits)}\t{' | '.join(best)}")

# Add misses
for f, label, mk, row in search:
    if (row,label,mk,f) not in hit_keys:
        out_lines.append(f"{row}\t{label}\t{mk}\t{f}\t0\t")

Path("/home/nandoravioli/bia4u/rumo/work/analysis/value_match_report_v2.tsv").write_text("\n".join(out_lines))
hits=len(matches); total=len(search)
print(f"matched: {hits}/{total}")
miss=total-hits
print(f"missed: {miss}")
