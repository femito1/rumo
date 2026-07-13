// frontend/src/features/closing/BudgetEditor.tsx
import { useState } from "react";
import { useBudget, type BudgetEntry } from "./useBudget";
import { formatBRL } from "../../lib/format";

const INSTITUCIONAL = "institucional";
/** POINT 13: "Orçamento Despesa" (Despesas Equipe budget) is entered per team. */
const DESPESAS_EQUIPE = "despesas_equipe";
const AREAS = ["Contencioso", "Econômico", "Arbitragem"] as const;

/** Annual Orcado editor (ADMIN + CLIENT). One input per institucional DRE line
 *  (the backend splits annual/12 for the monthly variance) plus a per-area
 *  "Orçamento Despesa" (Despesas Equipe) section for the three cost centers.
 *  Collapsed by default. */
export function BudgetEditor({ clientId, ano }: { clientId: string; ano: number }) {
  const { data, loading, error, save } = useBudget(clientId, ano);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [areaDraft, setAreaDraft] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveErr, setSaveErr] = useState<string | null>(null);
  const [syncedFor, setSyncedFor] = useState<string | null>(null);

  // Institucional lines only; Despesas Equipe is budgeted per area below.
  const instLines = (data?.lines ?? []).filter((l) => l.key !== DESPESAS_EQUIPE);

  // Seed the draft from loaded entries once per payload (render-phase sync).
  const payloadKey = data ? `${data.client_id}|${data.ano}|${data.entries.length}` : null;
  if (data && payloadKey && syncedFor !== payloadKey) {
    setSyncedFor(payloadKey);
    const seeded: Record<string, string> = {};
    for (const line of instLines) {
      const found = data.entries.find(
        (e) => e.area === INSTITUCIONAL && e.line_key === line.key,
      );
      seeded[line.key] = found ? String(found.annual_amount) : "";
    }
    setDraft(seeded);
    const areaSeeded: Record<string, string> = {};
    for (const area of AREAS) {
      const found = data.entries.find(
        (e) => e.area === area && e.line_key === DESPESAS_EQUIPE,
      );
      areaSeeded[area] = found ? String(found.annual_amount) : "";
    }
    setAreaDraft(areaSeeded);
  }

  async function onSave() {
    if (!data) return;
    setSaving(true);
    setSaveErr(null);
    const entries: BudgetEntry[] = instLines
      .map((line) => ({
        area: INSTITUCIONAL,
        line_key: line.key,
        annual_amount: Number.parseFloat(draft[line.key] ?? "") || 0,
      }))
      .filter((e) => e.annual_amount !== 0);
    for (const area of AREAS) {
      const amount = Number.parseFloat(areaDraft[area] ?? "") || 0;
      if (amount !== 0) {
        entries.push({ area, line_key: DESPESAS_EQUIPE, annual_amount: amount });
      }
    }
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
        {open ? "Fechar orçamento" : `Orçamento ${ano}`}
      </button>
      {open ? (
        <div className="budget-panel popover-panel">
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
                {instLines.map((line) => {
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

              <p className="muted budget-section-title">
                Orçamento Despesa por equipe (valor anual)
              </p>
              <div className="budget-grid">
                {AREAS.map((area) => {
                  const raw = Number.parseFloat(areaDraft[area] ?? "");
                  const monthly = Number.isFinite(raw) ? raw / 12 : null;
                  return (
                    <label key={area} className="budget-row">
                      <span className="budget-line-label">{area}</span>
                      <input
                        type="number"
                        inputMode="decimal"
                        step="0.01"
                        aria-label={`Orçamento Despesa ${area}`}
                        value={areaDraft[area] ?? ""}
                        placeholder="0,00"
                        onChange={(ev) =>
                          setAreaDraft((d) => ({ ...d, [area]: ev.target.value }))
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
