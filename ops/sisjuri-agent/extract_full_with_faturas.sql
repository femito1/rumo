-- SISJURI closing extract -> single JSON document on stdout.
-- Oracle 19c JSON functions. Read-only. Parameterised by &ANO_MES / &D_START / &D_END.
-- Invoked by run-agent.ps1 which substitutes the DEFINE values below.
--
-- Output contract: one JSON object with keys: meta, revenue, faturas,
-- rateio_prof, despesas_conta, custo_area, recebimento_area, faturamento_area,
-- faturas_analitico, prolabore, distribuicao_socio, custo_equipe_prof.
--
-- NOTE: `faturas_analitico` column names on LDESK.FAT_FATURA
-- (VALOR_HONORARIO / VALOR_LIQUIDO / DATA_PAGAMENTO / ID_CLIENTE) and the
-- LDESK.CAD_CLIENTE join are UNVERIFIED against the live schema — run the probe
-- block in probe_faturas_analitico.sql before trusting this on the server.
-- `faturamento_area` (POSFIN_RESULTFAT split, mirrors recebimento_area) is safe.
SET DEFINE ON
SET HEADING OFF
SET FEEDBACK OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 100000000
SET LONGCHUNKSIZE 100000000
SET TRIMSPACE ON
SET TERMOUT ON
WHENEVER SQLERROR EXIT FAILURE

