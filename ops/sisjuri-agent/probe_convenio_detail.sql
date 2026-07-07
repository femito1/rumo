-- Probe: CLOSE the last 2 residuals (EHF +558,20, RB +901,49). Both equal the
-- gap between LANCAMENTO convênio (0110) net and the ledger's convênio figure:
--   EHF: LANCAMENTO 2.122,30 vs ledger 1.564,10  (Δ 558,20)
--   RB:  LANCAMENTO 3.427,58 vs ledger 2.526,09  (Δ 901,49)
-- Hypothesis: 0110 bundles titular + dependent(s); the ledger books only part,
-- OR net vs a liquido. Break 0110 by histórico / row so we see the sub-amounts.
-- If a stable "dependente"/"titular" split exists we encode it; else it's a
-- per-lawyer manual nuance. Read-only, Feb 2026 (+ a couple months to test stability).
SET DEFINE OFF
SET PAGESIZE 1000
SET LINESIZE 340
SET FEEDBACK ON
COL prof FORMAT A6
COL hist FORMAT A55
COL mes FORMAT A7
WHENEVER SQLERROR CONTINUE

PROMPT === 1. Convênio 0110 raw rows for EHF/RB (all cols that could carry titular/dependente) ===
SELECT l.LANCPROFDEST prof, ROUND(l.LANNVALOR,2) net,
       SUBSTR(l.LANCHISTORICO,1,55) hist, l.LANDDATA
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0110'
   AND l.LANCPROFDEST IN ('EHF','RB')
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 ORDER BY l.LANCPROFDEST, l.LANNVALOR;

PROMPT === 2. Convênio 0110 by (prof, histórico) ALL lawyers Feb — is there a dependente line? ===
SELECT l.LANCPROFDEST prof, SUBSTR(l.LANCHISTORICO,1,45) hist,
       ROUND(SUM(l.LANNVALOR),2) net, COUNT(*) n
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0110'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 GROUP BY l.LANCPROFDEST, SUBSTR(l.LANCHISTORICO,1,45)
 ORDER BY l.LANCPROFDEST, net DESC;

PROMPT === 3. Convênio 0110 per (prof, month) Jan..Mai — is the EHF/RB extra STABLE? ===
SELECT l.LANCPROFDEST prof, TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
       ROUND(SUM(l.LANNVALOR),2) net, COUNT(*) n
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0110'
   AND l.LANCPROFDEST IN ('EHF','RB','IAC','FSM','AM','DC')
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY l.LANCPROFDEST, TO_CHAR(l.LANDDATA,'YYYY-MM')
 ORDER BY l.LANCPROFDEST, mes;

PROMPT === 4. Is there a dependente/beneficiario table for convênio? dictionary scan ===
SELECT owner, table_name FROM ALL_TABLES
 WHERE (table_name LIKE '%DEPENDENTE%' OR table_name LIKE '%BENEFIC%'
        OR table_name LIKE '%CONVENIO%' OR table_name LIKE '%PLANOSAUDE%')
   AND owner IN ('LDESK','SSJR','FINANCE') ORDER BY owner, table_name;

EXIT
