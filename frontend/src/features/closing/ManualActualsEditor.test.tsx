// frontend/src/features/closing/ManualActualsEditor.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { ManualActualsEditor } from "./ManualActualsEditor";
import * as api from "../../lib/api";

const manual = {
  client_id: "mbc",
  ano_mes: "2026-02",
  areas: ["Contencioso", "Econômico", "Arbitragem"],
  // Recebimento is SISJURI-derived now and not an editable manual line.
  lines: [
    { key: "comissao", label: "Comissão" },
    { key: "despesa_institucional", label: "Despesa Institucional" },
  ],
  entries: [
    { area: "Contencioso", line_key: "despesa_institucional", valor: 35425.45 },
  ],
};

describe("ManualActualsEditor", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("opens to show per-area inputs seeded from entries", async () => {
    vi.spyOn(api, "apiFetch").mockResolvedValue(manual as never);
    render(<ManualActualsEditor clientId="mbc" anoMes="2026-02" />);
    expect(screen.queryByText("Contencioso")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Lançamentos por área/ }));
    await waitFor(() => expect(screen.getByText("Contencioso")).toBeInTheDocument());
    const inputs = screen.getAllByRole("spinbutton") as HTMLInputElement[];
    // Grid is area x line; the seeded entry is Contencioso/despesa_institucional,
    // the 2nd line, so it lands in the 2nd input of the first row.
    expect(inputs[1].value).toBe("35425.45");
  });

  it("PUTs the manual entries on save to the ano_mes endpoint", async () => {
    const fetchSpy = vi.spyOn(api, "apiFetch").mockResolvedValue(manual as never);
    render(<ManualActualsEditor clientId="mbc" anoMes="2026-02" />);
    fireEvent.click(screen.getByRole("button", { name: /Lançamentos por área/ }));
    await waitFor(() => expect(screen.getByText("Arbitragem")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /Salvar lançamentos/ }));
    await waitFor(() => {
      const putCall = fetchSpy.mock.calls.find(
        (c) => (c[1] as RequestInit | undefined)?.method === "PUT",
      );
      expect(putCall).toBeTruthy();
      expect(String(putCall?.[0])).toContain("/api/clients/mbc/manual?ano_mes=2026-02");
    });
  });
});
