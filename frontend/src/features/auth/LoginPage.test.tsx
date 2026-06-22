// frontend/src/features/auth/LoginPage.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { LoginPage } from "./LoginPage";
import * as authStore from "./useAuth";

describe("LoginPage", () => {
  it("shows a PT-BR error when login fails", async () => {
    vi.spyOn(authStore, "useAuth").mockReturnValue({
      user: null, status: "unauthenticated",
      login: vi.fn().mockRejectedValue(Object.assign(new Error("x"), { detail: "E-mail ou senha inválidos" })),
      logout: vi.fn(),
    });
    render(<MemoryRouter><LoginPage /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText(/E-mail/i), "a@b.com");
    await userEvent.type(screen.getByLabelText(/Senha/i), "x");
    await userEvent.click(screen.getByRole("button", { name: /Entrar/i }));
    expect(await screen.findByText("E-mail ou senha inválidos")).toBeInTheDocument();
  });
});
