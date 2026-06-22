// frontend/src/features/auth/authStore.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { AuthProvider } from "./authStore";
import { useAuth } from "./useAuth";
import * as api from "../../lib/api";

function Probe() {
  const { user, status } = useAuth();
  return <div>{status}:{user?.role ?? "none"}</div>;
}

beforeEach(() => { localStorage.clear(); vi.restoreAllMocks(); });

describe("AuthProvider", () => {
  it("is unauthenticated when no token", async () => {
    render(<AuthProvider><Probe /></AuthProvider>);
    await waitFor(() => expect(screen.getByText("unauthenticated:none")).toBeInTheDocument());
  });

  it("restores session from token via /auth/me", async () => {
    localStorage.setItem("rumo_token", "abc");
    vi.spyOn(api, "apiFetch").mockResolvedValue({ id: "u", email: "a@b", role: "ADMIN", client_id: null });
    render(<AuthProvider><Probe /></AuthProvider>);
    await waitFor(() => expect(screen.getByText("authenticated:ADMIN")).toBeInTheDocument());
  });
});
