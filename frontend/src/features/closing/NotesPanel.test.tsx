// frontend/src/features/closing/NotesPanel.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NotesPanel } from "./NotesPanel";
import type { ClosingNote } from "../../lib/types";

const notas: ClosingNote[] = [
  {
    id: "vale-adm-meses-nao-ajustados",
    titulo: "Vale ADM de março, abril e maio: lançamento não ajustado na planilha",
    detalhe: "O vale-refeição e o vale-transporte são pagos num lançamento único…",
    severidade: "info",
    acao: "Nenhuma ação necessária.",
    contato: "Fernando Rimoli — fernando@bia4u.com.br",
  },
  {
    id: "despesas-area-formula-deslocada",
    titulo: "Despesas por área: fórmula da planilha deslocada uma linha",
    detalhe: "As fórmulas de janeiro a maio somam a linha de baixo…",
    severidade: "atencao",
    acao: "Vale conferir as linhas 204, 205 e 206.",
    contato: "Fernando Rimoli — fernando@bia4u.com.br",
  },
];

describe("NotesPanel", () => {
  it("renders nothing when there are no notes (no empty box on a clean month)", () => {
    const { container } = render(<NotesPanel notas={[]} mes="Junho 2026" cliente="MBC" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("lists each note with its PT-BR title and a count", () => {
    render(<NotesPanel notas={notas} mes="Março 2026" cliente="MBC" />);
    expect(screen.getByText(/Diferenças conhecidas/i)).toBeInTheDocument();
    expect(screen.getByText(/2/)).toBeInTheDocument();
    expect(screen.getByText(notas[0].titulo)).toBeInTheDocument();
    expect(screen.getByText(notas[1].titulo)).toBeInTheDocument();
  });

  it("reveals the detail and the action when a note is expanded", async () => {
    const user = userEvent.setup();
    render(<NotesPanel notas={notas} mes="Março 2026" cliente="MBC" />);
    // Collapsed by default: the panel must not wall off the numbers.
    expect(screen.queryByText(/vale-refeição e o vale-transporte/)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: new RegExp(notas[0].titulo) }));
    expect(screen.getByText(/vale-refeição e o vale-transporte/)).toBeInTheDocument();
    expect(screen.getByText(/Nenhuma ação necessária/)).toBeInTheDocument();
  });

  it("offers a mailto that pre-fills client, month and note so we get context", async () => {
    const user = userEvent.setup();
    render(<NotesPanel notas={notas} mes="Março 2026" cliente="MBC" />);
    await user.click(screen.getByRole("button", { name: new RegExp(notas[0].titulo) }));
    const link = screen.getByRole("link", { name: /Falar com o time/i });
    const href = link.getAttribute("href") ?? "";
    expect(href.startsWith("mailto:fernando@bia4u.com.br")).toBe(true);
    // The subject/body must carry enough to answer without a round trip.
    const decoded = decodeURIComponent(href);
    expect(decoded).toContain("MBC");
    expect(decoded).toContain("Março 2026");
    expect(decoded).toContain("vale-adm-meses-nao-ajustados");
  });

  it("marks an 'atencao' note distinctly from an 'info' one", () => {
    render(<NotesPanel notas={notas} mes="Março 2026" cliente="MBC" />);
    const atencao = screen.getByRole("button", { name: new RegExp(notas[1].titulo) });
    expect(atencao.closest(".nota")).toHaveClass("nota-atencao");
    const info = screen.getByRole("button", { name: new RegExp(notas[0].titulo) });
    expect(info.closest(".nota")).toHaveClass("nota-info");
  });
});
