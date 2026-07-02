// frontend/src/features/closing/BudgetEditor.tsx
import { useState } from "react";
import { useBudget, type BudgetEntry } from "./useBudget";
import { formatBRL } from "../../lib/format";

const AREA = "institucional";

/** Annual Orcado editor (ADMIN + CLIENT). One input per DRE line; the backend
 *  splits annual/12 for the monthly variance. Collapsed by default. */
export function BudgetEditor({ clientId, ano }: { clientId: string; ano: number }) {
  const { data, loading, error, save } = useBudget(clientId, ano);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveErr, setSaveErr] = useState<string | null>(null);
  const [syncedFor, setSyncedFor] = useState<string | null>(null);

  // Seed the draft from loaded entries once per payload (render-phase sync).
  const payloadKey = data ? `${data.client_id}|${data.ano}|${data.entries.length}` : null;
  if (data && payloadKey && syncedFor !== payloadKey) {
    setSyncedFor(payloadKey);
    const seeded: Record<string, string> = {};
    for (const line of data.lines) {
      const found = data.entries.find(
        (e) => e.area === AREA && e.line_key === line.key,
      );
      seeded[line.key] = found ? String(found.annual_amount) : "";
    }
    setDraft(seeded);
  }

  async function onSave() {
    if (!data) return;
    setSaving(true);
    setSaveErr(null);
    const entries: BudgetEntry[] = data.lines
      .map((line) => ({
        area: AREA,
        line_key: line.key,
        annual_amount: Number.parseFloat(draft[line.key] ?? "") || 0,
      }))
      .filter((e) => e.annual_amount !== 0);
    try {
      await save(entries);
    } catch (e) {
      setSaveErr((e as { detail?: string }).detail ?? "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="budget-editor">
      <button
        type="button"
        className="btn btn-ghost btn-sm"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        {open ? "Fechar orçamento" : `Editar orçamento ${ano}`}
      </button>
      {open ? (
        <div className="budget-panel">
          {loading ? (
            <div className="loading-block">
              <div className="spinner" aria-label="Carregando" />
              <span className="muted">Carregando orçamento…</span>
            </div>
          ) : error ? (
            <div className="error-state" role="alert">{error}</div>
          ) : data ? (
            <>
              <p className="muted">
                Valor anual por linha (o sistema divide por 12 para o mês).
              </p>
              <div className="budget-grid">
                {data.lines.map((line) => {
                  const raw = Number.parseFloat(draft[line.key] ?? "");
                  const monthly = Number.isFinite(raw) ? raw / 12 : null;
                  return (
                    <label key={line.key} className="budget-row">
                      <span className="budget-line-label">{line.label}</span>
                      <input
                        type="number"
                        inputMode="decimal"
                        step="0.01"
                        value={draft[line.key] ?? ""}
                        placeholder="0,00"
                        onChange={(ev) =>
                          setDraft((d) => ({ ...d, [line.key]: ev.target.value }))
                        }
                      />
                      <span className="budget-monthly muted">
                        {monthly != null ? `${formatBRL(monthly)}/mês` : ""}
                      </span>
                    </label>
                  );
                })}
              </div>
              {saveErr ? <div className="error-state" role="alert">{saveErr}</div> : null}
              <div className="budget-actions">
                <button
                  type="button"
                  className="btn btn-sm"
                  disabled={saving}
                  onClick={onSave}
                >
                  {saving ? "Salvando…" : "Salvar orçamento"}
                </button>
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
