-- probe_vale_adm.sql
-- Close the Salários Administração family: the workbook "Vale Refeição - ADM" and
-- "Vale Transporte" (part of row 116, inside row 198) do NOT come from 020.080.*
-- (that carries only tiny area-tagged staff vale). Find the real ADM vale source.
--
-- Workbook Vale-ADM targets (05 book, Jan..Mai):
--   Vale Refeição - ADM : 829.80 / 1014.20 / 2766.00 / 2766.00 / 2719.90
--   Vale Transporte     : 298.16 /  337.68 / 1217.22 /  655.36 /  607.04
-- Also confirm Gestão do Conhecimento Apr (wb 1450 vs DB 030.010.0180 = 1650).
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A Every account whose name mentions VALE (any prefix), Jan..Mai, per month/area
SELECT 'A|'||r.ANO_MES||'|'||r.ID_CONTA||'|'||MAX(r.NOME_CONTA)
       ||'|'||MAX(r.NOME_CONTA_PAI)||'|'||NVL(MAX(g.NOME),'(sem area)')
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2))
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND UPPER(r.NOME_CONTA) LIKE '%VALE%'
 GROUP BY r.ANO_MES, r.ID_CONTA, r.ID_GRUPOJURIDICO
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT #B Full 020.050.* (Salarios Administracao) sub-account list, Jan..Mai
SELECT 'B|'||r.ANO_MES||'|'||r.ID_CONTA||'|'||MAX(r.NOME_CONTA)
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2))
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.ID_CONTA LIKE '020.050.%'
 GROUP BY r.ANO_MES, r.ID_CONTA
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT #C Cursos/Treinamento 030.010.0180 per month/area (explain Apr 1650 vs wb 1450)
SELECT 'C|'||r.ANO_MES||'|'||r.ID_CONTA||'|'||NVL(MAX(g.NOME),'(sem area)')
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2))
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.ID_CONTA = '030.010.0180'
 GROUP BY r.ANO_MES, r.ID_CONTA, r.ID_GRUPOJURIDICO
 ORDER BY r.ANO_MES;

PROMPT #D Any account with CONVENIO/CONVÊNIO in name, Jan..Mai (Salarios Adm Convenio Medico)
SELECT 'D|'||r.ANO_MES||'|'||r.ID_CONTA||'|'||MAX(r.NOME_CONTA)
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2))
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND UPPER(r.NOME_CONTA) LIKE '%CONV%NIO%'
 GROUP BY r.ANO_MES, r.ID_CONTA
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT #END
EXIT
