-- probe_despesas_equipe_area.sql
-- GAP 2 (2026-07-14): per-area "Despesas Equipe" (workbook "Despesas Área" block) —
-- the ONE missing input that keeps per-area Despesa Institucional from tying to the
-- May book (our rateio overshoots each area by ~1.5-2.3k because ΣDespesasÁrea=0).
--
-- ⚠ SOURCE MUST BE LÍQUIDO FROM CONTASPAGAR, NOT GROSS FROM GERENC. The workbook books
-- the NET value (CPGNVALORLIQUIDO) — same basis as the working ``despesas_liquido``
-- block (memory: workbook-uses-liquido-not-bruto). The older probe_despesas_area.sql
-- used GERENC gross and is superseded for the numeric tie; keep it only for the
-- area-tagging discovery. This probe splits the CONTASPAGAR net by área.
--
-- MAY 2026 GROUND TRUTH (parsed from Fechamento MBC 05.2026.xlsx, Base_Resultado_V2 —
-- the ONE authoritative book; Feb layout was superseded):
--   Contencioso 2.276,22 · Econômico 2.300,10 · Arbitragem 1.204,47  (Σ 5.780,79)
-- Jan..Mai per area (workbook, for the multi-month check):
--   Contencioso: 1060,10 · 2129,32 · 2346,72 · 4183,92 · 2276,22
--   Econômico:   1871,81 · 3296,07 · 2129,32 · 2129,32 · 2300,10
--   Arbitragem:   146,00 · 2633,69 · 3728,18 · 2633,69 · 1204,47
--
-- GOAL: find the área key on CONTASPAGAR whose net (CPGNVALORLIQUIDO) rollup for MAY
-- = 2.276,22 / 2.300,10 / 1.204,47. Then emit a ``despesas_equipe_area`` extract block.
-- Read-only. Pipe-tagged single-line output (parseable from out.txt).
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A CONTASPAGAR columns that could carry área/grupo (discover the key name)
SELECT 'A|'||COLUMN_NAME||'|'||DATA_TYPE
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='FINANCE' AND TABLE_NAME='CONTASPAGAR'
   AND ( COLUMN_NAME LIKE '%GRUPO%' OR COLUMN_NAME LIKE '%AREA%'
      OR COLUMN_NAME LIKE '%JURID%' OR COLUMN_NAME LIKE '%CENTRO%'
      OR COLUMN_NAME LIKE '%SIGLA%' OR COLUMN_NAME LIKE '%DEST%'
      OR COLUMN_NAME LIKE '%PROJET%' OR COLUMN_NAME LIKE '%DEPART%' )
 ORDER BY COLUMN_NAME;

PROMPT #B May 020.* net (CPGNVALORLIQUIDO) that carries a non-null COD_ADVG -> home área
-- If Despesas Área lines are tagged by the paying lawyer, fold via prof->grupo.
SELECT 'B|'||NVL(cp.COD_ADVG,'?')||'|'||NVL(g.NOME,'(sem area)')
       ||'|'||TO_CHAR(ROUND(SUM(cp.CPGNVALORLIQUIDO),2))||'|n='||COUNT(*)
  FROM FINANCE.CONTASPAGAR cp
  LEFT JOIN LDESK.CAD_PROFISSIONAL p ON p.SIGLA = cp.COD_ADVG
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = p.ID_GRUPOJURIDICO
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '020.%'
   AND cp.COD_ADVG IS NOT NULL
 GROUP BY cp.COD_ADVG, g.NOME
 ORDER BY 2,1;

PROMPT #C May 020.* net by ID_PROJETO (some Despesas Área lines are project-tagged)
SELECT 'C|'||NVL(TO_CHAR(cp.ID_PROJETO),'(null)')
       ||'|'||TO_CHAR(ROUND(SUM(cp.CPGNVALORLIQUIDO),2))||'|n='||COUNT(*)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '020.%'
   AND cp.ID_PROJETO IS NOT NULL
 GROUP BY cp.ID_PROJETO
 ORDER BY 2 DESC;

PROMPT #D The 8 "Despesas Área" families by account name, May net, un-split (sanity of magnitude)
-- Workbook families: Assinaturas, Associações, Cursos, Eventos e Happy hour,
-- Material Gráfico, Patrocinio, Refeições, Viagens. Σ should be ~5.780,79 for May.
SELECT 'D|'||cp.PCTCNUMEROCONTA||'|'||SUBSTR(REPLACE(NVL(MAX(cp.CPGCHISTORICO),' '),'|','/'),1,32)
       ||'|'||TO_CHAR(ROUND(SUM(cp.CPGNVALORLIQUIDO),2))||'|n='||COUNT(*)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '020.%'
   AND ( UPPER(cp.CPGCHISTORICO) LIKE '%ASSINATURA%' OR UPPER(cp.CPGCHISTORICO) LIKE '%ASSOCIA%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%CURSO%'      OR UPPER(cp.CPGCHISTORICO) LIKE '%EVENTO%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%HAPPY%'      OR UPPER(cp.CPGCHISTORICO) LIKE '%MATERIAL%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%PATROC%'     OR UPPER(cp.CPGCHISTORICO) LIKE '%REFEI%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%VIAGE%' )
 GROUP BY cp.PCTCNUMEROCONTA
 ORDER BY 1;

PROMPT #E If (A) found a grupo/área column named e.g. ID_GRUPOJURIDICO on CONTASPAGAR:
-- direct split by it. (Runs only if the column exists — else errors, harmless w/ CONTINUE.)
SELECT 'E|'||NVL(g.NOME,'(sem area)')||'|'||TO_CHAR(ROUND(SUM(cp.CPGNVALORLIQUIDO),2))||'|n='||COUNT(*)
  FROM FINANCE.CONTASPAGAR cp
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = cp.ID_GRUPOJURIDICO
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '020.%'
   AND cp.ID_GRUPOJURIDICO IS NOT NULL
 GROUP BY g.NOME
 ORDER BY 1;

PROMPT #F CPDESDOBRAMENTO area tag: the desdobramento rows may carry the área the lump was split to
SELECT 'F|'||COLUMN_NAME||'|'||DATA_TYPE
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='FINANCE' AND TABLE_NAME='CPDESDOBRAMENTO'
   AND ( COLUMN_NAME LIKE '%GRUPO%' OR COLUMN_NAME LIKE '%AREA%'
      OR COLUMN_NAME LIKE '%JURID%' OR COLUMN_NAME LIKE '%SIGLA%'
      OR COLUMN_NAME LIKE '%ADVG%' OR COLUMN_NAME LIKE '%DEST%' )
 ORDER BY COLUMN_NAME;

PROMPT #END target MAY per-area Despesas Equipe: Contencioso 2276.22 / Econômico 2300.10 / Arbitragem 1204.47 (Σ 5780.79)
