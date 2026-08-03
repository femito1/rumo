// frontend/src/features/closing/PresentationPanel.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PresentationPanel } from "./PresentationPanel";
import type { Presentation } from "../../lib/types";

/** June 2026 — the month the client validated line by line. */
const data: Presentation = {
  titulo: "MBC",
  periodo: "Junho 2026",
  periodo_mes: "Junho",
  ano: 2026,
  meses_presentes: ["Jun"],
  headline: {
    faturamento: 1090965.2,
    recebimento: 265018.56,
    despesas: 316713.2,
    despesas_institucionais: 105932.16,
    custo_equipe: 210781.04,
    resultado_bruto: -51694.64,
    margem_bruta: -0.195,
    resultado_liquido: -99564.4,
    margem_liquida: -0.3757,
    reserva_bonus: -9956.44,
  },
  institucional_detalhe: { meses: ["Jun"], month_indices: [6], linhas: [] },
  meta: {
    anual: 8060000.04, receita_ytd: 2130830.27, resultado_bruto_ytd: 253819.11,
    resultado_liquido_ytd: -114507.52, margem_liquida_ytd: -0.05, atingimento: [],
  },
  analise_ytd: [],
  areas: [],
  reserva: { meses: ["Jun"], linhas: [] },
};

describe("PresentationPanel — institucional slide", () => {
  it("shows the Despesas card alongside faturamento, receita and resultado", () => {
    // Client 2026-07-28 (29:39 / 30:01): the institucional slide must read
    // faturamento → receita → despesas → resultado, because the result is the
    // difference between receita and despesa and reads "perdido" without it.
    render(<PresentationPanel data={data} />);
    expect(screen.getByText("Despesas")).toBeInTheDocument();
    // The total despesa = custo equipe + despesas institucionais.
    expect(screen.getByText("R$ 316.713,20")).toBeInTheDocument();
    // ...and the other three cards still render.
    expect(screen.getByText("Faturamento")).toBeInTheDocument();
    expect(screen.getByText("Receita Líquida")).toBeInTheDocument();
    expect(screen.getByText("Resultado Líquido")).toBeInTheDocument();
  });

  it("renders a null despesas card as an em dash instead of NaN", () => {
    const partial = { ...data, headline: { ...data.headline, despesas: null } };
    render(<PresentationPanel data={partial} />);
    expect(screen.getByText("Despesas")).toBeInTheDocument();
    expect(screen.queryByText(/NaN/)).not.toBeInTheDocument();
  });
});

describe("PresentationPanel — tables disclose why they may not add up", () => {
  it("states the K rounding on the monthly detail table", () => {
    // Rounded parts never sum to a rounded total at ANY precision (~49% of 6-month rows
    // diverge visibly at 1 and at 2 decimals — measured). So the deck discloses it
    // instead of pretending exactness. Also covers the margem rows, which are computed
    // on the accumulated base and are legitimately non-additive.
    render(<PresentationPanel data={data} />);
    const notes = screen.getAllByText(/valores em milhares/i);
    expect(notes.length).toBeGreaterThan(0);
    expect(screen.getByText(/margens são calculadas sobre o acumulado/i)).toBeInTheDocument();
  });

  it("explains that the three áreas do not sum to the institucional total", () => {
    // Adriana chased a ~7k gap in exactly this table (2026-07-29). Correct by design:
    // per-área receita follows each professional's home grupo and excludes
    // "Não Alocados"/"Administração". Say so on the slide.
    const comReserva: Presentation = {
      ...data,
      reserva: {
        meses: ["Jun"],
        linhas: [{ key: "institucional", label: "Institucional", months: { 6: -9956.44 }, ytd: -9956.44 }],
      },
    };
    render(<PresentationPanel data={comReserva} />);
    expect(
      screen.getByText(/não é a soma das três áreas/i),
    ).toBeInTheDocument();
  });
});

describe("PresentationPanel — open month must never present as a closing", () => {
  it("labels a partial month INSIDE the export root, not just in the page chrome", () => {
    // The workspace banner sits OUTSIDE #presentation-root and the print CSS hides
    // everything outside that root, so an open month used to export as a finished
    // closing. The label has to live in the deck itself (CLAUDE.md: "A partial month
    // must never render as a closing").
    const aberto: Presentation = {
      ...data,
      periodo: "Agosto 2026",
      periodo_mes: "Agosto",
      is_partial: true,
      status_label: "Agosto 2026 — mês em aberto (parcial, atualizado diariamente)",
    };
    const { container } = render(<PresentationPanel data={aberto} />);
    const root = container.querySelector("#presentation-root");
    expect(root).not.toBeNull();
    expect(root!.textContent).toMatch(/parcial/i);
    expect(root!.textContent).toMatch(/mês em aberto/i);
    // And it must NOT claim to be a monthly closing.
    expect(root!.textContent).not.toMatch(/Resultado Mensal de Agosto/);
  });

  it("leaves a CLOSED month exactly as it was", () => {
    const { container } = render(
      <PresentationPanel data={{ ...data, is_partial: false }} />,
    );
    const root = container.querySelector("#presentation-root")!;
    expect(root.textContent).toMatch(/Resultado Mensal de Junho/);
    expect(root.textContent).not.toMatch(/parcial/i);
    expect(root.textContent).not.toMatch(/mês em aberto/i);
  });
});
