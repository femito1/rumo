// frontend/src/features/closing/DayRangeFilter.tsx
export function DayRangeFilter({ from, to, onChange, onClear }:
  { from: number | null; to: number | null; onChange: (from: number, to: number) => void; onClear: () => void }) {
  return (
    <div className="day-range">
      <label>De
        <input type="number" min={1} max={31} value={from ?? ""} onChange={(e) => onChange(Number(e.target.value), to ?? Number(e.target.value))} />
      </label>
      <label>até
        <input type="number" min={1} max={31} value={to ?? ""} onChange={(e) => onChange(from ?? Number(e.target.value), Number(e.target.value))} />
      </label>
      {from || to ? <button className="btn btn-ghost" onClick={onClear}>Limpar</button> : null}
    </div>
  );
}
