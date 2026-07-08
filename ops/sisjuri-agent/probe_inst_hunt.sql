-- Probe: HUNT the exact Despesa Institucional total composition, and the exact
-- Despesas Área per-area assignment, both to the centavo.
-- Workbook targets:
--   Despesa Institucional total: Jan 100181,41 Feb 95047,39 Mar 101968,90 Apr 110156,11 Mai 105511,43
--   Despesas Área Cont: 1060,10 2129,32 2346,72 4183,92 2276,22
--   Despesas Área Econ: 1871,81 3296,07 2129,32 2129,32 2300,10
--   Despesas Área Arb : 146,00  2633,69 3728,18 2633,69 1204,47
-- Facts learned:
--   * Full 020+040 pool minus comissao (020.110): Feb 98185,28 (Δ +3137,89 vs WB).
--   * Area-tagged NON-030 lines don't match WB Despesas Área per-area (transposed/wrong).
-- New hypotheses:
--   A) WB total excludes "non-core" families: Benefícios 020.080, Marketing 040.010,
--      Biblioteca 040.050 (and maybe Financeiras 020.070).
--   B) WB Despesas Área uses a FIXED account whitelist (Assinaturas/Associações/
--      Cursos/Eventos/Material Grafico/Patrocinio/Refeições/Viagens), NOT the
--      ID_GRUPOJURIDICO tag — the tag disagrees with the workbook's manual area.
SET DEFINE OFF
SET PAGESIZE 4000
SET LINESIZE 340
SET FEEDBACK ON
COL ano_mes FORMAT A7
WHENEVER SQLERROR CONTINUE

PROMPT === A. Institutional total candidates, per month (several exclusion sets) ===
SELECT r.ANO_MES,
  ROUND(SUM(CASE WHEN r.ID_CONTA<>'020.110.0010' THEN r.VALOR ELSE 0 END),2) c_all,
  ROUND(SUM(CASE WHEN r.ID_CONTA NOT IN ('020.110.0010')
              AND r.ID_CONTA NOT LIKE '020.080.%' THEN r.VALOR ELSE 0 END),2) c_no_benef,
  ROUND(SUM(CASE WHEN r.ID_CONTA NOT IN ('020.110.0010')
              AND r.ID_CONTA NOT LIKE '020.080.%'
              AND r.ID_CONTA NOT LIKE '040.010.%'
              AND r.ID_CONTA NOT LIKE '040.050.%' THEN r.VALOR ELSE 0 END),2) c_no_benef_mkt_bib,
  ROUND(SUM(CASE WHEN r.ID_CONTA NOT IN ('020.110.0010')
              AND r.ID_CONTA NOT LIKE '020.070.%'
              AND r.ID_CONTA NOT LIKE '020.080.%'
              AND r.ID_CONTA NOT LIKE '040.010.%'
              AND r.ID_CONTA NOT LIKE '040.050.%' THEN r.VALOR ELSE 0 END),2) c_minus_fin_too
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
 GROUP BY r.ANO_MES
 ORDER BY r.ANO_MES;

PROMPT === B. Despesas Area by WHITELISTED account name (ignore ID_GRUPOJURIDICO), per area ===
-- Whitelist the workbook's Despesas Área account names; assign area by NOME_CONTA
-- suffix if present, else by ID_GRUPOJURIDICO. First: what do these accounts total
-- per area via ID_GRUPOJURIDICO (already have) vs total regardless of tag?
SELECT r.ANO_MES, r.ID_CONTA, MAX(r.NOME_CONTA) nome, ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (UPPER(r.NOME_CONTA) LIKE '%ASSINATURA%'
        OR UPPER(r.NOME_CONTA) LIKE '%ASSOCIA%'
        OR UPPER(r.NOME_CONTA) LIKE '%CURSO%'
        OR UPPER(r.NOME_CONTA) LIKE '%EVENTO%'
        OR UPPER(r.NOME_CONTA) LIKE '%MATERIAL GR%'
        OR UPPER(r.NOME_CONTA) LIKE '%PATROC%'
        OR UPPER(r.NOME_CONTA) LIKE '%REFEI%'
        OR UPPER(r.NOME_CONTA) LIKE '%VIAGE%')
 GROUP BY r.ANO_MES, r.ID_CONTA
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT === C. Does Associacoes(020.060.0020) alone tie to WB Despesas Area per area? ===
-- Feb WB: Cont 2129,32 Econ 3296,07 Arb 2633,69. Show 020.060.0020 by area.
SELECT r.ANO_MES, g.NOME area, ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.ID_CONTA='020.060.0020'
 GROUP BY r.ANO_MES, g.NOME
 ORDER BY r.ANO_MES, g.NOME;

PROMPT === D. Grand-total check: does Σ(all 020+040 minus comissao) - Σ DespesasArea(area-tag) ?= WB rateável ===
-- The rateio pool the workbook rateia = total - despesas_area. Show both so we can
-- reconstruct exactly which combination hits WB total AND WB despesas_area.
SELECT r.ANO_MES,
  ROUND(SUM(r.VALOR),2) pool_all_excl_comissao
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
   AND r.ID_CONTA<>'020.110.0010'
 GROUP BY r.ANO_MES ORDER BY r.ANO_MES;

EXIT
