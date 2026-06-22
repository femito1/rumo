// frontend/src/lib/format.test.ts
import { describe, it, expect } from "vitest";
import { formatBRL, formatMonthLabel, daysInMonth } from "./format";

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

describe("daysInMonth", () => {
  it("returns 28 for non-leap February", () => {
    expect(daysInMonth("2026-02")).toBe(28);
  });
  it("returns 29 for leap February", () => {
    expect(daysInMonth("2024-02")).toBe(29);
  });
  it("returns 30 and 31 for short/long months", () => {
    expect(daysInMonth("2026-04")).toBe(30);
    expect(daysInMonth("2026-05")).toBe(31);
  });
});
