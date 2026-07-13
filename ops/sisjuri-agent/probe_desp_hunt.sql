-- probe_desp_hunt.sql
-- Hunt the SISJURI source that reproduces the workbook row-198 despesas EXACTLY.
-- The workbook (Base_Resultado May) diverges from our GERENC/VW derivation by
-- specific families; per MEETING §H the system books these automatically, so the
-- data IS in the DB. Reverse-find it. Workbook May leaf targets to reproduce:
--   Ocupação: Aluguel 24230.60 (our DB 24359.77)
--   Consultoria: Contabilidade 8042.94 (our DB 8570.00)
--   Despesas Gerais: Limpeza e Copeira 3346.68, Manut ar-cond 919.76, Manut Jardim
--     994.65, Material Higiene e Copa 887.36  (our DB: Terceirização 3984.15,
--     Manut Escritório 1966.76, Material Copa 3053.89)
--   Salários Adm: + Vale Refeição-ADM 2719.90 + Vale Transporte 607.04
--   Informática: + Suporte Totvs 2917.77
SET DEFINE OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000
SET TRIMOUT ON
SET FEEDBACK OFF
SET HEADING OFF
WHENEVER SQLERROR CONTINUE

PROMPT #A TOTVS/Suporte anywhere in LANCAMENTO historico, May, per conta
SELECT 'A|'||NVL(l.PCTCNUMEROCONTADEST,'?')||'|'||SUBSTR(REPLACE(NVL(MAX(l.LANCHISTORICO),' '),'|','/'),1,40)||'|'||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))||'|n='||COUNT(*)
  FROM FINANCE.LANCAMENTO l
 WHERE (UPPER(l.LANCHISTORICO) LIKE '%TOTVS%' OR UPPER(l.LANCHISTORICO) LIKE '%SUPORTE%')
   AND l.LANDDATA >= DATE '2026-05-01' AND l.LANDDATA < DATE '2026-06-01'
 GROUP BY l.PCTCNUMEROCONTADEST
 ORDER BY 1;

PROMPT #B Vale-ADM on transitoria 200.010.0010 by historico VR/VT/Vale, May
SELECT 'B|'||NVL(l.SIGLADEST,'?')||'|'||SUBSTR(REPLACE(NVL(l.LANCHISTORICO,' '),'|','/'),1,50)||'|'||TO_CHAR(ROUND(l.LANNVALOR,2))
  FROM FINANCE.LANCAMENTO l
 WHERE l.PCTCNUMEROCONTADEST='200.010.0010'
   AND (UPPER(l.LANCHISTORICO) LIKE '%VR %' OR UPPER(l.LANCHISTORICO) LIKE '%VT %'
        OR UPPER(l.LANCHISTORICO) LIKE '%VALE%' OR UPPER(l.LANCHISTORICO) LIKE '%REFEI%'
        OR UPPER(l.LANCHISTORICO) LIKE '%TRANSP%')
   AND l.LANDDATA >= DATE '2026-05-01' AND l.LANDDATA < DATE '2026-06-01'
 ORDER BY 1;

PROMPT #C Reverse-find workbook leaf values (May) across LANCAMENTO by conta
SELECT 'C|'||NVL(l.PCTCNUMEROCONTADEST,'?')||'|'||TO_CHAR(ROUND(SUM(l.LANNVALOR),2))||'|hist='||SUBSTR(REPLACE(NVL(MAX(l.LANCHISTORICO),' '),'|','/'),1,30)
  FROM FINANCE.LANCAMENTO l
 WHERE l.LANDDATA >= DATE '2026-05-01' AND l.LANDDATA < DATE '2026-06-01'
   AND ROUND(l.LANNVALOR,2) IN (24230.60,8042.94,3346.68,919.76,994.65,887.36,2719.90,607.04,2917.77)
 GROUP BY l.PCTCNUMEROCONTADEST
 ORDER BY 1;

PROMPT #D VW_RESULTADO_MENSAL (non-DET) May level<=3 despesa/invest families vs workbook
SELECT 'D|'||NVL(TIPO,'?')||'|'||NVL(CONTA2,'?')||'|'||NVL(TITULO2,'?')||'|'||NVL(CONTA3,'?')||'|'||NVL(TITULO3,'?')||'|'||TO_CHAR(ROUND(SUM(VALOR),2))
  FROM FINANCE.VW_RESULTADO_MENSAL
 WHERE ANO_MES='2026-05' AND TIPO IN ('S','I','D')
 GROUP BY TIPO, CONTA2, TITULO2, CONTA3, TITULO3
 ORDER BY TIPO, CONTA2, CONTA3;

PROMPT #E Suporte Totvs / any conta whose NAME mentions Totvs or Suporte, May (resumo)
SELECT 'E|'||r.ID_CONTA||'|'||MAX(r.NOME_CONTA)||'|'||TO_CHAR(ROUND(SUM(r.VALOR),2))
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES='2026-05'
   AND (UPPER(r.NOME_CONTA) LIKE '%TOTVS%' OR UPPER(r.NOME_CONTA) LIKE '%SUPORTE%')
 GROUP BY r.ID_CONTA
 ORDER BY 1;

PROMPT #END
EXIT
