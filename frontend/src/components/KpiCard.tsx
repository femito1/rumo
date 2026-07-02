// frontend/src/components/KpiCard.tsx
import { formatBRL, formatNumber, formatPercent } from "../lib/format";

type KpiFormat = "brl" | "number" | "percent";

function render(value: number | null, format: KpiFormat): string {
  if (format === "number") return formatNumber(value);
  if (format === "percent") return formatPercent(value);
  return formatBRL(value);
}

export function KpiCard({
  label,
  value,
  foot,
  highlight = false,
  format = "brl",
}: {
  label: string;
  value: number | null;
  foot?: string;
  highlight?: boolean;
  format?: KpiFormat;
}) {
  return (
    <div className={`kpi${highlight ? " kpi-highlight" : ""}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value num">{render(value, format)}</div>
      {foot ? <div className="kpi-foot">{foot}</div> : null}
    </div>
  );
}
