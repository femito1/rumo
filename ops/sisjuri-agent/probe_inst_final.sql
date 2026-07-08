-- Probe FINAL: lock Despesa Institucional total + Despesas Área to the centavo.
-- Established so far:
--   * Despesa Institucional pool = 020.* + 040.* MINUS comissão 020.110, but the
--     raw sum is a few k off the workbook — so some accounts are re-bucketed.
--   * Despesas Área = the DRE-area-tagged NON-030 families only
--     (020.030/060/080/090); 030.* area tags are Custo equipe, Admin/comissão excluded.
--   * Workbook Despesa Institucional total = Σ of NOME_CONTA_PAI group subtotals
--     (Ocupação/Telecom/Despesas Gerais/Serviços Terceiros/Salários ADM/
--      Administrativas/Financeiras/Benefícios/Prospecção/Consultoria/Informática...).
-- Hypothesis to test: workbook_total = (020+040 pool) - (area-tagged Despesas Área
--   that get moved OUT of the institutional pool into the area blocks). i.e. the
--   institutional total EXCLUDES the area-tagged Despesas Área lines (they're
--   shown separately per area, then rateio adds back the remainder).
SET DEFINE OFF
SET PAGESIZE 4000
SET LINESIZE 340
SET FEEDBACK ON
COL nome_pai FORMAT A40
COL area FORMAT A26
COL ano_mes FORMAT A7
WHENEVER SQLERROR CONTINUE

PROMPT === 1. 020+040 pool split: area-tagged(DRE) vs untagged, per month ===
-- workbook Despesa Institucional total ?= untagged pool (area lines pulled out).
SELECT r.ANO_MES,
   ROUND(SUM(CASE WHEN g.NOME IS NOT NULL AND (UPPER(g.NOME) LIKE '%CONTENCIOSO%'
        OR UPPER(g.NOME) LIKE '%ECON%' OR UPPER(g.NOME) LIKE '%ARBITRAGEM%'
        OR UPPER(g.NOME) LIKE '%COMPLIANCE%') THEN r.VALOR ELSE 0 END),2) dre_area_tagged,
   ROUND(SUM(CASE WHEN g.NOME IS NULL OR NOT (UPPER(g.NOME) LIKE '%CONTENCIOSO%'
        OR UPPER(g.NOME) LIKE '%ECON%' OR UPPER(g.NOME) LIKE '%ARBITRAGEM%'
        OR UPPER(g.NOME) LIKE '%COMPLIANCE%') THEN r.VALOR ELSE 0 END),2) rest
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
   AND r.ID_CONTA <> '020.110.0010'
 GROUP BY r.ANO_MES
 ORDER BY r.ANO_MES;

PROMPT === 2. Despesas Área (DRE-area-tagged NON-030, excl comissao) per area/month ===
-- Compare to workbook: Cont 1060,10/2129,32/2346,72/4183,92/2276,22 ;
-- Econ 1871,81/3296,07/2129,32/2129,32/2300,10 ; Arb 146,00/2633,69/3728,18/2633,69/1204,47
SELECT r.ANO_MES, g.NOME area, ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
   AND r.ID_CONTA <> '020.110.0010'
   AND (UPPER(g.NOME) LIKE '%CONTENCIOSO%' OR UPPER(g.NOME) LIKE '%ECON%'
        OR UPPER(g.NOME) LIKE '%ARBITRAGEM%' OR UPPER(g.NOME) LIKE '%COMPLIANCE%')
 GROUP BY r.ANO_MES, g.NOME
 ORDER BY r.ANO_MES, g.NOME;

PROMPT === 3. The exact area-tagged NON-030 rows Jan..Mai (which accounts move to area) ===
SELECT r.ANO_MES, r.ID_CONTA, MAX(r.NOME_CONTA) nome, g.NOME area, ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
   AND r.ID_CONTA <> '020.110.0010'
   AND (UPPER(g.NOME) LIKE '%CONTENCIOSO%' OR UPPER(g.NOME) LIKE '%ECON%'
        OR UPPER(g.NOME) LIKE '%ARBITRAGEM%' OR UPPER(g.NOME) LIKE '%COMPLIANCE%')
 GROUP BY r.ANO_MES, r.ID_CONTA, g.NOME
 ORDER BY r.ANO_MES, g.NOME, r.ID_CONTA;

PROMPT === 4. Group-subtotals by NOME_CONTA_PAI (020+040) per month ===
-- To see the family structure the workbook's institutional total sums over.
SELECT r.ANO_MES, MAX(r.NOME_CONTA_PAI) nome_pai, SUBSTR(r.ID_CONTA,1,7) fam,
       ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
 GROUP BY r.ANO_MES, SUBSTR(r.ID_CONTA,1,7)
 ORDER BY r.ANO_MES, fam;

EXIT
