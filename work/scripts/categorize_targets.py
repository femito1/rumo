"""Categorize the 72 manual inputs into target groups for API matching."""
import json
from pathlib import Path

src = Path("/home/nandoravioli/bia4u/rumo/work/analysis/manual_inputs.json")
rows = json.loads(src.read_text())

CATEGORIES = [
    ("revenue_honorarios", lambda l: "Receita de honorários" in l),
    ("pro_labore", lambda l: "pro labore" in l.lower() or "pro-labore" in l.lower()),
    ("distribuicao_mensal_fixa", lambda l: "distribuição mensal fixa" in l.lower() or "distribuicao mensal fixa" in l.lower() or "reajuste de distribuição" in l.lower()),
    ("convenio_medico", lambda l: "convenio medico" in l.lower() or "convênio médico" in l.lower()),
    ("aasp_associacoes", lambda l: l.strip().endswith("- AASP") or l.lower().startswith("assinaturas") or l.lower().startswith("associações")),
    ("vale_refeicao_transporte", lambda l: "vale refeição" in l.lower() or "vale refeicao" in l.lower() or "vale transporte" in l.lower()),
    ("bolsa_estagiarios", lambda l: "bolsa" in l.lower() and "estag" in l.lower()),
    ("subsidio_pos", lambda l: "subsidio de pós" in l.lower() or "subsidio de pos" in l.lower()),
    ("salario_adm_ferias", lambda l: l.lower() in {"salario adm", "férias", "vale refeição- adm"}),
    ("ocupacao", lambda l: l.lower() in {"aluguel", "condomínio", "energia", "iptu", "seguro locação", "telefonia fixa"}),
    ("despesas_gerais", lambda l: l.lower() in {"limpeza e copeira - serviço terceirizado", "manutenção ar condicionado", "manutenção do escritório", "manutenção do jardim", "material de escritório", "motoboy", "oab / cs"}),
    ("consultoria_contabilidade", lambda l: "consultoria" in l.lower() or "contabilidade" in l.lower()),
    ("seguros", lambda l: "seguro" in l.lower() and "locação" not in l.lower()),
    ("comissoes_repasses", lambda l: "participação/comissão" in l.lower() or "participacao/comissao" in l.lower()),
    ("eventos_marketing", lambda l: "eventos" in l.lower() or "biblioteca" in l.lower()),
    ("impostos", lambda l: l.upper() in {"COFINS", "CSLL TRIMESTRAL", "E-SOCIAL", "FGTS", "IMPOSTOS 3ºS", "INSS FOLHA E PRO - LABORES", "IRRF FOLHA", "IRRF TRIMESTRAL", "ISS 3ºS", "PIS"}),
    ("ti_software", lambda l: "data center" in l.lower() or "oracle" in l.lower() or "licen" in l.lower() or "suporte de informática" in l.lower()),
]

groups = {name: [] for name, _ in CATEGORIES}
groups["__uncategorized__"] = []

for r in rows:
    label = r["label"]
    placed = False
    for name, pred in CATEGORIES:
        if pred(label):
            groups[name].append(r)
            placed = True
            break
    if not placed:
        groups["__uncategorized__"].append(r)

out = []
out.append("# Manual inputs by category (72 total)\n")
for name in [n for n,_ in CATEGORIES] + ["__uncategorized__"]:
    items = groups[name]
    if not items:
        continue
    out.append(f"## {name}  ({len(items)} rows)")
    for it in items:
        out.append(f"- row {it['row']:>3}: {it['label']}  jan={it['jan_2025_value']}  feb={it['feb_2025_value']}")
    out.append("")

Path("/home/nandoravioli/bia4u/rumo/work/analysis/manual_inputs_by_category.md").write_text("\n".join(out))
print("\n".join(out))
