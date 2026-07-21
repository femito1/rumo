-- probe_unknown_accounts.sql  (2026-07-21)
-- =====================================================================
-- Hunt for DB "unknowns": accounts that had NO movement in the May book we
-- reconciled against, but DO post in other 2026 months — so they could be
-- silently mis-classified or dropped by the extract. Excludes Orçamento &
-- Amortização per instruction.
--
-- Findings feeding this probe (from the raw May Extrato + chart of accounts):
--   * despesas_conta (GERENC, ALL accounts -> section_for) and despesas_liquido
--     (ALL 020.%/040.%) auto-sweep by prefix, so any 020/040 leaf that posts is
--     captured for the institutional TOTAL. Risk there = wrong FAMILY, not a drop.
--   * The real blind spots are 030.* leaves that are NOT team cost (the code only
--     carves out 030.010.0180 Cursos). If e.g. 030.010.0020 "Bônus Associados",
--     030.010.0150 "AASP", 030.010.0200 "Seguro de Vida", 030.010.0090
--     "Estacionamento/Ajuda de custo", 030.010.0160 "ISS", 030.010.0170 "OAB",
--     030.010.0190 "Adiantamento de DL", 030.010.0210 "IR-Equipe" post in any
--     month, they are being summed into CUSTO EQUIPE — verify that matches the
--     workbook's intent for those months.
--   * 150.010.0020 "Bônus" and 150.010.0010 "Adiantamento de DL" are 150.* leaves
--     the bonus block should catch — confirm no OTHER 150 leaf carries value.
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
PROMPT #A Every 030.* account by month (Jan..Jun 2026): value + which are NOT team cost
PROMPT ============================================================
PROMPT Watch for non-team leaves (0020 Bônus Assoc, 0090 Estac, 0150 AASP, 0160 ISS,
PROMPT 0170 OAB, 0190 Adiant DL, 0200 Seguro Vida, 0210 IR, 0220/0100 Vale) with value:
SELECT 'A|'||r.ID_CONTA
       ||'|'||MAX(SUBSTR(r.NOME_CONTA,1,28))
       ||'|'||r.ANO_MES
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2))
       ||'|n='||COUNT(*) AS out
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-06'
   AND r.ID_CONTA LIKE '030.%'
   AND r.ID_CONTA NOT IN ('030.010.0010','030.010.0050','030.010.0110',
                          '030.010.0120','030.010.0130','030.010.0140','030.010.0180','030.020.0010')
 GROUP BY r.ID_CONTA, r.ANO_MES
 HAVING ROUND(SUM(r.VALOR),2) <> 0
 ORDER BY 1,3;

PROMPT ============================================================
PROMPT #B Any 150.* leaf OTHER than the bonus/adiant leaves, by month
PROMPT ============================================================
SELECT 'B|'||l.PCTCNUMEROCONTADEST
       ||'|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|'||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
       ||'|n='||COUNT(*) AS out
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '150.%'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-07-01'
 GROUP BY l.PCTCNUMEROCONTADEST, TO_CHAR(l.LANDDATA,'YYYY-MM')
 ORDER BY 1,2;

PROMPT ============================================================
PROMPT #C Seasonal ADM payroll leaves (13o, rescisões, home office, exames, bolsa estag ADM)
PROMPT ============================================================
PROMPT These 020.050.* leaves are empty in Jan-May; confirm if/when they post (13o ~Nov/Dec):
SELECT 'C|'||r.ID_CONTA
       ||'|'||MAX(SUBSTR(r.NOME_CONTA,1,28))
       ||'|'||r.ANO_MES
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2)) AS out
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-06'
   AND r.ID_CONTA IN ('020.050.0030','020.050.0040','020.050.0070','020.050.0080',
                      '020.050.0090','020.050.0100','020.050.0120','020.050.0130',
                      '020.050.0150','020.050.0160')
 GROUP BY r.ID_CONTA, r.ANO_MES
 HAVING ROUND(SUM(r.VALOR),2) <> 0
 ORDER BY 1,3;

PROMPT ============================================================
PROMPT #D FULL GERENC account list for a NON-May month (2026-04) — catch anything unmapped
PROMPT ============================================================
PROMPT Every account with movement in April; compare families to the May classification:
SELECT 'D|'||r.ID_CONTA
       ||'|'||MAX(SUBSTR(NVL(r.NOME_CONTA,'?'),1,26))
       ||'|pai='||MAX(SUBSTR(NVL(r.NOME_CONTA_PAI,'?'),1,20))
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2)) AS out
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES = '2026-04'
 GROUP BY r.ID_CONTA
 HAVING ROUND(SUM(r.VALOR),2) <> 0
 ORDER BY 1;

PROMPT ============================================================
PROMPT #E Sanity: does GERENC carry any account family we never mapped? (prefix census, Apr)
PROMPT ============================================================
SELECT 'E|'||SUBSTR(r.ID_CONTA,1,3)
       ||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2))
       ||'|n_accts='||COUNT(DISTINCT r.ID_CONTA) AS out
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES = '2026-04'
 GROUP BY SUBSTR(r.ID_CONTA,1,3)
 ORDER BY 1;

PROMPT #END
EXIT
