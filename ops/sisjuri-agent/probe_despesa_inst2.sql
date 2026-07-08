-- Probe 2: pin the EXACT account boundaries for Despesa Institucional total and
-- Despesas Área, now that probe 1 mapped the families. Findings so far:
--   * SUM(020.*) = SUM(TIPO_CONTA='D') but is SMALLER than the workbook total
--     (Feb 68.771,58 vs 95.047,39; gap 26.275,81 ~ the 'I' family 30.913,70).
--   * 020.110.0010 (Participação Externa 1.500 Feb) is COMISSÃO, must be
--     excluded from Despesa Institucional.
--   * Area-tagged 020.* includes Administração (not a DRE area) + the comissão.
-- Ground truth (workbook): Despesa Institucional total per month =
--   Jan 100.181,41 · Feb 95.047,39 · Mar 101.968,90 · Apr 110.156,11 · Mai 105.511,43
-- Despesas Área per area (workbook):
--   Cont: 1060,10·2129,32·2346,72·4183,92·2276,22
--   Econ: 1871,81·3296,07·2129,32·2129,32·2300,10
--   Arb : 146,00·2633,69·3728,18·2633,69·1204,47
SET DEFINE OFF
SET PAGESIZE 3000
SET LINESIZE 340
SET FEEDBACK ON
COL id_conta FORMAT A16
COL nome FORMAT A45
COL area FORMAT A26
COL ano_mes FORMAT A7
COL tipo FORMAT A4
WHENEVER SQLERROR CONTINUE

PROMPT === 1. 020.* + 040.* (I) combined per month — does 020+040 hit the workbook total? ===
SELECT r.ANO_MES,
       ROUND(SUM(CASE WHEN r.ID_CONTA LIKE '020.%' THEN r.VALOR ELSE 0 END),2) f020,
       ROUND(SUM(CASE WHEN r.ID_CONTA LIKE '040.%' THEN r.VALOR ELSE 0 END),2) f040,
       ROUND(SUM(CASE WHEN r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%' THEN r.VALOR ELSE 0 END),2) f020_040
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
 GROUP BY r.ANO_MES
 ORDER BY r.ANO_MES;

PROMPT === 2. TIPO_CONTA=I accounts (the 040 family) per month — what are they? ===
SELECT r.ANO_MES, r.ID_CONTA, MAX(r.NOME_CONTA) nome, ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.TIPO_CONTA='I'
 GROUP BY r.ANO_MES, r.ID_CONTA
 ORDER BY r.ANO_MES, r.ID_CONTA;

PROMPT === 3. 020+040 EXCLUDING comissao (020.110) per month vs workbook total ===
-- Target: Jan 100.181,41 / Feb 95.047,39 / Mar 101.968,90 / Apr 110.156,11 / Mai 105.511,43
SELECT r.ANO_MES,
       ROUND(SUM(r.VALOR),2) inst_total_candidate
  FROM LDESK.GERENC_LANCAMENTORESUMO r
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (r.ID_CONTA LIKE '020.%' OR r.ID_CONTA LIKE '040.%')
   AND r.ID_CONTA <> '020.110.0010'
 GROUP BY r.ANO_MES
 ORDER BY r.ANO_MES;

PROMPT === 4. Area-tagged lines EXCLUDING Administracao & comissao, per area/month ===
-- Should tie to Despesas Área. Map Equipe Contencioso->Cont, Equipe Direito
-- Economico->Econ, Arbitragem->Arb. Include BOTH 020.* and 040.* and 030.* that
-- carry an ID_GRUPOJURIDICO of a DRE area.
SELECT r.ANO_MES, g.NOME area, ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND r.ID_CONTA <> '020.110.0010'
   AND UPPER(g.NOME) NOT LIKE '%ADMINISTRA%'
   AND UPPER(g.NOME) NOT LIKE '%ADM%'
   AND UPPER(g.NOME) NOT LIKE '%N_O ALOCAD%'
 GROUP BY r.ANO_MES, g.NOME
 ORDER BY r.ANO_MES, g.NOME;

PROMPT === 5. Which account FAMILIES ever carry a DRE-area ID_GRUPOJURIDICO? ===
-- Tells us whether Despesas Área is purely 020.* or also 030.*/040.*.
SELECT SUBSTR(r.ID_CONTA,1,7) familia, g.NOME area,
       ROUND(SUM(r.VALOR),2) total, COUNT(*) n
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES BETWEEN '2026-01' AND '2026-05'
   AND (UPPER(g.NOME) LIKE '%CONTENCIOSO%' OR UPPER(g.NOME) LIKE '%ECON%'
        OR UPPER(g.NOME) LIKE '%ARBITRAGEM%' OR UPPER(g.NOME) LIKE '%COMPLIANCE%')
 GROUP BY SUBSTR(r.ID_CONTA,1,7), g.NOME
 ORDER BY familia, area;

PROMPT === 6. Full list of area-tagged rows Feb (see exactly what composes each area) ===
SELECT r.ID_CONTA, MAX(r.NOME_CONTA) nome, g.NOME area, ROUND(SUM(r.VALOR),2) total
  FROM LDESK.GERENC_LANCAMENTORESUMO r
  JOIN LDESK.CAD_GRUPOJURIDICO g ON g.ID_GRUPOJURIDICO=r.ID_GRUPOJURIDICO
 WHERE r.ANO_MES='2026-02'
 GROUP BY r.ID_CONTA, r.ID_GRUPOJURIDICO, g.NOME
 ORDER BY g.NOME, r.ID_CONTA;

EXIT
