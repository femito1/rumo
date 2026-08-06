// frontend/src/features/auth/ChangePasswordPage.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { ChangePasswordPage } from "./ChangePasswordPage";
import { Ctx, type AuthCtx } from "./useAuth";
import type { AuthUser } from "../../lib/types";
import * as api from "../../lib/api";

function renderPage(mustChange = true) {
  const user: AuthUser = {
    id: "u", email: "novo@mbclaw.com.br", role: "CLIENT", client_id: "mbc",
    must_change_password: mustChange,
  };
  const ctx = {
    user, status: "authenticated", login: vi.fn(), logout: vi.fn(), refresh: vi.fn(),
  } as unknown as AuthCtx;
  return render(
    <Ctx.Provider value={ctx}>
      <MemoryRouter><ChangePasswordPage /></MemoryRouter>
    </Ctx.Provider>,
  );
}

describe("ChangePasswordPage", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("posts the change and sends both passwords", async () => {
    const spy = vi.spyOn(api, "apiFetch").mockResolvedValue({
      id: "u", email: "novo@mbclaw.com.br", role: "CLIENT", client_id: "mbc",
      active: true, must_change_password: false,
    } as never);
    renderPage();
    await userEvent.type(screen.getByLabelText(/Senha atual/i), "K7mq-2xPp");
    await userEvent.type(screen.getByLabelText(/^Nova senha$/i), "uma-senha-longa");
    await userEvent.type(screen.getByLabelText(/Confirmar/i), "uma-senha-longa");
    await userEvent.click(screen.getByRole("button", { name: /Alterar senha/i }));

    const call = spy.mock.calls.find((c) => (c[1] as RequestInit | undefined)?.method === "POST");
    expect(String(call?.[0])).toBe("/api/auth/change-password");
    expect(JSON.parse(String((call?.[1] as RequestInit).body))).toEqual({
      current_password: "K7mq-2xPp",
      new_password: "uma-senha-longa",
    });
  });

  it("refuses a mismatched confirmation without calling the API", async () => {
    const spy = vi.spyOn(api, "apiFetch");
    renderPage();
    await userEvent.type(screen.getByLabelText(/Senha atual/i), "K7mq-2xPp");
    await userEvent.type(screen.getByLabelText(/^Nova senha$/i), "uma-senha-longa");
    await userEvent.type(screen.getByLabelText(/Confirmar/i), "outra-senha-longa");
    await userEvent.click(screen.getByRole("button", { name: /Alterar senha/i }));
    expect(await screen.findByText(/não conferem/i)).toBeInTheDocument();
    expect(spy).not.toHaveBeenCalled();
  });

  it("enforces the same minimum length as the API, before calling it", async () => {
    const spy = vi.spyOn(api, "apiFetch");
    renderPage();
    await userEvent.type(screen.getByLabelText(/Senha atual/i), "K7mq-2xPp");
    await userEvent.type(screen.getByLabelText(/^Nova senha$/i), "curta");
    await userEvent.type(screen.getByLabelText(/Confirmar/i), "curta");
    await userEvent.click(screen.getByRole("button", { name: /Alterar senha/i }));
    expect(await screen.findByText(/8 caracteres/i)).toBeInTheDocument();
    expect(spy).not.toHaveBeenCalled();
  });

  it("surfaces the API's PT-BR error", async () => {
    vi.spyOn(api, "apiFetch").mockRejectedValue(
      Object.assign(new Error("x"), { detail: "Senha atual incorreta" }),
    );
    renderPage();
    await userEvent.type(screen.getByLabelText(/Senha atual/i), "errada");
    await userEvent.type(screen.getByLabelText(/^Nova senha$/i), "uma-senha-longa");
    await userEvent.type(screen.getByLabelText(/Confirmar/i), "uma-senha-longa");
    await userEvent.click(screen.getByRole("button", { name: /Alterar senha/i }));
    expect(await screen.findByText("Senha atual incorreta")).toBeInTheDocument();
  });

  it("explains WHY it is being forced when the password is provisional", () => {
    renderPage(true);
    expect(screen.getByText(/senha provisória/i)).toBeInTheDocument();
  });
});
