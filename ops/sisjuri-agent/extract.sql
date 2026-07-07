-- SISJURI closing extract -> single JSON document on stdout.
-- Oracle 19c JSON functions. Read-only. Parameterised by &ANO_MES / &D_START / &D_END.
-- Invoked by run-agent.ps1 which substitutes the DEFINE values below.
--
-- Output contract: one JSON object with keys: meta, revenue, faturas,
-- rateio_prof, despesas_conta, custo_area, recebimento_area, faturamento_area,
-- faturas_analitico, prolabore, distribuicao_socio, custo_equipe_prof.
--
-- faturas_analitico is per-CASE faturamento detail built on the (verified)
-- POSFIN_RESULTFAT view joined to CAD_CASO / CAD_AREAJURIDICA. FAT_FATURA was
-- the wrong source (invoice headers: no payment date, no liquido, no ID_CASO);
-- POSFIN_RESULTFAT is the received/faturamento basis with ID_CASO + VALOR1.
-- All columns used here are confirmed present (probe 2026-07-03).
SET DEFINE ON
SET HEADING OFF
SET FEEDBACK OFF
SET PAGESIZE 0
SET LINESIZE 200
SET LONG 100000000
SET LONGCHUNKSIZE 100000000
SET TRIMSPACE ON
SET TERMOUT ON
SET SERVEROUTPUT ON SIZE UNLIMITED
WHENEVER SQLERROR EXIT FAILURE

-- The JSON document routinely exceeds sqlplus's 32767 LINESIZE ceiling. Printing
-- it as a single CLOB column makes sqlplus truncate/wrap the line and corrupt the
-- JSON (observed on large months). Instead we build the CLOB, then emit it in
-- small fixed-size chunks via DBMS_OUTPUT so no physical line exceeds LINESIZE.
-- run-agent.ps1 strips the physical CR/LF to reassemble the document at any size.
DECLARE
  doc   CLOB;
  len   PLS_INTEGER;
  pos   PLS_INTEGER := 1;
  chunk PLS_INTEGER := 180;
