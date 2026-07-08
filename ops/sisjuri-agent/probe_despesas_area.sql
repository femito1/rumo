-- Probe: Despesas Equipe per area (workbook "Despesas Área" block).
--
-- The workbook lists these as area-suffixed lines under a "Despesas Área:" header:
--   Assinaturas - <area>, Associações - <area>, Cursos - <area>,
--   Eventos e Happy hour - <area>, Material Grafico - <area>,
--   Patrocinio - <area>, Refeições - <area>, Viagens - <area>
-- Feb 2026 ground truth (test_ledger_import.py):
--   Contencioso 2.129,32 · Econômico 3.296,07 · Arbitragem 2.633,69
-- Jan..Mai per area (workbook):
--   Contencioso: 1060,10 · 2129,32 · 2346,72 · 4183,92 · 2276,22
--   Econômico:   1871,81 · 3296,07 · 2129,32 · 2129,32 · 2300,10
--   Arbitragem:   146,00 · 2633,69 · 3728,18 · 2633,69 · 1204,47
--
-- The DB likely tags these lines with ID_GRUPOJURIDICO in GERENC_LANCAMENTORESUMO
-- (same column that Custo equipe area assignment uses). Probe both by
-- area-suffix in NOME_CONTA and by ID_GRUPOJURIDICO to find the cleanest key.
SET DEFINE OFF
SET PAGESIZE 3000
SET LINESIZE 340
SET FEEDBACK ON
COL id_conta FORMAT A16
COL nome FORMAT A60
COL area FORMAT A30
COL ano_mes FORMAT A7
WHENEVER SQLERROR CONTINUE

PROMPT === 1. Every 020.* account with ID_GRUPOJURIDICO set (area-tagged), Feb 2026 ===
-- If NOT NULL rows carry the area of Despesas Área, this is the derivation key.
SELECT r.ID_CONTA, MAX(r.NOME_CONTA) nome,
       MAX(g.NOME) area, ROUND(SUM(r.VALOR),2) total, COUNT(*) n
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES='2026-02'
   AND r.ID_CONTA LIKE '020.%'
   AND r.ID_GRUPOJURIDICO IS NOT NULL
 GROUP BY r.ID_CONTA, r.ID_GRUPOJURIDICO
 ORDER BY area, r.ID_CONTA;

PROMPT === 2. Same as (1) but ID_GRUPOJURIDICO NULL — the pure-institutional pool ===
SELECT r.ID_CONTA, MAX(r.NOME_CONTA) nome,
       ROUND(SUM(r.VALOR),2) total, COUNT(*) n
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES='2026-02'
   AND r.ID_CONTA LIKE '020.%'
   AND r.ID_GRUPOJURIDICO IS NULL
 GROUP BY r.ID_CONTA
 ORDER BY r.ID_CONTA;

PROMPT === 3. Feb 2026 area rollup of area-tagged 020.* — should equal workbook Despesas Área ===
-- Contencioso 2.129,32 / Econômico 3.296,07 / Arbitragem 2.633,69 target.
SELECT NVL(g.NOME,'(sem area)') area, ROUND(SUM(r.VALOR),2) total, COUNT(*) n
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES='2026-02'
   AND r.ID_CONTA LIKE '020.%'
   AND r.ID_GRUPOJURIDICO IS NOT NULL
 GROUP BY g.NOME
 ORDER BY area;

PROMPT === 4. Multi-month area rollup Jan..Mai — ties to workbook per-month grid? ===
SELECT r.ANO_MES, NVL(g.NOME,'(sem area)') area, ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.ID_CONTA LIKE '020.%'
   AND r.ID_GRUPOJURIDICO IS NOT NULL
 GROUP BY r.ANO_MES, g.NOME
 ORDER BY r.ANO_MES, area;

PROMPT === 5. If (1) came up empty, fall back to NOME_CONTA suffix ("- Contencioso" etc.) ===
-- Some workbook lines might be plain accounts with the area in the name text
-- rather than an ID_GRUPOJURIDICO. Detect by suffix.
SELECT r.ID_CONTA, r.NOME_CONTA nome, r.ANO_MES,
       ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.ID_CONTA LIKE '020.%'
   AND (UPPER(r.NOME_CONTA) LIKE '%CONTENCIOSO%'
        OR UPPER(r.NOME_CONTA) LIKE '%ECON_MICO%'
        OR UPPER(r.NOME_CONTA) LIKE '%ECON\U00CDMICO%'
        OR UPPER(r.NOME_CONTA) LIKE '%ARBITRAGEM%'
        OR UPPER(r.NOME_CONTA) LIKE '%COMPLIANCE%')
 GROUP BY r.ID_CONTA, r.NOME_CONTA, r.ANO_MES
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT === 6. All 020.* account names (help pick the right family / see naming) ===
SELECT DISTINCT r.ID_CONTA, r.NOME_CONTA, MAX(r.NOME_CONTA_PAI) nome_pai
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ID_CONTA LIKE '020.%'
   AND r.ANO_MES BETWEEN '2026-01' AND '2026-05'
 GROUP BY r.ID_CONTA, r.NOME_CONTA
 ORDER BY r.ID_CONTA;

EXIT
