-- Probe: Despesa Institucional total (workbook "Despesas Institucional" row).
-- Ground truth per month (test_ledger_import.py):
--   Jan 100.181,41 · Feb 95.047,39 · Mar 101.968,90 · Apr 110.156,11 · Mai 105.511,43
-- Two candidate summations to test:
--   (a) SUM(020.*)      — the "institutional" family per docs §4.
--   (b) SUM(TIPO_CONTA='D') — the "D" (Despesas) TIPO_CONTA per docs §4.
-- Also check whether 040.* (investments) contributes; the workbook may fold
-- some capex-ish lines into "Despesas Institucional".
SET DEFINE OFF
SET PAGESIZE 3000
SET LINESIZE 340
SET FEEDBACK ON
COL ano_mes FORMAT A7
COL id_conta FORMAT A16
COL nome FORMAT A60
WHENEVER SQLERROR CONTINUE

PROMPT === 1. SUM 020.* per month Jan..Mai (candidate a) ===
SELECT r.ANO_MES, ROUND(SUM(r.VALOR),2) total_020
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.ID_CONTA LIKE '020.%'
 GROUP BY r.ANO_MES
 ORDER BY r.ANO_MES;

PROMPT === 2. SUM TIPO_CONTA='D' per month Jan..Mai (candidate b) ===
SELECT r.ANO_MES, ROUND(SUM(r.VALOR),2) total_D
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.TIPO_CONTA='D'
 GROUP BY r.ANO_MES
 ORDER BY r.ANO_MES;

PROMPT === 3. Per-account 020.* totals Jan..Mai — see the breakdown ===
SELECT r.ANO_MES, r.ID_CONTA, MAX(r.NOME_CONTA) nome,
       ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.ID_CONTA LIKE '020.%'
 GROUP BY r.ANO_MES, r.ID_CONTA
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT === 4. What TIPO_CONTA values exist and their monthly totals? ===
SELECT r.ANO_MES, r.TIPO_CONTA, ROUND(SUM(r.VALOR),2) total, COUNT(*) n
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
 GROUP BY r.ANO_MES, r.TIPO_CONTA
 ORDER BY r.ANO_MES, r.TIPO_CONTA;

PROMPT === 5. Sanity: sum 020.* Feb 2026 should equal 95.047,39 to the centavo ===
-- If (1) doesn't match, look at (3) to see which accounts fold in/out. Also try
-- excluding area-tagged 020.* (Despesas Área is separate from the total).
SELECT ROUND(SUM(r.VALOR),2) sum_020_feb,
       ROUND(SUM(CASE WHEN r.ID_GRUPOJURIDICO IS NULL THEN r.VALOR ELSE 0 END),2) sum_020_null_grupo,
       ROUND(SUM(CASE WHEN r.ID_GRUPOJURIDICO IS NOT NULL THEN r.VALOR ELSE 0 END),2) sum_020_area_tagged
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES='2026-02'
   AND r.ID_CONTA LIKE '020.%';

EXIT
