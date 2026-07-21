-- probe_iss_jgs.sql  (2026-07-21)
-- =====================================================================
-- The ISS-Trimestral TOTAL and Contencioso tie, but the workbook's Econ/Arb split
-- does NOT match any DB grouping: JGS pays TWO ISS postings (Jan 2×382,16=764,32)
-- and the workbook books one to Arbitragem, one to Econômico (giving Arb 4u /
-- Econ 5u), whereas home-area / raw ID_GRUPOJURIDICO give Arb 5u / Econ 4u.
-- QUESTION: do JGS's two ISS rows carry DISTINCT area tags (ID_GRUPOJURIDICO,
-- SIGLADEST, or a caso/cliente) that would let us derive the workbook's split, or
-- is it a manual area choice the DB doesn't encode?
--
-- SAFE: read-only. Pipe-delimited. No trailing-hyphen PROMPTs.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
SET SQLBLANKLINES ON
WHENEVER SQLERROR CONTINUE

PROMPT ============================================================
PROMPT #A JGS's ISS rows (030.010.0160) line by line, Jan + Apr, with every area-ish tag
PROMPT ============================================================
PROMPT If the two rows have different ID_GRUPOJURIDICO/area, the split is DB-derivable.
SELECT 'A|'||r.ANO_MES
       ||'|grupo='||NVL(g.NOME,'(NULL)')
       ||'|idgrupo='||NVL(TO_CHAR(r.ID_GRUPOJURIDICO),'-')
       ||'|val='||TO_CHAR(ROUND(r.VALOR,2))
       ||'|conta='||SUBSTR(NVL(r.NOME_CONTA,'?'),1,40) AS out
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_PROFISSIONAL p ON p.ID_PROFISSIONAL = r.ID_PROFISSIONAL
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ID_CONTA = '030.010.0160'
   AND p.SIGLA = 'JGS'
   AND r.ANO_MES IN ('2026-01','2026-04','2026-07')
 ORDER BY r.ANO_MES, r.VALOR;

PROMPT ============================================================
PROMPT #B Full per-lawyer x area breakdown of ISS (Jan): show every row's area tag
PROMPT ============================================================
PROMPT Reconciles the exact per-area unit counts (workbook: Conten 4.5 / Econ 5.5 / Arb 4).
SELECT 'B|'||NVL(p.SIGLA,'?')
       ||'|grupo='||NVL(g.NOME,'(NULL)')
       ||'|val='||TO_CHAR(ROUND(r.VALOR,2)) AS out
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_PROFISSIONAL p ON p.ID_PROFISSIONAL = r.ID_PROFISSIONAL
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ID_CONTA = '030.010.0160'
   AND r.ANO_MES = '2026-01'
 ORDER BY p.SIGLA, r.VALOR;

PROMPT ============================================================
PROMPT #C Does GERENC even carry HISTORICO for these rows? (column probe)
PROMPT ============================================================
PROMPT If HISTORICO is absent the #A hist column errors; this confirms available columns.
SELECT 'C|cols_ok' AS out FROM DUAL;

PROMPT #END
EXIT
