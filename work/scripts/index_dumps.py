"""Build a searchable index of every API dump.

For each successful dump:
- Field names + types (inferred from a sample row)
- Sample of distinct values per field (max 3, max 60 chars)
- Detect date fields and their year/month coverage
- Detect numeric "amount" fields (Valor*, Total*, Saldo*, etc.) and their range/sum
- Classify the entity by content keywords (revenue, expense, payroll, tax, ...)
"""
import json
import re
from collections import defaultdict
from pathlib import Path

DUMPS = Path("/home/nandoravioli/bia4u/rumo/work/api_dumps")
ENTITIES = Path("/home/nandoravioli/bia4u/rumo/work/analysis/entities.json")
OUT = Path("/home/nandoravioli/bia4u/rumo/work/analysis/dumps_index.json")
OUT_TSV = Path("/home/nandoravioli/bia4u/rumo/work/analysis/dumps_index.tsv")
NONEMPTY_TSV = Path("/home/nandoravioli/bia4u/rumo/work/analysis/dumps_with_data.tsv")

ent_meta = {e["set"]: e for e in json.loads(ENTITIES.read_text())}

DATE_RE = re.compile(r"/Date\((-?\d+)\)/|^\d{4}-\d{2}-\d{2}")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")

KW_GROUPS = [
    ("revenue", ["receit", "honorar", "fatura", "recebim", "fatur", "honorário"]),
    ("expense", ["despes", "custo", "pagament", "saida", "saída"]),
    ("payroll", ["profission", "salar", "labore", "pro_labore", "rh", "ferias", "férias", "rateio"]),
    ("tax", ["imposto", "tributo", "iss", "irrf", "csll", "cofins", "pis", "fgts", "inss"]),
    ("invoice", ["fatura", "prefatura", "pre_fatura", "redacao", "redação"]),
    ("client", ["cliente", "caso", "contrato"]),
    ("budget", ["orcament", "orçament", "budget", "businessplan", "planejam", "meta"]),
    ("amortization", ["amortiz", "lancament", "lancamento"]),
]

def classify(name, fields):
    name_l = name.lower()
    fields_l = " ".join(fields).lower()
    cats = []
    for cat, kws in KW_GROUPS:
        if any(kw in name_l or kw in fields_l for kw in kws):
            cats.append(cat)
    return cats

def parse_date(v):
    if v is None:
        return None
    if isinstance(v, str):
        m = re.match(r"/Date\((-?\d+)(?:[+-]\d+)?\)/", v)
        if m:
            ms = int(m.group(1))
            from datetime import datetime, timezone
            try:
                return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
            except Exception:
                return None
        if ISO_DATE.match(v):
            from datetime import datetime
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00")[:19])
            except Exception:
                return None
    return None

index = []
for p in sorted(DUMPS.glob("*.json")):
    if p.name == "_metadata.xml":
        continue
    if p.name.endswith(".meta.json"):
        continue
    name = p.stem
    try:
        j = json.loads(p.read_text())
    except Exception as e:
        continue
    if not isinstance(j, dict) or "_error" in j:
        continue
    rows = j.get("value", [])
    n = len(rows)
    fields = []
    sample = {}
    date_field_years = defaultdict(set)
    numeric_fields = defaultdict(list)
    if rows:
        # Use union of keys from first 3 rows
        keys = []
        for r in rows[:3]:
            for k in r.keys():
                if k not in keys:
                    keys.append(k)
        fields = keys
        for k in keys:
            vals = [r.get(k) for r in rows if r.get(k) is not None]
            sample[k] = [str(v)[:80] for v in vals[:3]]
            # detect dates
            for v in vals:
                d = parse_date(v)
                if d:
                    date_field_years[k].add((d.year, d.month))
            # detect numeric
            for v in vals:
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    numeric_fields[k].append(v)

    et = ent_meta.get(name, {})
    metadata_props = {p["name"]: p["type"] for p in et.get("properties", [])}
    # Use metadata-declared dates for fields that don't appear in sample (because empty)
    declared_date_props = [p["name"] for p in et.get("properties", []) if p.get("type") and ("Date" in (p["type"] or ""))]

    cats = classify(name, fields or list(metadata_props.keys()))

    info = {
        "set": name,
        "n_rows": n,
        "fields": fields,
        "metadata_props": metadata_props,
        "declared_date_props": declared_date_props,
        "date_field_years": {k: sorted(list(v)) for k, v in date_field_years.items()},
        "numeric_fields": {k: {"n": len(v), "min": min(v), "max": max(v), "sum": sum(v)} for k, v in numeric_fields.items()},
        "categories": cats,
        "sample": sample,
    }
    index.append(info)

OUT.write_text(json.dumps(index, indent=2, ensure_ascii=False, default=str))

with open(OUT_TSV, "w", encoding="utf-8") as f:
    f.write("set\tn_rows\tcategories\tfields_sample\tdate_props\tnumeric_props\n")
    for info in index:
        date_props = list(info["date_field_years"].keys()) or info["declared_date_props"]
        f.write("\t".join([
            info["set"],
            str(info["n_rows"]),
            ",".join(info["categories"]),
            ",".join(info["fields"][:15]),
            ",".join(date_props),
            ",".join(info["numeric_fields"].keys()),
        ]) + "\n")

with open(NONEMPTY_TSV, "w", encoding="utf-8") as f:
    f.write("set\tn_rows\tcategories\tfields\n")
    for info in index:
        if info["n_rows"] == 0:
            continue
        f.write("\t".join([
            info["set"],
            str(info["n_rows"]),
            ",".join(info["categories"]),
            ",".join(info["fields"][:30]),
        ]) + "\n")

print(f"Indexed {len(index)} dumps")
print(f"Non-empty: {sum(1 for x in index if x['n_rows']>0)}")
