-- probe_dl_extras_clientes.sql
-- GOAL: attempt to automate the two blocks still marked "manual":
--   (1) Distribuicao de Lucros extras (workbook rows 191-195: Bonus equipe,
--       DL excedente socios, DL Extraordinaria, DL excedente MV, Repasse Cacione)
--   (2) Despesas para Clientes (rows 82-84: Reembolsaveis / Nao Reembolsaveis)
-- The workbook is SACRED; we want to find the DB rows that reproduce these to
-- the centavo. VW_RESULTADO_MENSAL TIPO='L' = Distribuicao de Lucros (Feb 94.696,15
-- headline; but the workbook DL-extras block totals differ, so decompose it).
--
-- Workbook DL-extras monthly (05.2026, C..G = Jan..Mai), block total row 191:
--   164477.34 / 101705.84 / 6627.00 / 0 / 0
--   - Bonus equipe:        row192  D=101705.84
--   - DL excedente socios: row193  C=164477.34
--   - DL Extraordinaria:   (02.2026 only) 164477.34
--   - DL excedente MV:     row194  E=6627.00
--   - Repasse Cacione:     row195  0
-- Workbook Despesas para Clientes (row 82) monthly:
--   8549.81 / 1212.73 / 0 / 1105.16 / 55.60
SET DEFINE OFF
SET PAGESIZE 50000
SET LINESIZE 400
SET FEEDBACK ON
SET TRIMSPACE ON
COL nome_conta     FORMAT A46
COL nome_conta_pai FORMAT A34
COL titulo1        FORMAT A26
COL titulo2        FORMAT A30
COL titulo3        FORMAT A36
COL ano_mes        FORMAT A7
COL tipo           FORMAT A5
COL historico      FORMAT A60
WHENEVER SQLERROR CONTINUE

PROMPT ============================================================
PROMPT === A. VW_RESULTADO_MENSAL TIPO='L' (Distribuicao de Lucros) titles Jan..Mai
PROMPT ============================================================
SELECT ANO_MES ano_mes, TITULO1 titulo1, TITULO2 titulo2, TITULO3 titulo3,
       ROUND(SUM(VALOR),2) total
  FROM FINANCE.VW_RESULTADO_MENSAL
 WHERE ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND TIPO = 'L'
 GROUP BY ANO_MES, TITULO1, TITULO2, TITULO3
 ORDER BY ANO_MES, TITULO1, TITULO2, TITULO3;

PROMPT ============================================================
PROMPT === B. LANCAMENTORESUMO: any account whose name looks like DL/Bonus/Lucros
PROMPT ===    /Reserva/Excedente/Cacione. Find the account numbers behind DL-extras.
PROMPT ============================================================
SELECT r.ANO_MES ano_mes, r.ID_CONTA,
       MAX(r.NOME_CONTA) nome_conta, MAX(r.NOME_CONTA_PAI) nome_conta_pai,
       ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND ( UPPER(r.NOME_CONTA) LIKE '%LUCRO%'
      OR UPPER(r.NOME_CONTA) LIKE '%B_NUS%'
      OR UPPER(r.NOME_CONTA) LIKE '%BONUS%'
      OR UPPER(r.NOME_CONTA) LIKE '%EXCEDENTE%'
      OR UPPER(r.NOME_CONTA) LIKE '%DISTRIBUI%'
      OR UPPER(r.NOME_CONTA) LIKE '%CACIONE%'
      OR UPPER(r.NOME_CONTA) LIKE '%REPASSE%' )
 GROUP BY r.ANO_MES, r.ID_CONTA
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT ============================================================
PROMPT === C. LANCAMENTO ledger: DL/Bonus movements by histrico (Feb) to see how
PROMPT ===    "Bonus equipe" / "DL Extraordinaria" are actually booked.
PROMPT ============================================================
SELECT l.PCTCNUMEROCONTADEST id_conta,
       SUBSTR(l.LANCHISTORICO,1,60) historico,
       ROUND(SUM(l.LANNVALOR),2) total, COUNT(*) n
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%LUCRO%'
      OR UPPER(l.LANCHISTORICO) LIKE '%B_NUS%'
      OR UPPER(l.LANCHISTORICO) LIKE '%BONUS%'
      OR UPPER(l.LANCHISTORICO) LIKE '%EXCEDENTE%'
      OR UPPER(l.LANCHISTORICO) LIKE '%EXTRAORDIN%'
      OR UPPER(l.LANCHISTORICO) LIKE '%CACIONE%' )
 GROUP BY l.PCTCNUMEROCONTADEST, SUBSTR(l.LANCHISTORICO,1,60)
 ORDER BY total DESC;

PROMPT ============================================================
PROMPT === D. Despesas para Clientes (Reembolsaveis). Candidate: a client-expense
PROMPT ===    account. Hunt account names, then the per-month totals.
PROMPT ============================================================
SELECT r.ANO_MES ano_mes, r.ID_CONTA,
       MAX(r.NOME_CONTA) nome_conta, MAX(r.NOME_CONTA_PAI) nome_conta_pai,
       ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND ( UPPER(r.NOME_CONTA) LIKE '%REEMBOL%'
      OR UPPER(r.NOME_CONTA) LIKE '%CLIENTE%'
      OR UPPER(r.NOME_CONTA_PAI) LIKE '%CLIENTE%'
      OR UPPER(r.NOME_CONTA_PAI) LIKE '%REEMBOL%' )
 GROUP BY r.ANO_MES, r.ID_CONTA
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT === D2. Despesas para Clientes via LANCAMENTO histrico (Feb) ===
SELECT l.PCTCNUMEROCONTADEST id_conta,
       SUBSTR(l.LANCHISTORICO,1,60) historico,
       ROUND(SUM(l.LANNVALOR),2) total, COUNT(*) n
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%REEMBOL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%CLIENTE%'
      OR UPPER(l.LANCHISTORICO) LIKE '%CUSTAS%'
      OR UPPER(l.LANCHISTORICO) LIKE '%DESPESA%CLIENTE%' )
 GROUP BY l.PCTCNUMEROCONTADEST, SUBSTR(l.LANCHISTORICO,1,60)
 ORDER BY total DESC;

EXIT
