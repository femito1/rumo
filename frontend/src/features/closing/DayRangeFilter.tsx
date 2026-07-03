// frontend/src/features/closing/DayRangeFilter.tsx
import { useEffect, useRef, useState } from "react";

interface Props {
  from: number | null;
  to: number | null;
  maxDay: number;
  onApply: (from: number, to: number) => void;
  onClear: () => void;
  busy?: boolean;
}

/**
 * Day-range refiner as a popover. It's an occasional refinement, so it stays
 * out of the toolbar until opened. Edits are held in local draft state and only
 * committed on "Aplicar" — typing never fires a request mid-edit. When a range
 * is active the trigger shows it and offers a one-click clear.
 */
export function DayRangeFilter({ from, to, maxDay, onApply, onClear, busy = false }: Props) {
  const appliedFrom = from?.toString() ?? "";
  const appliedTo = to?.toString() ?? "";
  const [open, setOpen] = useState(false);
  const [fromDraft, setFromDraft] = useState(appliedFrom);
  const [toDraft, setToDraft] = useState(appliedTo);
  const [err, setErr] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  // Sync drafts during render when the applied range changes from outside.
  const [syncedKey, setSyncedKey] = useState(`${appliedFrom}|${appliedTo}`);
  const appliedKey = `${appliedFrom}|${appliedTo}`;
  if (syncedKey !== appliedKey) {
    setSyncedKey(appliedKey);
    setFromDraft(appliedFrom);
    setToDraft(appliedTo);
    setErr(null);
  }

  // Close on outside click / Escape while open.
  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

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
    setOpen(false);
  }

  function clear() {
    setFromDraft("");
    setToDraft("");
    setErr(null);
    onClear();
    setOpen(false);
  }

  const hasApplied = from != null && to != null;
  const label = hasApplied ? `Dias ${from}–${to}` : "Filtrar por dia";

  return (
    <div className="day-range" ref={rootRef}>
      <div className={`day-range-trigger${hasApplied ? " is-active" : ""}`}>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          disabled={busy}
        >
          <span className="day-range-icon" aria-hidden="true">◔</span>
          {label}
        </button>
        {hasApplied ? (
          <button
            type="button"
            className="day-range-clear"
            onClick={clear}
            aria-label="Limpar filtro de dias"
            disabled={busy}
          >
            ×
          </button>
        ) : null}
      </div>

      {open ? (
        <div className="day-range-pop" role="dialog" aria-label="Filtrar por dia">
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
                autoFocus
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
          </div>
          {err ? <div className="day-range-err">{err}</div> : null}
          <div className="day-range-pop-actions">
            {hasApplied ? (
              <button className="btn btn-ghost btn-sm" onClick={clear} disabled={busy} type="button">
                Limpar
              </button>
            ) : null}
            <button className="btn btn-primary btn-sm" onClick={apply} disabled={busy} type="button">
              {busy ? "Aplicando…" : "Aplicar"}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
