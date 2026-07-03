// frontend/src/components/KpiCard.tsx
import { formatBRL, formatNumber, formatPercent } from "../lib/format";

type KpiFormat = "brl" | "number" | "percent";

function render(value: number | null, format: KpiFormat): string {
  if (format === "number") return formatNumber(value);
  if (format === "percent") return formatPercent(value);
  return formatBRL(value);
}

/**
 * KPI card following the metric → context scan pattern.
 *
 * - `hero` cards carry the heaviest visual weight (larger value, accent frame)
 *   and lead the top strip.
 * - `signed` cards color the value by sign (green positive / red negative) so a
 *   loss is legible at a glance instead of a bare "-R$".
 */
export function KpiCard({
  label,
  value,
  foot,
  hero = false,
  signed = false,
  format = "brl",
}: {
  label: string;
  value: number | null;
  foot?: string;
  hero?: boolean;
  signed?: boolean;
  format?: KpiFormat;
}) {
  const tone =
    signed && value != null ? (value < 0 ? " kpi-neg" : " kpi-pos") : "";
  return (
    <div className={`kpi${hero ? " kpi-hero" : ""}${tone}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value num">{render(value, format)}</div>
      {foot ? <div className="kpi-foot">{foot}</div> : null}
    </div>
  );
}
