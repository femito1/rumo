// frontend/src/app/guards.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { RequireAuth, RequireAdmin, RequireUserManager, HomeRedirect } from "./guards";
import * as authStore from "../features/auth/useAuth";

function mockAuth(status: string, role: string | null, extra: object = {}) {
  vi.spyOn(authStore, "useAuth").mockReturnValue({
    // Every non-ADMIN role belongs to a client. Keying this on `=== "CLIENT"` would
    // give a CLIENT_ADMIN `client_id: null`, and its redirect assertions would then
    // pass against "/clientes/null" — green for the wrong reason.
    user: role
      ? ({ id: "u", email: "a@b", role, client_id: role === "ADMIN" ? null : "mbc", ...extra } as never)
      : null,
    status: status as never, login: vi.fn(), logout: vi.fn(), refresh: vi.fn(),
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

  it("HomeRedirect sends ADMIN to /clientes", () => {
    mockAuth("authenticated", "ADMIN");
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/clientes" element={<div>CLIENTES</div>} />
          <Route path="/clientes/:id" element={<div>WORKSPACE</div>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("CLIENTES")).toBeInTheDocument();
  });

  it("HomeRedirect sends a CLIENT straight to its own workspace (not the admin list)", () => {
    mockAuth("authenticated", "CLIENT");
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/clientes" element={<div>CLIENTES</div>} />
          <Route path="/clientes/:id" element={<div>WORKSPACE</div>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("WORKSPACE")).toBeInTheDocument();
  });

  it("RequireAdmin bounces a CLIENT_ADMIN — /clientes lists every tenant", () => {
    // A Gestor manages its own client's logins; it is not RUMO staff, so the
    // cross-tenant client list stays closed to it (the API 403s it too).
    mockAuth("authenticated", "CLIENT_ADMIN");
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

  it.each(["ADMIN", "CLIENT_ADMIN"])("RequireUserManager admits %s", (role) => {
    mockAuth("authenticated", role);
    render(
      <MemoryRouter initialEntries={["/usuarios"]}>
        <Routes>
          <Route path="/clientes/:id" element={<div>WORKSPACE</div>} />
          <Route element={<RequireUserManager />}>
            <Route path="/usuarios" element={<div>USUARIOS</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("USUARIOS")).toBeInTheDocument();
  });

  it("RequireAuth forces a provisional password to be changed, from any route", () => {
    // A user created (or reset) by an admin carries a password a third party knows.
    // Gated in RequireAuth so no route can be deep-linked around it.
    mockAuth("authenticated", "CLIENT", { must_change_password: true });
    render(
      <MemoryRouter initialEntries={["/clientes/mbc"]}>
        <Routes>
          <Route path="/trocar-senha" element={<div>TROCAR</div>} />
          <Route element={<RequireAuth />}>
            <Route path="/clientes/:id" element={<div>WORKSPACE</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("TROCAR")).toBeInTheDocument();
  });

  it("RequireAuth does not trap the user on the change-password route itself", () => {
    mockAuth("authenticated", "CLIENT", { must_change_password: true });
    render(
      <MemoryRouter initialEntries={["/trocar-senha"]}>
        <Routes>
          <Route element={<RequireAuth />}>
            <Route path="/trocar-senha" element={<div>TROCAR</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("TROCAR")).toBeInTheDocument();
  });

  it("RequireUserManager bounces a plain CLIENT", () => {
    mockAuth("authenticated", "CLIENT");
    render(
      <MemoryRouter initialEntries={["/usuarios"]}>
        <Routes>
          <Route path="/clientes/:id" element={<div>WORKSPACE</div>} />
          <Route element={<RequireUserManager />}>
            <Route path="/usuarios" element={<div>USUARIOS</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("WORKSPACE")).toBeInTheDocument();
  });
});
