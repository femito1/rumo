-- probe_inst_reconstruct.sql
-- GOAL: reconstruct the workbook Base_Resultado institutional block (rows ~85-190)
-- and its total (row 198) from the DB *to the centavo*. The workbook is SACRED
-- TRUTH; we are proving whether each family subtotal + its sub-account lines can
-- be rebuilt account-by-account from the DB, across Jan..Mai 2026.
--
-- Workbook family subtotals to hit (05.2026 edition, monthly C..G = Jan..Mai):
--   Ocupacao            27660.20 / 34729.91 / 36273.05 / 36198.98 / 37189.87
--   Telecomunicacoes      807.16 /   807.16 /   807.16 /   824.81 /   825.01
--   Despesas Gerais      6773.44 /  5243.68 /  6492.79 /  5820.18 /  6170.39
--   Consultoria         30035.14 / 22509.85 / 22457.81 / 22343.08 / 22748.74
--   Salarios Adm         6408.59 /  6076.76 /  9751.18 /  9189.32 / 12344.91
--   Administrativas      4300.03 /  6892.33 /  7109.73 /  7304.73 /  2822.06
--   Invest. Prospeccao   1317.71 /  1166.75 /   811.14 /  1826.50 /  1426.72
--   Gestao Conhecimento   692.37 /      0   /  1094.49 /  1450.00 /  1600.00
--   Endomarketing           0    /      0   /    64.98 /    61.98 /   420.98
--   Informatica         22186.77 / 17620.95 / 17106.57 / 25136.53 / 19962.75
--   -> Despesa Institucional (row 198)
--                      100181.41 / 95047.39 /101968.90 /110156.11 /105511.43
--
-- NOTE: workbook Despesas Area (rows 204-206) are PULLED OUT of these families
-- into per-area blocks. The rateio (row 207) redistributes what remains. So the
-- reconstruction must also identify the area-tagged lines that leave the pool.
SET DEFINE OFF
SET PAGESIZE 50000
SET LINESIZE 400
SET FEEDBACK ON
SET TRIMSPACE ON
COL nome_conta     FORMAT A44
COL nome_conta_pai FORMAT A34
COL area           FORMAT A26
COL ano_mes        FORMAT A7
COL tipo           FORMAT A5
COL titulo1        FORMAT A26
COL titulo2        FORMAT A30
COL titulo3        FORMAT A34
COL setor          FORMAT A8
WHENEVER SQLERROR CONTINUE

PROMPT ============================================================
PROMPT === A. GERENC_LANCAMENTORESUMO: every 020/040 account, per month, with
PROMPT ===    its parent family + whether it carries a DRE-area tag. This is the
PROMPT ===    ground truth to rebuild each workbook family subtotal.
PROMPT ============================================================
SELECT r.ANO_MES ano_mes,
       r.ID_CONTA,
       MAX(r.NOME_CONTA)     nome_conta,
       MAX(r.NOME_CONTA_PAI) nome_conta_pai,
       NVL(MAX(g.NOME),'(sem area)') area,
       ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
 GROUP BY r.ANO_MES, r.ID_CONTA
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT ============================================================
PROMPT === B. Family (NOME_CONTA_PAI) subtotals, per month. Compare directly to
PROMPT ===    the workbook family subtotals listed in the header.
PROMPT ============================================================
SELECT r.ANO_MES ano_mes,
       MAX(r.NOME_CONTA_PAI) nome_conta_pai,
       SUBSTR(r.ID_CONTA,1,7) fam,
       ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
 GROUP BY r.ANO_MES, SUBSTR(r.ID_CONTA,1,7)
 ORDER BY r.ANO_MES, fam;

PROMPT ============================================================
PROMPT === C. VW_RESULTADO_MENSAL: the DB DRE engine, TIPO S+I level-2 titles
PROMPT ===    (institutional families) per month. These titles ARE the workbook
PROMPT ===    families; check value parity family-by-family.
PROMPT ============================================================
SELECT ANO_MES ano_mes, TIPO tipo, TITULO2 titulo2,
       ROUND(SUM(VALOR),2) total
  FROM FINANCE.VW_RESULTADO_MENSAL
 WHERE ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND TIPO IN ('S','I')
 GROUP BY ANO_MES, TIPO, TITULO2
 ORDER BY ANO_MES, TIPO, TITULO2;

PROMPT ============================================================
PROMPT === D. VW_RESULTADO_MENSAL: TIPO S+I grand total per month (candidate for
PROMPT ===    Despesa Institucional pool BEFORE removing comissao/area lines).
PROMPT ============================================================
SELECT ANO_MES ano_mes, TIPO tipo, ROUND(SUM(VALOR),2) total
  FROM FINANCE.VW_RESULTADO_MENSAL
 WHERE ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND TIPO IN ('S','I')
 GROUP BY ANO_MES, TIPO
 ORDER BY ANO_MES, TIPO;

PROMPT ============================================================
PROMPT === E. VW_RESULTADO_MENSAL_DET availability + shape (line-level detail).
PROMPT ===    If this exists we can map each workbook sub-account line to the
PROMPT ===    exact lancamentos, cracking the hand-typed =a+b+c cells.
PROMPT ============================================================
SELECT COUNT(*) det_rows_feb
  FROM FINANCE.VW_RESULTADO_MENSAL_DET
 WHERE ANO_MES = '2026-02';

PROMPT === E2. VW_RESULTADO_MENSAL_DET sample (Feb, TIPO S+I) — line detail ===
SELECT TIPO tipo, TITULO2 titulo2, TITULO3 titulo3, SETOR setor,
       ROUND(SUM(VALOR),2) total, COUNT(*) n
  FROM FINANCE.VW_RESULTADO_MENSAL_DET
 WHERE ANO_MES = '2026-02' AND TIPO IN ('S','I')
 GROUP BY TIPO, TITULO2, TITULO3, SETOR
 ORDER BY TIPO, TITULO2, TITULO3, SETOR;

PROMPT ============================================================
PROMPT === F. Despesa Institucional pool reconciliation per month:
PROMPT ===    (020+040) minus comissao 020.110 vs the workbook row-198 total.
PROMPT ===    workbook row198: 100181.41/95047.39/101968.90/110156.11/105511.43
PROMPT ============================================================
SELECT r.ANO_MES ano_mes,
       ROUND(SUM(r.VALOR),2) pool_020_040,
       ROUND(SUM(CASE WHEN r.ID_CONTA='020.110.0010' THEN r.VALOR ELSE 0 END),2) comissao,
       ROUND(SUM(r.VALOR) - SUM(CASE WHEN r.ID_CONTA='020.110.0010' THEN r.VALOR ELSE 0 END),2) pool_ex_comissao
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
 GROUP BY r.ANO_MES
 ORDER BY r.ANO_MES;

EXIT
