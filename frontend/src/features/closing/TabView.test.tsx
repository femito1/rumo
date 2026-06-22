// frontend/src/features/closing/TabView.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TabView } from "./TabView";

describe("TabView", () => {
  it("renders a rich tab name", () => {
    render(<TabView tab={{ kind: "rich", name: "Meta", kpis: {} }} />);
    expect(screen.getByText("Meta")).toBeInTheDocument();
  });

  it("renders a grid tab note", () => {
    render(<TabView tab={{ kind: "grid", name: "DRE 2026", note: "Fórmula", grid: [], rows: 0, cols: 0 }} />);
    expect(screen.getByText("DRE 2026")).toBeInTheDocument();
    expect(screen.getByText("Fórmula")).toBeInTheDocument();
  });

  it("renders empty-state when tab is missing", () => {
    render(<TabView tab={undefined} />);
    expect(screen.getByText(/Selecione uma aba/)).toBeInTheDocument();
  });
});
