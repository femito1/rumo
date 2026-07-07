-- Probe: the per-lawyer AMOUNT gap on account 030.010.0010. Area assignment is
-- solved (home area + AM 50/50 via CAD_RATEIO_GRUPO); the residual per-area error
-- is because some lawyers' NET 0010 total != the ledger's "Distribuição Fixa"
-- figure (e.g. JGS net 15.886 vs ledger 9.379; RB net 17.326 vs ledger 23.379).
-- The ledger splits 0010 into "Distribuição Mensal Fixa" + "Reajuste" (+ maybe DL
-- diferença / bônus). See the raw rows + histórico to learn the sub-structure.
-- Read-only, Feb 2026.
SET DEFINE OFF
SET PAGESIZE 1000
SET LINESIZE 340
SET FEEDBACK ON
COL prof FORMAT A8
COL hist FORMAT A55
WHENEVER SQLERROR CONTINUE

PROMPT === 1. Raw 030.010.0010 rows for the mismatch lawyers (JGS, RB, DC, IAC, FSM), Feb ===
PROMPT     Each row's histórico tells us Fixa vs Reajuste vs Diferença vs Bônus.
SELECT l.LANCPROFDEST AS prof, l.SIGLADEST AS cc, ROUND(l.LANNVALOR,2) net,
       SUBSTR(l.LANCHISTORICO,1,55) AS hist, l.LANDDATA
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
   AND l.LANCPROFDEST IN ('JGS','RB','DC','IAC','FSM')
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 ORDER BY l.LANCPROFDEST, l.LANNVALOR;

PROMPT === 2. ALL 0010 rows Feb by (prof, histórico) — the sub-type breakdown ===
SELECT l.LANCPROFDEST AS prof, SUBSTR(l.LANCHISTORICO,1,45) AS hist,
       ROUND(SUM(l.LANNVALOR),2) net, COUNT(*) n
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 GROUP BY l.LANCPROFDEST, SUBSTR(l.LANCHISTORICO,1,45)
 ORDER BY l.LANCPROFDEST, net DESC;

PROMPT === 3. CONTASPAGAR 0010 by (prof, histórico) — GROSS sub-types (ledger uses gross) ===
SELECT cp.COD_ADVG AS prof, SUBSTR(cp.CPGCHISTORICO,1,45) AS hist,
       ROUND(SUM(cp.CPGNVALORBASE),2) base, ROUND(SUM(cp.CPGNVALORLIQUIDO),2) liq, COUNT(*) n
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.PCTCNUMEROCONTA='030.010.0010'
   AND cp.CPGDVECTO >= DATE '2026-02-01' AND cp.CPGDVECTO < DATE '2026-03-01'
 GROUP BY cp.COD_ADVG, SUBSTR(cp.CPGCHISTORICO,1,45)
 ORDER BY cp.COD_ADVG, base DESC;

EXIT
