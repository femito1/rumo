// frontend/src/features/users/UsuariosPage.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { UsuariosPage } from "./UsuariosPage";
import { Ctx, type AuthCtx } from "../auth/useAuth";
import type { AuthUser } from "../../lib/types";
import * as api from "../../lib/api";

const USERS = [
  { id: "u1", email: "financeiro@mbclaw.com.br", role: "CLIENT", client_id: "mbc", active: true, must_change_password: false },
  { id: "u2", email: "renata@mbclaw.com.br", role: "CLIENT_ADMIN", client_id: "mbc", active: true, must_change_password: false },
  { id: "u3", email: "saiu@mbclaw.com.br", role: "CLIENT", client_id: "mbc", active: false, must_change_password: false },
];

function renderAs(role: AuthUser["role"], clientId: string | null = "mbc") {
  const user: AuthUser = { id: "me", email: "me@x", role, client_id: clientId };
  const ctx: AuthCtx = { user, status: "authenticated", login: vi.fn(), logout: vi.fn(), refresh: vi.fn() };
  return render(
    <Ctx.Provider value={ctx}>
      <MemoryRouter><UsuariosPage /></MemoryRouter>
    </Ctx.Provider>,
  );
}

function mockApi(users = USERS) {
  return vi.spyOn(api, "apiFetch").mockImplementation((path: string, init?: RequestInit) => {
    if (init?.method === "POST" && path.endsWith("/users"))
      return Promise.resolve({
        id: "new", email: "novo@mbclaw.com.br", role: "CLIENT", client_id: "mbc",
        active: true, must_change_password: true, temp_password: "K7mq-2xPp-9vLt-4Zab",
      } as never);
    if (init?.method === "PATCH")
      return Promise.resolve({ ...users[0], active: false } as never);
    if (path === "/api/clients")
      return Promise.resolve([{ id: "mbc", name: "MBC", provider: "legaldesk+sisjuri" }] as never);
    return Promise.resolve(users as never);
  });
}

describe("UsuariosPage", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("lists the client's users, marking who is deactivated", async () => {
    mockApi();
    renderAs("CLIENT_ADMIN");
    await waitFor(() => {
      expect(screen.getByText("financeiro@mbclaw.com.br")).toBeInTheDocument();
    });
    // The Gestor's role reads in PT-BR, not as the enum value.
    expect(screen.getByText("Gestor")).toBeInTheDocument();
    // A deactivated user must stay visible, or it silently vanishes and gets re-created.
    expect(screen.getByText("saiu@mbclaw.com.br")).toBeInTheDocument();
    expect(screen.getByText("Inativo")).toBeInTheDocument();
  });

  it("creates a user and shows the temporary password once, with a copy button", async () => {
    const spy = mockApi();
    renderAs("ADMIN");
    await waitFor(() => expect(screen.getByText("financeiro@mbclaw.com.br")).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /Novo usuário/i }));
    await userEvent.type(screen.getByLabelText(/E-mail/i), "novo@mbclaw.com.br");
    await userEvent.click(screen.getByRole("button", { name: /^Criar$/ }));

    const post = spy.mock.calls.find((c) => (c[1] as RequestInit | undefined)?.method === "POST");
    expect(post).toBeTruthy();
    expect(String(post?.[0])).toBe("/api/clients/mbc/users");
    expect(JSON.parse(String((post?.[1] as RequestInit).body))).toEqual({
      email: "novo@mbclaw.com.br",
      role: "CLIENT",
    });

    // Shown once, verbatim, with an explicit warning that it will not reappear.
    expect(await screen.findByText("K7mq-2xPp-9vLt-4Zab")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Copiar/i })).toBeInTheDocument();
    expect(screen.getByText(/aparece apenas uma vez/i)).toBeInTheDocument();
  });

  it("only RUMO may pick the role or the client", async () => {
    mockApi();
    renderAs("ADMIN");
    await waitFor(() => expect(screen.getByText("financeiro@mbclaw.com.br")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /Novo usuário/i }));
    expect(screen.getByLabelText(/Papel/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Cliente/i)).toBeInTheDocument();
  });

  it("a Gestor gets no role and no client selector", async () => {
    // It may only ever create an ordinary CLIENT for its own client, so offering
    // either control would just render a request the API is going to refuse.
    mockApi();
    renderAs("CLIENT_ADMIN");
    await waitFor(() => expect(screen.getByText("financeiro@mbclaw.com.br")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /Novo usuário/i }));
    expect(screen.queryByLabelText(/Papel/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/^Cliente$/i)).not.toBeInTheDocument();
  });

  it("surfaces the API's PT-BR message when creation fails", async () => {
    vi.spyOn(api, "apiFetch").mockImplementation((path: string, init?: RequestInit) => {
      if (init?.method === "POST")
        return Promise.reject(Object.assign(new Error("x"), { detail: "E-mail já cadastrado" }));
      if (path === "/api/clients") return Promise.resolve([] as never);
      return Promise.resolve(USERS as never);
    });
    renderAs("CLIENT_ADMIN");
    await waitFor(() => expect(screen.getByText("financeiro@mbclaw.com.br")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /Novo usuário/i }));
    await userEvent.type(screen.getByLabelText(/E-mail/i), "financeiro@mbclaw.com.br");
    await userEvent.click(screen.getByRole("button", { name: /^Criar$/ }));
    expect(await screen.findByText("E-mail já cadastrado")).toBeInTheDocument();
  });

  it("deactivates a user through PATCH", async () => {
    const spy = mockApi();
    renderAs("ADMIN");
    await waitFor(() => expect(screen.getByText("financeiro@mbclaw.com.br")).toBeInTheDocument());
    await userEvent.click(screen.getAllByRole("button", { name: /Desativar/i })[0]);
    const patch = spy.mock.calls.find((c) => (c[1] as RequestInit | undefined)?.method === "PATCH");
    expect(patch).toBeTruthy();
    expect(String(patch?.[0])).toBe("/api/clients/mbc/users/u1");
    expect(JSON.parse(String((patch?.[1] as RequestInit).body))).toEqual({ active: false });
  });
});
