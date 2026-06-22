// frontend/src/features/closing/useClosing.ts
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { ClosingPayload } from "../../lib/types";

export function useClosing(clientId: string, month: string, from: number | null, to: number | null) {
  const [data, setData] = useState<ClosingPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const requestKey = `${clientId}|${month}|${from}|${to}`;
  const [prevKey, setPrevKey] = useState(requestKey);
  if (prevKey !== requestKey) {
    // Inputs changed: reset to a loading state during render (not in an effect)
    // so consumers show the skeleton again instead of stale data.
    setPrevKey(requestKey);
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    let ignore = false;
    const q = new URLSearchParams({ month });
    if (from && to) { q.set("from", String(from)); q.set("to", String(to)); }
    apiFetch<ClosingPayload>(`/api/clients/${clientId}/closing?${q.toString()}`)
      .then((d) => {
        if (ignore) return;
        setData(d);
        setError(null);
        setLoading(false);
      })
      .catch((e) => {
        if (ignore) return;
        setError((e as { detail?: string }).detail ?? "Erro ao carregar fechamento");
        setLoading(false);
      });
    return () => { ignore = true; };
  }, [clientId, month, from, to]);
  return { data, error, loading };
}
