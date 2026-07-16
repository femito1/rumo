-- probe_dl_extraordinaria_cacione.sql  (GAP 3 — the last two DL-extras lines)
-- CONTEXT: in the AUTHORITATIVE book (Fechamento MBC 05.2026, aba Base_Resultado_V2)
-- the two lines "DL Extraordinária" and "Repasse Cacione" are BLANK in every month
-- Jan-Mai — the "Distribuição de Lucros extras" block (r191) is fully = Bônus equipe
-- (r192) + DL excedente sócios (r193) + DL excedente MV (r194), all already DB-derived.
-- The 164.477,34 an older probe called "DL Extraordinária (02.2026)" is the SAME value
-- the 05 book relabels as "DL excedente dos sócios" (Jan) — already automated (POINT 17).
--
-- So there is NO ground-truth value to tie for these two lines. This is a DISCOVERY probe:
-- confirm whether Extraordinária / Cacione EVER get booked (any month 2024-2026), and if
-- so capture the account + histórico pattern so we can auto-derive them when a month has
-- one (blank stays correct when absent). Cacione = a person's name (a repasse to Cacione).
--
-- ⚠ SQL: single concatenated SELECT column → ORDER BY 1 or none. Read-only. Pipe-tagged.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A FINANCE.LANCAMENTO across ALL history: any histórico ~ Extraordinár / Cacione
-- The DL lines we cracked (bonus, excedente) live in FINANCE.LANCAMENTO keyed by histórico.
-- Widest net: every lançamento whose histórico mentions these, with conta + month + value.
SELECT 'A|'||l.PCTCNUMEROCONTADEST
       ||'|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|'||SUBSTR(REPLACE(NVL(l.LANCHISTORICO,' '),'|','/'),1,60)
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANDDATA >= DATE '2024-01-01' AND l.LANDDATA < DATE '2026-07-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%EXTRAORDIN%'
      OR UPPER(l.LANCHISTORICO) LIKE '%CACIONE%' )
 ORDER BY 1;

PROMPT #B Same net on CONTASPAGAR histórico (in case a repasse is a payable, not a ledger move)
SELECT 'B|'||cp.PCTCNUMEROCONTA
       ||'|'||TO_CHAR(cp.CPGDVECTO,'YYYY-MM')
       ||'|liq='||TO_CHAR(ROUND(cp.CPGNVALORLIQUIDO,2))
       ||'|adv='||NVL(cp.COD_ADVG,'-')
       ||'|'||SUBSTR(REPLACE(NVL(cp.CPGCHISTORICO,' '),'|','/'),1,60)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2024-01-01' AND cp.CPGDVECTO < DATE '2026-07-01'
   AND ( UPPER(cp.CPGCHISTORICO) LIKE '%EXTRAORDIN%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%CACIONE%' )
 ORDER BY 1;

PROMPT #C The DL-excedente account 030.010.0010 — ALL 2026 histórico patterns (context)
-- Shows what actually posts here (excedente/reserva/extraordinária) so we know the
-- vocabulary and can tell an "Extraordinária" apart from the excedente we already handle.
SELECT 'C|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|'||SUBSTR(REPLACE(NVL(l.LANCHISTORICO,' '),'|','/'),1,60)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-07-01'
 ORDER BY 1;

PROMPT #D Any account whose NAME mentions Cacione / Extraordinária / Repasse (plano de contas)
SELECT 'D|'||OWNER||'.'||TABLE_NAME||'|found via ALL_TAB_COLUMNS check skipped'
  FROM DUAL WHERE 1=0;
-- Names live in GERENC_LANCAMENTORESUMO.NOME_CONTA; scan distinct account names 2026.
SELECT 'D|'||r.ID_CONTA||'|'||SUBSTR(r.NOME_CONTA,1,50)
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND ( UPPER(r.NOME_CONTA) LIKE '%CACIONE%'
      OR UPPER(r.NOME_CONTA) LIKE '%EXTRAORDIN%'
      OR UPPER(r.NOME_CONTA) LIKE '%REPASSE%' )
 GROUP BY r.ID_CONTA, r.NOME_CONTA
 ORDER BY 1;

PROMPT #END GAP3: both lines are BLANK in the 05.2026 book — this probe confirms if/where they ever occur
