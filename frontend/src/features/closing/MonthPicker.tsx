// frontend/src/features/closing/MonthPicker.tsx
const MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

export function MonthPicker({ value, availableMonths, onChange }:
  { value: string; availableMonths: string[]; onChange: (anoMes: string) => void }) {
  const [year] = value.split("-").map(Number);
  const available = new Set(availableMonths);
  return (
    <div className="month-picker">
      <div className="month-picker-year">{year}</div>
      <div className="month-grid">
        {MESES.map((label, i) => {
          const anoMes = `${year}-${String(i + 1).padStart(2, "0")}`;
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
