-- SISJURI closing extract -> single JSON document on stdout.
-- Oracle 19c JSON functions. Read-only. Parameterised by &ANO_MES / &D_START / &D_END.
-- Invoked by run-agent.ps1 which substitutes the DEFINE values below.
--
-- Output contract: one JSON object with keys: meta, revenue, faturas,
-- rateio_prof, despesas_conta, custo_area, prolabore, distribuicao_socio,
-- custo_equipe_prof.
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
