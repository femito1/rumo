-- probe_recebimento_area_prof.sql  (follow-up to probe_recebimento_area_basis.sql)
-- FINDING from v1: the workbook per-área Recebimento (Contencioso 240.445 /
-- Econômico 166.876 / Arbitragem 41.860, Σ 449.181) matches NEITHER cash-by-case
-- (A: 205.157/162.473/48.298, Σ=sacred 415.928) NOR faturado-by-case (B:
-- 321.146/155.711/243.131, Σ=sacred 719.988) NOR faturado-share×cash (C). Crucially
-- workbook Arbitragem (41.860) is BELOW its cash AND faturado — so per-área recebimento
-- is NOT a case-área measure. Signature of a PER-PROFISSIONAL participation allocation
-- rolled to each lawyer's home grupo = the "Demonstrativo Resultado Profissional".
-- v1 #E revealed the source family: DB_RESULTADO_PROF (RECEITA_REC + NOMEGRUPO) and
-- DB_VW_DEMONSTRATIVO_RESULTADOS (VALOR_RECEITA, PARTICIPACAO, per caso/prof).
--
-- GOAL: find the candidate whose MAY per-área rollup = 240.445 / 166.876 / 41.860
-- (Σ 449.181). Group by NOMEGRUPO; fold Ambiental→Arbitragem later; watch the TOTAL
-- row of each candidate (449.181 is the target sum). Read-only, pipe-tagged.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A DB_RESULTADO_PROF May: per-grupo RECEITA_REC vs RECEITA_FAT (which sums to 449.181?)
SELECT 'A|'||NVL(NOMEGRUPO,'(null)')
       ||'|rec='||TO_CHAR(ROUND(SUM(RECEITA_REC),2))
       ||'|fat='||TO_CHAR(ROUND(SUM(RECEITA_FAT),2))
       ||'|recl_desc='||TO_CHAR(ROUND(SUM(NVL(RECEITA_REC,0)-NVL(DESCONTO_RECEBIMENTO,0)),2))
  FROM LDESK.DB_RESULTADO_PROF
 WHERE ANO_MES='2026-05'
 GROUP BY NOMEGRUPO
 ORDER BY 1;

PROMPT #A2 DB_RESULTADO_PROF May GRAND TOTALS (spot the 449.181)
SELECT 'A2|TOTAL'
       ||'|rec='||TO_CHAR(ROUND(SUM(RECEITA_REC),2))
       ||'|fat='||TO_CHAR(ROUND(SUM(RECEITA_FAT),2))
       ||'|reclq_rec='||TO_CHAR(ROUND(SUM(NVL(RECEITA_REC,0)),2))
  FROM LDESK.DB_RESULTADO_PROF
 WHERE ANO_MES='2026-05';

PROMPT #B DB_VW_RESULTADO_PROF May: RECEITA by grupo x TIPO (TIPO may split rec/fat)
SELECT 'B|'||NVL(NOMEGRUPO,'(null)')||'|tipo='||NVL(TIPO,'?')
       ||'|receita='||TO_CHAR(ROUND(SUM(RECEITA),2))
       ||'|rec_liq='||TO_CHAR(ROUND(SUM(RECEITA_LIQUIDA),2))
  FROM LDESK.DB_VW_RESULTADO_PROF
 WHERE ANO_MES='2026-05'
 GROUP BY NOMEGRUPO, TIPO
 ORDER BY 1,2;

PROMPT #C DB_VW_DEMONSTRATIVO_RESULTADOS May: VALOR_RECEITA / RECEITA_LIQUIDA by grupo x TIPO
SELECT 'C|'||NVL(NOMEGRUPO,'(null)')||'|tipo='||NVL(TIPO,'?')
       ||'|vreceita='||TO_CHAR(ROUND(SUM(VALOR_RECEITA),2))
       ||'|rec_liq='||TO_CHAR(ROUND(SUM(RECEITA_LIQUIDA),2))
       ||'|valor='||TO_CHAR(ROUND(SUM(VALOR),2))
  FROM LDESK.DB_VW_DEMONSTRATIVO_RESULTADOS
 WHERE ANO_MES='2026-05'
 GROUP BY NOMEGRUPO, TIPO
 ORDER BY 1,2;

PROMPT #C2 DEMONSTRATIVO May distinct TIPO values (so we know which TIPO = recebimento)
SELECT 'C2|tipo='||NVL(TIPO,'?')||'|n='||COUNT(*)||'|Σvreceita='||TO_CHAR(ROUND(SUM(VALOR_RECEITA),2))
  FROM LDESK.DB_VW_DEMONSTRATIVO_RESULTADOS
 WHERE ANO_MES='2026-05'
 GROUP BY TIPO
 ORDER BY 1;

PROMPT #D Columns of the DB_VW_RESULT_REC* recebimento-basis views (need value col names)
SELECT 'D|'||TABLE_NAME||'|'||COLUMN_NAME||'|'||DATA_TYPE
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='LDESK'
   AND TABLE_NAME IN ('DB_VW_RESULT_REC_PROF','DB_VW_RESULT_REC','DB_VW_RESULT_REC_AREACLI',
                      'DB_RESULTADO_AREA','DB_VW_RESULTADO')
 ORDER BY TABLE_NAME, COLUMN_ID;

PROMPT #E DB_RESULTADO_AREA May (if it exists as a per-área rollup already) — dump raw cols=value
-- Discover columns first (above), but try the obvious: sum any RECEITA-ish col by área.
SELECT 'E|'||NVL(NOMEGRUPO,'(null)')||'|n='||COUNT(*)
  FROM LDESK.DB_RESULTADO_AREA
 WHERE ANO_MES='2026-05'
 GROUP BY NOMEGRUPO
 ORDER BY 1;

PROMPT #F GERENC_VW_FATREC_CASO_AREA May — a ready-made fat+rec-by-área view (v1 #D found it)
SELECT 'F|'||COLUMN_NAME||'|'||DATA_TYPE
  FROM ALL_TAB_COLUMNS
 WHERE OWNER='LDESK' AND TABLE_NAME='GERENC_VW_FATREC_CASO_AREA'
 ORDER BY COLUMN_ID;

PROMPT #END target MAY per-área: Contencioso 240445 / Econômico 166876 / Arbitragem(+Ambiental) 41860 (Σ 449181)
