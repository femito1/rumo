// frontend/src/app/guards.tsx
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../features/auth/useAuth";
import { AppShell } from "./AppShell";

export function RequireAuth() {
  const { status } = useAuth();
  if (status === "loading") return <div className="page-loading">Carregando…</div>;
  if (status === "unauthenticated") return <Navigate to="/login" replace />;
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
