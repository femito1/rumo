// frontend/src/features/auth/authStore.tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiFetch, getToken, setToken } from "../../lib/api";
import type { AuthUser } from "../../lib/types";

type Status = "loading" | "authenticated" | "unauthenticated";

interface AuthCtx {
  user: AuthUser | null;
  status: Status;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    if (!getToken()) { setStatus("unauthenticated"); return; }
    apiFetch<AuthUser>("/api/auth/me")
      .then((u) => { setUser(u); setStatus("authenticated"); })
      .catch(() => { setToken(null); setStatus("unauthenticated"); });
  }, []);

  async function login(email: string, password: string) {
    const res = await apiFetch<{ access_token: string; user: AuthUser }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(res.access_token);
    setUser(res.user);
    setStatus("authenticated");
  }

  function logout() {
    setToken(null);
    setUser(null);
    setStatus("unauthenticated");
  }

  return <Ctx.Provider value={{ user, status, login, logout }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}
