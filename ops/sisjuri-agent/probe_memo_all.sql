-- Dump FULL 030.010.0110 histórico for EHF and RB across ALL months of 2026.
-- The memo (Mar+ EHF, Mar+ RB) contains the ledger convênio as "= R$ X,YY".
-- Confirm this holds for Feb (where memo might be on 500.010 row) and every
-- month — if so, the ledger convênio is DB-derivable via histórico regex. RO.
SET DEFINE OFF
SET PAGESIZE 500
SET LINESIZE 400
SET LONG 4000
SET FEEDBACK ON
COL prof FORMAT A6
COL mes FORMAT A7
COL hist FORMAT A280
WHENEVER SQLERROR CONTINUE

PROMPT === EHF/RB 030.010.0110 full LANCHISTORICO, Jan..Mai 2026 ===
SELECT l.LANCPROFDEST prof, TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
       ROUND(l.LANNVALOR,2) net, l.LANCHISTORICO hist
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0110'
   AND l.LANCPROFDEST IN ('EHF','RB')
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 ORDER BY prof, mes;

PROMPT === EHF/RB 500.010.<SIGLA> full LANCHISTORICO, Jan..Mai 2026 ===
SELECT l.PCTCNUMEROCONTADEST conta, TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
       ROUND(l.LANNVALOR,2) net, l.LANCHISTORICO hist
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST IN ('500.010.EHF','500.010.RB')
   AND UPPER(l.LANCHISTORICO) LIKE '%CONV%'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 ORDER BY conta, mes;

PROMPT === Check: does every OTHER convênio row (all lawyers) also carry the memo? ===
PROMPT     If yes, the parse rule generalizes; if no, EHF/RB are the only two using it.
SELECT l.LANCPROFDEST prof, TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
       ROUND(l.LANNVALOR,2) net,
       CASE WHEN UPPER(l.LANCHISTORICO) LIKE '%PARTE MBC%' THEN 'YES' ELSE 'no' END has_mbc,
       CASE WHEN INSTR(l.LANCHISTORICO,'=')>0 THEN 'YES' ELSE 'no' END has_eq
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0110'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 ORDER BY prof;

EXIT
