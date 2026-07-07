-- Probe: CLOSE the last 5 per-lawyer residuals in Custo equipe reconciliation.
-- Feb recipe (0010 gross ex-Bônus + 0130 gross + 0110 net, area=home+AM50/50)
-- reconciled 8/13 to the centavo. Remaining, and the hypotheses to test:
--   AM -108,70 / DC -108,70  : identical -> a shared small line (AASP 0150? IR? ISS?)
--   JGS +1.911,95            : == his convênio -> ledger caps JGS at round 11.000?
--   RB  +901,49 / EHF +558,20: lawyer-specific (bolsa/IR/reajuste/timing?)
-- Strategy: pull EVERY 030.010.* account for these lawyers, BOTH net (LANCAMENTO by
-- LANCPROFDEST) and gross (CONTASPAGAR by COD_ADVG), for Jan..Mai so we see if the
-- residual is stable (=> config) or varies (=> genuine monthly manual). Read-only.
SET DEFINE OFF
SET PAGESIZE 2000
SET LINESIZE 340
SET FEEDBACK ON
COL prof FORMAT A6
COL conta FORMAT A16
COL mes FORMAT A7
WHENEVER SQLERROR CONTINUE

PROMPT === 1. NET by (prof, account, month) for the 5 residual lawyers, Jan..Mai ===
SELECT l.LANCPROFDEST AS prof, l.PCTCNUMEROCONTADEST AS conta,
       TO_CHAR(l.LANDDATA,'YYYY-MM') AS mes, ROUND(SUM(l.LANNVALOR),2) net
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '030.010.%'
   AND l.LANCPROFDEST IN ('AM','DC','JGS','RB','EHF')
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY l.LANCPROFDEST, l.PCTCNUMEROCONTADEST, TO_CHAR(l.LANDDATA,'YYYY-MM')
 ORDER BY l.LANCPROFDEST, mes, conta;

PROMPT === 2. GROSS by (prof, account, month) via CONTASPAGAR for the same lawyers ===
SELECT cp.COD_ADVG AS prof, cp.PCTCNUMEROCONTA AS conta,
       TO_CHAR(cp.CPGDVECTO,'YYYY-MM') AS mes, ROUND(SUM(cp.CPGNVALORBASE),2) base
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.PCTCNUMEROCONTA LIKE '030.010.%'
   AND cp.COD_ADVG IN ('AM','DC','JGS','RB','EHF')
   AND cp.CPGDVECTO >= DATE '2026-01-01' AND cp.CPGDVECTO < DATE '2026-06-01'
 GROUP BY cp.COD_ADVG, cp.PCTCNUMEROCONTA, TO_CHAR(cp.CPGDVECTO,'YYYY-MM')
 ORDER BY cp.COD_ADVG, mes, conta;

PROMPT === 3. AM & DC full account list Feb (find the shared -108,70 line; AASP 0150?) ===
SELECT l.LANCPROFDEST AS prof, l.PCTCNUMEROCONTADEST AS conta,
       ROUND(SUM(l.LANNVALOR),2) net, SUBSTR(MAX(l.LANCHISTORICO),1,40) hist
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANCPROFDEST IN ('AM','DC')
   AND l.PCTCNUMEROCONTADEST LIKE '030.%'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 GROUP BY l.LANCPROFDEST, l.PCTCNUMEROCONTADEST
 ORDER BY l.LANCPROFDEST, conta;

PROMPT === 4. JGS all rows Feb across ALL accounts (is 11.000 a cap? where does convênio go?) ===
SELECT l.LANCPROFDEST AS prof, l.PCTCNUMEROCONTADEST AS conta,
       ROUND(SUM(l.LANNVALOR),2) net, SUBSTR(MAX(l.LANCHISTORICO),1,45) hist
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANCPROFDEST='JGS'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 GROUP BY l.LANCPROFDEST, l.PCTCNUMEROCONTADEST
 ORDER BY conta;

PROMPT === 5. Distinct 0010 histórico patterns Jan..Mai (catalog Fixa/Reajuste/Bônus/Diferença) ===
SELECT SUBSTR(REGEXP_REPLACE(l.LANCHISTORICO,'[0-9]',''),1,40) AS hist_pattern,
       COUNT(*) n, ROUND(SUM(l.LANNVALOR),2) net
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY SUBSTR(REGEXP_REPLACE(l.LANCHISTORICO,'[0-9]',''),1,40)
 ORDER BY net DESC;

EXIT
