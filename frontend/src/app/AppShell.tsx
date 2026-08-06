import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/useAuth";
import { apiFetch } from "../lib/api";
import rumoLogo from "../assets/rumo-logo.png";
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
            <img className="brand-logo" src={rumoLogo} alt="RUMO Gestão de Negócios" />
            <span className="brand-sub">Fechamento Mensal</span>
          </Link>

          {/* Usuários is reachable by RUMO and by a client's Gestor; the Clientes
              list and the client switcher stay RUMO-only. */}
          {user?.role === "ADMIN" || user?.role === "CLIENT_ADMIN" ? (
            <nav className="topnav">
              <Link
                to="/usuarios"
                className={`topnav-link${location.pathname === "/usuarios" ? " active" : ""}`}
              >
                Usuários
              </Link>
            </nav>
          ) : null}

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
