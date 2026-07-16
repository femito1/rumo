-- probe_despesas_area_key.sql  (GAP 2, v5 — the definitive per-area key)
-- BREAKTHROUGH from the workbook (Base_Resultado r124-160): "Despesas Área" = the
-- Grupo='S' auto-rateio families {Associações, Cursos/Treinamento, Viagens/Prospecção,
-- Assinaturas, Eventos/HH, Material Gráfico}, each shown as "{Família} - {Área}". May
-- detail (ties to the r204-206 subtotals to the centavo):
--   Contencioso 2.276,22 = Assoc-Conten 917,50 + Viagens 1.358,72
--   Econômico   2.300,10 = Assoc-Econ 700,10 + Cursos 1.600,00
--   Arbitragem  1.204,47 = Assoc-Arb 1.204,47   (assento Viagens 68,00 EXCLUDED)
-- Confirmed DB ties already: Assoc-Conten = AASP 217,40 + IBRAC 700,09 (DESCSETOR=ECT);
-- Assoc-Econ = IBRAC 700,10 (DESCSETOR=EDE); Assoc-Arb = Patrocínio 1.204,47 (SIGLA=ESP).
-- OPEN: the Viagens line 1.358,72 (020.090.0010, COD_ADVG=RB whose HOME is Econômico,
-- SIGLA=EDE) lands in CONTENCIOSO — so the área key is NEITHER home-area NOR SIGLA/DESCSETOR.
-- Candidate keys still untested: RATNCODIG (rateio code, on CONTASPAGAR+CPDESDOBRAMENTO),
-- ID_PROJETO, DESNCASO -> case área. This probe dumps the family-account lines with ALL of
-- them so the key is unambiguous.
--
-- Family accounts (from SISJURI_DB): Associações 020.060.*, Prospecção/Viagens 020.090.*,
-- Cursos 030.010.0180, Assinaturas (find), Eventos/HH 020.090.0040, Material Gráfico (find).
-- ⚠ SQL: single concatenated column → ORDER BY 1 or none. Read-only. Pipe-tagged.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A The Viagens line (020.090.0010) May: ALL candidate area keys on CONTASPAGAR
SELECT 'A|'||cp.PCTCNUMEROCONTA||'|pagar='||cp.CPGCNUMEROPAGAR
       ||'|liq='||TO_CHAR(ROUND(cp.CPGNVALORLIQUIDO,2))
       ||'|adv='||NVL(cp.COD_ADVG,'-')||'|sig='||NVL(cp.SIGLA,'-')
       ||'|rat='||NVL(TO_CHAR(cp.RATNCODIG),'-')||'|proj='||NVL(TO_CHAR(cp.ID_PROJETO),'-')
       ||'|'||SUBSTR(REPLACE(NVL(cp.CPGCHISTORICO,' '),'|','/'),1,40)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '020.090.%'
 ORDER BY 1;

PROMPT #B RATNCODIG -> what does it join to? Dump CAD_RATEIO* / RATEIO* table names + key cols
SELECT 'B|'||OWNER||'.'||TABLE_NAME
  FROM ALL_TABLES
 WHERE OWNER IN ('FINANCE','LDESK') AND TABLE_NAME LIKE '%RATEIO%'
 ORDER BY 1;

PROMPT #B2 columns of FINANCE rateio tables (so we can resolve RATNCODIG -> área %)
SELECT 'B2|'||TABLE_NAME||'|'||COLUMN_NAME||'|'||DATA_TYPE
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='FINANCE' AND TABLE_NAME LIKE '%RATEIO%'
 ORDER BY TABLE_NAME, COLUMN_ID;

PROMPT #C Cursos/Treinamento 030.010.0180 May lines: value + all keys (the 1.600 Econ line)
SELECT 'C|'||cp.PCTCNUMEROCONTA||'|liq='||TO_CHAR(ROUND(cp.CPGNVALORLIQUIDO,2))
       ||'|adv='||NVL(cp.COD_ADVG,'-')||'|sig='||NVL(cp.SIGLA,'-')
       ||'|rat='||NVL(TO_CHAR(cp.RATNCODIG),'-')
       ||'|'||SUBSTR(REPLACE(NVL(cp.CPGCHISTORICO,' '),'|','/'),1,40)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA = '030.010.0180'
 ORDER BY 1;

PROMPT #D All Associações slices (020.060.*) with RATNCODIG too (cross-check the DESCSETOR key)
SELECT 'D|'||d.DESCCONTADESTINO||'|setor='||NVL(d.DESCSETOR,'-')
       ||'|rat='||NVL(TO_CHAR(d.RATNCODIG),'-')||'|caso='||NVL(TO_CHAR(d.DESNCASO),'-')
       ||'|val='||TO_CHAR(ROUND(d.DESNVALOR,2))
       ||'|'||SUBSTR(REPLACE(NVL(d.DESCHISTORICO,' '),'|','/'),1,36)
  FROM FINANCE.CPDESDOBRAMENTO d
  JOIN FINANCE.CONTASPAGAR cp
    ON cp.EMPNCOD=d.EMPNCOD AND cp.CPGCNUMEROPAGAR=d.CPGCNUMEROPAGAR
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND d.DESCCONTADESTINO LIKE '020.060.%'
 ORDER BY 1;

PROMPT #E If RATNCODIG resolves to área %, show the rateio rows for the codes seen above.
-- Try the common shape: a rateio detail with ID_GRUPOJURIDICO + percentual. Adjust after #B2.
SELECT 'E|'||r.RATNCODIG||'|grupo='||NVL(g.NOME,'?')||'|pct='||NVL(TO_CHAR(r.PERCENTUAL),'?')
  FROM FINANCE.RATEIO_ITEM r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE ROWNUM <= 200
 ORDER BY 1;

PROMPT #END target MAY Despesas Área: Contencioso 2276.22 / Econômico 2300.10 / Arbitragem 1204.47
