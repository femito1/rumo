// frontend/src/features/closing/WorkspacePage.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { WorkspacePage } from "./WorkspacePage";
import { Ctx, type AuthCtx } from "../auth/useAuth";
import type { AuthUser } from "../../lib/types";
import * as api from "../../lib/api";

const payload = {
  client: { id: "mbc", name: "MBC" },
  period: { ano_mes: "2026-05", label: "Maio 2026", column_letter: "G" },
  day_range: { from: "2026-05-01", to: "2026-06-01", is_full_month: true },
  kpis: { receita_honorarios: 415927.84, faturamento_realizado: 719988.05 },
  presentation: {
    titulo: "MBC", periodo: "Maio 2026",
    headline: { faturamento: 719988.05, recebimento: 415927.84, resultado_bruto: 100197.94, margem_bruta: 0.24, resultado_liquido: 29691.61, margem_liquida: 0.07, reserva_bonus: 2969.16 },
    institucional: { recebimento: 415927.84, despesas: 105640.6, imposto: 62389.2, amortizacao: 8117 },
    areas: [], meta_anual: 8060000.04, atingimento_mes: 0.6, recebimento_mensal: [],
  },
  tab_order: ["meta"],
  tabs: { meta: { kind: "rich", name: "Meta", kpis: {} } },
  generated_at: "2026-06-01T00:00:00Z",
};

function renderAs(role: "ADMIN" | "CLIENT") {
  const user: AuthUser = { id: "u", email: "e", role, client_id: role === "CLIENT" ? "mbc" : null };
  const ctx: AuthCtx = { user, status: "authenticated", login: vi.fn(), logout: vi.fn() };
  return render(
    <Ctx.Provider value={ctx}>
      <MemoryRouter initialEntries={["/clientes/mbc"]}>
        <Routes><Route path="/clientes/:id" element={<WorkspacePage />} /></Routes>
      </MemoryRouter>
    </Ctx.Provider>,
  );
}

describe("WorkspacePage", () => {
  function mockApi(overrides: Record<string, unknown> = {}) {
    vi.spyOn(api, "apiFetch").mockImplementation((path: string) => {
      if (path.includes("/closing")) return Promise.resolve({ ...payload, ...overrides } as never);
      if (path.includes("/budget"))
        return Promise.resolve({ client_id: "mbc", ano: 2026, areas: ["institucional"], lines: [], entries: [] } as never);
      return Promise.resolve({ id: "mbc", name: "MBC", provider: "legaldesk", available_months: ["2026-05"] } as never);
    });
  }

  it("renders client name + headline KPI from the closing (admin)", async () => {
    mockApi();
    renderAs("ADMIN");
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1, name: "MBC" })).toBeInTheDocument();
      expect(screen.getByText("Fechamento mensal")).toBeInTheDocument();
      // Recebimento shows in both the KPI strip and the presentation panel.
      expect(screen.getAllByText("R$ 415.927,84").length).toBeGreaterThan(0);
    });
  });

  it("admin sees the mode toggle and detail tab rail", async () => {
    mockApi();
    renderAs("ADMIN");
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Acumulado" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Meta" })).toBeInTheDocument();
    });
  });

  it("client sees only the presentation panel (no mode toggle, no detail tabs)", async () => {
    mockApi({ tab_order: [], tabs: {} });
    renderAs("CLIENT");
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1, name: "MBC" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Acumulado" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Meta" })).not.toBeInTheDocument();
    // The PDF download is available to the client.
    expect(screen.getByRole("button", { name: /Baixar apresentação/ })).toBeInTheDocument();
  });
});
