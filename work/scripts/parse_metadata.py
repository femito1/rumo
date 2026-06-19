"""Parse OData v3 $metadata to map EntitySet -> EntityType -> properties (with types & keys)."""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

META = Path("/home/nandoravioli/bia4u/rumo/work/api_dumps/_metadata.xml")
OUT = Path("/home/nandoravioli/bia4u/rumo/work/analysis/entities.json")
OUT_TSV = Path("/home/nandoravioli/bia4u/rumo/work/analysis/entities.tsv")

NS = {
    "edmx": "http://schemas.microsoft.com/ado/2007/06/edmx",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
    "edm": "http://schemas.microsoft.com/ado/2009/11/edm",
}

tree = ET.parse(META)
root = tree.getroot()

# Detect edm namespace version (v3 commonly 2009/11/edm)
edm_ns = None
for child in root.iter():
    if child.tag.endswith("}Schema"):
        edm_ns = child.tag.split("}")[0].lstrip("{")
        break
NS["edm"] = edm_ns
print("EDM namespace:", edm_ns)

# Build EntityType registry: name -> { keys, properties: [{name,type,nullable}] }
entity_types = {}
for schema in root.iter(f"{{{edm_ns}}}Schema"):
    schema_ns = schema.attrib.get("Namespace", "")
    for et in schema.findall(f"{{{edm_ns}}}EntityType"):
        name = et.attrib.get("Name")
        full = f"{schema_ns}.{name}"
        keys = []
        key_el = et.find(f"{{{edm_ns}}}Key")
        if key_el is not None:
            keys = [pr.attrib["Name"] for pr in key_el.findall(f"{{{edm_ns}}}PropertyRef")]
        props = []
        for p in et.findall(f"{{{edm_ns}}}Property"):
            props.append({
                "name": p.attrib.get("Name"),
                "type": p.attrib.get("Type"),
                "nullable": p.attrib.get("Nullable", "true"),
            })
        entity_types[full] = {"keys": keys, "properties": props, "short": name}
        # also index by short name for resolution
        entity_types.setdefault(name, entity_types[full])

# Build EntitySet -> EntityType map
sets = []
for cont in root.iter(f"{{{edm_ns}}}EntityContainer"):
    for es in cont.findall(f"{{{edm_ns}}}EntitySet"):
        es_name = es.attrib["Name"]
        et_full = es.attrib["EntityType"]
        et = entity_types.get(et_full) or entity_types.get(et_full.split(".")[-1])
        if et is None:
            sets.append({"set": es_name, "entity_type": et_full, "keys": [], "properties": []})
            continue
        sets.append({
            "set": es_name,
            "entity_type": et_full,
            "keys": et["keys"],
            "properties": et["properties"],
        })

OUT.write_text(json.dumps(sets, indent=2, ensure_ascii=False))

with open(OUT_TSV, "w", encoding="utf-8") as f:
    f.write("set\tn_props\tn_date_props\tdate_props\thas_valor\thas_data\thas_recebimento\thas_caso\thas_cliente\tprops_sample\n")
    for s in sets:
        prop_names = [p["name"] for p in s["properties"]]
        date_props = [p["name"] for p in s["properties"] if p["type"] and ("Date" in p["type"] or "DateTime" in p["type"])]
        valor = any("valor" in p.lower() for p in prop_names)
        data = any(p.lower().startswith("data") for p in prop_names)
        recebimento = any("recebimento" in p.lower() for p in prop_names)
        caso = any("caso" in p.lower() for p in prop_names)
        cliente = any("cliente" in p.lower() for p in prop_names)
        f.write("\t".join([
            s["set"],
            str(len(prop_names)),
            str(len(date_props)),
            ",".join(date_props),
            str(valor),
            str(data),
            str(recebimento),
            str(caso),
            str(cliente),
            ",".join(prop_names[:25]),
        ]) + "\n")

print(f"Total entity sets: {len(sets)}")
print(f"With Date* property: {sum(1 for s in sets if any('Date' in (p['type'] or '') for p in s['properties']))}")
print(f"With Valor* property: {sum(1 for s in sets if any('valor' in p['name'].lower() for p in s['properties']))}")
