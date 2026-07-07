-- Probe: get the FULL untruncated convênio histórico for EHF/RB and hunt the
-- titular-only figure the ledger uses (EHF ledger 1.564,10 vs LANCAMENTO 2.122,30;
-- RB 2.526,09 vs 3.427,58). The histórico literally says "A parte de dependentes"
-- -> DB bundles titular+dependente in ONE 0110 row. Does the titular-only amount
-- live in CONTASPAGAR, account 0120, or must it be parsed from the histórico text?
-- Read-only, Feb..Mai 2026.
SET DEFINE OFF
SET PAGESIZE 1000
SET LINESIZE 600
SET LONG 4000
SET FEEDBACK ON
COL prof FORMAT A6
COL hist FORMAT A200
COL mes FORMAT A7
WHENEVER SQLERROR CONTINUE

PROMPT === 1. FULL convênio histórico for EHF/RB (untruncated), Feb..Mai ===
SELECT l.LANCPROFDEST prof, TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
       ROUND(l.LANNVALOR,2) net, l.LANCHISTORICO hist
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0110'
   AND l.LANCPROFDEST IN ('EHF','RB')
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-06-01'
 ORDER BY prof, mes;

PROMPT === 2. Convênio 0110 CONTASPAGAR side for EHF/RB (maybe titular-only here) ===
SELECT cp.COD_ADVG prof, TO_CHAR(cp.CPGDVECTO,'YYYY-MM') mes,
       ROUND(SUM(cp.CPGNVALORBASE),2) base, ROUND(SUM(cp.CPGNVALORLIQUIDO),2) liq,
       COUNT(*) n
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.PCTCNUMEROCONTA='030.010.0110' AND cp.COD_ADVG IN ('EHF','RB')
   AND cp.CPGDVECTO >= DATE '2026-02-01' AND cp.CPGDVECTO < DATE '2026-06-01'
 GROUP BY cp.COD_ADVG, TO_CHAR(cp.CPGDVECTO,'YYYY-MM')
 ORDER BY prof, mes;

PROMPT === 3. Account 0120 (Participação I) for EHF/RB — the ledger's other convênio piece? ===
SELECT l.LANCPROFDEST prof, l.PCTCNUMEROCONTADEST conta, TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
       ROUND(SUM(l.LANNVALOR),2) net
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANCPROFDEST IN ('EHF','RB') AND l.PCTCNUMEROCONTADEST IN ('030.010.0120')
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY l.LANCPROFDEST, l.PCTCNUMEROCONTADEST, TO_CHAR(l.LANDDATA,'YYYY-MM')
 ORDER BY prof, mes;

PROMPT === 4. AASP: full histórico of AM 0160 rows (is monthly AASP hidden in ISS-Trimestral?) ===
SELECT l.LANCPROFDEST prof, TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
       ROUND(l.LANNVALOR,2) net, l.LANCHISTORICO hist
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANCPROFDEST='AM' AND l.PCTCNUMEROCONTADEST='030.010.0160'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 ORDER BY mes;

EXIT
