// frontend/src/features/closing/WorkspacePage.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { WorkspacePage } from "./WorkspacePage";
import * as api from "../../lib/api";

const payload = {
  client: { id: "mbc", name: "MBC" },
  period: { ano_mes: "2026-05", label: "Maio 2026", column_letter: "G" },
  day_range: { from: "2026-05-01", to: "2026-06-01", is_full_month: true },
  kpis: { receita_honorarios: 415927.84, faturamento_realizado: 719988.05, faturas_emitidas: 53 },
  tab_order: ["meta"],
  tabs: { meta: { kind: "rich", name: "Meta", kpis: {} } },
  generated_at: "2026-06-01T00:00:00Z",
};

describe("WorkspacePage", () => {
  it("renders client name + headline KPI from the closing", async () => {
    vi.spyOn(api, "apiFetch").mockImplementation((path: string) => {
      if (path.includes("/closing")) return Promise.resolve(payload as never);
      if (path.includes("/budget"))
        return Promise.resolve({ client_id: "mbc", ano: 2026, areas: ["institucional"], lines: [], entries: [] } as never);
      if (path.includes("/manual"))
        return Promise.resolve({ client_id: "mbc", ano_mes: "2026-05", areas: [], lines: [], entries: [] } as never);
      return Promise.resolve({ id: "mbc", name: "MBC", provider: "legaldesk", available_months: ["2026-05"] } as never);
    });
    render(
      <MemoryRouter initialEntries={["/clientes/mbc"]}>
        <Routes><Route path="/clientes/:id" element={<WorkspacePage />} /></Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "MBC" })).toBeInTheDocument();
      expect(screen.getByText("Fechamento mensal")).toBeInTheDocument();
      expect(screen.getByText("R$ 415.927,84")).toBeInTheDocument();
    });
  });
});
