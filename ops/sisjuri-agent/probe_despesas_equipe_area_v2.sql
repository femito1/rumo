-- probe_despesas_equipe_area_v2.sql  (corrected; supersedes probe_despesas_equipe_area.sql)
-- GAP 2: per-area "Despesas Equipe" (workbook "Despesas Área"). MAY ground truth
-- (authoritative 05.2026 book): Contencioso 2.276,22 · Econômico 2.300,10 ·
-- Arbitragem 1.204,47  (Σ 5.780,79).
--
-- v1 findings: CONTASPAGAR has NO grupo/área column (only SIGLA, ID_PROJETO). And the
-- Patrocínio account 020.060.0020 = 1.204,47 = Arbitragem's EXACT target — so Despesas
-- Área lines look like SPECIFIC ACCOUNTS, not a grupo rollup. Meanwhile DB_RESULTADO_PROF
-- (which nailed per-area Recebimento via RECEITA_REC by NOMEGRUPO) also carries per-grupo
-- despesa columns — check those FIRST; if one ties 2.276,22/2.300,10/1.204,47 we reuse the
-- exact source that already works.
--
-- ⚠ SQL RULE (I broke this twice): when the SELECT list is ONE concatenated string, use
-- ORDER BY 1 or NONE — never ORDER BY 2. Column names verified against v1/v2 schema dumps.
-- Read-only. Pipe-tagged single-line output.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A DB_RESULTADO_PROF May: per-grupo despesa columns — does any tie 2276/2300/1204?
-- Verified cols on this view: DESP_DIRETA, DESP_INDIRETA, DESPESAS_RECEBIMENTO,
-- DESPESAS_INCORRIDAS_REC, CUSTO_DIRETO, CUSTO_INDIRETO. Show them per grupo.
SELECT 'A|'||NVL(NOMEGRUPO,'(null)')
       ||'|desp_dir='||TO_CHAR(ROUND(SUM(DESP_DIRETA),2))
       ||'|desp_ind='||TO_CHAR(ROUND(SUM(DESP_INDIRETA),2))
       ||'|desp_rec='||TO_CHAR(ROUND(SUM(DESPESAS_RECEBIMENTO),2))
       ||'|desp_inc_rec='||TO_CHAR(ROUND(SUM(DESPESAS_INCORRIDAS_REC),2))
  FROM LDESK.DB_RESULTADO_PROF
 WHERE ANO_MES='2026-05'
 GROUP BY NOMEGRUPO
 ORDER BY 1;

PROMPT #B DB_RESULTADO_AREA May: same idea on the AREA-basis rollup (cols use NOMEAREA)
SELECT 'B|'||NVL(NOMEAREA,'(null)')
       ||'|desp_dir='||TO_CHAR(ROUND(SUM(DESP_DIRETA),2))
       ||'|desp_ind='||TO_CHAR(ROUND(SUM(DESP_INDIRETA),2))
       ||'|desp_rec='||TO_CHAR(ROUND(SUM(DESPESAS_RECEBIMENTO),2))
  FROM LDESK.DB_RESULTADO_AREA
 WHERE ANO_MES='2026-05'
 GROUP BY NOMEAREA
 ORDER BY 1;

PROMPT #C The 8 Despesas-Área FAMILIES as specific accounts, May net (broadened histórico)
-- v1 caught only 3. Broaden: also match by ACCOUNT NAME, not just histórico, and widen terms.
SELECT 'C|'||cp.PCTCNUMEROCONTA
       ||'|'||SUBSTR(REPLACE(NVL(MAX(cp.CPGCHISTORICO),' '),'|','/'),1,34)
       ||'|liq='||TO_CHAR(ROUND(SUM(cp.CPGNVALORLIQUIDO),2))||'|n='||COUNT(*)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '020.%'
   AND ( UPPER(cp.CPGCHISTORICO) LIKE '%ASSINATURA%' OR UPPER(cp.CPGCHISTORICO) LIKE '%ASSOCIA%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%CURSO%'      OR UPPER(cp.CPGCHISTORICO) LIKE '%EVENTO%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%HAPPY%'      OR UPPER(cp.CPGCHISTORICO) LIKE '%MATERIAL%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%GR_FIC%'     OR UPPER(cp.CPGCHISTORICO) LIKE '%PATROC%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%REFEI%'      OR UPPER(cp.CPGCHISTORICO) LIKE '%VIAGE%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%PASSAGE%'    OR UPPER(cp.CPGCHISTORICO) LIKE '%SMS%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%M_TRICA%'    OR UPPER(cp.CPGCHISTORICO) LIKE '%CANAL%' )
 GROUP BY cp.PCTCNUMEROCONTA
 ORDER BY 1;

PROMPT #D EVERY 020.* account with a non-null paying SIGLA (advogado) May, folded to home grupo
-- If Despesas Área = the 020.* lines paid by/for a lawyer, fold SIGLA -> home grupo.
SELECT 'D|'||NVL(cp.SIGLA,'?')||'|'||NVL(g.NOME,'(sem grupo)')
       ||'|liq='||TO_CHAR(ROUND(SUM(cp.CPGNVALORLIQUIDO),2))||'|n='||COUNT(*)
  FROM FINANCE.CONTASPAGAR cp
  LEFT JOIN LDESK.CAD_PROFISSIONAL p ON p.SIGLA = cp.SIGLA
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = p.ID_GRUPOJURIDICO
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '020.%'
   AND cp.SIGLA IS NOT NULL
 GROUP BY cp.SIGLA, g.NOME
 ORDER BY 1;

PROMPT #E Full list of 020.* accounts + names present in May (so we can identify the 8 families)
SELECT 'E|'||cp.PCTCNUMEROCONTA
       ||'|liq='||TO_CHAR(ROUND(SUM(cp.CPGNVALORLIQUIDO),2))||'|n='||COUNT(*)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '020.%'
 GROUP BY cp.PCTCNUMEROCONTA
 ORDER BY 1;

PROMPT #F How Despesas Área maps to grupo in DB_VW_RESULTADO (per-caso, has NOMEGRUPO + área)
-- DB_VW_RESULTADO carries NOMEGRUPO, NOMEAREA and a VALORDESPADM/DESPESAS col per caso.
-- Sum any despesa-ish col by NOMEGRUPO for May to see if a 2276/2300/1204 split appears.
SELECT 'F|'||NVL(NOMEGRUPO,'(null)')
       ||'|despadm='||TO_CHAR(ROUND(SUM(VALORDESPADM),2))
       ||'|desp_inc='||TO_CHAR(ROUND(SUM(DESPESAS_INCORRIDAS),2))
  FROM LDESK.DB_VW_RESULTADO
 WHERE ANO_MES='2026-05'
 GROUP BY NOMEGRUPO
 ORDER BY 1;

PROMPT #END target MAY Despesas Equipe: Contencioso 2276.22 / Econômico 2300.10 / Arbitragem 1204.47 (Σ 5780.79)
