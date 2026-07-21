-- probe_janapr_reconcile.sql
-- =====================================================================
-- UNFORGIVING Jan–Apr 2026 reconciliation of the three families the
-- NOTA_CLIENTE currently calls "lançamentos manuais / não derivável do banco":
--   (1) Vale-ADM  (Vale Refeição/Transporte administrativo)
--   (2) Associações (020.060.0020: ICC / IBRAC / AASP / Canal Arbitragem)
--   (3) DL extras  (Bônus equipe 150.* + 030.010.0010; DL excedente sócios/MV)
--
-- WHY THIS EXISTS (2026-07-21 finding):
--   The RAW May system export "lancextrato de contas.xls" (Extrato de Contas,
--   built from FINANCE.LANCAMENTO) PROVES all three are ordinary system postings,
--   not hand-entries:
--     * Vale: transitória 200.010.0010 unfolds the "VR Mensal"/"VT Mensal" parent
--       (May 2.719,90 + 607,04 = 3.326,94 = workbook G122+G123) into per-person
--       destinations 500.010.MLA / .JVO / .VSR AND a slice to 020.030.0060. The
--       per-person ADM-vs-área split the prior note said "the DB doesn't store"
--       is literally in the desdobramento destination accounts + histórico.
--     * Associações 020.060.0020 = 2.822,06 with the AREA SPLIT written in the
--       histórico: "AASP AM, DC" (Contencioso), IBRAC "Dividido em Contencioso e
--       Econômico" (posted as TWO rows 700,09 + 700,10), "Patrocínio ... 100%
--       Arbitragem (MV)". Not invented by finance — transcribed from the system.
--     * DL extras post ~1x/yr in specific months; already DB-wired (bonus_equipe,
--       dl_excedente_socios/mv) and tie Feb/Jan/Mar to the centavo.
--
-- The OPEN question this probe settles: for Jan–Apr, do these same system
-- postings REPRODUCE the workbook cell to the centavo? If yes, the "manual /
-- not derivable" framing is wrong and Jan–Apr can be un-blanked from the DB.
-- The prior vale probe under-counted because it summed the wrong leg; this one
-- reconstructs the PARENT VR/VT Mensal amount the way the desdobramento does.
--
-- SAFE: read-only SELECTs. Pipe-delimited, block-prefixed output.
-- Column facts (docs/SISJURI_DB.md): FINANCE.LANCAMENTO is double-entry with
-- PCTCNUMEROCONTAORG / PCTCNUMEROCONTADEST, LANNVALOR, LANCHISTORICO, LANDDATA,
-- LANCPROFDEST, SIGLADEST. Date axis matching the workbook = LANDDATA.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT ============================================================
PROMPT #1 VALE-ADM per month — reconstruct the VR/VT "Mensal" PARENT
PROMPT ============================================================
PROMPT Workbook Vale-ADM targets: jan 1.127,96 | fev 1.351,88 | mar 3.983,22 | abr 3.421,36 | mai 3.326,94
PROMPT --- 1a: the PARENT postings (the amount the desdobramento unfolds) ---
-- The May export shows VR Mensal + VT Mensal booked into 200.010.0010 as the
-- positive parent leg (dest=100.010.0010, i.e. paid from Itaú). Sum the parent
-- "Pagamento de VR/VT Mensal para ..." lines per month. This is the true ADM Vale.
SELECT '1a|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|vr_vt_mensal_parent='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
       ||'|n='||COUNT(*)
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE 'PAGAMENTO DE VR%'
      OR UPPER(l.LANCHISTORICO) LIKE 'PAGAMENTO DE VT%' )
   AND l.LANNVALOR > 0
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM')
 ORDER BY 1;

PROMPT --- 1b: the DESDOBRAMENTO legs (per-person split) that sum to the parent ---
-- Vale unfolded to 500.010.<SIGLA> personal accounts + the 020.030.0060 slice.
-- Sums here (abs) should reconcile to 1a. Shows WHO is ADM vs área per month:
--   ADM (rateado): MLA, VSR, JVO(area lawyer -> per-area), etc.
SELECT '1b|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|dest='||NVL(l.PCTCNUMEROCONTADEST,'-')
       ||'|val='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
       ||'|n='||COUNT(*)
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%VALE REFEI%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VALE TRANSP%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%' )
   AND l.PCTCNUMEROCONTADEST LIKE '500.010.%'
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.PCTCNUMEROCONTADEST
 ORDER BY 1,2;

