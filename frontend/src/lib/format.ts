// frontend/src/lib/format.ts
const BRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatBRL(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return BRL.format(value).replace("\u00a0", " ");
}

const NUM = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return NUM.format(value);
}

const PCT = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

/** Format a ratio (e.g. 0.4123) as a PT-BR percentage ("41,2%"). */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return PCT.format(value);
}

const NUM1 = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

/** Compact money for slide tables/cards — "444,5K" / "2.372,5K" / "-14,9K",
 *  mirroring the PPTX. Values are shown in thousands (K) with one decimal. */
export function formatBRLShort(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${NUM1.format(value / 1000)}K`;
}

/** Signed percentage-point / percent with an explicit + on gains ("+2,4%"). */
export function formatPercentSigned(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const s = PCT.format(value);
  return value > 0 ? `+${s}` : s;
}

const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

export function formatMonthLabel(anoMes: string): string {
  const [y, m] = anoMes.split("-").map(Number);
  return `${MESES[m - 1]} ${y}`;
}

/** Number of days in a YYYY-MM competence month (28/29/30/31). */
export function daysInMonth(anoMes: string): number {
  const [y, m] = anoMes.split("-").map(Number);
  if (!y || !m) return 31;
  return new Date(y, m, 0).getDate(); // day 0 of next month = last day of this one
}
