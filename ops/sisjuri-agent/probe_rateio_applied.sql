-- Probe: the DB's OWN rateio/DRE output. GERENC_LANCAMENTORESUMORATEIO is the
-- resumo WITH rateio applied, split into DESP_DIRETA / CUSTO_DIRETO /
-- DESP_INDIRETA_PERCAPITA / DESP_INDIRETA_PESO / INVESTIMENTO_* per
-- ID_GRUPOJURIDICO. DB_RESULTADO_AREA is a per-area resultado. Either may
-- reproduce the workbook's per-area Despesa Institucional + Despesas Área.
-- Workbook Feb targets:
--   Despesa Institucional total 95.047,39
--   Despesas Área Cont 2.129,32 / Econ 3.296,07 / Arb 2.633,69
--   Despesa Institucional rateada (row I, from ledger_import): derived per area
-- Areas: Equipe Contencioso / Equipe Direito Econômico / Arbitragem.
SET DEFINE OFF
SET PAGESIZE 2000
SET LINESIZE 300
SET FEEDBACK ON
COL area FORMAT A26
COL nome FORMAT A34
COL id_conta FORMAT A16
WHENEVER SQLERROR CONTINUE

PROMPT === 1. RESUMORATEIO: per-area totals of each rateio component, Feb 2026 ===
SELECT NVL(g.NOME,'(sem)') area,
       ROUND(SUM(r.DESP_DIRETA),2) desp_dir,
       ROUND(SUM(r.CUSTO_DIRETO),2) custo_dir,
       ROUND(SUM(r.DESP_INDIRETA_PERCAPITA),2) desp_ind_pc,
       ROUND(SUM(r.DESP_INDIRETA_PESO),2) desp_ind_peso,
       ROUND(SUM(r.INVESTIMENTO_PERCAPITA),2) inv_pc,
       ROUND(SUM(r.INVESTIMENTO_PESO),2) inv_peso
  FROM LDESK.GERENC_LANCAMENTORESUMORATEIO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES='2026-02'
 GROUP BY g.NOME
 ORDER BY area;

PROMPT === 2. RESUMORATEIO: totals across ALL areas of each component (sanity vs pool) ===
SELECT ROUND(SUM(r.DESP_DIRETA),2) desp_dir,
       ROUND(SUM(r.CUSTO_DIRETO),2) custo_dir,
       ROUND(SUM(r.DESP_INDIRETA_PERCAPITA + r.DESP_INDIRETA_PESO),2) desp_indireta,
       ROUND(SUM(r.INVESTIMENTO_PERCAPITA + r.INVESTIMENTO_PESO),2) investimento
  FROM LDESK.GERENC_LANCAMENTORESUMORATEIO r
 WHERE r.ANO_MES='2026-02';

PROMPT === 3. RESUMORATEIO per-area: DRE-area only, indireta+investimento = Despesa Inst rateada? ===
-- Compare Cont/Econ/Arb indireta+inv to the workbook's per-area Despesa Institucional.
SELECT g.NOME area,
       ROUND(SUM(r.DESP_INDIRETA_PERCAPITA + r.DESP_INDIRETA_PESO
                 + r.INVESTIMENTO_PERCAPITA + r.INVESTIMENTO_PESO),2) desp_inst_rateada,
       ROUND(SUM(r.DESP_DIRETA),2) desp_direta_area
  FROM LDESK.GERENC_LANCAMENTORESUMORATEIO r
  JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES='2026-02'
   AND (UPPER(g.NOME) LIKE '%CONTENCIOSO%' OR UPPER(g.NOME) LIKE '%ECON%'
        OR UPPER(g.NOME) LIKE '%ARBITRAGEM%' OR UPPER(g.NOME) LIKE '%COMPLIANCE%')
 GROUP BY g.NOME ORDER BY area;

PROMPT === 4. RESUMORATEIO multi-month (Jan..Mai) per DRE area: indireta+inv & direta ===
SELECT r.ANO_MES, g.NOME area,
       ROUND(SUM(r.DESP_INDIRETA_PERCAPITA + r.DESP_INDIRETA_PESO
                 + r.INVESTIMENTO_PERCAPITA + r.INVESTIMENTO_PESO),2) desp_inst_rat,
       ROUND(SUM(r.DESP_DIRETA),2) desp_direta
  FROM LDESK.GERENC_LANCAMENTORESUMORATEIO r
  JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (UPPER(g.NOME) LIKE '%CONTENCIOSO%' OR UPPER(g.NOME) LIKE '%ECON%'
        OR UPPER(g.NOME) LIKE '%ARBITRAGEM%' OR UPPER(g.NOME) LIKE '%COMPLIANCE%')
 GROUP BY r.ANO_MES, g.NOME ORDER BY r.ANO_MES, area;

PROMPT === 5. DB_RESULTADO_AREA: per-area DRE for Feb 2026 (the dashboard's own?) ===
SELECT NOMEAREA area,
       ROUND(SUM(CUSTO_DIRETO),2) custo_dir,
       ROUND(SUM(CUSTO_INDIRETO),2) custo_ind,
       ROUND(SUM(DESP_DIRETA),2) desp_dir,
       ROUND(SUM(DESP_INDIRETA),2) desp_ind,
       ROUND(SUM(INVESTIMENTO),2) inv
  FROM LDESK.DB_RESULTADO_AREA
 WHERE ANO_MES='2026-02'
 GROUP BY NOMEAREA ORDER BY area;

PROMPT === 6. DB_RESULTADO_AREA: row count / distinct ANO_MES present (is it populated?) ===
SELECT ANO_MES, COUNT(*) n FROM LDESK.DB_RESULTADO_AREA
 WHERE ANO_MES BETWEEN '2026-01' AND '2026-05'
 GROUP BY ANO_MES ORDER BY ANO_MES;

EXIT
