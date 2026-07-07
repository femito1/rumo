-- Probe: is Aurelio Marchini Santos' (AM) cross-area distribuição split
-- (50% Contencioso / 50% Econômico in the ledger) recorded ANYWHERE in the DB?
-- SIGLADEST and home grupo both say 100% Econômico. This is the LAST unknown
-- blocking full automation of per-area Custo equipe. Read-only.
SET DEFINE OFF
SET PAGESIZE 400
SET LINESIZE 400
SET FEEDBACK ON
WHENEVER SQLERROR CONTINUE

PROMPT === A. AM raw LANCAMENTO rows (030.010.0010), UNGROUPED, all area-bearing cols, Feb 2026 ===
PROMPT     Looking for two rows / two cost-centers / a caso / cliente that encodes the split.
SELECT l.COD_ADVG, l.SIGLADEST, l.SIGLAORG, l.LANNVALOR,
       l.LANNCASODEST, l.LANNCLIENTEDEST, l.LANCPROFDEST, l.LANCPROFORG,
       SUBSTR(l.LANCHISTORICO,1,50) AS hist
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
   AND l.COD_ADVG='AM'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 ORDER BY l.LANNVALOR;

PROMPT === B. Is there a per-professional -> multiple grupo (rateio) table? Search dictionary ===
SELECT owner, table_name FROM ALL_TABLES
 WHERE (table_name LIKE '%RATEIO%' OR table_name LIKE '%PROF%GRUPO%'
        OR table_name LIKE '%GRUPO%PROF%' OR table_name LIKE '%PROFISSIONAL%GRUPO%')
   AND owner IN ('LDESK','SSJR','FINANCE') ORDER BY owner, table_name;

PROMPT === C. Does CAD_PROFISSIONAL have a secondary/percent-area column for AM? ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE owner='LDESK' AND table_name='CAD_PROFISSIONAL'
   AND (column_name LIKE '%GRUPO%' OR column_name LIKE '%AREA%'
        OR column_name LIKE '%PERC%' OR column_name LIKE '%RATEIO%');

PROMPT === D. AM CONTASPAGAR rows (gross) for distribuição, ungrouped, all cols that could carry area ===
SELECT cp.COD_ADVG, cp.SIGLA, cp.CPGNVALORBASE, cp.CPGNVALORBRUTO, cp.CPGNVALORLIQUIDO,
       cp.ID_PROJETO, SUBSTR(cp.CPGCHISTORICO,1,50) AS hist
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.PCTCNUMEROCONTA='030.010.0010'
   AND cp.COD_ADVG='AM'
   AND cp.CPGDVECTO >= DATE '2026-02-01' AND cp.CPGDVECTO < DATE '2026-03-01';

PROMPT === E. All distinct SIGLADEST values that appear for 030.010.0010 (the CC universe) ===
SELECT l.SIGLADEST, COUNT(*) n, ROUND(SUM(l.LANNVALOR),2) tot
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 GROUP BY l.SIGLADEST ORDER BY l.SIGLADEST;

EXIT
