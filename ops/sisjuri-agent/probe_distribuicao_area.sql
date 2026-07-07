-- Probe: is the per-lawyer Distribuição Mensal Fixa (030.010.0010) split by area
-- IN THE DATABASE, so per-area Custo equipe can be fully automated (no monthly
-- manual ledger)? Read-only. Run on MBC-LDESK01 via the sqlplus-over-RDP recipe.
--
-- Context: custo_equipe_prof returns Distribuição as a lump with NULL prof.
-- distribuicao_socio (FINANCE.LANCAMENTO, COD_ADVG + SIGLADEST) came back EMPTY
-- in the snapshot — likely because the documented LANCHISTORICO LIKE 'Distribui%Fixa%'
-- filter matches nothing. This probe drops that filter and inspects the raw rows.
--
-- The question we MUST answer (per "assume automation is possible until proven
-- otherwise"): does COD_ADVG + SIGLADEST reproduce, to the centavo, the ledger's
-- per-lawyer distribution AND its area split (e.g. Aurelio 50/50 Contencioso/
-- Econômico)? If yes -> full automation; a future lawyer's split flows through
-- automatically. If no -> we then (and only then) discuss minimal manual config.
SET DEFINE OFF
SET PAGESIZE 400
SET LINESIZE 400
SET FEEDBACK ON
WHENEVER SQLERROR CONTINUE

PROMPT === 0. Columns on FINANCE.LANCAMENTO (confirm COD_ADVG / SIGLADEST / LANCHISTORICO / value cols) ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE owner='FINANCE' AND table_name='LANCAMENTO' ORDER BY column_id;

PROMPT === 1. RAW distribuicao rows for 030.010.0010 (NO historico filter), Feb 2026 ===
PROMPT     Grouped by lawyer + destination cost-center. Does SIGLADEST look like an area?
SELECT l.COD_ADVG                 AS sigla,
       l.SIGLADEST                AS cost_center,
       ROUND(SUM(l.LANNVALOR), 2) AS valor,
       COUNT(*)                   AS n
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST = '030.010.0010'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01'
 GROUP BY l.COD_ADVG, l.SIGLADEST
 ORDER BY l.COD_ADVG, l.SIGLADEST;

PROMPT === 1b. Distinct LANCHISTORICO values present (so we know the real sub-type text) ===
SELECT DISTINCT SUBSTR(l.LANCHISTORICO,1,60) AS historico
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST = '030.010.0010'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01';

PROMPT === 2. Grand total of raw distribuicao (must tie to ledger lump 172.129,96 / account total) ===
SELECT ROUND(SUM(l.LANNVALOR),2) AS total_net, COUNT(*) AS n
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST = '030.010.0010'
   AND l.LANDDATA >= DATE '2026-02-01' AND l.LANDDATA < DATE '2026-03-01';

PROMPT === 3. What does SIGLADEST decode to? Compare against grupo jurídico / area names ===
SELECT ID_GRUPOJURIDICO, NOME FROM LDESK.CAD_GRUPOJURIDICO ORDER BY NOME;

PROMPT === 4. Does SIGLADEST match a professional's sigla (i.e. is it a person, not an area)? ===
SELECT p.SIGLA, p.SOCIO, g.NOME AS grupo_area
  FROM LDESK.CAD_PROFISSIONAL p
  LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = p.ID_GRUPOJURIDICO
 ORDER BY p.SIGLA;

PROMPT === 5. GROSS per-lawyer distribuicao via CONTASPAGAR (the ledger uses GROSS, e.g. 12500) ===
PROMPT     If LANCAMENTO is net, gross likely lives here; check it also carries a cost-center/area.
SELECT column_name, data_type FROM ALL_TAB_COLUMNS
 WHERE owner='FINANCE' AND table_name='CONTASPAGAR' ORDER BY column_id;

SELECT cp.COD_ADVG AS sigla,
       ROUND(SUM(cp.CPGNVALORBASE),2) AS bruto,
       COUNT(*) AS n
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.PCTCNUMEROCONTA = '030.010.0010'
   AND cp.CPGDVECTO >= DATE '2026-02-01' AND cp.CPGDVECTO < DATE '2026-03-01'
 GROUP BY cp.COD_ADVG
 ORDER BY cp.COD_ADVG;

EXIT
