// frontend/src/features/closing/ManualActualsEditor.tsx
import { useState } from "react";
import { useManualActuals, type ManualEntry } from "./useManualActuals";

/** Per-area manual Realizado editor (ADMIN + CLIENT). The prime use is per-area
 *  Recebimento, which the workbook assigns by hand (case-by-area + transfers)
 *  and SISJURI cannot derive. One input per area x line. Collapsed by default. */
export function ManualActualsEditor({
  clientId,
  anoMes,
}: {
  clientId: string;
  anoMes: string;
}) {
  const { data, loading, error, save } = useManualActuals(clientId, anoMes);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveErr, setSaveErr] = useState<string | null>(null);
  const [syncedFor, setSyncedFor] = useState<string | null>(null);

  const cellKey = (area: string, line: string) => `${area}::${line}`;

  const payloadKey = data
    ? `${data.client_id}|${data.ano_mes}|${data.entries.length}`
    : null;
  if (data && payloadKey && syncedFor !== payloadKey) {
    setSyncedFor(payloadKey);
    const seeded: Record<string, string> = {};
    for (const area of data.areas) {
      for (const line of data.lines) {
        const found = data.entries.find(
          (e) => e.area === area && e.line_key === line.key,
        );
        seeded[cellKey(area, line.key)] = found ? String(found.valor) : "";
      }
    }
    setDraft(seeded);
  }

  async function onSave() {
    if (!data) return;
    setSaving(true);
    setSaveErr(null);
    const entries: ManualEntry[] = [];
    for (const area of data.areas) {
      for (const line of data.lines) {
        const raw = Number.parseFloat(draft[cellKey(area, line.key)] ?? "");
        if (Number.isFinite(raw) && raw !== 0) {
          entries.push({ area, line_key: line.key, valor: raw });
        }
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
        {open ? "Fechar lançamentos por área" : "Lançar recebimento por área"}
      </button>
      {open ? (
        <div className="budget-panel">
          {loading ? (
            <div className="loading-block">
              <div className="spinner" aria-label="Carregando" />
              <span className="muted">Carregando lançamentos…</span>
            </div>
          ) : error ? (
            <div className="error-state" role="alert">{error}</div>
          ) : data ? (
            <>
              <p className="muted">
                Recebimento e despesas por área (Contencioso/Econômico/Arbitragem)
                para {data.ano_mes}. Estes valores não vêm do SISJURI — são a
                classificação manual por área (como na aba Resumo_Recebidas).
              </p>
              <div className="manual-grid">
                <table className="grid-table">
                  <thead>
                    <tr>
                      <th>Área</th>
                      {data.lines.map((l) => (
                        <th key={l.key} className="num">{l.label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.areas.map((area) => (
                      <tr key={area}>
                        <td>{area}</td>
                        {data.lines.map((line) => (
                          <td key={line.key} className="num">
                            <input
                              type="number"
                              inputMode="decimal"
                              step="0.01"
                              value={draft[cellKey(area, line.key)] ?? ""}
                              placeholder="0,00"
                              onChange={(ev) =>
                                setDraft((d) => ({
                                  ...d,
                                  [cellKey(area, line.key)]: ev.target.value,
                                }))
                              }
                            />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {saveErr ? <div className="error-state" role="alert">{saveErr}</div> : null}
              <div className="budget-actions">
                <button
                  type="button"
                  className="btn btn-sm"
                  disabled={saving}
                  onClick={onSave}
                >
                  {saving ? "Salvando…" : "Salvar lançamentos"}
                </button>
              </div>
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
