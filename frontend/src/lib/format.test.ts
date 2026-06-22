// frontend/src/lib/format.test.ts
import { describe, it, expect } from "vitest";
import { formatBRL, formatMonthLabel } from "./format";

describe("formatBRL", () => {
  it("formats with R$, thousands dot, decimal comma", () => {
    expect(formatBRL(415927.84)).toBe("R$ 415.927,84");
  });
  it("renders null as em dash", () => {
    expect(formatBRL(null)).toBe("—");
  });
});

describe("formatMonthLabel", () => {
  it("maps ano_mes to a PT-BR label", () => {
    expect(formatMonthLabel("2026-05")).toBe("Maio 2026");
  });
});
