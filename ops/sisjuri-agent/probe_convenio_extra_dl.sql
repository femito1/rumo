-- probe_convenio_extra_dl.sql
-- GOAL: automate the "convênio extra per lawyer" DL deduction (T-remaining #2).
-- Mechanism (transitoria-desdobramento-mechanism memory, client transcript):
--   The office pays a base convênio (030.010.0110, ties to workbook). If a lawyer
--   upgrades / adds dependentes, that EXTRA is booked to 500.010.<SIGLA> and
--   DEDUCTED FROM THAT LAWYER'S Distribuição de Lucros (DL) — it is NOT an office
--   expense. Only ~3 lawyers do this: Ricardo/RB, Aurélio/AM, Daniel/DC.
-- We need: per-sigla, per-month the 500.010.<SIGLA> convênio/dependente amount, so
-- the DL block can subtract it from that partner's distribution automatically.
-- Read-only. Pipe-tagged single-line statements.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A 500.010.<SIGLA> personal debits with convênio/dependente/saúde/plano histórico, Jan..Mai
-- CONTASPAGAR is the gross-base source for the personal-debit namespace.
SELECT 'A|'||cp.PCTCNUMEROCONTA||'|'||NVL(cp.COD_ADVG,'?')
       ||'|'||TO_CHAR(cp.CPGDVECTO,'YYYY-MM')
       ||'|base='||TO_CHAR(ROUND(cp.CPGNVALORBASE,2))
       ||'|liq='||TO_CHAR(ROUND(cp.CPGNVALORLIQUIDO,2))
       ||'|'||SUBSTR(REPLACE(NVL(cp.CPGCHISTORICO,' '),'|','/'),1,40)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.PCTCNUMEROCONTA LIKE '500.010.%'
   AND cp.CPGDVECTO >= DATE '2026-01-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND ( UPPER(cp.CPGCHISTORICO) LIKE '%CONV_NIO%' OR UPPER(cp.CPGCHISTORICO) LIKE '%CONVENIO%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%DEPENDENTE%' OR UPPER(cp.CPGCHISTORICO) LIKE '%SA_DE%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%SAUDE%' OR UPPER(cp.CPGCHISTORICO) LIKE '%PLANO%' )
 ORDER BY cp.PCTCNUMEROCONTA, cp.CPGDVECTO;

PROMPT #B Same, from LANCAMENTO ledger (net) — some 500.010 lines only exist here
SELECT 'B|'||l.PCTCNUMEROCONTADEST||'|'||NVL(l.LANCPROFDEST,'?')
       ||'|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|'||SUBSTR(REPLACE(NVL(l.LANCHISTORICO,' '),'|','/'),1,40)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '500.010.%'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%CONV_NIO%' OR UPPER(l.LANCHISTORICO) LIKE '%CONVENIO%'
      OR UPPER(l.LANCHISTORICO) LIKE '%DEPENDENTE%' OR UPPER(l.LANCHISTORICO) LIKE '%SA_DE%'
      OR UPPER(l.LANCHISTORICO) LIKE '%SAUDE%' OR UPPER(l.LANCHISTORICO) LIKE '%PLANO%' )
 ORDER BY l.PCTCNUMEROCONTADEST, l.LANDDATA;

PROMPT #C Base convênio 030.010.0110 per lawyer (May) — the office-paid part that DOES tie
SELECT 'C|'||NVL(l.LANCPROFDEST,'?')||'|val='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))||'|n='||COUNT(*)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0110'
   AND l.LANDDATA >= DATE '2026-05-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY l.LANCPROFDEST ORDER BY 1;

PROMPT #D Plano de saúde lump desdobramento (May) — 31.882,29 per transcript; per-sigla slices
-- The plano de saúde total unfolds per-advogado via CPDESDOBRAMENTO; show the destinos.
SELECT 'D|'||d.DESCCONTADESTINO||'|val='||TO_CHAR(ROUND(SUM(d.DESNVALOR),2))||'|n='||COUNT(*)
  FROM FINANCE.CPDESDOBRAMENTO d
  JOIN FINANCE.CONTASPAGAR cp ON cp.EMPNCOD=d.EMPNCOD AND cp.CPGCNUMEROPAGAR=d.CPGCNUMEROPAGAR
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND ( UPPER(cp.CPGCHISTORICO) LIKE '%PLANO%SA_DE%' OR UPPER(cp.CPGCHISTORICO) LIKE '%PLANO%SAUDE%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%CONV_NIO%M_DIC%' OR UPPER(cp.CPGCHISTORICO) LIKE '%SAUDE%' )
 GROUP BY d.DESCCONTADESTINO ORDER BY 2 DESC;

PROMPT #END
EXIT
