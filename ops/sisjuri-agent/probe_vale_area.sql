-- Sanity: does GERENC_LANCAMENTORESUMO carry Vale Refeição (0100) + Transporte
-- (0220) with a grupo (area) for Feb 2026, so the new custo_equipe_area extract
-- block can find them? Ledger Contencioso: 1.014,20 + 235,20 = 1.249,40. Read-only.
SET DEFINE OFF
SET PAGESIZE 400
SET LINESIZE 200
SET FEEDBACK ON
WHENEVER SQLERROR CONTINUE

PROMPT === Vale accounts by area, Feb 2026 (area from grupo, blank professional) ===
SELECT g.NOME AS area, r.ID_CONTA AS conta,
       ROUND(SUM(r.VALOR),2) AS total, COUNT(*) AS n
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES='2026-02'
   AND r.ID_CONTA IN ('030.010.0100','030.010.0220')
   AND r.ID_PROFISSIONAL IS NULL
   AND g.NOME IS NOT NULL
 GROUP BY g.NOME, r.ID_CONTA ORDER BY g.NOME, r.ID_CONTA;

PROMPT === Same but ALL rows (in case some carry a prof or no grupo) ===
SELECT r.ID_CONTA, r.ID_PROFISSIONAL prof, r.ID_GRUPOJURIDICO grupo,
       ROUND(r.VALOR,2) v
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES='2026-02'
   AND r.ID_CONTA IN ('030.010.0100','030.010.0220')
 ORDER BY r.ID_CONTA;

EXIT
