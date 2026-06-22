import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/useAuth";
import { apiFetch } from "../lib/api";
import type { ClientSummary } from "../lib/types";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [clients, setClients] = useState<ClientSummary[]>([]);

  useEffect(() => {
    let ignore = false;
    if (user?.role === "ADMIN") {
      apiFetch<ClientSummary[]>("/api/clients")
        .then((cs) => !ignore && setClients(cs))
        .catch(() => !ignore && setClients([]));
    }
    return () => {
      ignore = true;
    };
  }, [user?.role]);

  // Current client id from /clientes/:id, if any.
  const match = location.pathname.match(/^\/clientes\/([^/]+)/);
  const currentClient = match ? match[1] : "";

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-left">
          <Link to="/" className="brand-link">
            <span className="brand">RUMO</span>
            <span className="brand-sub">Fechamento Mensal</span>
          </Link>

          {user?.role === "ADMIN" ? (
            <nav className="topnav">
              <Link
                to="/clientes"
                className={`topnav-link${location.pathname === "/clientes" ? " active" : ""}`}
              >
                Clientes
              </Link>
              <select
                className="client-switcher"
                value={currentClient}
                onChange={(e) => e.target.value && navigate(`/clientes/${e.target.value}`)}
                aria-label="Ir para um cliente"
              >
                <option value="">Ir para cliente…</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </nav>
          ) : null}
        </div>

        <div className="topbar-right">
          <span className="topbar-user" title={user?.email}>
            {user?.email}
          </span>
          <button className="btn btn-ghost btn-sm" onClick={logout}>
            Sair
          </button>
        </div>
      </header>
      <main className="content">{children}</main>
    </div>
  );
}
