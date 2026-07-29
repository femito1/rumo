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
    titulo: "MBC", periodo: "Maio 2026", periodo_mes: "Maio", ano: 2026,
    meses_presentes: ["Mai"],
    headline: { faturamento: 719988.05, recebimento: 415927.84, resultado_bruto: 100197.94, margem_bruta: 0.24, resultado_liquido: 29691.61, margem_liquida: 0.07, reserva_bonus: 2969.16 },
    institucional_detalhe: { meses: ["Mai"], month_indices: [5], linhas: [] },
    meta: { anual: 8060000.04, receita_ytd: 415927.84, resultado_bruto_ytd: 100197.94, resultado_liquido_ytd: 29691.61, margem_liquida_ytd: 0.07, atingimento: [] },
    analise_ytd: [], areas: [], reserva: { meses: ["Mai"], linhas: [] },
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

  it("admin sees the acumulado TAB in the rail, not a mensal/acumulado toggle", async () => {
    // The cumulative view is a tab served by the backend (tab_order), so it needs
    // no toolbar control and no second request.
    mockApi({
      tab_order: ["meta", "acumulado"],
      tabs: {
        meta: { kind: "rich", name: "Meta", kpis: {} },
        acumulado: { kind: "rich", name: "Acumulado (Jan → Maio)", rows: [] },
      },
    });
    renderAs("ADMIN");
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Meta" })).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: "Acumulado (Jan → Maio)" }),
    ).toBeInTheDocument();
    // No segmented period control any more.
    expect(screen.queryByRole("group", { name: "Período" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Mensal" })).not.toBeInTheDocument();
  });

  it("client sees only the presentation panel (no detail tabs)", async () => {
    mockApi({ tab_order: [], tabs: {} });
    renderAs("CLIENT");
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1, name: "MBC" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Meta" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Acumulado/ })).not.toBeInTheDocument();
    // The PDF download is available to the client.
    expect(screen.getByRole("button", { name: /Baixar apresentação/ })).toBeInTheDocument();
  });

  it("renders the annual goal as money, never NaN", async () => {
    // Regression: the backend returned meta.anual as a sourced cell
    // ({value, source}); formatBRL of an object rendered "R$ NaN". The deck shows
    // the annual meta as the Receita YTD stat-card footnote ("Meta: R$ …").
    mockApi();
    renderAs("ADMIN");
    await waitFor(() => {
      expect(screen.getByText(/Meta: R\$ 8\.060\.000,04/)).toBeInTheDocument();
    });
    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument();
  });

  it("colors a negative Reserva de bônus like the other signed KPIs", async () => {
    // Regression: the Reserva card was the ONLY KPI missing `signed`, so a negative
    // reserva (a loss month CONSUMES provision — see dre.bonus_reserve) rendered in
    // the default ink while Resultado/Margem next to it turned red. Client asked
    // "why is that number not red?" — all negatives must read the same.
    mockApi({
      kpis: {
        receita_honorarios: 415927.84,
        faturamento_realizado: 719988.05,
        resultado_liquido: -99564.42,
        resultado_bruto: -51694.64,
        reserva_bonus: -9956.44,
      },
    });
    renderAs("ADMIN");
    const card = await waitFor(() => {
      const label = screen.getByText("Reserva de bônus");
      return label.closest(".kpi") as HTMLElement;
    });
    expect(card).toHaveClass("kpi-neg");
    expect(card).not.toHaveClass("kpi-pos");
  });

  it("labels an OPEN month as a partial, never as a fechamento", async () => {
    // The client asked for the in-progress month (2026-07-28, 6:45). It must be
    // visibly a partial: a month-to-date view must never read as a closing, which is
    // why the gate was relaxed rather than deleted.
    mockApi({
      period: {
        ano_mes: "2026-07", label: "Julho 2026", column_letter: "I",
        is_partial: true, is_closing: false,
        status_label: "Julho 2026 — mês em aberto (parcial, atualizado diariamente)",
      },
    });
    renderAs("ADMIN");
    // The eyebrow says partial, not "Fechamento mensal"...
    await waitFor(() => {
      expect(screen.getByText("Mês em aberto · parcial")).toBeInTheDocument();
    });
    expect(screen.queryByText("Fechamento mensal")).not.toBeInTheDocument();
    // ...and a banner spells out that these numbers are not a closing.
    const banner = screen.getByRole("status");
    expect(banner).toHaveTextContent(/mês em aberto/i);
    expect(banner).toHaveTextContent(/não são um fechamento/i);
  });

  it("keeps the fechamento label for a CLOSED month", async () => {
    mockApi({
      period: {
        ano_mes: "2026-05", label: "Maio 2026", column_letter: "G",
        is_partial: false, is_closing: true, status_label: "Fechamento de Maio 2026",
      },
    });
    renderAs("ADMIN");
    await waitFor(() => {
      expect(screen.getByText("Fechamento mensal")).toBeInTheDocument();
    });
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    expect(screen.queryByText("Mês em aberto · parcial")).not.toBeInTheDocument();
  });
});
