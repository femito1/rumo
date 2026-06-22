// frontend/src/features/clients/ClientsPage.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ClientsPage } from "./ClientsPage";
import * as api from "../../lib/api";

describe("ClientsPage", () => {
  it("renders a card per client", async () => {
    vi.spyOn(api, "apiFetch").mockResolvedValue([
      { id: "mbc", name: "MBC", provider: "legaldesk" },
      { id: "demo", name: "Cliente Demonstração", provider: "fixture" },
    ]);
    render(<MemoryRouter><ClientsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText("MBC")).toBeInTheDocument();
      expect(screen.getByText("Cliente Demonstração")).toBeInTheDocument();
    });
  });
});
