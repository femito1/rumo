// frontend/src/app/guards.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { RequireAuth, RequireAdmin } from "./guards";
import * as authStore from "../features/auth/authStore";

function mockAuth(status: string, role: string | null) {
  vi.spyOn(authStore, "useAuth").mockReturnValue({
    user: role ? ({ id: "u", email: "a@b", role, client_id: role === "CLIENT" ? "mbc" : null } as never) : null,
    status: status as never, login: vi.fn(), logout: vi.fn(),
  });
}

describe("guards", () => {
  it("RequireAuth redirects to /login when unauthenticated", () => {
    mockAuth("unauthenticated", null);
    render(
      <MemoryRouter initialEntries={["/clientes"]}>
        <Routes>
          <Route path="/login" element={<div>LOGIN</div>} />
          <Route element={<RequireAuth />}>
            <Route path="/clientes" element={<div>CLIENTES</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("LOGIN")).toBeInTheDocument();
  });

  it("RequireAdmin redirects a CLIENT to its own workspace", () => {
    mockAuth("authenticated", "CLIENT");
    render(
      <MemoryRouter initialEntries={["/clientes"]}>
        <Routes>
          <Route path="/clientes/:id" element={<div>WORKSPACE</div>} />
          <Route element={<RequireAdmin />}>
            <Route path="/clientes" element={<div>CLIENTES</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("WORKSPACE")).toBeInTheDocument();
  });
});
