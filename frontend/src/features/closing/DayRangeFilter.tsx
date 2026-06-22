// frontend/src/features/closing/DayRangeFilter.tsx
import { useState } from "react";

interface Props {
  from: number | null;
  to: number | null;
  maxDay: number;
  onApply: (from: number, to: number) => void;
  onClear: () => void;
  busy?: boolean;
}

/**
 * Day-range refiner. Edits are held in *local draft state* and only committed
 * when the user clicks "Aplicar" — so typing never fires a request mid-edit and
 * never auto-fills the other field. Inputs are string-typed to allow an empty
 * value (no sticky leading zero).
 */
export function DayRangeFilter({ from, to, maxDay, onApply, onClear, busy = false }: Props) {
  const appliedFrom = from?.toString() ?? "";
  const appliedTo = to?.toString() ?? "";
  const [fromDraft, setFromDraft] = useState(appliedFrom);
  const [toDraft, setToDraft] = useState(appliedTo);
  const [err, setErr] = useState<string | null>(null);

  // Sync drafts during render (not in an effect) when the *applied* range
  // changes from outside — e.g. switching month resets the filter.
  const [syncedKey, setSyncedKey] = useState(`${appliedFrom}|${appliedTo}`);
  const appliedKey = `${appliedFrom}|${appliedTo}`;
  if (syncedKey !== appliedKey) {
    setSyncedKey(appliedKey);
    setFromDraft(appliedFrom);
    setToDraft(appliedTo);
    setErr(null);
  }

  const dirty = fromDraft !== appliedFrom || toDraft !== appliedTo;

  function clampDay(raw: string): string {
    const digits = raw.replace(/[^\d]/g, "").slice(0, 2);
    if (digits === "") return "";
    const n = Math.min(maxDay, Math.max(0, Number(digits)));
    return n === 0 ? "" : String(n);
  }

  function apply() {
    const f = Number(fromDraft);
    const t = Number(toDraft);
    if (!fromDraft || !toDraft || f < 1 || t < 1) {
      setErr("Informe os dois dias.");
      return;
    }
    if (f > t) {
      setErr("O dia inicial deve ser menor ou igual ao final.");
      return;
    }
    setErr(null);
    onApply(f, t);
  }

  function clear() {
    setFromDraft("");
    setToDraft("");
    setErr(null);
    onClear();
  }

  const hasApplied = from != null && to != null;

  return (
    <div className="day-range">
      <div className="day-range-fields">
        <label>
          Dia inicial
          <input
            type="text"
            inputMode="numeric"
            placeholder="1"
            value={fromDraft}
            onChange={(e) => setFromDraft(clampDay(e.target.value))}
            onKeyDown={(e) => e.key === "Enter" && apply()}
          />
        </label>
        <span className="day-range-sep">até</span>
        <label>
          Dia final
          <input
            type="text"
            inputMode="numeric"
            placeholder={String(maxDay)}
            value={toDraft}
            onChange={(e) => setToDraft(clampDay(e.target.value))}
            onKeyDown={(e) => e.key === "Enter" && apply()}
          />
        </label>
        <button className="btn btn-primary" onClick={apply} disabled={busy || !dirty} type="button">
          {busy ? "Aplicando…" : "Aplicar"}
        </button>
        {hasApplied || fromDraft || toDraft ? (
          <button className="btn btn-ghost" onClick={clear} disabled={busy} type="button">
            Limpar
          </button>
        ) : null}
      </div>
      {err ? <div className="day-range-err">{err}</div> : null}
    </div>
  );
}
