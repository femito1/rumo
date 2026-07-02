// frontend/src/features/closing/TabView.tsx
import { TableScroll } from "../../components/TableScroll";
import { formatPercent } from "../../lib/format";

/** Shown wherever a value isn't available from the source yet (was MANUAL/blank). */
export const MISSING_LABEL = "ainda não temos";

interface GridCell { t: "label" | "number" | "formula" | "empty"; v?: string | null; n?: number | null }
interface RichTab { kind: "rich"; name: string; columns?: string[]; rows?: RichRow[]; invoices?: RichInvoice[]; [k: string]: unknown }
interface GridTab { kind: "grid"; name: string; note?: string; grid: GridCell[][]; rows: number; cols: number }
type Tab = RichTab | GridTab | undefined | unknown;

interface SourcedCell { value: number | null; source?: string }
type RichRow = Record<string, unknown>;
interface RichInvoice {
  fatura?: string | number | null;
  cliente?: string | null;
  caso?: string | null;
  data_emissao?: string | null;
  valor_faturado?: number | null;
  lawyers?: { sigla?: string | null; nome?: string | null; valor_trabalhado?: number | null }[];
}

const numberFmt = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function TabView({ tab }: { tab: Tab }) {
  if (!tab || typeof tab !== "object") {
    return <div className="empty-state">Selecione uma aba para ver o fechamento.</div>;
  }
  const t = tab as RichTab | GridTab;
  if (t.kind === "grid") return <GridTabView tab={t as GridTab} />;
  return <RichTabView tab={t as RichTab} />;
}

function GridTabView({ tab: g }: { tab: GridTab }) {
  const [head, ...body] = g.grid ?? [];
  return (
    <div className="tab grid-tab">
      <h2>{g.name}</h2>
      {g.note ? <p className="muted">{g.note}</p> : null}
      <TableScroll>
        <table className="grid-table">
          {head ? (
            <thead>
              <tr>
                {head.map((c, ci) => (
                  <th key={ci} className={c.t === "number" || c.t === "formula" ? "num" : ""}>{cellText(c)}</th>
                ))}
              </tr>
            </thead>
          ) : null}
          <tbody>
            {body.map((row, ri) => (
              <tr key={ri}>
                {row.map((c, ci) => (
                  <td key={ci} className={c.t === "number" || c.t === "formula" ? "num" : ""}>{cellText(c)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
    </div>
  );
}

/**
 * Rich tabs carry a known structure (columns + rows/invoices) with live API
 * values mixed with not-yet-available cells. We render the real table shape and
 * fill every missing value with an explanatory placeholder instead of a blank.
 */
function RichTabView({ tab }: { tab: RichTab }) {
  if (tab.invoices) return <RichInvoicesView tab={tab} invoices={tab.invoices} />;
  const columns = tab.columns ?? [];
  const rows = tab.rows ?? [];
  if (!columns.length || !rows.length) {
    return (
      <div className="tab rich-tab">
        <h2>{tab.name}</h2>
        <p className="muted">{MISSING_LABEL}</p>
      </div>
    );
  }
  const keys = rowKeys(rows[0], columns.length);
  return (
    <div className="tab rich-tab">
      <h2>{tab.name}</h2>
      {tab.snapshot_missing === true ? (
        <div className="missing-banner" role="status">
          Dados institucionais ainda não importados para este mês.
        </div>
      ) : null}
      <TableScroll>
        <table className="grid-table">
          <thead>
            <tr>{columns.map((c, ci) => <th key={ci} className={ci === 0 ? "" : "num"}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={ri} className={rowClass(row)}>
                {keys.map((k, ci) => (
                  <td
                    key={ci}
                    className={ci === 0 ? cellIndentClass(row) : "num"}
                  >
                    {renderRichValue(row[k], ci === 0, isPercentColumn(columns[ci]))}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
    </div>
  );
}

/** Row styling from DRE metadata (is_total/kind), ignored for plain tables. */
function rowClass(row: RichRow): string {
  const kind = row.kind;
  const isTotal = row.is_total;
  const parts: string[] = [];
  if (kind === "header") parts.push("row-section");
  if (isTotal === true) parts.push("row-total");
  if (kind === "margin") parts.push("row-margin");
  return parts.join(" ");
}

function cellIndentClass(row: RichRow): string {
  return row.indent === 1 ? "cell-indent" : "";
}

function isPercentColumn(header: string | undefined): boolean {
  return typeof header === "string" && header.trim().endsWith("%");
}

function RichInvoicesView({ tab, invoices }: { tab: RichTab; invoices: RichInvoice[] }) {
  const columns = tab.columns ?? ["Fatura", "Cliente", "Caso", "Advogado", "Valor", "DT Emissão", "Total Fatura"];
  return (
    <div className="tab rich-tab">
      <h2>{tab.name}</h2>
      <TableScroll>
        <table className="grid-table">
          <thead>
            <tr>{columns.map((c, ci) => <th key={ci} className={c === "Valor" || c === "Total Fatura" ? "num" : ""}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {invoices.flatMap((inv, ii) => {
              const lawyers = inv.lawyers?.length ? inv.lawyers : [{ nome: null, valor_trabalhado: null }];
              return lawyers.map((law, li) => (
                <tr key={`${ii}-${li}`}>
                  <td>{li === 0 ? orMissing(inv.fatura) : ""}</td>
                  <td>{li === 0 ? orMissing(inv.cliente) : ""}</td>
                  <td>{li === 0 ? orMissing(inv.caso) : ""}</td>
                  <td>{orMissing(law.nome ?? law.sigla)}</td>
                  <td className="num">{moneyOrMissing(law.valor_trabalhado)}</td>
                  <td>{li === 0 ? orMissing(inv.data_emissao) : ""}</td>
                  <td className="num">{li === 0 ? moneyOrMissing(inv.valor_faturado) : ""}</td>
                </tr>
              ));
            })}
          </tbody>
        </table>
      </TableScroll>
    </div>
  );
}

/** Derive the ordered keys to read off each row, given the declared columns. */
function rowKeys(sample: RichRow, columnCount: number): string[] {
  const keys = Object.keys(sample);
  return keys.slice(0, columnCount);
}

function renderRichValue(v: unknown, isFirstColumn: boolean, isPercent = false): string {
  if (isPercent) {
    if (isSourcedCell(v)) return v.value == null ? MISSING_LABEL : formatPercent(v.value);
    if (typeof v === "number") return formatPercent(v);
    return v == null ? MISSING_LABEL : String(v);
  }
  if (isSourcedCell(v)) return moneyOrMissing(v.value);
  if (typeof v === "number") return numberFmt.format(v);
  if (typeof v === "string") return v === "" ? MISSING_LABEL : v;
  if (v == null) return isFirstColumn ? "" : MISSING_LABEL;
  return String(v);
}

function isSourcedCell(v: unknown): v is SourcedCell {
  return typeof v === "object" && v != null && "value" in (v as Record<string, unknown>);
}

function orMissing(v: unknown): string {
  if (v == null || v === "") return MISSING_LABEL;
  return String(v);
}

function moneyOrMissing(n: number | null | undefined): string {
  if (n == null) return MISSING_LABEL;
  return numberFmt.format(n);
}

function cellText(c: GridCell): string {
  if (c.t === "label") return c.v ?? "";
  if ((c.t === "number" || c.t === "formula") && c.n != null) {
    return numberFmt.format(c.n);
  }
  return "";
}
