// frontend/src/features/closing/useManualActuals.ts
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";

export interface ManualLine {
  key: string;
  label: string;
}

export interface ManualEntry {
  area: string;
  line_key: string;
  valor: number;
}

export interface ManualPayload {
  client_id: string;
  ano_mes: string;
  areas: string[];
  lines: ManualLine[];
  entries: ManualEntry[];
}

/** Load + persist per-area manual Realizado inputs (per-area Recebimento etc.)
 *  for a client/competence month. Own module for react-refresh compliance. */
export function useManualActuals(clientId: string, anoMes: string | null) {
  const [data, setData] = useState<ManualPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number>(0);

  const key = `${clientId}|${anoMes}|${savedAt}`;
  const [prevKey, setPrevKey] = useState<string | null>(null);
  if (anoMes != null && prevKey !== key) {
    setPrevKey(key);
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    if (anoMes == null) return;
    let ignore = false;
    apiFetch<ManualPayload>(`/api/clients/${clientId}/manual?ano_mes=${anoMes}`)
      .then((d) => {
        if (ignore) return;
        setData(d);
        setLoading(false);
      })
      .catch((e) => {
        if (ignore) return;
        setError((e as { detail?: string }).detail ?? "Erro ao carregar lançamentos");
        setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [clientId, anoMes, savedAt]);

  async function save(entries: ManualEntry[]): Promise<void> {
    if (anoMes == null) return;
    await apiFetch(`/api/clients/${clientId}/manual?ano_mes=${anoMes}`, {
      method: "PUT",
      body: JSON.stringify({ entries }),
    });
    setSavedAt(Date.now());
  }

  return { data, loading, error, save };
}