PROMPT --- 1c: EVERY vale/refeição/transporte line Jan..Apr (eyeball the wording per month) ---
SELECT '1c|'||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|org='||NVL(l.PCTCNUMEROCONTAORG,'-')
       ||'|dest='||NVL(l.PCTCNUMEROCONTADEST,'-')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|'||SUBSTR(l.LANCHISTORICO,1,70)
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-05-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%VALE%'
      OR UPPER(l.LANCHISTORICO) LIKE '%REFEI%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VR %'
      OR UPPER(l.LANCHISTORICO) LIKE '%VT %' )
   AND ( l.PCTCNUMEROCONTADEST LIKE '500.010.%'
      OR l.PCTCNUMEROCONTADEST = '200.010.0010'
      OR l.PCTCNUMEROCONTADEST = '020.030.0060' )
 ORDER BY 1;

PROMPT ============================================================
PROMPT #2 ASSOCIAÇÕES 020.060.0020 per month — total + per-line histórico
PROMPT ============================================================
PROMPT Workbook Associações totals (C..F): jan 1.400,19 | fev 3.829,42 | mar 4.046,82 | abr 4.046,82
PROMPT (workbook = Conten + Econ + Arb rows; verify the DB total AND the area split in histórico)
SELECT '2a|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|assoc_total='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
       ||'|n='||COUNT(*)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='020.060.0020'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
   AND l.LANNVALOR <> 0
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM')
 ORDER BY 1;

PROMPT --- 2b: every Associações line Jan..Apr with histórico (the area split is written here) ---
SELECT '2b|'||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|setor='||NVL(l.SIGLADEST,'-')
       ||'|'||SUBSTR(l.LANCHISTORICO,1,90)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='020.060.0020'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-05-01'
   AND l.LANNVALOR <> 0
 ORDER BY 1;

PROMPT ============================================================
PROMPT #3 DL EXTRAS per month — Bônus (150.* + 030.010.0010) and DL excedente
PROMPT ============================================================
PROMPT Workbook: Bônus equipe fev D192; DL excedente sócios jan C193; DL excedente MV mar E194
PROMPT --- 3a: Bônus 150.% by month (should be ~fev only) ---
SELECT '3a|'||TO_CHAR(l.LANDDATA,'YYYY-MM')
       ||'|bonus_150='||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))||'|n='||COUNT(*)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '150.%'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM')
 ORDER BY 1;

PROMPT --- 3b: 030.010.0010 lines whose histórico mentions Bônus / DL excedente / DL / Reserva, by month ---
SELECT '3b|'||TO_CHAR(l.LANDDATA,'YYYY-MM-DD')
       ||'|val='||TO_CHAR(ROUND(l.LANNVALOR,2))
       ||'|sig='||NVL(l.SIGLADEST,'-')
       ||'|'||SUBSTR(l.LANCHISTORICO,1,70)
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%BONUS%'
      OR UPPER(l.LANCHISTORICO) LIKE '%B_NUS%'
      OR UPPER(l.LANCHISTORICO) LIKE '%EXCEDENTE%'
      OR UPPER(l.LANCHISTORICO) LIKE '%RESERVA%'
      OR UPPER(l.LANCHISTORICO) LIKE '%CACIONE%' )
 ORDER BY 1;

PROMPT ============================================================
PROMPT #4 FULL institutional despesas per month, GROSS from the ledger (family roll-up)
PROMPT ============================================================
PROMPT Compare Σ to workbook row-198 targets: jan 100.181,41 | fev 95.047,39 | mar 101.968,90 | abr 110.285,28 | mai 105.640,60
PROMPT (this is GROSS/competence via GERENC-style roll-up; net adj + reclass applied in code)
SELECT '4|'||r.ANO_MES
       ||'|inst_020_040_gross='||TO_CHAR(ROUND(SUM(r.VALOR),2))||'|n='||COUNT(*)
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
   AND r.ID_CONTA NOT IN ('020.030.0140','020.030.0060')
 GROUP BY r.ANO_MES
 ORDER BY 1;

PROMPT #END
EXIT
