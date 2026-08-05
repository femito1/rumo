"""Render a repo markdown document to a printable A4 PDF, via headless Chrome.

Written for the client-facing `docs/DIFERENCAS_ACUMULADO_2026.md`, which finance reads next
to their own workbook. Two properties matter more than looking pretty:

* **The wide tables must stay readable.** The account breakdown has seven columns and cells
  that hold several lançamentos each, so the page is landscape and the account lists wrap
  inside their cell rather than forcing the table off the page.
* **Nothing may be silently dropped.** ``markdown`` needs the ``tables`` extension or every
  pipe table renders as a paragraph of pipes — quietly, with no error. The script asserts
  the rendered HTML contains as many ``<table>`` elements as the source has tables.

Chrome is used because it is what this box has (no pandoc/weasyprint); its ``--print-to-pdf``
honours ``@page`` and CSS well enough for a document like this one.

Run: cd backend && python -m scripts.md_to_pdf [<caminho.md>] [-o <saida.pdf>]
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PADRAO = REPO / "docs" / "DIFERENCAS_ACUMULADO_2026.md"

CSS = """
@page { size: A4 landscape; margin: 12mm 10mm; }
body {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 8.5pt; line-height: 1.45; color: #1a1a1a; margin: 0;
}
h1 { font-size: 17pt; margin: 0 0 2mm; color: #111; }
h2 {
  font-size: 12.5pt; margin: 7mm 0 2mm; padding-bottom: 1mm;
  border-bottom: 1.5px solid #333; page-break-after: avoid;
}
h3 { font-size: 10.5pt; margin: 5mm 0 1.5mm; page-break-after: avoid; }
h4 { font-size: 9.5pt; margin: 4mm 0 1.5mm; color: #333; page-break-after: avoid; }
p, ul, ol { margin: 0 0 2mm; }
li { margin-bottom: 0.8mm; }
strong { color: #000; }
code {
  font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 0.9em;
  background: #f2f2f2; padding: 0.4mm 1mm; border-radius: 2px;
}
table {
  border-collapse: collapse; width: 100%; margin: 2mm 0 4mm;
  font-size: 7.6pt; page-break-inside: auto;
}
/* Keep a row intact; a lançamento list split across pages is unreadable. */
tr { page-break-inside: avoid; }
thead { display: table-header-group; }
th, td {
  border: 0.5px solid #c4c4c4; padding: 1.1mm 1.6mm;
  text-align: left; vertical-align: top; word-break: break-word;
}
th { background: #ececec; font-weight: 600; white-space: nowrap; }
/* markdown's ---: alignment lands as inline style="text-align: right" */
td[style*="right"], th[style*="right"] { white-space: nowrap; }
/* One lançamento per line inside a cell, tight enough that a 4-entry list still fits. */
td br { line-height: 1.3; }
tbody tr:nth-child(even) { background: #fafafa; }
blockquote { margin: 2mm 0; padding-left: 3mm; border-left: 2px solid #ccc; color: #444; }
em { color: #333; }
"""


def _n_tabelas(md: str) -> int:
    """How many pipe tables the SOURCE has, counted by their separator row."""
    return len(re.findall(r"^\|[\s:|-]+\|\s*$", md, flags=re.MULTILINE))


#: Cells in the account breakdown hold several lançamentos, separated by ``<br>`` so each
#: sits on its own line. A markdown formatter (VS Code's, for one) strips those tags while
#: re-aligning the tables, which silently glues the lançamentos into one run-on line —
#: "R$ 919,76 r104 Manutenção do Jardim · R$ 836,00 r106 …". The PDF is what the client
#: reads, so detect it and re-break rather than trusting the file to be pristine.
#: A break belongs between two lançamentos in the SAME cell: after a **money value**, before
#: the next entry. Both halves are load-bearing and each was got wrong once:
#: * looking across a ``|`` fires at every cell boundary (7 phantom breaks in a clean file);
#: * requiring only "a digit" before the break splits ``r129 Associações`` right after the
#:   row number, because the name that follows also looks like the start of an entry.
#: So: the left side must be a ``R$ n,nn`` value, and matching is done per cell.
_LANC = re.compile(
    r"(?<=\d,\d\d)\s+(?=r\d{2,3} |[A-ZÁÂÃÉÊÍÓÔÕÚÇ][^·]*· R\$)"
)


def _rebreak(md: str) -> tuple[str, int]:
    """Restore the line breaks between lançamentos inside a table cell.

    Splits each table row into cells and only re-breaks a cell that holds MORE THAN ONE
    ``· R$`` value — a single-lançamento cell has nothing to break, and treating the end of
    it as a break point is exactly the bug this guards against. Returns the text and how
    many breaks were inserted, so the caller reports it instead of fixing silently.
    """
    out, n = [], 0
    for line in md.splitlines():
        if not (line.startswith("|") and "·" in line and "<br>" not in line):
            out.append(line)
            continue
        celulas = line.split("|")
        for i, cel in enumerate(celulas):
            if cel.count("· R$") < 2:
                continue
            celulas[i], k = _LANC.subn("<br>", cel)
            n += k
        out.append("|".join(celulas))
    return "\n".join(out), n


def render(md_path: Path, out_path: Path) -> None:
    import markdown

    md = md_path.read_text(encoding="utf-8")
    md, remendos = _rebreak(md)
    if remendos:
        print(
            f"aviso: {remendos} quebras de linha reinseridas — o .md perdeu os <br> das "
            "células (formatador de markdown). O PDF sai correto; regenere o .md com "
            "build_diferencas_doc.py para corrigir a fonte."
        )
    corpo = markdown.markdown(md, extensions=["tables", "sane_lists"])

    esperadas = _n_tabelas(md)
    obtidas = corpo.count("<table>")
    if obtidas != esperadas:
        raise SystemExit(
            f"tabelas: fonte tem {esperadas}, HTML tem {obtidas} — "
            "a extensão 'tables' falhou e o PDF sairia com canos no lugar das tabelas"
        )

    html = (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        f"<title>{md_path.stem}</title><style>{CSS}</style></head>"
        f"<body>{corpo}</body></html>"
    )

    chrome = next(
        (
            c
            for c in ("google-chrome", "chromium", "chromium-browser", "chrome")
            if shutil.which(c)
        ),
        None,
    )
    if chrome is None:
        raise SystemExit("nenhum Chrome/Chromium encontrado no PATH")

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "doc.html"
        html_path.write_text(html, encoding="utf-8")
        # --no-pdf-header-footer drops Chrome's own URL/date furniture; the document
        # already carries its own extraction date in the first paragraph.
        proc = subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--user-data-dir={tmp}/profile",
                "--no-pdf-header-footer",
                f"--print-to-pdf={out_path}",
                html_path.as_uri(),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
    if not out_path.exists() or out_path.stat().st_size == 0:
        sys.stderr.write(proc.stderr[-2000:] + "\n")
        raise SystemExit("Chrome não gerou o PDF")

    print(
        f"wrote {out_path.relative_to(REPO)}  "
        f"({out_path.stat().st_size / 1024:.0f} KB, {esperadas} tabelas)"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("md", nargs="?", default=str(PADRAO), help="arquivo .md de entrada")
    ap.add_argument("-o", "--out", default=None, help="arquivo .pdf de saída")
    a = ap.parse_args()
    md_path = Path(a.md).resolve()
    if not md_path.is_file():
        raise SystemExit(f"não encontrei {md_path}")
    out = Path(a.out).resolve() if a.out else md_path.with_suffix(".pdf")
    render(md_path, out)


if __name__ == "__main__":
    main()
