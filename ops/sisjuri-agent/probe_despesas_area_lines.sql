-- probe_despesas_area_lines.sql  (GAP 2, v3 — line-level, stop guessing sums)
-- MAY workbook "Despesas Área": Contencioso 2.276,22 · Econômico 2.300,10 ·
-- Arbitragem 1.204,47 (Σ 5.780,79). Arbitragem = 020.060.0020 Patrocínio exactly.
-- Contencioso/Econômico are NOT whole-account sums → they are SLICES of accounts
-- split across areas (desdobramento, keyed per-line). Dump the raw lines so we can
-- SEE the composition + the split key instead of brute-forcing sums.
--
-- The workbook values carry a ,215/,095 fractional → smells like a ÷2 split (the
-- known two-area-lawyer pattern). Confirm from the line detail.
--
-- ⚠ SQL: single concatenated SELECT column → ORDER BY 1 or none. NEVER ORDER BY 2.
-- Read-only. Pipe-tagged.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A CONTASPAGAR full column list (find the ORIENTAÇÃO / área / prof-dest column names)
SELECT 'A|'||COLUMN_NAME||'|'||DATA_TYPE
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='FINANCE' AND TABLE_NAME='CONTASPAGAR'
 ORDER BY COLUMN_NAME;

PROMPT #B Every 020.* LINE in May: conta | valores | COD_ADVG | SIGLA | histórico (one row per pay line)
SELECT 'B|'||cp.PCTCNUMEROCONTA
       ||'|liq='||TO_CHAR(ROUND(cp.CPGNVALORLIQUIDO,2))
       ||'|base='||TO_CHAR(ROUND(cp.CPGNVALORBASE,2))
       ||'|adv='||NVL(cp.COD_ADVG,'-')
       ||'|sig='||NVL(cp.SIGLA,'-')
       ||'|'||SUBSTR(REPLACE(NVL(cp.CPGCHISTORICO,' '),'|','/'),1,50)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '020.%'
 ORDER BY 1;

PROMPT #C CPDESDOBRAMENTO rows whose DESTINO is a 020.* account, May (the split slices)
-- If a lump is desdobrada across areas, each slice is a row here. This is where a
-- 2.276,22 / 2.300,10 split would live if it's an unfolded account.
SELECT 'C|'||d.DESCCONTADESTINO
       ||'|val='||TO_CHAR(ROUND(d.DESNVALOR,2))
       ||'|'||SUBSTR(REPLACE(NVL(d.DESCHISTORICO,' '),'|','/'),1,60)
  FROM FINANCE.CPDESDOBRAMENTO d
  JOIN FINANCE.CONTASPAGAR cp
    ON cp.EMPNCOD=d.EMPNCOD AND cp.CPGCNUMEROPAGAR=d.CPGCNUMEROPAGAR
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND d.DESCCONTADESTINO LIKE '020.%'
 ORDER BY 1;

PROMPT #D CPDESDOBRAMENTO full column list (look for an área/grupo/prof/orientação tag on the slice)
SELECT 'D|'||COLUMN_NAME||'|'||DATA_TYPE
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='FINANCE' AND TABLE_NAME='CPDESDOBRAMENTO'
 ORDER BY COLUMN_NAME;

PROMPT #E The three candidate accounts' lines with EVERY value column (spot a ÷2 or partial)
-- 020.040.0010 (SMS/métricas, tot 9252.45), 020.090.0010 (passagens 1426.72),
-- 020.060.0020 (patrocínio 1204.47). Show base/bruto/liquido/despesa to see splits.
SELECT 'E|'||cp.PCTCNUMEROCONTA||'|pagar='||cp.CPGCNUMEROPAGAR
       ||'|base='||TO_CHAR(ROUND(cp.CPGNVALORBASE,2))
       ||'|bruto='||TO_CHAR(ROUND(cp.CPGNVALORBRUTO,2))
       ||'|liq='||TO_CHAR(ROUND(cp.CPGNVALORLIQUIDO,2))
       ||'|'||SUBSTR(REPLACE(NVL(cp.CPGCHISTORICO,' '),'|','/'),1,40)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA IN ('020.040.0010','020.090.0010','020.060.0020')
 ORDER BY 1;

PROMPT #END target: Contencioso 2276.22 / Econômico 2300.10 / Arbitragem 1204.47 (Σ 5780.79)
