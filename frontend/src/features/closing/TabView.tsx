// frontend/src/features/closing/TabView.tsx
import { TableScroll } from "../../components/TableScroll";

interface GridCell { t: "label" | "number" | "formula" | "empty"; v?: string | null; n?: number | null }
interface RichTab { kind: "rich"; name: string; [k: string]: unknown }
interface GridTab { kind: "grid"; name: string; note?: string; grid: GridCell[][]; rows: number; cols: number }
type Tab = RichTab | GridTab | undefined | unknown;

export function TabView({ tab }: { tab: Tab }) {
  if (!tab || typeof tab !== "object") {
    return <div className="empty-state">Selecione uma aba para ver o fechamento.</div>;
  }
  const t = tab as RichTab | GridTab;
  if (t.kind === "grid") {
    const g = t as GridTab;
    return (
      <div className="tab grid-tab">
        <h2>{g.name}</h2>
        {g.note ? <p className="muted">{g.note}</p> : null}
        <TableScroll>
          <table className="grid-table">
            <tbody>
              {g.grid.map((row, ri) => (
                <tr key={ri}>{row.map((c, ci) => <td key={ci} className={c.t === "number" || c.t === "formula" ? "num" : ""}>{cellText(c)}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </TableScroll>
      </div>
    );
  }
  return (
    <div className="tab rich-tab">
      <h2>{(t as RichTab).name}</h2>
      <p className="muted">Renderização rica com valores ao vivo.</p>
    </div>
  );
}

function cellText(c: GridCell): string {
  if (c.t === "label") return c.v ?? "";
  if ((c.t === "number" || c.t === "formula") && c.n != null) {
    return new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(c.n);
  }
  return "";
}
