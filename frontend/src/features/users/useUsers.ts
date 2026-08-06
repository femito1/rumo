// frontend/src/features/users/useUsers.ts
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { Role } from "../../lib/types";

export interface ManagedUser {
  id: string;
  email: string;
  role: Role;
  client_id: string | null;
  active: boolean;
  must_change_password: boolean;
}

/** A created user, plus the generated password. The password is present ONLY in the
 *  creation response — it is never stored and never returned again. */
export interface CreatedUser extends ManagedUser {
  temp_password: string;
}

/** Load + mutate one client's users. In its own module to satisfy
 *  react-refresh/only-export-components (same shape as useBudget). */
export function useUsers(clientId: string) {
  const [users, setUsers] = useState<ManagedUser[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadAt, setReloadAt] = useState(0);

  // Reset the list when the target client changes, so the previous client's people
  // are never shown under the new one's heading (render-phase sync, not an effect).
  const key = `${clientId}|${reloadAt}`;
  const [syncedKey, setSyncedKey] = useState<string | null>(null);
  if (syncedKey !== key) {
    setSyncedKey(key);
    setUsers(null);
    setError(null);
  }

  useEffect(() => {
    if (!clientId) return;
    let ignore = false;
    apiFetch<ManagedUser[]>(`/api/clients/${clientId}/users`)
      .then((u) => !ignore && setUsers(u))
      .catch(
        (e) =>
          !ignore &&
          setError((e as { detail?: string }).detail ?? "Erro ao carregar usuários"),
      );
    return () => {
      ignore = true;
    };
  }, [clientId, reloadAt]);

  async function createUser(email: string, role: Role): Promise<CreatedUser> {
    const created = await apiFetch<CreatedUser>(`/api/clients/${clientId}/users`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    });
    setReloadAt((n) => n + 1);
    return created;
  }

  async function setActive(userId: string, active: boolean): Promise<void> {
    await apiFetch<ManagedUser>(`/api/clients/${clientId}/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify({ active }),
    });
    setReloadAt((n) => n + 1);
  }

  async function resetPassword(userId: string): Promise<CreatedUser> {
    const reset = await apiFetch<CreatedUser>(
      `/api/clients/${clientId}/users/${userId}/reset-password`,
      { method: "POST" },
    );
    setReloadAt((n) => n + 1);
    return reset;
  }

  return { users, error, createUser, setActive, resetPassword };
}
