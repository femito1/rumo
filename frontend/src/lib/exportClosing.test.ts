import { describe, it, expect } from "vitest";
import * as XLSX from "xlsx";
import { tabToAoA, buildWorkbook, MISSING_LABEL } from "./exportClosing";
import type { ClosingPayload } from "./types";

const gridTab = {
  kind: "grid",
  name: "DRE 2026",
  rows: 2,
  cols: 2,
  grid: [
    [
      { t: "label", v: "Linha" },
      { t: "label", v: "Valor" },
    ],
    [
      { t: "label", v: "Receita" },
      { t: "number", n: 100.5 },
    ],
  ],
};

const richTab = {
  kind: "rich",
  name: "Meta",
  columns: ["Mês", "Recebimento", "Meta"],
  rows: [
    {
      label: "Maio",
      recebimento: { value: 415927.84, source: "api" },
      meta: { value: null, source: "manual" },
    },
  ],
};

describe("tabToAoA", () => {
  it("converts a grid tab to a 2D array keeping numbers numeric", () => {
    const aoa = tabToAoA(gridTab);
    expect(aoa[0]).toEqual(["Linha", "Valor"]);
    expect(aoa[1]).toEqual(["Receita", 100.5]);
  });

  it("converts a rich tab and fills missing values with the placeholder", () => {
    const aoa = tabToAoA(richTab);
    expect(aoa[0]).toEqual(["Mês", "Recebimento", "Meta"]);
    expect(aoa[1][0]).toBe("Maio");
    expect(aoa[1][1]).toBe(415927.84);
    expect(aoa[1][2]).toBe(MISSING_LABEL);
  });
});

describe("tabToAoA on the cumulative tab", () => {
  // richToAoA derives its keys from Object.keys(rows[0]) — and row 0 of the
  // stacked cumulative view is a section header. If a header keeps the monthly
  // keys, every value cell exports blank and the row `key` leaks into the last
  // column.
  const ytdTab = {
    kind: "rich",
    name: "Acumulado (Jan → Junho)",
    columns: [
      "Linha", "Orçado YTD", "Realizado YTD", "Variação", "Desvio %",
      "Orçado Anual", "Falta p/ meta",
    ],
    rows: [
      {
        Linha: "RESULTADO INSTITUCIONAL",
        "Orçado YTD": null,
        "Realizado YTD": null,
        "Variação": null,
        "Desvio %": null,
        "Orçado Anual": null,
        "Falta p/ meta": null,
        key: "hdr::RESULTADO INSTITUCIONAL",
        kind: "header",
      },
      {
        Linha: "Receita",
        "Orçado YTD": { value: 4030000.02, source: "orcado" },
        "Realizado YTD": { value: 2130830.87, source: "realizado" },
        "Variação": { value: -1899169.15, source: "realizado" },
        "Desvio %": 0.5287,
        "Orçado Anual": { value: 8060000.04, source: "orcado" },
        "Falta p/ meta": { value: 5929169.17, source: "realizado" },
        key: "recebimento",
        kind: "amount",
      },
    ],
  };

  it("exports all seven columns with numbers, not row keys", () => {
    const aoa = tabToAoA(ytdTab) as unknown[][];
    expect(aoa[0]).toEqual([
      "Linha", "Orçado YTD", "Realizado YTD", "Variação", "Desvio %",
      "Orçado Anual", "Falta p/ meta",
    ]);
    const receita = aoa.find((r) => r[0] === "Receita")!;
    expect(receita).toHaveLength(7);
    expect(receita[2]).toBe(2130830.87);
    expect(receita[6]).toBe(5929169.17);
    // The metadata `key` must never land in a cell.
    expect(receita).not.toContain("recebimento");
  });
});

describe("buildWorkbook", () => {
  it("creates one sheet per tab in tab_order", () => {
    const payload = {
      client: { id: "mbc", name: "MBC" },
      period: { ano_mes: "2026-05", label: "Maio 2026", column_letter: "G" },
      day_range: { from: "2026-05-01", to: "2026-06-01", is_full_month: true },
      kpis: {},
      tab_order: ["meta", "dre_2026"],
      tabs: { meta: richTab, dre_2026: gridTab },
      generated_at: "2026-06-01T00:00:00Z",
    } as unknown as ClosingPayload;
    const wb = buildWorkbook(XLSX, payload);
    expect(wb.SheetNames).toContain("Meta");
    expect(wb.SheetNames).toContain("DRE 2026");
    expect(wb.SheetNames.length).toBe(2);
  });

  it("builds a single-sheet workbook when given a tabId", () => {
    const payload = {
      client: { id: "mbc", name: "MBC" },
      period: { ano_mes: "2026-05", label: "Maio 2026", column_letter: "G" },
      day_range: { from: "2026-05-01", to: "2026-06-01", is_full_month: true },
      kpis: {},
      tab_order: ["meta", "dre_2026"],
      tabs: { meta: richTab, dre_2026: gridTab },
      generated_at: "2026-06-01T00:00:00Z",
    } as unknown as ClosingPayload;
    const wb = buildWorkbook(XLSX, payload, "dre_2026");
    expect(wb.SheetNames).toEqual(["DRE 2026"]);
    const sheet = wb.Sheets["DRE 2026"];
    const aoa = XLSX.utils.sheet_to_json(sheet, { header: 1 });
    expect(aoa[0]).toEqual(["Linha", "Valor"]);
  });
});