SELECT JSON_OBJECT(
  'meta' VALUE JSON_OBJECT(
     'ano_mes' VALUE '&ANO_MES',
     'd_start' VALUE '&D_START',
     'd_end'   VALUE '&D_END',
     'generated_at' VALUE TO_CHAR(SYSTIMESTAMP, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM')
  ),
  'revenue' VALUE (
     SELECT JSON_OBJECT(
        'recebimento_bruto' VALUE NVL((SELECT ROUND(SUM(VALOR1),2) FROM LDESK.GERENC_VW_POSFIN_RESULTREC WHERE ANO_MES='&ANO_MES'),0),
        'recebimento_rows'  VALUE (SELECT COUNT(*) FROM LDESK.GERENC_VW_POSFIN_RESULTREC WHERE ANO_MES='&ANO_MES'),
        'faturamento_bruto' VALUE NVL((SELECT ROUND(SUM(VALOR1),2) FROM LDESK.GERENC_VW_POSFIN_RESULTFAT WHERE ANO_MES='&ANO_MES'),0),
        'faturamento_rows'  VALUE (SELECT COUNT(*) FROM LDESK.GERENC_VW_POSFIN_RESULTFAT WHERE ANO_MES='&ANO_MES')
     ) FROM dual
  ),
  'faturas' VALUE JSON_OBJECT(
     'faturas_emitidas' VALUE (SELECT COUNT(*) FROM LDESK.FAT_FATURA WHERE DATA_EMISSAO >= DATE '&D_START' AND DATA_EMISSAO < DATE '&D_END')
  ),
  'rateio_prof' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'id_profissional' VALUE ID_PROFISSIONAL,
        'faturado'   VALUE faturado,
        'trabalhado' VALUE trabalhado
     ) RETURNING CLOB)
     FROM (SELECT ID_PROFISSIONAL,
                  ROUND(SUM(VALOR_FATURADO),2)  AS faturado,
                  ROUND(SUM(VALOR_TRABALHADO),2) AS trabalhado
             FROM LDESK.FAT_RATEIOFATURA_PROF
            WHERE ANO_MES='&ANO_MES'
            GROUP BY ID_PROFISSIONAL)
  ),
  'despesas_conta' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'id_conta'   VALUE id_conta,
        'nome_conta' VALUE nome_conta,
        'nome_conta_pai' VALUE nome_conta_pai,
        'tipo_conta' VALUE tipo_conta,
        'total'      VALUE total,
        'n'          VALUE n
     ) RETURNING CLOB)
     FROM (SELECT r.ID_CONTA id_conta, MAX(r.NOME_CONTA) nome_conta,
                  MAX(r.NOME_CONTA_PAI) nome_conta_pai, r.TIPO_CONTA tipo_conta,
                  ROUND(SUM(r.VALOR),2) total, COUNT(*) n
             FROM LDESK.GERENC_LANCAMENTORESUMO r
            WHERE r.ANO_MES='&ANO_MES'
            GROUP BY r.ID_CONTA, r.TIPO_CONTA)
  ),
  'custo_area' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'area'  VALUE area,
        'total' VALUE total,
        'n'     VALUE n
     ) RETURNING CLOB)
     FROM (SELECT g.NOME area, ROUND(SUM(r.VALOR),2) total, COUNT(*) n
             FROM LDESK.GERENC_LANCAMENTORESUMO r
             LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
            WHERE r.ANO_MES='&ANO_MES' AND r.ID_CONTA LIKE '030.%'
            GROUP BY g.NOME)
  ),
  -- Per-area RECEBIMENTO (cash received), the workbook's per-area base.
  -- Split the sacred receipt view by CASO -> área jurídica. Verified to the
  -- centavo vs the workbook (Jan/Fev 2026). The workbook then applies small
  -- manual cross-area transfers (Resumo_Recebidas) on top of this base.
  'recebimento_area' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'area'  VALUE area,
        'total' VALUE total,
        'n'     VALUE n
     ) RETURNING CLOB)
     FROM (SELECT NVL(a.NOME, '(sem area)') area,
                  ROUND(SUM(r.VALOR1),2) total, COUNT(*) n
             FROM LDESK.GERENC_VW_POSFIN_RESULTREC r
             LEFT JOIN LDESK.CAD_CASO c ON c.ID_CASO = r.ID_CASO
             LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA = c.ID_AREAJURIDICA
            WHERE r.ANO_MES = '&ANO_MES'
            GROUP BY a.NOME)
  ),
  -- Per-area FATURAMENTO (invoices issued), the 'FATURAS Analitico' rollup.
  -- Same CASO -> área jurídica split as recebimento_area, but on the faturamento
  -- view. This is the invoiced basis (not cash); the workbook's FATURAS
  -- Analitico tab is per-invoice at this grain (Sócio Responsável == área).
  'faturamento_area' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'area'  VALUE area,
        'total' VALUE total,
        'n'     VALUE n
     ) RETURNING CLOB)
     FROM (SELECT NVL(a.NOME, '(sem area)') area,
                  ROUND(SUM(r.VALOR1),2) total, COUNT(*) n
             FROM LDESK.GERENC_VW_POSFIN_RESULTFAT r
             LEFT JOIN LDESK.CAD_CASO c ON c.ID_CASO = r.ID_CASO
             LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA = c.ID_AREAJURIDICA
            WHERE r.ANO_MES = '&ANO_MES'
            GROUP BY a.NOME)
  ),
  -- Per-invoice FATURAS Analitico detail: número, cliente, caso, valores e área
  -- (Sócio Responsável). Payment/cancel date drives the workbook's month.
  'faturas_analitico' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'num_fatura'     VALUE num_fatura,
        'cliente'        VALUE cliente,
        'caso'           VALUE caso,
        'data_pagto'     VALUE data_pagto,
        'valor_original' VALUE valor_original,
        'valor_liquido'  VALUE valor_liquido,
        'area'           VALUE area
     ) RETURNING CLOB)
     FROM (SELECT f.NUMERO num_fatura,
                  cl.NOME cliente,
                  cs.NOME caso,
                  TO_CHAR(f.DATA_PAGAMENTO, 'YYYY-MM-DD') data_pagto,
                  ROUND(f.VALOR_HONORARIO,2) valor_original,
                  ROUND(f.VALOR_LIQUIDO,2)   valor_liquido,
                  NVL(a.NOME, '(sem area)')  area
             FROM LDESK.FAT_FATURA f
             LEFT JOIN LDESK.CAD_CASO cs ON cs.ID_CASO = f.ID_CASO
             LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA = cs.ID_AREAJURIDICA
             LEFT JOIN LDESK.CAD_CLIENTE cl ON cl.ID_CLIENTE = f.ID_CLIENTE
            WHERE f.DATA_PAGAMENTO >= DATE '&D_START' AND f.DATA_PAGAMENTO < DATE '&D_END')
  ),
  'prolabore' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'sigla'    VALUE sigla,
        'bruto'    VALUE bruto,
        'liquido'  VALUE liquido
     ) RETURNING CLOB)
     FROM (SELECT cp.COD_ADVG sigla,
                  ROUND(cp.CPGNVALORBASE,2) bruto,
                  ROUND(cp.CPGNVALORLIQUIDO,2) liquido
             FROM FINANCE.CONTASPAGAR cp
            WHERE cp.PCTCNUMEROCONTA='030.010.0130'
              AND cp.CPGDVECTO >= DATE '&D_START' AND cp.CPGDVECTO < DATE '&D_END')
  ),
  'distribuicao_socio' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'sigla'       VALUE sigla,
        'cost_center' VALUE cost_center,
        'valor'       VALUE valor
     ) RETURNING CLOB)
     FROM (SELECT l.COD_ADVG sigla, l.SIGLADEST cost_center, ROUND(SUM(l.LANNVALOR),2) valor
             FROM FINANCE.LANCAMENTO l
            WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
              AND l.LANDDATA >= DATE '&D_START' AND l.LANDDATA < DATE '&D_END'
            GROUP BY l.COD_ADVG, l.SIGLADEST)
  ),
  -- Per-lawyer x account detail for Custo equipe (030.*), for Base_Resultado.
  -- sigla + area (via professional -> grupo jurídico) so rows can be grouped
  -- by area. Distribuição Mensal Fixa (030.010.0010) has NULL professional and
  -- is carried at account level; the per-partner split is in distribuicao_socio.
  'custo_equipe_prof' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'sigla'      VALUE sigla,
        'area'       VALUE area,
        'id_conta'   VALUE id_conta,
        'nome_conta' VALUE nome_conta,
        'valor'      VALUE valor
     ) RETURNING CLOB)
     FROM (SELECT NVL(p.SIGLA, r.ID_PROFISSIONAL) sigla,
                  g.NOME area,
                  r.ID_CONTA id_conta,
                  MAX(r.NOME_CONTA) nome_conta,
                  ROUND(SUM(r.VALOR),2) valor
             FROM LDESK.GERENC_LANCAMENTORESUMO r
             LEFT JOIN LDESK.CAD_PROFISSIONAL p ON p.ID_PROFISSIONAL = r.ID_PROFISSIONAL
             LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = p.ID_GRUPOJURIDICO
            WHERE r.ANO_MES='&ANO_MES' AND r.ID_CONTA LIKE '030.%'
            GROUP BY NVL(p.SIGLA, r.ID_PROFISSIONAL), g.NOME, r.ID_CONTA)
  )
  RETURNING CLOB
) AS closing_json
FROM dual;

EXIT;
