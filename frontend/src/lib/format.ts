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
