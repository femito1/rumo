// frontend/src/features/auth/LoginPage.tsx
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./useAuth";
import rumoLogo from "../../assets/rumo-logo.png";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError((err as { detail?: string }).detail ?? "Não foi possível entrar");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={onSubmit}>
        {/* The logo carries the brand visually; the h1 stays for screen readers and
            document outline (visually hidden, not removed). */}
        <img className="login-logo" src={rumoLogo} alt="" aria-hidden="true" />
        <h1 className="visually-hidden">RUMO</h1>
        <p className="muted">Plataforma de Fechamento Mensal</p>
        <label htmlFor="email">E-mail</label>
        <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoFocus />
        <label htmlFor="senha">Senha</label>
        <input id="senha" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error ? <div className="form-error" role="alert">{error}</div> : null}
        <button className="btn btn-primary" disabled={busy} type="submit">{busy ? "Entrando…" : "Entrar"}</button>
      </form>
    </div>
  );
}
