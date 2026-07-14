-- probe_socio_split_validate.sql  (POINT 17 — validate the exact SQL before folding into extract.sql)
-- Confirms, against the LIVE DB for Jan..May 2026, the two provable DL splits:
--   1) Bônus equipe = Σ 150.* — but the current extract reads GERENC_LANCAMENTORESUMO
--      (returns NULL for Feb!). The 150.* bonus actually lives in FINANCE.LANCAMENTO.
--      This probe proves G (gerencial) is empty and L (FINANCE) = 94.696,15 for Feb.
--   2) DL excedente per sigla in 030.010.0010, split by CAD_PROFISSIONAL.SOCIO and by
--      the MV-specific workbook line. Must tie: Jan sócios (AM+DC+RB)=164.477,34;
--      Mar MV=6.627. Feb = none.
-- Sigla is parsed from the histórico as the 2nd whitespace token ("Bônus FSM ..." -> FSM;
-- "DL excedente AM - Reserva ..." -> the token after "excedente"). Read-only.
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #G current approach: Sigma GERENC_LANCAMENTORESUMO 150.% by month (expect NULL/empty -> the bug)
SELECT 'G|'||r.ANO_MES||'|'||TO_CHAR(NVL(ROUND(SUM(r.VALOR),2),0))
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES IN ('2026-01','2026-02','2026-03','2026-04','2026-05')
   AND r.ID_CONTA LIKE '150.%'
 GROUP BY r.ANO_MES ORDER BY r.ANO_MES;

PROMPT #L new approach: Sigma FINANCE.LANCAMENTO 150.% by month (expect Feb 94.696,15)
SELECT 'L|'||TO_CHAR(l.LANDDATA,'YYYY-MM')||'|'||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '150.%'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM') ORDER BY 1;

PROMPT #LE new approach WITH socio-exclusion: Sigma FINANCE.LANCAMENTO 150.% where 2nd-token sigla is NOT a socio
SELECT 'LE|'||TO_CHAR(l.LANDDATA,'YYYY-MM')||'|'||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST LIKE '150.%'
   AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
   AND NOT EXISTS (
     SELECT 1 FROM LDESK.CAD_PROFISSIONAL p
      WHERE p.SIGLA = UPPER(TRIM(REGEXP_SUBSTR(l.LANCHISTORICO, '\S+\s+(\S+)', 1, 1, NULL, 1)))
        AND p.SOCIO = 'S' )
 GROUP BY TO_CHAR(l.LANDDATA,'YYYY-MM') ORDER BY 1;

PROMPT #LSIG 150.% lines per parsed 2nd-token sigla + that sigla SOCIO flag (sanity: all employees, socio=N or unknown)
SELECT 'LSIG|'||mes||'|'||sig||'|'||NVL(MAX(socio),'?')||'|'||TO_CHAR(ROUND(SUM(valor),2))
  FROM (
    SELECT TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
           UPPER(TRIM(REGEXP_SUBSTR(l.LANCHISTORICO, '\S+\s+(\S+)', 1, 1, NULL, 1))) sig,
           l.LANNVALOR valor
      FROM FINANCE.LANCAMENTO l
     WHERE l.PCTCNUMEROCONTADEST LIKE '150.%'
       AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
  ) x
  LEFT JOIN LDESK.CAD_PROFISSIONAL p ON p.SIGLA = x.sig
 GROUP BY mes, sig ORDER BY mes, sig;

PROMPT #X 030.010.0010 EXCEDENTE lines per parsed sigla (token after 'excedente') + SOCIO flag, by month
SELECT 'X|'||mes||'|'||sig||'|'||NVL(socio,'?')||'|'||TO_CHAR(ROUND(SUM(valor),2))||'|'||SUBSTR(MAX(hist),1,45)
  FROM (
    SELECT TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
           UPPER(TRIM(REGEXP_SUBSTR(l.LANCHISTORICO, 'excedente\s+(\S+)', 1, 1, 'i', 1))) sig,
           l.LANNVALOR valor,
           l.LANCHISTORICO hist
      FROM FINANCE.LANCAMENTO l
     WHERE l.PCTCNUMEROCONTADEST = '030.010.0010'
       AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
       AND UPPER(l.LANCHISTORICO) LIKE '%EXCEDENTE%'
  ) x
  LEFT JOIN LDESK.CAD_PROFISSIONAL p ON p.SIGLA = x.sig
 GROUP BY mes, sig, p.SOCIO ORDER BY mes, sig;

PROMPT #XS dl_excedente_socios = Sigma excedente where sigla != MV, by month (expect Jan 164.477,34)
SELECT 'XS|'||mes||'|'||TO_CHAR(ROUND(SUM(valor),2))
  FROM (
    SELECT TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
           UPPER(TRIM(REGEXP_SUBSTR(l.LANCHISTORICO, 'excedente\s+(\S+)', 1, 1, 'i', 1))) sig,
           l.LANNVALOR valor
      FROM FINANCE.LANCAMENTO l
     WHERE l.PCTCNUMEROCONTADEST = '030.010.0010'
       AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
       AND UPPER(l.LANCHISTORICO) LIKE '%EXCEDENTE%'
  ) WHERE sig <> 'MV' GROUP BY mes ORDER BY mes;

PROMPT #XM dl_excedente_mv = Sigma excedente where sigla = MV, by month (expect Mar 6.627)
SELECT 'XM|'||mes||'|'||TO_CHAR(ROUND(SUM(valor),2))
  FROM (
    SELECT TO_CHAR(l.LANDDATA,'YYYY-MM') mes,
           UPPER(TRIM(REGEXP_SUBSTR(l.LANCHISTORICO, 'excedente\s+(\S+)', 1, 1, 'i', 1))) sig,
           l.LANNVALOR valor
      FROM FINANCE.LANCAMENTO l
     WHERE l.PCTCNUMEROCONTADEST = '030.010.0010'
       AND l.LANDDATA >= DATE '2026-01-01' AND l.LANDDATA < DATE '2026-06-01'
       AND UPPER(l.LANCHISTORICO) LIKE '%EXCEDENTE%'
  ) WHERE sig = 'MV' GROUP BY mes ORDER BY mes;

PROMPT #END
EXIT
