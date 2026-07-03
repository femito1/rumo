// frontend/src/features/closing/ManualActualsEditor.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { ManualActualsEditor } from "./ManualActualsEditor";
import * as api from "../../lib/api";

const manual = {
  client_id: "mbc",
  ano_mes: "2026-02",
  areas: ["Contencioso", "Econômico", "Arbitragem"],
  lines: [
    { key: "recebimento", label: "Recebimento" },
    { key: "comissao", label: "Comissão" },
  ],
  entries: [{ area: "Contencioso", line_key: "recebimento", valor: 138600.13 }],
};

describe("ManualActualsEditor", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("opens to show per-area inputs seeded from entries", async () => {
    vi.spyOn(api, "apiFetch").mockResolvedValue(manual as never);
    render(<ManualActualsEditor clientId="mbc" anoMes="2026-02" />);
    expect(screen.queryByText("Contencioso")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Recebimento por área/ }));
    await waitFor(() => expect(screen.getByText("Contencioso")).toBeInTheDocument());
    const inputs = screen.getAllByRole("spinbutton") as HTMLInputElement[];
    expect(inputs[0].value).toBe("138600.13");
  });

  it("PUTs the manual entries on save to the ano_mes endpoint", async () => {
    const fetchSpy = vi.spyOn(api, "apiFetch").mockResolvedValue(manual as never);
    render(<ManualActualsEditor clientId="mbc" anoMes="2026-02" />);
    fireEvent.click(screen.getByRole("button", { name: /Recebimento por área/ }));
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
