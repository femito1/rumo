// frontend/src/features/auth/ChangePasswordPage.tsx
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../../lib/api";
import { useAuth } from "./useAuth";

/** Same floor the API enforces. Checked here too so a too-short password is refused
 *  before a round-trip, and the wording matches the server's message. */
const MIN_LEN = 8;

/**
 * Password change. Reached voluntarily, and forced when the account still carries a
 * password someone else chose — a user created through /usuarios gets a generated
 * one, and an admin reset issues another, so in both cases a third party knows it.
 */
export function ChangePasswordPage() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const forced = user?.must_change_password === true;

  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (next !== confirm) {
      setError("As senhas não conferem.");
      return;
    }
    if (next.length < MIN_LEN) {
      setError(`A nova senha precisa de ao menos ${MIN_LEN} caracteres.`);
      return;
    }
    setError(null);
    setBusy(true);
    try {
      await apiFetch("/api/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ current_password: current, new_password: next }),
      });
      // Re-read the session so `must_change_password` clears and the guard lets go.
      await refresh();
      navigate("/");
    } catch (err) {
      setError((err as { detail?: string }).detail ?? "Não foi possível alterar a senha");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={onSubmit}>
        <h1>Trocar senha</h1>
        {forced ? (
          <p className="muted">
            Sua senha provisória precisa ser trocada antes de continuar.
          </p>
        ) : (
          <p className="muted">Escolha uma nova senha para sua conta.</p>
        )}

        <label htmlFor="senha-atual">Senha atual</label>
        <input
          id="senha-atual"
          type="password"
          autoFocus
          autoComplete="current-password"
          value={current}
          onChange={(e) => setCurrent(e.target.value)}
        />

        <label htmlFor="senha-nova">Nova senha</label>
        <input
          id="senha-nova"
          type="password"
          autoComplete="new-password"
          value={next}
          onChange={(e) => setNext(e.target.value)}
        />

        <label htmlFor="senha-confirma">Confirmar nova senha</label>
        <input
          id="senha-confirma"
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
        />

        {error ? <div className="form-error" role="alert">{error}</div> : null}

        <button className="btn btn-primary" disabled={busy} type="submit">
          {busy ? "Alterando…" : "Alterar senha"}
        </button>
      </form>
    </div>
  );
}
