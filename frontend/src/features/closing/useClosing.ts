// frontend/src/features/closing/useClosing.ts
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { ClosingPayload } from "../../lib/types";

export function useClosing(clientId: string, month: string, from: number | null, to: number | null) {
  const [data, setData] = useState<ClosingPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setLoading(true);
    setError(null);
    const q = new URLSearchParams({ month });
    if (from && to) { q.set("from", String(from)); q.set("to", String(to)); }
    apiFetch<ClosingPayload>(`/api/clients/${clientId}/closing?${q.toString()}`)
      .then(setData)
      .catch((e) => setError((e as { detail?: string }).detail ?? "Erro ao carregar fechamento"))
      .finally(() => setLoading(false));
  }, [clientId, month, from, to]);
  return { data, error, loading };
}
