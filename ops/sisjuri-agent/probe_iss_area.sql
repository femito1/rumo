-- probe_iss_area.sql  (2026-07-21)
-- =====================================================================
-- Settle how ISS jurídico (030.010.0160, TRIMESTRAL) must be folded into per-area
-- Custo equipe so we can un-drop it. The workbook books it per area ("ISS
-- Trimestral", Base_Resultado rows 25/54/79):
--   Jan: Contencioso 1.719,72 · Econômico 2.101,88 · Arbitragem 1.528,64 = 5.350,24
--   Abr: Contencioso 2.028,56 · Econômico 2.028,56 · Arbitragem 1.521,42 = 5.578,54
-- QUESTION: does GERENC 030.010.0160 carry ID_GRUPOJURIDICO (area) so we can group
-- by area directly, or is it per-lawyer (ID_PROFISSIONAL), or untagged
-- (institutional -> would need a rateio)? Also confirm Jul/Oct are the other
-- quarter months (so the fix is future-proof).
--
-- SAFE: read-only. Pipe-delimited, block-prefixed. No trailing-hyphen PROMPTs.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
SET SQLBLANKLINES ON
WHENEVER SQLERROR CONTINUE

PROMPT ============================================================
PROMPT #A ISS 030.010.0160 grouped by AREA (ID_GRUPOJURIDICO -> NOME), Jan & Apr
PROMPT ============================================================
PROMPT Compare to workbook: Jan C 1719,72/E 2101,88/A 1528,64 | Abr C 2028,56/E 2028,56/A 1521,42
SELECT 'A|'||r.ANO_MES
       ||'|area='||NVL(g.NOME,'(NULL)')
       ||'|total='||TO_CHAR(ROUND(SUM(r.VALOR),2))
       ||'|n='||COUNT(*) AS out
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ID_CONTA = '030.010.0160'
   AND r.ANO_MES IN ('2026-01','2026-04')
 GROUP BY r.ANO_MES, g.NOME
 ORDER BY r.ANO_MES, g.NOME;

PROMPT ============================================================
PROMPT #B ISS 030.010.0160 grouped by PROFISSIONAL (sigla), Jan & Apr
PROMPT ============================================================
PROMPT If area (#A) is NULL but this has siglas, fold per-lawyer via home area instead.
SELECT 'B|'||r.ANO_MES
       ||'|sigla='||NVL(p.SIGLA, NVL(TO_CHAR(r.ID_PROFISSIONAL),'(NULL)'))
       ||'|total='||TO_CHAR(ROUND(SUM(r.VALOR),2))
       ||'|n='||COUNT(*) AS out
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_PROFISSIONAL p ON p.ID_PROFISSIONAL = r.ID_PROFISSIONAL
 WHERE r.ID_CONTA = '030.010.0160'
   AND r.ANO_MES IN ('2026-01','2026-04')
 GROUP BY r.ANO_MES, p.SIGLA, r.ID_PROFISSIONAL
 ORDER BY r.ANO_MES, p.SIGLA;

PROMPT ============================================================
PROMPT #C ISS 030.010.0160 by month across all 2026 (confirm the quarter cadence)
PROMPT ============================================================
SELECT 'C|'||r.ANO_MES||'|total='||TO_CHAR(ROUND(SUM(r.VALOR),2))||'|n='||COUNT(*) AS out
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ID_CONTA = '030.010.0160'
   AND r.ANO_MES BETWEEN '2026-01' AND '2026-12'
 GROUP BY r.ANO_MES
 ORDER BY r.ANO_MES;

PROMPT ============================================================
PROMPT #D Cross-check: does raw GERENC 030.% by area (INCLUDING ISS) match the
PROMPT     workbook per-area Custo equipe target for Jan? (target C 73576,32/E 75653,19/A 62013,17)
PROMPT ============================================================
PROMPT (raw sum differs from the derived recipe, but shows the ISS contribution in context)
SELECT 'D|'||r.ANO_MES
       ||'|area='||NVL(g.NOME,'(NULL)')
       ||'|all030='||TO_CHAR(ROUND(SUM(r.VALOR),2)) AS out
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ID_CONTA LIKE '030.%'
   AND r.ANO_MES = '2026-01'
 GROUP BY r.ANO_MES, g.NOME
 ORDER BY g.NOME;

PROMPT ============================================================
PROMPT #E JAN full account census (quarter month) — catch any OTHER quarter-only account
PROMPT ============================================================
PROMPT April/May can't show quarter-only accounts; Jan can. Compare families to the map.
SELECT 'E|'||r.ID_CONTA
       ||'|'||MAX(SUBSTR(NVL(r.NOME_CONTA,'?'),1,26))
       ||'|pai='||MAX(SUBSTR(NVL(r.NOME_CONTA_PAI,'?'),1,20))
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2)) AS out
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES = '2026-01'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '030.%' OR r.ID_CONTA LIKE '040.%')
 GROUP BY r.ID_CONTA
 HAVING ROUND(SUM(r.VALOR),2) <> 0
 ORDER BY r.ID_CONTA;

PROMPT #END
EXIT
