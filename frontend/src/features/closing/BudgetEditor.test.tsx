// frontend/src/features/closing/BudgetEditor.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BudgetEditor } from "./BudgetEditor";
import * as api from "../../lib/api";

const budget = {
  client_id: "mbc",
  ano: 2026,
  areas: ["institucional", "Contencioso", "Econômico", "Arbitragem"],
  lines: [
    { key: "faturamento", label: "Faturamento" },
    { key: "impostos", label: "Impostos" },
    { key: "despesas_equipe", label: "Despesas Equipe" },
  ],
  entries: [{ area: "institucional", line_key: "faturamento", annual_amount: 8060000 }],
};

describe("BudgetEditor", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("is collapsed by default and opens to show annual inputs", async () => {
    vi.spyOn(api, "apiFetch").mockResolvedValue(budget as never);
    render(<BudgetEditor clientId="mbc" ano={2026} />);
    // Collapsed: inputs not shown yet.
    expect(screen.queryByText("Faturamento")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Orçamento 2026/ }));
    await waitFor(() => {
      expect(screen.getByText("Faturamento")).toBeInTheDocument();
    });
    // Seeded from the loaded entry.
    const inputs = screen.getAllByRole("spinbutton") as HTMLInputElement[];
    expect(inputs[0].value).toBe("8060000");
  });

  it("shows a per-area Orçamento Despesa section for the three cost centers", async () => {
    vi.spyOn(api, "apiFetch").mockResolvedValue(budget as never);
    render(<BudgetEditor clientId="mbc" ano={2026} />);
    fireEvent.click(screen.getByRole("button", { name: /Orçamento 2026/ }));
    await waitFor(() => {
      expect(screen.getByText(/Orçamento Despesa por equipe/i)).toBeInTheDocument();
    });
    expect(screen.getByText("Contencioso")).toBeInTheDocument();
    expect(screen.getByText("Econômico")).toBeInTheDocument();
    expect(screen.getByText("Arbitragem")).toBeInTheDocument();
  });

  it("PUTs the per-area Despesas Equipe budget on save", async () => {
    const fetchSpy = vi.spyOn(api, "apiFetch").mockResolvedValue(budget as never);
    render(<BudgetEditor clientId="mbc" ano={2026} />);
    fireEvent.click(screen.getByRole("button", { name: /Orçamento 2026/ }));
    await waitFor(() =>
      expect(screen.getByText(/Orçamento Despesa por equipe/i)).toBeInTheDocument(),
    );
    const contInput = screen.getByLabelText(
      "Orçamento Despesa Contencioso",
    ) as HTMLInputElement;
    fireEvent.change(contInput, { target: { value: "30000" } });
    fireEvent.click(screen.getByRole("button", { name: /Salvar orçamento/ }));
    await waitFor(() => {
      const putCall = fetchSpy.mock.calls.find(
        (c) => (c[1] as RequestInit | undefined)?.method === "PUT",
      );
      expect(putCall).toBeTruthy();
      const body = JSON.parse(String((putCall?.[1] as RequestInit).body));
      expect(body.entries).toContainEqual({
        area: "Contencioso",
        line_key: "despesas_equipe",
        annual_amount: 30000,
      });
    });
  });

  it("PUTs the edited entries on save", async () => {
    const fetchSpy = vi.spyOn(api, "apiFetch").mockResolvedValue(budget as never);
    render(<BudgetEditor clientId="mbc" ano={2026} />);
    fireEvent.click(screen.getByRole("button", { name: /Orçamento 2026/ }));
    await waitFor(() => expect(screen.getByText("Impostos")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Salvar orçamento/ }));
    await waitFor(() => {
      const putCall = fetchSpy.mock.calls.find(
        (c) => (c[1] as RequestInit | undefined)?.method === "PUT",
      );
      expect(putCall).toBeTruthy();
      expect(String(putCall?.[0])).toContain("/api/clients/mbc/budget?ano=2026");
    });
  });
});
