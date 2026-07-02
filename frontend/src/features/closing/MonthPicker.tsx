// frontend/src/features/closing/MonthPicker.tsx
import { useState } from "react";

const MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

export function MonthPicker({ value, availableMonths, onChange }:
  { value: string; availableMonths: string[]; onChange: (anoMes: string) => void }) {
  const available = new Set(availableMonths);
  const [selYear] = value.split("-").map(Number);

  // Years we can browse: everything with data, plus the selected year so the
  // picker never lands on an empty range.
  const years = Array.from(
    new Set([...availableMonths.map((m) => Number(m.slice(0, 4))), selYear]),
  ).sort((a, b) => a - b);

  // The year currently shown in the grid (may differ from the selected month's
  // year while the user browses). Starts on the selected month's year.
  const [viewYear, setViewYear] = useState<number>(selYear);
  const minYear = years[0];
  const maxYear = years[years.length - 1];
  const canPrev = viewYear > minYear;
  const canNext = viewYear < maxYear;

  return (
    <div className="month-picker">
      <div className="month-picker-year">
        <button
          type="button"
          className="year-nav"
          aria-label="Ano anterior"
          disabled={!canPrev}
          onClick={() => canPrev && setViewYear(viewYear - 1)}
        >
          ‹
        </button>
        <span className="year-label">{viewYear}</span>
        <button
          type="button"
          className="year-nav"
          aria-label="Próximo ano"
          disabled={!canNext}
          onClick={() => canNext && setViewYear(viewYear + 1)}
        >
          ›
        </button>
      </div>
      <div className="month-grid">
        {MESES.map((label, i) => {
          const anoMes = `${viewYear}-${String(i + 1).padStart(2, "0")}`;
          const enabled = available.has(anoMes);
          const selected = anoMes === value;
          return (
            <button
              key={label}
              className={`month-cell${selected ? " selected" : ""}`}
              disabled={!enabled}
              title={enabled ? "" : "Mês ainda em aberto"}
              onClick={() => onChange(anoMes)}
            >
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
