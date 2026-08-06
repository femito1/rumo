// frontend/src/features/users/UsuariosPage.tsx
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useAuth } from "../auth/useAuth";
import { useUsers, type CreatedUser } from "./useUsers";
import { Skeleton } from "../../components/Skeleton";
import type { ClientSummary, Role } from "../../lib/types";

/** PT-BR labels for the roles a manager can see. "Gestor" is the client-side manager
 *  (CLIENT_ADMIN) — deliberately not "Administrador", which would read as RUMO. */
const ROLE_LABEL: Record<string, string> = {
  ADMIN: "RUMO",
  CLIENT_ADMIN: "Gestor",
  CLIENT: "Cliente",
};

/**
 * User provisioning. RUMO picks the client and the role; a Gestor manages only its
 * own client's ordinary users, so it gets neither selector — offering them would just
 * render a request the API refuses.
 *
 * A created user's password is generated server-side and shown ONCE (there is no
 * e-mail delivery), so the reveal is deliberately hard to miss and hard to lose.
 */
export function UsuariosPage() {
  const { user } = useAuth();
  const isRumo = user?.role === "ADMIN";

  // RUMO chooses among clients; a Gestor is pinned to its own.
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [clientId, setClientId] = useState<string>(user?.client_id ?? "");

  useEffect(() => {
    if (!isRumo) return;
    let ignore = false;
    apiFetch<ClientSummary[]>("/api/clients")
      .then((cs) => {
        if (ignore) return;
        setClients(cs);
        setClientId((cur) => cur || cs[0]?.id || "");
      })
      .catch(() => !ignore && setClients([]));
    return () => {
      ignore = true;
    };
  }, [isRumo]);

  const { users, error, createUser, setActive, resetPassword } = useUsers(clientId);

  const [formOpen, setFormOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("CLIENT");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [revealed, setRevealed] = useState<CreatedUser | null>(null);
  const [copied, setCopied] = useState(false);

  async function onCreate() {
    setBusy(true);
    setFormError(null);
    try {
      const created = await createUser(email.trim(), role);
      setRevealed(created);
      setCopied(false);
      setFormOpen(false);
      setEmail("");
      setRole("CLIENT");
    } catch (e) {
      setFormError((e as { detail?: string }).detail ?? "Não foi possível criar o usuário");
    } finally {
      setBusy(false);
    }
  }

  async function onToggleActive(id: string, active: boolean) {
    setFormError(null);
    try {
      await setActive(id, active);
    } catch (e) {
      setFormError((e as { detail?: string }).detail ?? "Não foi possível alterar o usuário");
    }
  }

  async function onReset(id: string) {
    setFormError(null);
    try {
      setRevealed(await resetPassword(id));
      setCopied(false);
    } catch (e) {
      setFormError((e as { detail?: string }).detail ?? "Não foi possível gerar uma nova senha");
    }
  }

  function copy(text: string) {
    navigator.clipboard?.writeText(text);
    setCopied(true);
  }

  return (
    <div className="clients-page">
      <header className="page-head">
        <h1>Usuários</h1>
        {users ? <span className="muted">{users.length} no total</span> : null}
      </header>

      <div className="toolbar-actions users-toolbar">
        {isRumo ? (
          <label className="users-client-pick">
            Cliente
            <select value={clientId} onChange={(e) => setClientId(e.target.value)}>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </label>
        ) : null}
        <button type="button" className="btn btn-primary btn-sm" onClick={() => setFormOpen((o) => !o)}>
          Novo usuário
        </button>
      </div>

      {/* The one-time password reveal. Kept on the page (not in a dismissable
          overlay) so it cannot be lost by a stray click before it is copied. */}
      {revealed ? (
        <div className="temp-password-card" role="status">
          <div className="temp-password-head">
            Usuário <strong>{revealed.email}</strong> criado
          </div>
          <div className="temp-password-row">
            <code className="temp-password-value">{revealed.temp_password}</code>
            <button type="button" className="btn btn-sm" onClick={() => copy(revealed.temp_password)}>
              {copied ? "Copiado!" : "Copiar"}
            </button>
          </div>
          <p className="temp-password-note">
            ⚠ Esta senha aparece apenas uma vez. Envie-a ao usuário — ele terá de
            trocá-la no primeiro acesso.
          </p>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setRevealed(null)}>
            Já enviei
          </button>
        </div>
      ) : null}

      {formOpen ? (
        <div className="budget-panel users-form">
          <label htmlFor="novo-email">E-mail</label>
          <input
            id="novo-email"
            type="email"
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          {isRumo ? (
            <>
              <label htmlFor="novo-papel">Papel</label>
              <select id="novo-papel" value={role} onChange={(e) => setRole(e.target.value as Role)}>
                <option value="CLIENT">Cliente — apenas visualiza o fechamento</option>
                <option value="CLIENT_ADMIN">Gestor — também cria usuários do cliente</option>
              </select>
            </>
          ) : null}
          <div className="users-form-actions">
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setFormOpen(false)}>
              Cancelar
            </button>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              disabled={busy || !email.trim()}
              onClick={onCreate}
            >
              {busy ? "Criando…" : "Criar"}
            </button>
          </div>
        </div>
      ) : null}

      {formError ? <div className="form-error" role="alert">{formError}</div> : null}
      {error ? <div className="error-state" role="alert">{error}</div> : null}

      {!users && !error ? <Skeleton rows={4} /> : null}

      {users ? (
        <table className="grid-table users-table">
          <thead>
            <tr>
              <th>E-mail</th>
              <th>Papel</th>
              <th>Situação</th>
              <th aria-label="Ações" />
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className={u.active ? "" : "row-inactive"}>
                <td>{u.email}</td>
                <td>{ROLE_LABEL[u.role] ?? u.role}</td>
                <td>
                  {u.active ? "Ativo" : "Inativo"}
                  {u.must_change_password ? (
                    <span className="muted"> · senha provisória</span>
                  ) : null}
                </td>
                <td className="users-row-actions">
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => onReset(u.id)}>
                    Nova senha
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => onToggleActive(u.id, !u.active)}
                  >
                    {u.active ? "Desativar" : "Reativar"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}
