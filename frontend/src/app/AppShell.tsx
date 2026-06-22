import { useAuth } from "../features/auth/useAuth";
export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">RUMO</div>
        <div className="sidebar-foot">
          <span className="muted">{user?.email}</span>
          <button className="btn btn-ghost" onClick={logout}>Sair</button>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
