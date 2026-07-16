-- SISJURI closing extract -> single JSON document on stdout.
-- Oracle 19c JSON functions. Read-only. Parameterised by &ANO_MES / &D_START / &D_END.
-- Invoked by run-agent.ps1 which substitutes the DEFINE values below.
--
-- Output contract: one JSON object with keys (KEEP THIS LIST IN SYNC WITH THE
-- JSON_OBJECT BELOW — the previous header omitted the derived blocks):
--   meta, revenue, faturas, rateio_prof, despesas_conta, despesas_liquido,
--   despesas_desdobramento, custo_area,
--   despesas_equipe_area, recebimento_area, recebimento_area_prof, faturamento_area, faturas_analitico, prolabore,
--   distribuicao_socio, custo_equipe_deriv, convenio_memo, custo_equipe_area,
--   comissao_deriv, rateio_grupo, home_area, custo_equipe_prof, bonus_equipe,
--   bonus_equipe_030, convenio_extra_dl, faturas_moeda,
--   dl_excedente_socios, dl_excedente_mv.
-- The derived blocks feed the DRE assembler (app/closing/dre.py), NOT
-- sisjuri_db.py: custo_equipe_deriv + rateio_grupo + home_area (+ custo_equipe_area)
-- reconstruct per-area Custo equipe; comissao_deriv the per-area Comissão.
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
  -- Institutional despesas at LÍQUIDO (net of retained 3rd-party tax) — the basis
  -- the workbook uses (2026-07-13 client confirm + probe). GERENC gives GROSS;
  -- CONTASPAGAR.CPGNVALORLIQUIDO gives the net paid to service providers. Direct
  -- 020.*/040.* payments here; the desdobramento (card/transitória lumps) is in the
  -- ``despesas_desdobramento`` block below. Reconciled to the workbook to R$129,17
  -- (May, the residual is the client's own aluguel pending). Keyed by conta so the
  -- assembler folds via section_for the same way as despesas_conta.
  'despesas_liquido' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'id_conta' VALUE id_conta,
        'liquido'  VALUE liquido,
        'bruto'    VALUE bruto,
        'n'        VALUE n
     ) RETURNING CLOB)
     FROM (SELECT cp.PCTCNUMEROCONTA id_conta,
                  ROUND(SUM(cp.CPGNVALORLIQUIDO),2) liquido,
                  ROUND(SUM(cp.CPGNVALORBRUTO),2) bruto, COUNT(*) n
             FROM FINANCE.CONTASPAGAR cp
            WHERE cp.CPGDVECTO >= DATE '&D_START' AND cp.CPGDVECTO < DATE '&D_END'
              AND (cp.PCTCNUMEROCONTA LIKE '020.%' OR cp.PCTCNUMEROCONTA LIKE '040.%'
                   OR cp.PCTCNUMEROCONTA='030.010.0180')
            GROUP BY cp.PCTCNUMEROCONTA)
  ),
  -- Desdobramento of lump payments (cartão de crédito, transitória de pagamentos)
  -- into their real destination expense accounts. FINANCE.CPDESDOBRAMENTO holds one
  -- row per unfolded slice (DESCCONTADESTINO, DESNVALOR, DESCHISTORICO). We keep the
  -- histórico so the assembler can apply the few known reclassifications (e.g. a
  -- "Claude"/software line booked to Material de Copa must move to Informática).
  'despesas_desdobramento' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'id_conta'  VALUE id_conta,
        'valor'     VALUE valor,
        'historico' VALUE historico
     ) RETURNING CLOB)
     FROM (SELECT d.DESCCONTADESTINO id_conta, ROUND(d.DESNVALOR,2) valor,
                  SUBSTR(d.DESCHISTORICO,1,80) historico
             FROM FINANCE.CPDESDOBRAMENTO d
             JOIN FINANCE.CONTASPAGAR cp
               ON cp.EMPNCOD=d.EMPNCOD AND cp.CPGCNUMEROPAGAR=d.CPGCNUMEROPAGAR
            WHERE cp.CPGDVECTO >= DATE '&D_START' AND cp.CPGDVECTO < DATE '&D_END'
              AND (d.DESCCONTADESTINO LIKE '020.%' OR d.DESCCONTADESTINO LIKE '040.%'))
  ),
  -- Per-area "Despesas Área" (workbook Despesas Equipe per area) — the Grupo='S'
  -- auto-rateio families {Associações 020.060.*, Viagens/Prospecção 020.090.*, Cursos
  -- 030.010.0180, Assinaturas, Eventos/HH, Material Gráfico}, attributed to área by the
  -- line's cost-center: direct CONTASPAGAR line -> SIGLA, unfolded slice -> DESCSETOR
  -- (ECT=Contencioso, EDE=Econômico, ESP=Arbitragem; anything else = institutional, kept
  -- out of the area buckets). Proven vs May (2026-07-14 probe_despesas_area_key): AASP
  -- 217,40 + IBRAC 700,09 = ECT 917,49; IBRAC 700,10 = EDE; Patrocínio 1.204,47 = ESP;
  -- Cursos ASG 1.600 = EDE; passagens 1.358,72 = EDE (the DB is self-consistent — the
  -- workbook's Contencioso cell mis-references that EDE row, a spreadsheet quirk; DB wins
  -- per the "SISJURI is authoritative" rule). These amounts already live inside the
  -- institutional despesas total; this block only tags their ÁREA so the per-area tabs
  -- can show Despesas Equipe and the Despesa Institucional rateio carves them out first.
  -- direct lines (no desdobramento) tagged by SIGLA + slices tagged by DESCSETOR.
  'despesas_equipe_area' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'cc'    VALUE cc,
        'total' VALUE total,
        'n'     VALUE n
     ) RETURNING CLOB)
     FROM (
        SELECT cc, ROUND(SUM(v),2) total, COUNT(*) n FROM (
           -- direct 020.060/090.* + Cursos 030.010.0180 lines that are NOT desdobradas
           SELECT NVL(cp.SIGLA,'?') cc, cp.CPGNVALORLIQUIDO v
             FROM FINANCE.CONTASPAGAR cp
            WHERE cp.CPGDVECTO >= DATE '&D_START' AND cp.CPGDVECTO < DATE '&D_END'
              AND (cp.PCTCNUMEROCONTA LIKE '020.060.%' OR cp.PCTCNUMEROCONTA LIKE '020.090.%'
                   OR cp.PCTCNUMEROCONTA = '030.010.0180')
              AND NOT EXISTS (SELECT 1 FROM FINANCE.CPDESDOBRAMENTO d2
                               WHERE d2.EMPNCOD=cp.EMPNCOD AND d2.CPGCNUMEROPAGAR=cp.CPGCNUMEROPAGAR)
           UNION ALL
           -- unfolded slices destined for the same family accounts, tagged by DESCSETOR
           SELECT NVL(d.DESCSETOR,'?') cc, d.DESNVALOR v
             FROM FINANCE.CPDESDOBRAMENTO d
             JOIN FINANCE.CONTASPAGAR cp
               ON cp.EMPNCOD=d.EMPNCOD AND cp.CPGCNUMEROPAGAR=d.CPGCNUMEROPAGAR
            WHERE cp.CPGDVECTO >= DATE '&D_START' AND cp.CPGDVECTO < DATE '&D_END'
              AND (d.DESCCONTADESTINO LIKE '020.060.%' OR d.DESCCONTADESTINO LIKE '020.090.%'
                   OR d.DESCCONTADESTINO = '030.010.0180')
        )
        WHERE cc IN ('ECT','EDE','ESP')
        GROUP BY cc)
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
  -- Per-area RECEBIMENTO on the DEMONSTRATIVO (per-profissional) basis — the
  -- workbook's ACTUAL per-area Recebimento (2026-07-14 probe_recebimento_area_prof).
  -- ⚠ This, NOT recebimento_area (cash-by-case), is what the workbook shows. It is
  -- the same sacred cash re-attributed to each lawyer by participation %, rolled to
  -- the lawyer's home grupo (NOMEGRUPO). Proven vs the authoritative May book to R$1:
  -- Equipe Contencioso 240.444,72 / Equipe Direito Econômico 166.875,57 / Arbitragem
  -- 41.997,50 + Equipe Ambiental −138,15 = 41.859,35. Grand total over ALL grupos
  -- (incl. "Não Alocados"/"Administração", which the area tabs EXCLUDE) = 415.927,84
  -- = sacred cash. Source: LDESK.DB_RESULTADO_PROF.RECEITA_REC by NOMEGRUPO.
  'recebimento_area_prof' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'grupo' VALUE grupo,
        'total' VALUE total,
        'fat'   VALUE fat
     ) RETURNING CLOB)
     FROM (SELECT NVL(NOMEGRUPO,'(sem grupo)') grupo,
                  ROUND(SUM(RECEITA_REC),2) total,
                  ROUND(SUM(RECEITA_FAT),2) fat
             FROM LDESK.DB_RESULTADO_PROF
            WHERE ANO_MES = '&ANO_MES'
            GROUP BY NOMEGRUPO)
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
  -- Per-invoice faturamento lists (workbook tabs 'Nacional' = BRL, 'Moedas' =
  -- EUR/USD). Source CONFIRMED + VALIDATED to the centavo (2026-07-14):
  -- LDESK.DB_VW_FATURASEMI_REC bounded by DATA (emission) within the month sums to
  -- honorarios_nac = 719.988,05 = the sacred faturamento_bruto('2026-05') EXACTLY,
  -- splitting R$ 708.659,18 (72) + US$ 11.328,87 (3). The view is per-invoice-LINE
  -- (n=75 rows for ~53 invoices — e.g. invoice 4143 has 6 lines of 678 = 4.068),
  -- so we GROUP BY NUMERO to the per-invoice grain the workbook uses. The sacred
  -- cross-check (an INDEPENDENT view also = 719.988,05) proves the lines are real,
  -- not a join fan-out, so summing is correct. Column map to the workbook:
  --   NUMERO->Fatura# · CLIENTE(id)->Cliente · CASO->Histórico · DATA->Emissão ·
  --   DATA_VENCIMENTO->Vencimento · DATA_RECEBIMENTO->Recebimento ·
  --   SIGLA_MOEDA->Moeda · VALOR_HONORARIOS(+_NAC)->Honorários (moeda + BRL) ·
  --   VALOR_DESPESAS(+_NAC)->Despesas · CR_HON(+_NAC)->Valor Recebido.
  -- Backend splits Nacional (moeda_nac) vs Moedas (foreign SIGLA_MOEDA).
  'faturas_moeda' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'numero'          VALUE numero,
        'cliente'         VALUE cliente,
        'caso'            VALUE caso,
        'data_emissao'    VALUE data_emissao,
        'vencimento'      VALUE vencimento,
        'recebimento'     VALUE recebimento,
        'moeda'           VALUE moeda,
        'moeda_nac'       VALUE moeda_nac,
        'honorarios'      VALUE honorarios,
        'honorarios_nac'  VALUE honorarios_nac,
        'despesas'        VALUE despesas,
        'despesas_nac'    VALUE despesas_nac,
        'recebido_hon'    VALUE recebido_hon,
        'recebido_hon_nac' VALUE recebido_hon_nac
     ) RETURNING CLOB)
     FROM (SELECT v.NUMERO numero,
                  MAX(v.CLIENTE) cliente,
                  MAX(v.CASO) caso,
                  TO_CHAR(MAX(v.DATA),'YYYY-MM-DD') data_emissao,
                  TO_CHAR(MAX(v.DATA_VENCIMENTO),'YYYY-MM-DD') vencimento,
                  TO_CHAR(MAX(v.DATA_RECEBIMENTO),'YYYY-MM-DD') recebimento,
                  MAX(v.SIGLA_MOEDA) moeda,
                  MAX(v.SIGLA_MOEDA_NACIONAL) moeda_nac,
                  ROUND(SUM(v.VALOR_HONORARIOS),2) honorarios,
                  ROUND(SUM(v.VALOR_HONORARIOS_NAC),2) honorarios_nac,
                  ROUND(SUM(v.VALOR_DESPESAS),2) despesas,
                  ROUND(SUM(v.VALOR_DESPESAS_NAC),2) despesas_nac,
                  ROUND(SUM(v.CR_HON),2) recebido_hon,
                  ROUND(SUM(v.CR_HON_NAC),2) recebido_hon_nac
             FROM LDESK.DB_VW_FATURASEMI_REC v
            WHERE v.DATA >= DATE '&D_START' AND v.DATA < DATE '&D_END'
            GROUP BY v.NUMERO)
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
  -- Per-lawyer convênio memo: some lawyers (EHF, RB today) have a "parte MBC"
  -- hand-net that the finance team documents in the LANCHISTORICO of the
  -- 030.010.0110 row, e.g.: "3.520,31 - 1.956,21 (Parte MBC) = R$ 1.564,10".
  -- The parsed final number IS the ledger figure to book instead of LANCAMENTO
  -- 0110. Emit sigla + parsed value so the backend applies a set_account
  -- override automatically. Falls back gracefully when the memo is absent or
  -- stale (parse fails -> no override, LANCAMENTO value stands).
  'convenio_memo' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'sigla'        VALUE sigla,
        'parsed_valor' VALUE parsed_valor,
        'raw_memo'     VALUE raw_memo
     ) RETURNING CLOB)
     FROM (
        SELECT l.LANCPROFDEST sigla,
               -- Capture the amount after "=" (with optional "R$"), Brazilian
               -- notation (thousand-sep '.', decimal ','). Return NUMBER.
               TO_NUMBER(
                 REPLACE(REPLACE(
                   REGEXP_SUBSTR(l.LANCHISTORICO,
                     '\(\s*[Pp]arte\s*MBC\s*\)\s*=\s*R?\$?\s*([0-9.]+,[0-9]{2})',
                     1, 1, NULL, 1),
                   '.', ''),
                   ',', '.'
                 )
               ) parsed_valor,
               SUBSTR(l.LANCHISTORICO, 1, 300) raw_memo
          FROM FINANCE.LANCAMENTO l
         WHERE l.PCTCNUMEROCONTADEST='030.010.0110'
           AND l.LANDDATA >= DATE '&D_START' AND l.LANDDATA < DATE '&D_END'
           AND l.LANCPROFDEST IS NOT NULL
           AND UPPER(l.LANCHISTORICO) LIKE '%PARTE MBC%'
     )
     WHERE parsed_valor IS NOT NULL
  ),
  -- Area-level Custo-equipe lines that the ledger books at the AREA level
  -- (a lawyer's Vale Refeição/Transporte becomes an area cost). These live in
  -- the personal-debit namespace ``500.010.<SIGLA>`` with histórico
  -- ``Vale refeição``/``Vale transporte`` — NOT in 030.010.0100/0220 (unused).
  -- Restrict to lawyers who ALSO have a distribuição/pró-labore movement in the
  -- same month (i.e. active this month) so legacy movements from ex-lawyers
  -- like MLA don't leak in. We emit per-``sigla`` net; the app folds by home
  -- area/rateio. Feb 2026 verified: JVO 1.249,40 → Contencioso ledger.
  'custo_equipe_area' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'sigla'    VALUE sigla,
        'id_conta' VALUE id_conta,
        'valor'    VALUE valor
     ) RETURNING CLOB)
     FROM (SELECT SUBSTR(l.PCTCNUMEROCONTADEST, 9) sigla,
                  '030.010.0100/0220' id_conta,
                  ROUND(SUM(l.LANNVALOR),2) valor
             FROM FINANCE.LANCAMENTO l
            WHERE l.PCTCNUMEROCONTADEST LIKE '500.010.%'
              AND UPPER(l.LANCHISTORICO) LIKE '%VALE%'
              AND l.LANDDATA >= DATE '&D_START' AND l.LANDDATA < DATE '&D_END'
              AND SUBSTR(l.PCTCNUMEROCONTADEST, 9) IN (
                  SELECT DISTINCT cp2.COD_ADVG
                    FROM FINANCE.CONTASPAGAR cp2
                   WHERE cp2.PCTCNUMEROCONTA LIKE '030.010.%'
                     AND cp2.CPGDVECTO >= DATE '&D_START' AND cp2.CPGDVECTO < DATE '&D_END'
                     AND cp2.COD_ADVG IS NOT NULL
              )
            GROUP BY SUBSTR(l.PCTCNUMEROCONTADEST, 9))
  ),
  -- Comissao (Participacao + Repasse) per area. Two DB sources, both verified to
  -- the workbook to the centavo (docs/SISJURI_QUERIES.md 12a):
  --  * 020.110.0010 "Participacao Externa (comissoes)": area-tagged via
  --    ID_GRUPOJURIDICO (emit kind='area', area=grupo name).
  --  * 030.010.0120 "Participacao Interna (comissoes)": per-lawyer via
  --    CONTASPAGAR.COD_ADVG (emit kind='lawyer', sigla), folded to home area +
  --    rateio by the backend the same way Custo equipe is. 030.010.0080 is empty.
  --    NB (2026-07-13 probe): the LANCAMENTO row for 0120 carries LANCPROFDEST
  --    NULL (sigla lives only in the histórico "Comissão EHF"), so the old
  --    LANCPROFDEST arm dropped it and comissao_deriv came back null. CONTASPAGAR
  --    carries COD_ADVG=EHF with the same 2.128,06, exactly as for custo equipe.
  'comissao_deriv' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'kind'  VALUE kind,
        'sigla' VALUE sigla,
        'area'  VALUE area,
        'valor' VALUE valor
     ) RETURNING CLOB)
     FROM (
        -- Participacao Externa: area-level, keyed by ID_GRUPOJURIDICO.
        SELECT 'area' kind, CAST(NULL AS VARCHAR2(20)) sigla,
               g.NOME area, ROUND(SUM(r.VALOR),2) valor
          FROM LDESK.GERENC_LANCAMENTORESUMO r
          LEFT JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
         WHERE r.ANO_MES='&ANO_MES' AND r.ID_CONTA='020.110.0010'
         GROUP BY g.NOME
        UNION ALL
        -- Participacao Interna: per-lawyer, keyed by CONTASPAGAR.COD_ADVG (gross
        -- base). LANCAMENTO.LANCPROFDEST is NULL on these rows, so we mirror the
        -- custo_equipe_deriv approach and read the payable ledger instead.
        SELECT 'lawyer' kind, cp.COD_ADVG sigla,
               CAST(NULL AS VARCHAR2(60)) area, ROUND(SUM(cp.CPGNVALORBASE),2) valor
          FROM FINANCE.CONTASPAGAR cp
         WHERE cp.PCTCNUMEROCONTA='030.010.0120'
           AND cp.CPGDVECTO >= DATE '&D_START' AND cp.CPGDVECTO < DATE '&D_END'
           AND cp.COD_ADVG IS NOT NULL
         GROUP BY cp.COD_ADVG
     )
  ),
  -- Vale-ADM (Vale Refeição/Transporte administrativo). The workbook books it in
  -- Salários Administração, but it is NOT under 020.050.* — it is paid via the
  -- transitória de pagamentos 200.010.0010 ("desdobramento - histórico"),
  -- identified by the histórico "VR/VT Mensal para ..." (confirmed vs
  -- Pagtos maio.XLS.xlsx: VR 2.719,90 + VT 607,04 = 3.326,94 = workbook G122+G123).
  -- Emit the total; the backend adds it to the institutional Salários Administração
  -- section (and FGTS-ADM moves to Impostos to tie the family to the centavo).
  'vale_adm' VALUE (
     SELECT NVL(ROUND(SUM(l.LANNVALOR),2), 0)
       FROM FINANCE.LANCAMENTO l
      WHERE l.PCTCNUMEROCONTADEST='200.010.0010'
        AND l.LANDDATA >= DATE '&D_START' AND l.LANDDATA < DATE '&D_END'
        AND ( UPPER(l.LANCHISTORICO) LIKE '%VR MENSAL%'
           OR UPPER(l.LANCHISTORICO) LIKE '%VT MENSAL%'
           OR UPPER(l.LANCHISTORICO) LIKE '%VALE REFEI%MENSAL%'
           OR UPPER(l.LANCHISTORICO) LIKE '%VALE TRANSP%MENSAL%' )
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
  ),
  -- POINT 16 + 17 (2026-07-14): "Bônus equipe" = soma dos bônus individuais dos
  -- FUNCIONÁRIOS, na conta contábil 150.000.0000 ('150.%'). Feeds the
  -- Base_Resultado "Distribuição de Lucros extras" > "Bônus equipe" line.
  -- ⚠ FONTE CORRIGIDA (probe_socio_split_validate #G/#L): os lançamentos 150.*
  -- vivem em FINANCE.LANCAMENTO, NÃO em GERENC_LANCAMENTORESUMO (que retornava
  -- NULL/vazio para fev — era o bug). Fev FINANCE.LANCAMENTO 150.% = 94.696,15 =
  -- workbook (150.* part) exato. A sigla vem como 2º token do histórico ("Bônus
  -- FSM ..."). POINT 17 automatizado por NÓS: excluímos qualquer sigla que seja
  -- SÓCIO (CAD_PROFISSIONAL.SOCIO='S'); hoje é no-op (as 6 siglas em 150.* —
  -- FSM/EHF/BMP/IAC/BBX/ASG — são todas SOCIO='N', provado por #LSIG), mas
  -- future-proof: se um sócio for lançado em 150.* no futuro, ele NÃO entra no
  -- bônus de equipe. O ``bonus_equipe_030`` abaixo soma os bônus de FUNCIONÁRIO
  -- lançados em 030.010.0010 (JGS). NVL → NULL (não 0) quando não há lançamentos,
  -- para a linha ficar em branco ("ainda não temos") em vez de zero inventado.
  'bonus_equipe' VALUE (
     SELECT ROUND(SUM(l.LANNVALOR),2)
       FROM FINANCE.LANCAMENTO l
      WHERE l.PCTCNUMEROCONTADEST LIKE '150.%'
        AND l.LANDDATA >= DATE '&D_START' AND l.LANDDATA < DATE '&D_END'
        AND NOT EXISTS (
          SELECT 1 FROM LDESK.CAD_PROFISSIONAL p
           WHERE p.SIGLA = UPPER(TRIM(REGEXP_SUBSTR(l.LANCHISTORICO, '\S+\s+(\S+)', 1, 1, NULL, 1)))
             AND p.SOCIO = 'S' )
  ),
  -- Bônus booked in 030.010.0010 (NOT 150.*). Proven vs Feb (2026-07-14 probe):
  -- the workbook "Bônus equipe" D192 = 94.696,15 (150.010.0010) + 7.009,84 JGS,
  -- and the JGS bônus is a 030.010.0010 LANCAMENTO with histórico "Bônus JGS
  -- referente a 2025". These are exactly the lines custo_equipe_deriv EXCLUDES
  -- (its %B_NUS%/%BONUS% filter), so adding them here does NOT double-count team
  -- cost. The backend adds this to ``bonus_equipe`` so Feb ties to the centavo.
  -- NULL when none (line stays blank). DL-excedente-sócios also lands in 0010
  -- (histórico "DL excedente <SIGLA> - Reserva"), intentionally EXCLUDED here — it
  -- feeds the separate ``dl_excedente_socios`` / ``dl_excedente_mv`` blocks below,
  -- which we now derive from the DB (POINT 17 automated by us, 2026-07-14).
  'bonus_equipe_030' VALUE (
     SELECT ROUND(SUM(l.LANNVALOR),2)
       FROM FINANCE.LANCAMENTO l
      WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
        AND l.LANDDATA >= DATE '&D_START' AND l.LANDDATA < DATE '&D_END'
        AND (UPPER(l.LANCHISTORICO) LIKE '%B_NUS%' OR UPPER(l.LANCHISTORICO) LIKE '%BONUS%')
  ),
  -- Convênio extra por advogado (upgrade/dependentes) — deduzido da DL do sócio,
  -- NÃO é despesa do escritório. Proven Jan–Mai (2026-07-14 probe_convenio_extra_dl):
  -- constante DC 3.796,78 / RB 5.151,75 / EHF 1.398,01 no namespace 500.010.<SIGLA>
  -- (LANCPROFDEST NULL → sigla = sufixo da conta). Aurélio/AM: extra já embutido na
  -- base 030.010.0110, não em 500.010. Emitimos per-sigla; o backend subtrai da DL
  -- do sócio correspondente. Ver [[transitoria-desdobramento-mechanism]].
  'convenio_extra_dl' VALUE (
     SELECT JSON_ARRAYAGG(JSON_OBJECT(
        'sigla'     VALUE sigla,
        'valor'     VALUE valor,
        'historico' VALUE historico
     ) RETURNING CLOB)
     FROM (SELECT SUBSTR(l.PCTCNUMEROCONTADEST, 9) sigla,
                  ROUND(SUM(l.LANNVALOR),2) valor,
                  SUBSTR(MAX(l.LANCHISTORICO),1,60) historico
             FROM FINANCE.LANCAMENTO l
            WHERE l.PCTCNUMEROCONTADEST LIKE '500.010.%'
              AND l.LANDDATA >= DATE '&D_START' AND l.LANDDATA < DATE '&D_END'
              AND ( UPPER(l.LANCHISTORICO) LIKE '%CONV_NIO%' OR UPPER(l.LANCHISTORICO) LIKE '%CONVENIO%'
                 OR UPPER(l.LANCHISTORICO) LIKE '%DEPENDENTE%' OR UPPER(l.LANCHISTORICO) LIKE '%UPGRADE%'
                 OR UPPER(l.LANCHISTORICO) LIKE '%SA_DE%'    OR UPPER(l.LANCHISTORICO) LIKE '%SAUDE%'
                 OR UPPER(l.LANCHISTORICO) LIKE '%PLANO%' )
            GROUP BY SUBSTR(l.PCTCNUMEROCONTADEST, 9))
  ),
  -- POINT 17 (automatizado por NÓS, 2026-07-14 — NÃO é tarefa do RUMO): split do
  -- "DL excedente" dos sócios, derivado do próprio DB. Os excedentes vivem em
  -- 030.010.0010 com histórico "DL excedente <SIGLA> - Reserva ...". Classificamos
  -- a sigla (token após "excedente") pelo flag ESTRUTURAL CAD_PROFISSIONAL.SOCIO:
  --   * dl_excedente_socios = Σ onde SOCIO='S' E sigla<>'MV' (os 3 sócios núcleo:
  --     AM/DC/RB). Provado vs 05.2026: jan = 164.477,34 = Base_Resultado D193.
  --   * dl_excedente_mv     = Σ da sigla 'MV' (Martim, mantido separado como no
  --     workbook). Provado: mar = 6.627 = Base_Resultado D194.
  -- NVL → NULL quando não há excedente no mês (linha em branco, nunca zero).
  -- Ver probe_socio_split.sql / probe_socio_split_validate.sql (#X/#XS/#XM).
  'dl_excedente_socios' VALUE (
     SELECT ROUND(SUM(valor),2) FROM (
        SELECT l.LANNVALOR valor,
               UPPER(TRIM(REGEXP_SUBSTR(l.LANCHISTORICO, 'excedente\s+(\S+)', 1, 1, 'i', 1))) sig
          FROM FINANCE.LANCAMENTO l
         WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
           AND l.LANDDATA >= DATE '&D_START' AND l.LANDDATA < DATE '&D_END'
           AND UPPER(l.LANCHISTORICO) LIKE '%EXCEDENTE%'
     ) x
     WHERE x.sig <> 'MV'
       AND EXISTS (SELECT 1 FROM LDESK.CAD_PROFISSIONAL p
                    WHERE p.SIGLA = x.sig AND p.SOCIO='S')
  ),
  'dl_excedente_mv' VALUE (
     SELECT ROUND(SUM(l.LANNVALOR),2)
       FROM FINANCE.LANCAMENTO l
      WHERE l.PCTCNUMEROCONTADEST='030.010.0010'
        AND l.LANDDATA >= DATE '&D_START' AND l.LANDDATA < DATE '&D_END'
        AND UPPER(l.LANCHISTORICO) LIKE '%EXCEDENTE%'
        AND UPPER(TRIM(REGEXP_SUBSTR(l.LANCHISTORICO, 'excedente\s+(\S+)', 1, 1, 'i', 1))) = 'MV'
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
