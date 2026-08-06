// frontend/src/app/guards.tsx
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../features/auth/useAuth";
import { AppShell } from "./AppShell";

export function RequireAuth() {
  const { status, user } = useAuth();
  const location = useLocation();
  if (status === "loading") return <div className="page-loading">Carregando…</div>;
  if (status === "unauthenticated") return <Navigate to="/login" replace />;
  // A password someone else chose (created or reset by an admin) must be replaced
  // before anything else is reachable. Gated here so no route can be deep-linked
  // around it; the exemption is the change-password screen itself.
  if (user?.must_change_password && location.pathname !== "/trocar-senha")
    return <Navigate to="/trocar-senha" replace />;
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

export function RequireAdmin() {
  const { status, user } = useAuth();
  if (status === "loading") return <div className="page-loading">Carregando…</div>;
  if (status === "unauthenticated") return <Navigate to="/login" replace />;
  if (user?.role !== "ADMIN") return <Navigate to={`/clientes/${user?.client_id}`} replace />;
  return <Outlet />;
}

/** Routes that manage logins: RUMO staff, or a client's own Gestor (who is scoped
 *  to its own client server-side). Separate from `RequireAdmin` because that gate
 *  guards cross-tenant surfaces like the client list. */
export function RequireUserManager() {
  const { status, user } = useAuth();
  if (status === "loading") return <div className="page-loading">Carregando…</div>;
  if (status === "unauthenticated") return <Navigate to="/login" replace />;
  if (user?.role !== "ADMIN" && user?.role !== "CLIENT_ADMIN")
    return <Navigate to={`/clientes/${user?.client_id}`} replace />;
  return <Outlet />;
}

/** Landing route: send each role to the right home. */
export function HomeRedirect() {
  const { status, user } = useAuth();
  if (status === "loading") return <div className="page-loading">Carregando…</div>;
  if (status === "unauthenticated" || !user) return <Navigate to="/login" replace />;
  if (user.role === "ADMIN") return <Navigate to="/clientes" replace />;
  return <Navigate to={`/clientes/${user.client_id}`} replace />;
}
