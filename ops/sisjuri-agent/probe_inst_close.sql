-- probe_inst_close.sql
-- GOAL: close the LAST institutional-family residuals against the AUTHORITATIVE
-- 05.2026 workbook. Everything below is a raw GERENC_LANCAMENTORESUMO pull (the
-- posting-level source the aggregated views summarise), pipe-delimited and keyed
-- on stable numeric ID_CONTA, so we can trace each workbook =a+b+c cell to postings.
--
-- Open residuals to explain (built - wb, corrected map):
--   SalariosAdm Feb -1351.88  -> expect Vale Refeicao 020.080.0050 (1014.20)
--                                 + Vale Transporte 020.080.0060 (337.68), ADM/instit.
--   GestaoConhec May +1600    -> a Cursos/Treinamento account (code unknown; find it)
--   DespGerais  Feb +667.62   -> Terceir.Limpeza 020.040.0030 area split (3630.03 vs 3049.23)
--   Informatica Feb +626.95   -> a Licenca line (040.040.0030) the author excluded
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A Vale + Beneficios (020.080.*) raw postings, per month/area
SELECT 'A|'||r.ANO_MES||'|'||r.ID_CONTA||'|'||MAX(r.NOME_CONTA)
       ||'|'||NVL(MAX(g.NOME),'(sem area)')
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2))
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.ID_CONTA LIKE '020.080.%'
 GROUP BY r.ANO_MES, r.ID_CONTA, r.ID_GRUPOJURIDICO
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT #B Any account whose name mentions Curso/Treinamento/Gestao/Conhecimento/Biblioteca
SELECT 'B|'||r.ANO_MES||'|'||r.ID_CONTA||'|'||MAX(r.NOME_CONTA)
       ||'|'||MAX(r.NOME_CONTA_PAI)||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2))
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND ( UPPER(r.NOME_CONTA) LIKE '%CURSO%'
      OR UPPER(r.NOME_CONTA) LIKE '%TREINAMENTO%'
      OR UPPER(r.NOME_CONTA_PAI) LIKE '%GEST%CONHEC%'
      OR UPPER(r.NOME_CONTA) LIKE '%BIBLIOTEC%' )
 GROUP BY r.ANO_MES, r.ID_CONTA
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT #C Terceirizacao Limpeza 020.040.0030 raw postings per month/area (area split proof)
SELECT 'C|'||r.ANO_MES||'|'||r.ID_CONTA||'|'||NVL(MAX(g.NOME),'(sem area)')
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2))
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.ID_CONTA = '020.040.0030'
 GROUP BY r.ANO_MES, r.ID_CONTA, r.ID_GRUPOJURIDICO
 ORDER BY r.ANO_MES;

PROMPT #D Licencas 040.040.0030 raw postings per month/area (find the 626.95 excluded line)
SELECT 'D|'||r.ANO_MES||'|'||r.ID_CONTA||'|'||NVL(MAX(g.NOME),'(sem area)')
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2))||'|n='||COUNT(*)
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.ID_CONTA LIKE '040.040.%'
 GROUP BY r.ANO_MES, r.ID_CONTA, r.ID_GRUPOJURIDICO
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT #END
EXIT
