// frontend/src/lib/format.test.ts
import { describe, it, expect } from "vitest";
import {
  formatBRL,
  formatBRLShort,
  formatMonthLabel,
  daysInMonth,
  formatNumber,
  formatPercent,
} from "./format";

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

describe("formatNumber", () => {
  it("formats integers with a PT-BR thousands dot", () => {
    expect(formatNumber(48)).toBe("48");
    expect(formatNumber(1234)).toBe("1.234");
  });
  it("renders null as em dash", () => {
    expect(formatNumber(null)).toBe("—");
  });
});

describe("formatPercent", () => {
  it("formats a ratio as a PT-BR percentage", () => {
    expect(formatPercent(0.411)).toBe("41,1%");
  });
  it("renders null as em dash", () => {
    expect(formatPercent(null)).toBe("—");
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

describe("formatBRLShort", () => {
  it("renders thousands with one decimal and a K suffix", () => {
    expect(formatBRLShort(444545.69)).toBe("444,5K");
    expect(formatBRLShort(3463471.84)).toBe("3.463,5K");
    expect(formatBRLShort(-14900)).toBe("-14,9K");
  });

  it("renders null as an em dash", () => {
    expect(formatBRLShort(null)).toBe("—");
    expect(formatBRLShort(undefined)).toBe("—");
  });

  it("is NOT additive, which is why the deck says so out loud", () => {
    // Rounded parts do not sum to a rounded total, and precision does not fix it:
    // measured over 200k random 6-month rows, ~49% diverge visibly at ONE decimal and
    // ~49% at TWO. So the deck must DISCLOSE the rounding rather than chase exactness
    // in a K format. This test pins the reason down so nobody "fixes" it by adding
    // decimals (which was my first instinct, and it made a real row worse).
    const parseK = (s: string) =>
      parseFloat(s.replace("K", "").replace(/\./g, "").replace(",", "."));
    const months = [534752.84, 719988.05, 1090965.2];
    const shownSum = months.map((m) => parseK(formatBRLShort(m))).reduce((a, b) => a + b, 0);
    expect(shownSum).toBeCloseTo(2345.8, 5);
    expect(parseK(formatBRLShort(months.reduce((a, b) => a + b, 0)))).toBeCloseTo(2345.7, 5);
  });
});
