-- probe_vale_desdobramento.sql
-- QUESTION: is the per-person VR/VT split retrievable for Jan–Jun 2026, and from
-- WHICH table? We need it to charge only the ADM person (Maria Luiza / MLA) to
-- institutional "Salários Administração", leaving the two estagiários in their áreas.
--
-- WHY THIS EXISTS. The committed twin rule in extract.sql is BROKEN: it drops a
-- transitória row only when a 500.010.<SIGLA> row has the SAME histórico AND
-- (within half a centavo) the SAME value. Proven against Jan–Jun on 2026-07-30
-- (probe_vale_twin_allmonths, block C): n_rows_dropped = 0 for EVERY month.
-- Reason: the transitória books a 3-person LUMP (June VR 3.042,60 = 1.014,20 × 3),
-- so no single per-person row ever equals it, and the histories differ too
-- ("...para João Victor, Maria Luiza e Vitoria" vs "...para João Victor." plus a
-- "Vale refeição: 22 dias x 46,10" tail). So vale_adm has been over-counting the
-- lawyers all along; June only ever tied because its snapshot was hand-patched.
--
-- WHAT RENATA SAID (voice notes, 2026-07-30) — this is the spec:
--   * "faz um lançamento único numa conta transitória, e DEPOIS ELE ABRE isso dentro
--      do sistema... dizendo pra QUAL PESSOA é essa despesa"  -> an unfold exists;
--   * "tem o vale transporte e o vale refeição, por isso que somam dois valores...
--      na verdade é despesa segregada de cada funcionário";
--   * "o IDEAL é que tenha lançamentos feitos para o ADM, lançamentos feitos para as
--      áreas específicas, porque são DOIS ESTAGIÁRIOS dentro de cada área, e tenha a
--      Maria Luiza que é da parte administrativa" -> ADM-only is the intended rule;
--   * mar/abr/mai in her workbook are NOT adjusted yet ("teve um mês que ficou tudo
--      na Malu... depois eu acabei ajustando"), and she explicitly said not to chase
--      them: "não vale a pena corrigir, o valor é irrisório". So those months are
--      allowed to differ — do NOT fit a formula to them.
--
-- WHAT TO DO WITH THE OUTPUT.
--   Block A — is the transitória payable even desdobrada? If DESDOBRADA=0 for the
--             VR/VT titles, CPDESDOBRAMENTO is NOT the mechanism and B/C will be
--             empty; the answer is then block D (LANCAMENTO 500.010.*), which we
--             already know exists for June only.
--   Block B — the unfolded slices with their cost-center (DESCSETOR) and histórico.
--             This is the candidate source for the per-person split.
--   Block C — per (month, DESCSETOR) totals. Compare the ADM bucket against the
--             workbook's typed Vale-ADM (Base_Resultado r122+r123):
--               Jan 1.127,96 | Fev 1.351,88 | Jun 1.333,12   <- adjusted months
--               Mar 3.983,22 | Abr 3.421,36 | Mai 3.326,94   <- NOT adjusted, ignore
--             A tie on Jan/Fev/Jun means we can derive ADM-only from this table.
--   Block D — the 500.010.<SIGLA> per-person rows, all six months, so we can see
--             exactly which months have them (June did; Jan–May appeared not to).
--
-- SAFE: read-only SELECTs. Columns verified against extract.sql (CONTASPAGAR:
-- PCTCNUMEROCONTA, CPGDVECTO, CPGNVALORLIQUIDO, CPGCHISTORICO, SIGLA;
-- CPDESDOBRAMENTO: DESCCONTADESTINO, DESNVALOR, DESCHISTORICO, DESCSETOR).
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 400
SET FEEDBACK OFF
SET TRIMSPOOL ON

PROMPT
PROMPT === BLOCK A: transitoria VR/VT payables — is each one DESDOBRADA? ===
PROMPT ano_mes|conta|valor_liq|n_slices|historico
SELECT TO_CHAR(cp.CPGDVECTO,'YYYY-MM') || '|' ||
       cp.PCTCNUMEROCONTA || '|' ||
       TO_CHAR(cp.CPGNVALORLIQUIDO,'FM999999990.00') || '|' ||
       (SELECT COUNT(*) FROM FINANCE.CPDESDOBRAMENTO d2
         WHERE d2.EMPNCOD = cp.EMPNCOD AND d2.CPGCNUMEROPAGAR = cp.CPGCNUMEROPAGAR) || '|' ||
       SUBSTR(cp.CPGCHISTORICO, 1, 80)
  FROM FINANCE.CONTASPAGAR cp
 WHERE cp.CPGDVECTO >= DATE '2026-01-01' AND cp.CPGDVECTO < DATE '2026-07-01'
   AND ( UPPER(cp.CPGCHISTORICO) LIKE '%VR MENSAL%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%VT MENSAL%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%VALE REFEI%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%VALE TRANSP%' )
 ORDER BY TO_CHAR(cp.CPGDVECTO,'YYYY-MM'), cp.PCTCNUMEROCONTA;

PROMPT
PROMPT === BLOCK B: the unfolded slices of those payables (per-person candidates) ===
PROMPT ano_mes|conta_destino|setor|valor|historico
SELECT TO_CHAR(cp.CPGDVECTO,'YYYY-MM') || '|' ||
       d.DESCCONTADESTINO || '|' ||
       NVL(d.DESCSETOR,'(null)') || '|' ||
       TO_CHAR(d.DESNVALOR,'FM999999990.00') || '|' ||
       SUBSTR(d.DESCHISTORICO, 1, 70)
  FROM FINANCE.CPDESDOBRAMENTO d
  JOIN FINANCE.CONTASPAGAR cp
    ON cp.EMPNCOD = d.EMPNCOD AND cp.CPGCNUMEROPAGAR = d.CPGCNUMEROPAGAR
 WHERE cp.CPGDVECTO >= DATE '2026-01-01' AND cp.CPGDVECTO < DATE '2026-07-01'
   AND ( UPPER(cp.CPGCHISTORICO) LIKE '%VR MENSAL%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%VT MENSAL%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%VALE REFEI%'
      OR UPPER(cp.CPGCHISTORICO) LIKE '%VALE TRANSP%' )
 ORDER BY TO_CHAR(cp.CPGDVECTO,'YYYY-MM'), d.DESCSETOR, d.DESCCONTADESTINO;

PROMPT
PROMPT === BLOCK C: per (month, setor) totals — compare the ADM bucket to the book ===
PROMPT ano_mes|setor|total|n_slices
SELECT m || '|' || setor || '|' || TO_CHAR(tot,'FM999999990.00') || '|' || n
  FROM (
    SELECT TO_CHAR(cp.CPGDVECTO,'YYYY-MM') m,
           NVL(d.DESCSETOR,'(null)') setor,
           ROUND(SUM(d.DESNVALOR),2) tot,
           COUNT(*) n
      FROM FINANCE.CPDESDOBRAMENTO d
      JOIN FINANCE.CONTASPAGAR cp
        ON cp.EMPNCOD = d.EMPNCOD AND cp.CPGCNUMEROPAGAR = d.CPGCNUMEROPAGAR
     WHERE cp.CPGDVECTO >= DATE '2026-01-01' AND cp.CPGDVECTO < DATE '2026-07-01'
       AND ( UPPER(cp.CPGCHISTORICO) LIKE '%VR MENSAL%'
          OR UPPER(cp.CPGCHISTORICO) LIKE '%VT MENSAL%'
          OR UPPER(cp.CPGCHISTORICO) LIKE '%VALE REFEI%'
          OR UPPER(cp.CPGCHISTORICO) LIKE '%VALE TRANSP%' )
     GROUP BY TO_CHAR(cp.CPGDVECTO,'YYYY-MM'), NVL(d.DESCSETOR,'(null)')
  )
 ORDER BY m, setor;

PROMPT
PROMPT === BLOCK D: the 500.010.<SIGLA> per-person rows, all six months ===
PROMPT ano_mes|conta_dest|sigla|valor
SELECT TO_CHAR(l.LANDDATA,'YYYY-MM') || '|' ||
       l.PCTCNUMEROCONTADEST || '|' ||
       SUBSTR(l.PCTCNUMEROCONTADEST, 9) || '|' ||
       TO_CHAR(l.LANNVALOR,'FM999999990.00')
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '500.010.%'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-07-01'
   AND ( UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VALE REFEI%'
      OR UPPER(l.LANCHISTORICO) LIKE '%VALE TRANSP%' )
 ORDER BY TO_CHAR(l.LANDDATA,'YYYY-MM'), l.PCTCNUMEROCONTADEST;

PROMPT
PROMPT === done ===
EXIT
