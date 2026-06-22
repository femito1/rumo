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
});
