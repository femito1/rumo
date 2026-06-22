// frontend/src/components/KpiCard.tsx
import { formatBRL } from "../lib/format";
export function KpiCard({ label, value, foot, highlight = false }: { label: string; value: number | null; foot?: string; highlight?: boolean }) {
  return (
    <div className={`kpi${highlight ? " kpi-highlight" : ""}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value num">{formatBRL(value)}</div>
      {foot ? <div className="kpi-foot">{foot}</div> : null}
    </div>
  );
}
