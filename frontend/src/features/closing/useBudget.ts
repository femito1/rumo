// frontend/src/features/closing/useBudget.ts
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";

export interface BudgetLine {
  key: string;
  label: string;
}

export interface BudgetEntry {
  area: string;
  line_key: string;
  annual_amount: number;
}

export interface BudgetPayload {
  client_id: string;
  ano: number;
  areas: string[];
  lines: BudgetLine[];
  entries: BudgetEntry[];
}

/** Load + persist the annual Orcado for a client/year. Kept in its own module
 *  to satisfy react-refresh/only-export-components. */
export function useBudget(clientId: string, ano: number | null) {
  const [data, setData] = useState<BudgetPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number>(0);

  const key = `${clientId}|${ano}|${savedAt}`;
  const [prevKey, setPrevKey] = useState<string | null>(null);
  if (ano != null && prevKey !== key) {
    setPrevKey(key);
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    if (ano == null) return;
    let ignore = false;
    apiFetch<BudgetPayload>(`/api/clients/${clientId}/budget?ano=${ano}`)
      .then((d) => {
        if (ignore) return;
        setData(d);
        setLoading(false);
      })
      .catch((e) => {
        if (ignore) return;
        setError((e as { detail?: string }).detail ?? "Erro ao carregar orçamento");
        setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [clientId, ano, savedAt]);

  async function save(entries: BudgetEntry[]): Promise<void> {
    if (ano == null) return;
    await apiFetch(`/api/clients/${clientId}/budget?ano=${ano}`, {
      method: "PUT",
      body: JSON.stringify({ entries }),
    });
    setSavedAt(Date.now());
  }

  return { data, loading, error, save };
}
