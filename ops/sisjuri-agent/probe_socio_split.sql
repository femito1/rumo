-- probe_socio_split.sql  (automate POINT 17 ourselves — no RUMO chart-of-accounts change)
-- GOAL: split "Bônus equipe" (employees) from "DL excedente dos sócios" (partners)
-- from the DB alone, WITHOUT hardcoding the 4 partner names. The meeting note (item 17)
-- assumed RUMO must book partners to a separate account; but if the DB already encodes
-- "who is a sócio" (a flag/type/table/grupo), we classify by data like every other
-- desdobramento we cracked. Sócios named by the client: Ricardo, Aurélio(AM), Daniel(DC),
-- Martim(MV) — find their siglas + a STRUCTURAL sócio signal.
-- Read-only. Pipe-tagged single-line statements.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A CAD_PROFISSIONAL full column list — hunt a tipo/categoria/cargo/socio flag
SELECT 'A|'||column_id||'|'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='CAD_PROFISSIONAL' ORDER BY column_id;

PROMPT #B Any LDESK table/column whose NAME hints sócio/societário/partner/quota/tipo-prof
SELECT 'B|'||table_name||'.'||column_name||'|'||data_type
  FROM ALL_TAB_COLUMNS WHERE owner='LDESK'
   AND ( UPPER(column_name) LIKE '%SOCIO%' OR UPPER(column_name) LIKE '%SOCIET%'
      OR UPPER(column_name) LIKE '%PARTNER%' OR UPPER(column_name) LIKE '%QUOTA%'
      OR UPPER(column_name) LIKE '%CATEGORIA%' OR UPPER(column_name) LIKE '%CARGO%'
      OR (UPPER(column_name) LIKE '%TIPO%' AND UPPER(table_name) LIKE '%PROFISSIONAL%') )
 ORDER BY table_name, column_name;

PROMPT #B2 Any LDESK table whose NAME hints sócio / cargo / categoria
SELECT 'B2|'||object_name||'|'||object_type
  FROM ALL_OBJECTS WHERE owner='LDESK'
   AND ( UPPER(object_name) LIKE '%SOCIO%' OR UPPER(object_name) LIKE '%SOCIET%'
      OR UPPER(object_name) LIKE '%CARGO%' OR UPPER(object_name) LIKE '%CATEGORIA%' )
 ORDER BY object_name;

PROMPT #C Sample CAD_PROFISSIONAL rows for the known people — sigla + every likely-classifying col
-- Show the four partners + a couple employees so we can spot which column separates them.
-- (SELECT * so we see all values; siglas of interest: AM/DC/MV + Ricardo's + FSM/EHF/BBX.)
SELECT 'C|'||p.SIGLA||'|'||SUBSTR(NVL(p.NOME,'?'),1,28) nome
  FROM LDESK.CAD_PROFISSIONAL p
 WHERE p.SIGLA IN ('AM','DC','MV','RB','RC','FSM','EHF','BBX','BMP','IAC','ASG','JGS')
 ORDER BY p.SIGLA;

PROMPT #C2 Full row for the 4 suspected partners (all columns) to see the distinguishing value
SELECT * FROM LDESK.CAD_PROFISSIONAL WHERE SIGLA IN ('AM','DC','MV','RB');

PROMPT #D ALL 150.* bonus lines (any month 2026) with sigla-in-histórico + professional key
-- LANCAMENTO carries LANCPROFDEST (often NULL) + LANCHISTORICO (has "Bônus <SIGLA> ...").
SELECT 'D|'||l.PCTCNUMEROCONTADEST||'|'||NVL(l.LANCPROFDEST,'-')
       ||'|'||TO_CHAR(l.LANDDATA,'YYYY-MM')||'|'||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|'||SUBSTR(REPLACE(NVL(l.LANCHISTORICO,' '),'|','/'),1,50)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '150.%'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2027-01-01'
 ORDER BY l.LANDDATA, l.LANNVALOR DESC;

PROMPT #E 030.010.0010 excedente/reserva lines by sigla (where partner excess DL lives), 2026
SELECT 'E|'||NVL(l.LANCPROFDEST,'-')||'|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|'||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|'||SUBSTR(REPLACE(NVL(l.LANCHISTORICO,' '),'|','/'),1,55)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2027-01-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%EXCEDENTE%' OR UPPER(l.LANCHISTORICO) LIKE '%RESERVA%'
      OR UPPER(l.LANCHISTORICO) LIKE '%S_CIO%' OR UPPER(l.LANCHISTORICO) LIKE '%SOCIO%' )
 ORDER BY l.LANDDATA, l.LANNVALOR DESC;

PROMPT #F CAD_GRUPOJURIDICO list — is there a "Sócios" grupo (siglas map to groups via home_area)?
SELECT 'F|'||g.ID_GRUPOJURIDICO||'|'||SUBSTR(NVL(g.NOME,'?'),1,40)
  FROM LDESK.CAD_GRUPOJURIDICO g ORDER BY g.NOME;

PROMPT #END
EXIT
