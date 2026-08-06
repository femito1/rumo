// frontend/src/features/auth/useAuth.ts
import { createContext, useContext } from "react";
import type { AuthUser } from "../../lib/types";

export type Status = "loading" | "authenticated" | "unauthenticated";

export interface AuthCtx {
  user: AuthUser | null;
  status: Status;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  /** Re-read the session. Used after a password change so `must_change_password`
   *  clears without forcing the user to log in again. */
  refresh: () => Promise<void>;
}

export const Ctx = createContext<AuthCtx | null>(null);

export function useAuth(): AuthCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}
