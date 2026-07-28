# Reference artifacts

Ground-truth files used during LegalDesk/SISJURI investigation and workbook validation.
**Not used at runtime** — the app reads live API data, the SISJURI snapshot store, or test
fixtures. These are the source-of-truth exports we reconcile against.

## Workbooks (the "number of record")
| Path | Description |
| --- | --- |
| `workbook/Fechamento MBC 05.2026.xlsx` | **Authoritative** reference book (05.2026 wins on conflict) |
| `workbook/Fechamento MBC 06.2026.xlsx` | June book — the untuned validation month (2026-07 checkpoint) |
| `workbook/Copy of Fechamento MBC 02.2026.xlsx` | Earlier sample (structure reference) |
| `workbook/MBC_formula_audit_v2.xlsx` | Formula audit workbook |
| `workbook/Guia_entendimento_workbook_MBC_02_2026.docx` | Workbook walkthrough (PT-BR) |

## Raw SISJURI / LegalDesk exports (used to prove numbers)
| Path | Description |
| --- | --- |
| `workbook/lancextrato de contas.xls` · `...junho.pdf` | Raw "Extrato de Contas" (FINANCE.LANCAMENTO) — May + June |
| `workbook/Pagtos maio.XLS.xlsx` | CONTASPAGAR (carries bruto AND líquido) |
| `workbook/PLANO CONTAS.XLS.xlsx` · `plano_contas_dump.csv` | Chart of accounts |
| `workbook/Demonstrativo_Resultado_Profissional_*.pdf` | Per-professional recebimento allocation report |
| `workbook/MBC Resultado Jan a Mai 2026.pdf` | Client dashboard (YTD) |
| `workbook/Juritis LegalDesk API.postman_collection.json` | Postman collection for OData exploration |

## Presentations & meetings
| Path | Description |
| --- | --- |
| `workbook/MBC_JanJun_2026.pptx` | Rumo's monthly client deck — the template the presentation panel mirrors |
| `workbook/Pontos da Reuniao com RUMO em 10JUL2026.xlsx` | Meeting points (2026-07-10) |
| `workbook/Transcript - Checkpoint c RUMO - projeto MBC.docx` · `meeting_transcript.MD` | Meeting transcripts |
| `comparativo/` | Generated 3-way comparison spreadsheets (proof-of-match) |

Business rules from the meetings: `docs/MEETING_2026-07-10.md`. Client-facing summary:
`docs/NOTA_CLIENTE.md`. API behaviour + sacred numbers: `docs/LEGALDESK.md`.
