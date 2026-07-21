// frontend/src/features/closing/TabView.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen, within, fireEvent } from "@testing-library/react";
import { TabView, MISSING_LABEL, NA_LABEL } from "./TabView";

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

  it("renders a total row's empty text cells as blank, not the missing placeholder", () => {
    const { container } = render(
      <TabView
        tab={{
          kind: "rich",
          name: "Moedas",
          columns: ["Fatura", "Cliente", "Caso", "Moeda", "Honorários (R$)"],
          rows: [
            {
              Fatura: 4160,
              Cliente: "87",
              Caso: "2",
              Moeda: "US$",
              "Honorários (R$)": { value: 5083.65, source: "realizado" },
              kind: "amount",
            },
            {
              Fatura: "",
              Cliente: "",
              Caso: "Total",
              Moeda: "",
              "Honorários (R$)": { value: 11328.87, source: "realizado" },
              kind: "total",
              is_total: true,
            },
          ],
        }}
      />,
    );
    // The Total row's structurally-empty cells (Fatura/Cliente/Moeda) must be
    // blank, never the "ainda não temos" placeholder.
    const totalRow = container.querySelector("tr.row-total") as HTMLElement;
    expect(totalRow).not.toBeNull();
    expect(within(totalRow).queryByText(MISSING_LABEL)).toBeNull();
    expect(within(totalRow).getByText("Total")).toBeInTheDocument();
    expect(within(totalRow).getByText("11.328,87")).toBeInTheDocument();
  });

  it("shows '—' for null Orçado/Desvio% but 'ainda não temos' for null Realizado", () => {
    const { container } = render(
      <TabView
        tab={{
          kind: "rich",
          name: "Contencioso",
          columns: ["Linha", "Orçado", "Realizado", "Desvio %"],
          rows: [
            {
              Linha: "Comissão",
              // Orçado not budgeted at this grain → "not applicable" (dash).
              "Orçado": { value: null, source: "orcado" },
              // Realizado genuinely missing → keep the "ainda não temos" label.
              Realizado: { value: null, source: "realizado" },
              // Desvio % can't be computed without Orçado → dash.
              "Desvio %": null,
              key: "comissao",
            },
          ],
        }}
      />,
    );
    const row = container.querySelector("tbody tr") as HTMLElement;
    const cells = within(row).getAllByRole("cell");
    // cells: [Linha, Orçado, Realizado, Desvio %]
    expect(cells[1]).toHaveTextContent(NA_LABEL); // Orçado → —
    expect(cells[2]).toHaveTextContent(MISSING_LABEL); // Realizado → ainda não temos
    expect(cells[3]).toHaveTextContent(NA_LABEL); // Desvio % → —
    // The dash and the missing-label are distinct.
    expect(NA_LABEL).not.toEqual(MISSING_LABEL);
  });

  it("renders '—' (not 'ainda não temos') for a null value on an empty_dash row", () => {
    // Event-driven DL-extras lines (Bônus equipe, DL excedente, Repasse Cacione)
    // are correctly empty in months where the event didn't occur — the backend
    // flags them empty_dash, so a null renders as a neutral dash, not pending.
    const { container } = render(
      <TabView
        tab={{
          kind: "rich",
          name: "Base_Resultado Mensal",
          columns: ["Linha", "Valor"],
          rows: [
            { Linha: "Bônus equipe", Valor: null, key: "extra::bonus_equipe", empty_dash: true },
            { Linha: "Comissão", Valor: null, key: "comissao" },
          ],
        }}
      />,
    );
    const rows = container.querySelectorAll("tbody tr");
    const bonusCells = within(rows[0] as HTMLElement).getAllByRole("cell");
    expect(bonusCells[1]).toHaveTextContent(NA_LABEL); // empty_dash → —
    expect(within(rows[0] as HTMLElement).queryByText(MISSING_LABEL)).toBeNull();
    // A normal row with a null Realizado still shows the pending placeholder.
    const comCells = within(rows[1] as HTMLElement).getAllByRole("cell");
    expect(comCells[1]).toHaveTextContent(MISSING_LABEL);
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

  it("drills down per professional when clicking an area section (collapsed by default)", () => {
    render(
      <TabView
        tab={{
          kind: "rich",
          name: "Base_Resultado Mensal",
          columns: ["Linha", "Valor"],
          rows: [
            {
              Linha: "Custo equipe - Contencioso",
              Valor: { value: 74141.21, source: "realizado" },
              indent: 0,
              is_total: true,
              kind: "section_total",
              key: "custo_Contencioso",
            },
            {
              Linha: "IAC - Distribuição Mensal Fixa",
              Valor: { value: 14039, source: "realizado" },
              indent: 1,
              is_total: false,
              kind: "amount",
              key: "prof::Contencioso::IAC::Distribuição Mensal Fixa",
            },
          ],
        }}
      />,
    );
    // The area group is clickable and its per-professional row is hidden until clicked.
    const areaBtn = screen.getByRole("button", { name: /Custo equipe - Contencioso/ });
    expect(screen.queryByText("IAC - Distribuição Mensal Fixa")).not.toBeInTheDocument();
    fireEvent.click(areaBtn);
    expect(screen.getByText("IAC - Distribuição Mensal Fixa")).toBeInTheDocument();
    // Clicking again collapses it back.
    fireEvent.click(areaBtn);
    expect(screen.queryByText("IAC - Distribuição Mensal Fixa")).not.toBeInTheDocument();
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
