"""Quick fuzzy match: for each manual-input row in the workbook, search every
dumped JSON file for an exact decimal match to its Jan or Feb value.

This is the brute-force "does the value exist anywhere in the API at all?"
test. We don't yet care about which endpoint or how to filter it; we just
want to know if the answer is reachable.
"""
import json
import re
from pathlib import Path

DUMPS_DIRS = [
    Path("/home/nandoravioli/bia4u/rumo/work/api_dumps"),
    Path("/home/nandoravioli/bia4u/rumo/work/api_dumps_filtered"),
]
TARGETS = json.loads(Path("/home/nandoravioli/bia4u/rumo/work/analysis/manual_inputs.json").read_text())

# Build (value, label, month) tuples to search for
search_terms = []
for t in TARGETS:
    for mk, key in (("jan_2025_value","jan"),("feb_2025_value","feb")):
        v = t.get(mk)
        if v in (None, "", 0): continue
        try:
            f = float(v)
        except Exception: continue
        search_terms.append((f, t["label"], key, t["row"]))

print(f"Search terms: {len(search_terms)}")

# For speed, just textual search over the JSON files for the formatted number
# Try several formats: 279821.07 / 279821 / "279821.07" etc.

def normalize(v):
    s = f"{v:.2f}"
    if s.endswith(".00"): s = s[:-3]
    return s

found = {}
for direc in DUMPS_DIRS:
    for p in direc.iterdir():
        if not p.is_file() or p.suffix != ".json":
            continue
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for v, label, mk, row in search_terms:
            n = normalize(v)
            if n in text:
                found.setdefault((row, label, mk, v), []).append(p.name)

print(f"Hits: {len(found)} of {len(search_terms)}")
out = []
out.append("row\tlabel\tmonth\tvalue\thit_count\tfiles_first3")
for (row,label,mk,v), files in sorted(found.items()):
    out.append(f"{row}\t{label}\t{mk}\t{v}\t{len(files)}\t{', '.join(files[:3])}")
# missed
miss = []
seen = set((r[0],r[1],r[2],r[3]) for r in found.keys())
for v,label,mk,row in search_terms:
    if (row,label,mk,v) not in seen:
        miss.append(f"{row}\t{label}\t{mk}\t{v}\t0\t")
out.extend(miss)
Path("/home/nandoravioli/bia4u/rumo/work/analysis/value_match_report.tsv").write_text("\n".join(out))
print(f"\nFound: {len(found)}/{len(search_terms)}")
print(f"Missed: {len(miss)}")

# Print short summary of which categories matched
def cat(label):
    l = label.lower()
    if "honorário" in l or "honorario" in l or l.startswith("receita"): return "revenue"
    if "convenio medico" in l or "convênio médico" in l: return "convenio_medico"
    if "pro labore" in l or "pro-labore" in l: return "pro_labore"
    if "distribuição mensal fixa" in l: return "dist_mensal_fixa"
    if "aasp" in l: return "aasp"
    if "vale refeição" in l or "vale transporte" in l: return "vale"
    if "salar" in l or "férias" in l: return "salario_adm"
    if l in {"aluguel","condomínio","energia","iptu","seguro locação","telefonia fixa"}: return "ocupacao"
    if "consultoria" in l or "contabilidade" in l: return "consultoria"
    if "seguro" in l: return "seguros"
    if "comiss" in l: return "comissao"
    if l in {"cofins","csll trimestral","e-social","fgts","impostos 3ºs","inss folha e pro - labores","irrf folha","irrf trimestral","iss 3ºs","pis"}: return "imposto"
    if "data center" in l or "oracle" in l: return "ti"
    return "other"

cat_stats = {}
for v,label,mk,row in search_terms:
    c = cat(label)
    cat_stats.setdefault(c,[0,0])[1] += 1
    if (row,label,mk,v) in found:
        cat_stats[c][0] += 1
print("\nCategory match stats (matched / total):")
for c,(m,t) in sorted(cat_stats.items()):
    print(f"  {c:20s}  {m}/{t}")
