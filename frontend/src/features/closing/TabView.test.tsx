// frontend/src/features/closing/TabView.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { TabView, MISSING_LABEL } from "./TabView";

describe("TabView", () => {
  it("renders a rich tab as a table with its columns and live values", () => {
    render(
      <TabView
        tab={{
          kind: "rich",
          name: "Meta",
          columns: ["Mês", "Recebimento", "Faturamento", "Meta", "Despesas"],
          rows: [
            {
              label: "Maio",
              recebimento: { value: 415927.84, source: "api" },
              faturamento: { value: 719988.05, source: "api" },
              meta: { value: null, source: "manual" },
              despesas: { value: null, source: "manual" },
            },
          ],
        }}
      />,
    );
    expect(screen.getByRole("heading", { name: "Meta" })).toBeInTheDocument();
    expect(screen.getByText("Recebimento")).toBeInTheDocument();
    // Missing (manual) values show the explanatory placeholder, not a dash.
    expect(screen.getAllByText(MISSING_LABEL).length).toBeGreaterThan(0);
  });

  it("fills missing rich values with the 'ainda não temos' placeholder", () => {
    render(
      <TabView
        tab={{
          kind: "rich",
          name: "Base_Resultado",
          columns: ["#", "Linha", "Valor"],
          rows: [
            { row: 4, label: "Receita de honorários", value: 415927.84, source: "api" },
            { row: 5, label: "Despesa institucional", value: null, source: "manual" },
          ],
        }}
      />,
    );
    expect(screen.getByText("Receita de honorários")).toBeInTheDocument();
    expect(screen.getByText(MISSING_LABEL)).toBeInTheDocument();
  });

  it("renders a grid tab with a sticky header row in a thead", () => {
    const { container } = render(
      <TabView
        tab={{
          kind: "grid",
          name: "DRE 2026",
          note: "Fórmula",
          rows: 2,
          cols: 2,
          grid: [
            [
              { t: "label", v: "Linha" },
              { t: "label", v: "Valor" },
            ],
            [
              { t: "label", v: "Receita" },
              { t: "number", n: 100 },
            ],
          ],
        }}
      />,
    );
    expect(screen.getByText("DRE 2026")).toBeInTheDocument();
    const thead = container.querySelector("thead");
    expect(thead).not.toBeNull();
    expect(within(thead as HTMLElement).getByText("Linha")).toBeInTheDocument();
  });

  it("renders empty-state when tab is missing", () => {
    render(<TabView tab={undefined} />);
    expect(screen.getByText(/Selecione uma aba/)).toBeInTheDocument();
  });

  it("formats a percent column (Desvio %) and shows the missing-data banner", () => {
    render(
      <TabView
        tab={{
          kind: "rich",
          name: "Resultado Institucional",
          columns: ["Linha", "Orcado", "Realizado", "Variacao", "Desvio %"],
          snapshot_missing: true,
          rows: [
            {
              Linha: "Margem Bruta",
              Orcado: { value: null, source: "orcado" },
              Realizado: { value: 0.411, source: "realizado" },
              Variacao: { value: null, source: "formula" },
              "Desvio %": 0.98,
              key: "margem_bruta",
              indent: 1,
              is_total: false,
              kind: "margin",
            },
          ],
        }}
      />,
    );
    // The banner appears when snapshot_missing is true.
    expect(
      screen.getByText(/Dados institucionais ainda não importados/),
    ).toBeInTheDocument();
    // The Desvio % column renders as a PT-BR percentage.
    expect(screen.getByText("98,0%")).toBeInTheDocument();
  });

  it("indents sub-account rows in a grouped expense tree", () => {
    const { container } = render(
      <TabView
        tab={{
          kind: "rich",
          name: "Institucional - Despesas",
          columns: ["Conta", "Valor", "Lancamentos"],
          rows: [
            { Conta: "Ocupação", Valor: { value: 100, source: "realizado" }, Lancamentos: 2, indent: 0, is_total: true },
            { Conta: "Aluguel", Valor: { value: 90, source: "realizado" }, Lancamentos: 1, indent: 1, is_total: false },
          ],
        }}
      />,
    );
    expect(container.querySelector("tr.row-total")).not.toBeNull();
    expect(container.querySelector("td.cell-indent")).not.toBeNull();
  });
});
