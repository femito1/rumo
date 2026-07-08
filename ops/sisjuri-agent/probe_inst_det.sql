-- probe_inst_det.sql
-- GOAL: dump VW_RESULTADO_MENSAL_DET line-level detail for the institutional
-- block (TIPO S+I) across Jan..Mai, so we can (1) build the per-account ->
-- workbook-family mapping and (2) measure exactly how large the residual
-- "hand-adjustment" is per month (workbook row-198 vs DB-built families).
--
-- _DET carries TITULO1/2/3 (family/line hierarchy), SETOR (ADM/ECT/EDE/ESP),
-- and ORCAMENTO. 657 rows/month for Feb. We aggregate to the line grain
-- (TITULO2 x TITULO3 x SETOR) to keep output compact but complete.
--
-- Workbook is SACRED: the account/line names here map to the workbook sub-account
-- rows (85-190). Compare each family sum to the workbook family subtotals:
--   (05.2026 C..G = Jan..Mai)
--   Ocupacao 27660.20/34729.91/36273.05/36198.98/37189.87
--   Telecom    807.16/807.16/807.16/824.81/825.01
--   Despesas Gerais 6773.44/5243.68/6492.79/5820.18/6170.39
--   Consultoria 30035.14/22509.85/22457.81/22343.08/22748.74
--   Salarios Adm 6408.59/6076.76/9751.18/9189.32/12344.91
--   Administrativas 4300.03/6892.33/7109.73/7304.73/2822.06
--   Invest Prospec 1317.71/1166.75/811.14/1826.50/1426.72
--   Gestao Conhec 692.37/0/1094.49/1450.00/1600.00
--   Endomarketing 0/0/64.98/61.98/420.98
--   Informatica 22186.77/17620.95/17106.57/25136.53/19962.75
--   row198 100181.41/95047.39/101968.90/110156.11/105511.43
SET DEFINE OFF
SET PAGESIZE 50000
SET LINESIZE 400
SET FEEDBACK ON
COL tipo    FORMAT A5
COL titulo1 FORMAT A24
COL titulo2 FORMAT A30
COL titulo3 FORMAT A38
COL setor   FORMAT A6
COL ano_mes FORMAT A7
WHENEVER SQLERROR CONTINUE

PROMPT ============================================================
PROMPT === A. _DET column inventory (so we know every dimension available) ===
PROMPT ============================================================
SELECT column_name, data_type
  FROM ALL_TAB_COLUMNS
 WHERE table_name = 'VW_RESULTADO_MENSAL_DET' AND owner = 'FINANCE'
 ORDER BY column_id;

PROMPT ============================================================
PROMPT === B. Institutional line detail (TIPO S+I) Jan..Mai, line grain ===
PROMPT ===    TITULO2 (family) x TITULO3 (line) x SETOR, with account if present.
PROMPT ============================================================
SELECT ANO_MES ano_mes, TIPO tipo, TITULO2 titulo2, TITULO3 titulo3,
       SETOR setor, ROUND(SUM(VALOR),2) total, COUNT(*) n
  FROM FINANCE.VW_RESULTADO_MENSAL_DET
 WHERE ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND TIPO IN ('S','I')
 GROUP BY ANO_MES, TIPO, TITULO2, TITULO3, SETOR
 ORDER BY ANO_MES, TIPO, TITULO2, TITULO3, SETOR;

PROMPT ============================================================
PROMPT === C. Same, rolled to family (TITULO2) per month — direct compare to the
PROMPT ===    workbook family subtotals in the header.
PROMPT ============================================================
SELECT ANO_MES ano_mes, TIPO tipo, TITULO2 titulo2, ROUND(SUM(VALOR),2) total
  FROM FINANCE.VW_RESULTADO_MENSAL_DET
 WHERE ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND TIPO IN ('S','I')
 GROUP BY ANO_MES, TIPO, TITULO2
 ORDER BY ANO_MES, TIPO, TITULO2;

PROMPT ============================================================
PROMPT === D. Does _DET expose the LANNCODIG / account number per line? If so we
PROMPT ===    can map account -> workbook family exactly. Sample Feb.
PROMPT ============================================================
SELECT * FROM (
  SELECT TITULO2, TITULO3, SETOR, VALOR
    FROM FINANCE.VW_RESULTADO_MENSAL_DET
   WHERE ANO_MES='2026-02' AND TIPO IN ('S','I')
   ORDER BY TITULO2, TITULO3
) WHERE ROWNUM <= 40;

EXIT
