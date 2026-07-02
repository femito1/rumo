// frontend/src/features/closing/MonthPicker.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MonthPicker } from "./MonthPicker";

describe("MonthPicker", () => {
  it("disables months not in availableMonths", () => {
    render(<MonthPicker value="2026-05" availableMonths={["2026-05", "2026-04"]} onChange={() => {}} />);
    // current/open month e.g. 2026-06 is not available -> rendered disabled
    const open = screen.getByRole("button", { name: /Jun/ });
    expect(open).toBeDisabled();
  });

  it("emits the selected ano_mes on click", async () => {
    const onChange = vi.fn();
    render(<MonthPicker value="2026-05" availableMonths={["2026-05", "2026-04"]} onChange={onChange} />);
    await userEvent.click(screen.getByRole("button", { name: /Abr/ }));
    expect(onChange).toHaveBeenCalledWith("2026-04");
  });

  it("navigates to a previous year and selects a month there", async () => {
    const onChange = vi.fn();
    render(
      <MonthPicker
        value="2026-05"
        availableMonths={["2026-05", "2025-11", "2025-03"]}
        onChange={onChange}
      />,
    );
    // starts on 2026
    expect(screen.getByText("2026")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Ano anterior/ }));
    expect(screen.getByText("2025")).toBeInTheDocument();
    // Nov 2025 is available in the browsed year
    await userEvent.click(screen.getByRole("button", { name: /Nov/ }));
    expect(onChange).toHaveBeenCalledWith("2025-11");
  });

  it("disables year nav past the range with data", () => {
    render(
      <MonthPicker value="2026-05" availableMonths={["2026-05"]} onChange={() => {}} />,
    );
    // single year -> both arrows disabled
    expect(screen.getByRole("button", { name: /Ano anterior/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Próximo ano/ })).toBeDisabled();
  });
});
