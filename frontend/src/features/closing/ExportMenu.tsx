// frontend/src/features/closing/ExportMenu.tsx
import { useEffect, useRef, useState } from "react";

/**
 * Export split-menu: one compact button opens a small menu with the two export
 * scopes, so exporting takes one toolbar slot instead of two loose buttons.
 */
export function ExportMenu({
  disabled,
  onExportAll,
  onExportPage,
  pageEnabled,
}: {
  disabled: boolean;
  onExportAll: () => void;
  onExportPage: () => void;
  pageEnabled: boolean;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
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

  return (
    <div className="export-menu" ref={ref}>
      <button
        type="button"
        className="btn btn-ghost btn-sm"
        disabled={disabled}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((o) => !o)}
      >
        <span aria-hidden="true">↓</span>
        Exportar
        <span className="export-caret" aria-hidden="true">▾</span>
      </button>
      {open ? (
        <div className="export-menu-pop" role="menu">
          <button
            type="button"
            role="menuitem"
            className="export-menu-item"
            onClick={() => {
              onExportAll();
              setOpen(false);
            }}
          >
            Exportar tudo
          </button>
          <button
            type="button"
            role="menuitem"
            className="export-menu-item"
            disabled={!pageEnabled}
            onClick={() => {
              onExportPage();
              setOpen(false);
            }}
          >
            Exportar página atual
          </button>
        </div>
      ) : null}
    </div>
  );
}
