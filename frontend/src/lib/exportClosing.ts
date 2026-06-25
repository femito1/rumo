import type { WorkBook } from "xlsx";
import type { ClosingPayload } from "./types";

/** Mirrors the on-screen placeholder for not-yet-available values. */
export const MISSING_LABEL = "ainda não temos";

type CellValue = string | number;
type AoA = CellValue[][];

interface GridCell { t: "label" | "number" | "formula" | "empty"; v?: string | null; n?: number | null }
interface SourcedCell { value: number | null; source?: string }
interface RichInvoice {
  fatura?: string | number | null;
  cliente?: string | null;
  caso?: string | null;
  data_emissao?: string | null;
  valor_faturado?: number | null;
  lawyers?: { sigla?: string | null; nome?: string | null; valor_trabalhado?: number | null }[];
}

/** Convert any tab (grid or rich) into a 2D array suitable for a worksheet. */
export function tabToAoA(tab: unknown): AoA {
  if (!tab || typeof tab !== "object") return [];
  const t = tab as Record<string, unknown>;
  if (t.kind === "grid") return gridToAoA(t);
  return richToAoA(t);
}

function gridToAoA(t: Record<string, unknown>): AoA {
  const grid = (t.grid as GridCell[][]) ?? [];
  return grid.map((row) =>
    row.map((c): CellValue => {
      if (c.t === "label") return c.v ?? "";
      if ((c.t === "number" || c.t === "formula") && c.n != null) return c.n;
      return "";
    }),
  );
}

function richToAoA(t: Record<string, unknown>): AoA {
  if (Array.isArray(t.invoices)) return invoicesToAoA(t);
  const columns = (t.columns as string[]) ?? [];
  const rows = (t.rows as Record<string, unknown>[]) ?? [];
  if (!columns.length || !rows.length) return columns.length ? [columns] : [];
  const keys = Object.keys(rows[0]).slice(0, columns.length);
  const out: AoA = [columns];
  for (const row of rows) {
    out.push(keys.map((k, ci) => richValue(row[k], ci === 0)));
  }
  return out;
}

function invoicesToAoA(t: Record<string, unknown>): AoA {
  const columns = (t.columns as string[]) ?? ["Fatura", "Cliente", "Caso", "Advogado", "Valor", "DT Emissão", "Total Fatura"];
  const invoices = (t.invoices as RichInvoice[]) ?? [];
  const out: AoA = [columns];
  for (const inv of invoices) {
    const lawyers = inv.lawyers?.length ? inv.lawyers : [{ nome: null, valor_trabalhado: null }];
    lawyers.forEach((law, li) => {
      out.push([
        li === 0 ? orMissing(inv.fatura) : "",
        li === 0 ? orMissing(inv.cliente) : "",
        li === 0 ? orMissing(inv.caso) : "",
        orMissing(law.nome ?? law.sigla),
        moneyOrMissing(law.valor_trabalhado),
        li === 0 ? orMissing(inv.data_emissao) : "",
        li === 0 ? moneyOrMissing(inv.valor_faturado) : "",
      ]);
    });
  }
  return out;
}

function richValue(v: unknown, isFirstColumn: boolean): CellValue {
  if (isSourcedCell(v)) return v.value == null ? MISSING_LABEL : v.value;
  if (typeof v === "number") return v;
  if (typeof v === "string") return v === "" ? MISSING_LABEL : v;
  if (v == null) return isFirstColumn ? "" : MISSING_LABEL;
  return String(v);
}

function isSourcedCell(v: unknown): v is SourcedCell {
  return typeof v === "object" && v != null && "value" in (v as Record<string, unknown>);
}

function orMissing(v: unknown): CellValue {
  if (v == null || v === "") return MISSING_LABEL;
  return typeof v === "number" ? v : String(v);
}

function moneyOrMissing(n: number | null | undefined): CellValue {
  return n == null ? MISSING_LABEL : n;
}

function tabName(tab: unknown, fallback: string): string {
  const name = (tab as { name?: string } | undefined)?.name ?? fallback;
  // Excel sheet names: max 31 chars and no : \ / ? * [ ]
  return name.replace(/[:\\/?*[\]]/g, " ").slice(0, 31) || fallback;
}

type XlsxModule = typeof import("xlsx");

/** Build a workbook. With `onlyTabId`, the workbook has just that one sheet. */
export function buildWorkbook(XLSX: XlsxModule, payload: ClosingPayload, onlyTabId?: string): WorkBook {
  const wb = XLSX.utils.book_new();
  const order = onlyTabId ? [onlyTabId] : payload.tab_order;
  const used = new Set<string>();
  for (const id of order) {
    const tab = payload.tabs[id];
    if (!tab) continue;
    const aoa = tabToAoA(tab);
    const sheet = XLSX.utils.aoa_to_sheet(aoa);
    let name = tabName(tab, id);
    while (used.has(name)) name = name.slice(0, 28) + "~" + (used.size % 10);
    used.add(name);
    XLSX.utils.book_append_sheet(wb, sheet, name);
  }
  return wb;
}

function fileBase(payload: ClosingPayload): string {
  const client = (payload.client?.name ?? "fechamento").replace(/[^\w-]+/g, "_");
  return `${client}_${payload.period.ano_mes}`;
}

/** Download a multi-sheet workbook with every tab of the closing. */
export async function exportAllSheets(payload: ClosingPayload): Promise<void> {
  const XLSX = await import("xlsx");
  const wb = buildWorkbook(XLSX, payload);
  XLSX.writeFile(wb, `${fileBase(payload)}_completo.xlsx`);
}

/** Download a single-sheet workbook for the currently-visible tab. */
export async function exportSingleSheet(payload: ClosingPayload, tabId: string): Promise<void> {
  const XLSX = await import("xlsx");
  const wb = buildWorkbook(XLSX, payload, tabId);
  const name = tabName(payload.tabs[tabId], tabId).replace(/\s+/g, "_");
  XLSX.writeFile(wb, `${fileBase(payload)}_${name}.xlsx`);
}
