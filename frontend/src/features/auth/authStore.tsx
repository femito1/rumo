// frontend/src/features/auth/authStore.tsx
import { useEffect, useState, type ReactNode } from "react";
import { apiFetch, getToken, setToken } from "../../lib/api";
import type { AuthUser } from "../../lib/types";
import { Ctx, type Status } from "./useAuth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<Status>(() =>
    getToken() ? "loading" : "unauthenticated",
  );

  useEffect(() => {
    if (!getToken()) return;
    let ignore = false;
    apiFetch<AuthUser>("/api/auth/me")
      .then((u) => {
        if (ignore) return;
        setUser(u);
        setStatus("authenticated");
      })
      .catch(() => {
        if (ignore) return;
        setToken(null);
        setStatus("unauthenticated");
      });
    return () => {
      ignore = true;
    };
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
