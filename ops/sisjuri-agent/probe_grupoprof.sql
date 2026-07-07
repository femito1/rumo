-- Probe: does LDESK.CAD_GRUPOJURPROFISSIONAL (grupo <-> profissional M:N) or a
-- rateio table encode Aurelio's (AM) 50/50 Contencioso/Econômico split? His
-- distribuição is a single EDE row in LANCAMENTO/CONTASPAGAR, so the split must
-- be a static per-professional area mapping if it is derivable at all. Read-only.
SET DEFINE OFF
SET PAGESIZE 500
SET LINESIZE 300
SET FEEDBACK ON
WHENEVER SQLERROR CONTINUE

PROMPT === 1. Columns of CAD_GRUPOJURPROFISSIONAL ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE owner='LDESK' AND table_name='CAD_GRUPOJURPROFISSIONAL' ORDER BY column_id;

PROMPT === 2. AM's grupo memberships (does he belong to TWO grupos?) ===
PROMPT     Join to grupo names. If AM -> {Contencioso, Econômico} that IS the split signal.
SELECT gp.*, g.NOME AS grupo_nome
  FROM LDESK.CAD_GRUPOJURPROFISSIONAL gp
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g
    ON g.ID_GRUPOJURIDICO = gp.ID_GRUPOJURIDICO
 WHERE gp.SIGLA = 'AM' OR gp.COD_ADVG = 'AM';

PROMPT === 3. Full map: every professional -> grupos, so we see who is multi-area ===
SELECT gp.SIGLA, gp.COD_ADVG, g.NOME AS grupo_nome
  FROM LDESK.CAD_GRUPOJURPROFISSIONAL gp
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g
    ON g.ID_GRUPOJURIDICO = gp.ID_GRUPOJURIDICO
 ORDER BY gp.SIGLA, g.NOME;

PROMPT === 4. Any percentage column? Dump CAD_RATEIO_GRUPO + CAD_RATEIOADVG_HIST cols ===
SELECT 'CAD_RATEIO_GRUPO' tbl, column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE owner='LDESK' AND table_name='CAD_RATEIO_GRUPO'
UNION ALL
SELECT 'CAD_RATEIOADVG_HIST', column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE owner='SSJR' AND table_name='CAD_RATEIOADVG_HIST'
 ORDER BY 1,2;

PROMPT === 5. AM in CAD_RATEIOADVG_HIST (per-lawyer rateio history) if present ===
SELECT * FROM SSJR.CAD_RATEIOADVG_HIST WHERE SIGLA='AM' OR COD_ADVG='AM';

EXIT
