// frontend/src/features/clients/ClientsPage.tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../../lib/api";
import type { ClientSummary } from "../../lib/types";
import { Skeleton } from "../../components/Skeleton";

export function ClientsPage() {
  const [clients, setClients] = useState<ClientSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<ClientSummary[]>("/api/clients")
      .then(setClients)
      .catch((e) => setError((e as { detail?: string }).detail ?? "Erro ao carregar clientes"));
  }, []);

  if (error) return <div className="error-state" role="alert">{error}</div>;
  if (!clients) return <div className="clients-page"><Skeleton rows={4} /></div>;

  return (
    <div className="clients-page">
      <header className="page-head"><h1>Clientes</h1><span className="muted">{clients.length} ativos</span></header>
      <div className="client-cards">
        {clients.map((c) => (
          <Link key={c.id} to={`/clientes/${c.id}`} className="client-card">
            <div className="client-card-name">{c.name}</div>
            <div className="client-card-open">Abrir →</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
