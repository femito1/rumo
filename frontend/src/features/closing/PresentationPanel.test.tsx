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
