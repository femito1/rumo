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
