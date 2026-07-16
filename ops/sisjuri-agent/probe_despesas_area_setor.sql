-- probe_despesas_area_setor.sql  (GAP 2, v4 — the split key)
-- v3 discovered: (1) CPDESDOBRAMENTO has DESCSETOR + DESCPROFISSIONAL columns (a
-- setor/prof tag on each unfolded slice — the split key I hadn't dumped); (2) direct
-- 020.* CONTASPAGAR lines carry a SIGLA cost-center = ECT/EDE/ESP/ADM, and per the
-- docs ECT=Contencioso, EDE=Econômico, ESP=Arbitragem/Compliance. Patrocínio 1.204,47
-- (SIGLA=ESP) = Arbitragem's exact target ✓. But direct-line SIGLA sums are small
-- (ECT 77,54 / EDE 1.358,72 / ESP 1.272,47) vs targets (2.276 / 2.300 / 1.204) — so
-- the bulk of Contencioso/Econômico Despesas Área is in DESDOBRAMENTO slices keyed by
-- DESCSETOR. GOAL: group ALL 020.* despesa (direct lines by SIGLA + slices by
-- DESCSETOR) and hit Contencioso 2.276,22 / Econômico 2.300,10 / Arbitragem 1.204,47.
--
-- ⚠ SQL: single concatenated column → ORDER BY 1 or none. Read-only. Pipe-tagged.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A CPDESDOBRAMENTO 020.* slices May WITH DESCSETOR + DESCPROFISSIONAL (the split key)
SELECT 'A|'||d.DESCCONTADESTINO
       ||'|setor='||NVL(d.DESCSETOR,'-')
       ||'|prof='||NVL(d.DESCPROFISSIONAL,'-')
       ||'|val='||TO_CHAR(ROUND(d.DESNVALOR,2))
       ||'|'||SUBSTR(REPLACE(NVL(d.DESCHISTORICO,' '),'|','/'),1,40)
  FROM FINANCE.CPDESDOBRAMENTO d
  JOIN FINANCE.CONTASPAGAR cp
    ON cp.EMPNCOD=d.EMPNCOD AND cp.CPGCNUMEROPAGAR=d.CPGCNUMEROPAGAR
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND d.DESCCONTADESTINO LIKE '020.%'
 ORDER BY 1;

PROMPT #B Distinct DESCSETOR values on 020.* slices May (Σ per setor) — do they tie the targets?
SELECT 'B|setor='||NVL(d.DESCSETOR,'(null)')||'|Σval='||TO_CHAR(ROUND(SUM(d.DESNVALOR),2))||'|n='||COUNT(*)
  FROM FINANCE.CPDESDOBRAMENTO d
  JOIN FINANCE.CONTASPAGAR cp
    ON cp.EMPNCOD=d.EMPNCOD AND cp.CPGCNUMEROPAGAR=d.CPGCNUMEROPAGAR
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND d.DESCCONTADESTINO LIKE '020.%'
 GROUP BY d.DESCSETOR
 ORDER BY 1;

PROMPT #C Direct 020.* lines: Σ CPGNVALORLIQUIDO by SIGLA cost-center (ECT/EDE/ESP/ADM)
SELECT 'C|sigla='||NVL(cp.SIGLA,'(null)')||'|Σliq='||TO_CHAR(ROUND(SUM(cp.CPGNVALORLIQUIDO),2))||'|n='||COUNT(*)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
   AND cp.PCTCNUMEROCONTA LIKE '020.%'
 GROUP BY cp.SIGLA
 ORDER BY 1;

PROMPT #D COMBINED per setor/sigla: direct-line SIGLA + slice DESCSETOR (union), Σ — hit 2276/2300/1204?
-- Normalize both keys into one bucket per cost-center and sum.
SELECT 'D|cc='||cc||'|Σ='||TO_CHAR(ROUND(SUM(v),2))||'|n='||COUNT(*)
  FROM (
    SELECT NVL(cp.SIGLA,'(null)') cc, cp.CPGNVALORLIQUIDO v
      FROM FINANCE.CONTASPAGAR cp
     WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
       AND cp.PCTCNUMEROCONTA LIKE '020.%'
       AND NOT EXISTS (SELECT 1 FROM FINANCE.CPDESDOBRAMENTO d2
                        WHERE d2.EMPNCOD=cp.EMPNCOD AND d2.CPGCNUMEROPAGAR=cp.CPGCNUMEROPAGAR)
    UNION ALL
    SELECT NVL(d.DESCSETOR,'(null)') cc, d.DESNVALOR v
      FROM FINANCE.CPDESDOBRAMENTO d
      JOIN FINANCE.CONTASPAGAR cp
        ON cp.EMPNCOD=d.EMPNCOD AND cp.CPGCNUMEROPAGAR=d.CPGCNUMEROPAGAR
     WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
       AND d.DESCCONTADESTINO LIKE '020.%'
  )
 GROUP BY cc
 ORDER BY 1;

PROMPT #E Distinct DESCSETOR values across ALL CPDESDOBRAMENTO May (understand the setor vocabulary)
SELECT 'E|setor='||NVL(d.DESCSETOR,'(null)')||'|n='||COUNT(*)
  FROM FINANCE.CPDESDOBRAMENTO d
  JOIN FINANCE.CONTASPAGAR cp
    ON cp.EMPNCOD=d.EMPNCOD AND cp.CPGCNUMEROPAGAR=d.CPGCNUMEROPAGAR
 WHERE cp.CPGDVECTO >= DATE '2026-05-01' AND cp.CPGDVECTO < DATE '2026-06-01'
 GROUP BY d.DESCSETOR
 ORDER BY 1;

PROMPT #END target MAY Despesas Equipe: ECT/Contencioso 2276.22 / EDE/Econômico 2300.10 / ESP/Arbitragem 1204.47
