-- Probe: verify FAT_FATURA columns before trusting extract.sql's faturas_analitico.
-- F0 is the source of truth (column list); F3 dumps one full row so we see real
-- column names+values even if our guessed names are wrong. Read-only.
-- All statements single-line (paste-safe on the RDP console).
SET DEFINE OFF
SET PAGESIZE 200
SET LINESIZE 400
SET FEEDBACK OFF
WHENEVER SQLERROR CONTINUE
PROMPT === F0) FAT_FATURA columns ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='FAT_FATURA' ORDER BY column_id;
PROMPT === F1) client table candidates ===
SELECT owner, table_name FROM ALL_TABLES WHERE owner='LDESK' AND table_name LIKE '%CLIENTE%' ORDER BY table_name;
PROMPT === F2) CAD_CLIENTE columns (if present) ===
SELECT column_name, data_type FROM ALL_TAB_COLUMNS WHERE owner='LDESK' AND table_name='CAD_CLIENTE' ORDER BY column_id;
PROMPT === F3) one full FAT_FATURA row (see real column names/values) ===
SELECT * FROM LDESK.FAT_FATURA WHERE ROWNUM = 1;
PROMPT === F4) per-area faturamento via POSFIN_RESULTFAT (safe, mirrors recebimento) ===
SELECT r.ANO_MES, NVL(a.NOME,'(sem area)') area, ROUND(SUM(r.VALOR1),2) total, COUNT(*) n FROM LDESK.GERENC_VW_POSFIN_RESULTFAT r LEFT JOIN LDESK.CAD_CASO c ON c.ID_CASO=r.ID_CASO LEFT JOIN LDESK.CAD_AREAJURIDICA a ON a.ID_AREAJURIDICA=c.ID_AREAJURIDICA WHERE r.ANO_MES IN ('2026-01','2026-02') GROUP BY r.ANO_MES, a.NOME ORDER BY r.ANO_MES, total DESC;
PROMPT === DONE ===
EXIT