BEGIN
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
  -- Per-CASE faturamento detail (the 'FATURAS Analitico' grain). POSFIN_RESULTFAT
  -- is per financial-position row (VALOR1) tagged by ID_CASO; join to CAD_CASO for
  -- código/assunto/área. Client name lives behind CAD_CLIENTE->CAD_PESSOA (unverified
  -- 2-hop) so it is intentionally omitted; the workbook shows the case name anyway.
  'faturas_analitico' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'id_caso'    VALUE id_caso,
        'codigo'     VALUE codigo,
        'caso'       VALUE caso,
        'area'       VALUE area,
        'total'      VALUE total,
        'n'          VALUE n
     ) RETURNING CLOB)
     FROM (SELECT r.ID_CASO id_caso,
                  MAX(c.CODIGO) codigo,
                  MAX(c.ASSUNTO) caso,
                  NVL(MAX(a.NOME), '(sem area)') area,
                  ROUND(SUM(r.VALOR1),2) total, COUNT(*) n
             FROM LDESK.GERENC_VW_POSFIN_RESULTFAT r
             LEFT JOIN LDESK.CAD_CASO c ON c.ID_CASO = r.ID_CASO
             LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA = c.ID_AREAJURIDICA
            WHERE r.ANO_MES = '&ANO_MES'
            GROUP BY r.ID_CASO)
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
  -- Per-lawyer team-cost COMPONENTS for the SISJURI-derived per-area Custo
  -- equipe (docs/SISJURI_QUERIES.md §11). One row per (sigla, id_conta, valor):
  --  * 030.010.0010 Distribuição: CONTASPAGAR gross base, EXCLUDING "Bônus"
  --    histórico (Fixa + Diferença), keyed by COD_ADVG.
  --  * 030.010.0130 Pró-Labore, 030.010.0140 Bolsa: CONTASPAGAR gross base by
  --    COD_ADVG.
  --  * 030.010.0110 Convênio: LANCAMENTO net by LANCPROFDEST (CONTASPAGAR does
  --    not carry it). INSS 030.010.0050 is intentionally omitted (excluded from
  --    per-lawyer Custo equipe). The app folds these to areas via home grupo +
  --    CAD_RATEIO_GRUPO %s (rateio_grupo / home_area below).
  'custo_equipe_deriv' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'sigla'    VALUE sigla,
        'id_conta' VALUE id_conta,
        'valor'    VALUE valor
     ) RETURNING CLOB)
     FROM (
        -- Gross components from CONTASPAGAR (distribuição ex-bônus, pró-labore, bolsa)
        SELECT cp.COD_ADVG sigla, cp.PCTCNUMEROCONTA id_conta,
               ROUND(SUM(cp.CPGNVALORBASE),2) valor
          FROM FINANCE.CONTASPAGAR cp
         WHERE cp.PCTCNUMEROCONTA IN ('030.010.0010','030.010.0130','030.010.0140')
           AND cp.CPGDVECTO >= DATE '&D_START' AND cp.CPGDVECTO < DATE '&D_END'
           -- Exclude non-recurring profit movements booked in 0010: annual Bônus
           -- and the January "DL excedente ... Reserva" excess-distribution
           -- reserves. Keep only Fixa + monthly Diferença (docs §11).
           AND UPPER(cp.CPGCHISTORICO) NOT LIKE '%B_NUS%'
           AND UPPER(cp.CPGCHISTORICO) NOT LIKE '%BONUS%'
           AND UPPER(cp.CPGCHISTORICO) NOT LIKE '%EXCEDENTE%'
           AND UPPER(cp.CPGCHISTORICO) NOT LIKE '%RESERVA%'
         GROUP BY cp.COD_ADVG, cp.PCTCNUMEROCONTA
        UNION ALL
        -- Net convênio (0110) from LANCAMENTO, keyed by destination professional.
        -- CONTASPAGAR does not carry convênio, so it comes from the cash ledger.
        SELECT l.LANCPROFDEST sigla, l.PCTCNUMEROCONTADEST id_conta,
               ROUND(SUM(l.LANNVALOR),2) valor
          FROM FINANCE.LANCAMENTO l
         WHERE l.PCTCNUMEROCONTADEST = '030.010.0110'
           AND l.LANDDATA >= DATE '&D_START' AND l.LANDDATA < DATE '&D_END'
           AND l.LANCPROFDEST IS NOT NULL
         GROUP BY l.LANCPROFDEST, l.PCTCNUMEROCONTADEST
     )
  ),
  -- CAD_RATEIO_GRUPO: per-professional area percentages (active window only).
  -- Multi-area lawyers (e.g. Aurelio 50/50) get their split here; the app uses
  -- home_area (100%) for everyone else.
  'rateio_grupo' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'sigla'      VALUE sigla,
        'grupo'      VALUE grupo,
        'percentual' VALUE percentual
     ) RETURNING CLOB)
     FROM (SELECT p.SIGLA sigla, g.NOME grupo, rg.PERCENTUAL percentual
             FROM LDESK.CAD_RATEIO_GRUPO rg
             JOIN LDESK.CAD_PROFISSIONAL p ON p.ID_PROFISSIONAL = rg.ID_PROFISSIONAL
             LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = rg.ID_GRUPOJURIDICO
            WHERE rg.ANO_MES_INICIAL <= '&ANO_MES'
              AND rg.ANO_MES_FINAL   >= '&ANO_MES'
              AND rg.PERCENTUAL > 0)
  ),
  -- Home area per professional (sigla -> grupo jurídico name). Fallback area for
  -- any lawyer without a CAD_RATEIO_GRUPO entry.
  'home_area' VALUE (
     SELECT JSON_OBJECTAGG(sigla VALUE grupo RETURNING CLOB)
     FROM (SELECT p.SIGLA sigla, MAX(g.NOME) grupo
             FROM LDESK.CAD_PROFISSIONAL p
             LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO = p.ID_GRUPOJURIDICO
            WHERE p.SIGLA IS NOT NULL
            GROUP BY p.SIGLA)
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
) INTO doc FROM dual;

  len := DBMS_LOB.GETLENGTH(doc);
  WHILE pos <= len LOOP
    DBMS_OUTPUT.PUT_LINE(DBMS_LOB.SUBSTR(doc, chunk, pos));
    pos := pos + chunk;
  END LOOP;
END;
/

EXIT;
