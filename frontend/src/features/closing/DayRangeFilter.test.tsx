// frontend/src/features/closing/DayRangeFilter.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DayRangeFilter } from "./DayRangeFilter";

describe("DayRangeFilter", () => {
  it("does not fire onApply while typing — only on Aplicar", async () => {
    const onApply = vi.fn();
    render(<DayRangeFilter from={null} to={null} maxDay={31} onApply={onApply} onClear={() => {}} />);

    const inputs = screen.getAllByRole("textbox");
    await userEvent.type(inputs[0], "1");
    await userEvent.type(inputs[1], "15");
    expect(onApply).not.toHaveBeenCalled(); // no auto-fetch mid-edit

    await userEvent.click(screen.getByRole("button", { name: "Aplicar" }));
    expect(onApply).toHaveBeenCalledWith(1, 15);
  });

  it("rejects an inverted range with a message and no apply", async () => {
    const onApply = vi.fn();
    render(<DayRangeFilter from={null} to={null} maxDay={31} onApply={onApply} onClear={() => {}} />);
    const inputs = screen.getAllByRole("textbox");
    await userEvent.type(inputs[0], "20");
    await userEvent.type(inputs[1], "5");
    await userEvent.click(screen.getByRole("button", { name: "Aplicar" }));
    expect(onApply).not.toHaveBeenCalled();
    expect(screen.getByText(/menor ou igual/i)).toBeInTheDocument();
  });

  it("clamps non-numeric and out-of-range input (no sticky leading zero)", async () => {
    render(<DayRangeFilter from={null} to={null} maxDay={31} onApply={() => {}} onClear={() => {}} />);
    const inputs = screen.getAllByRole("textbox") as HTMLInputElement[];
    await userEvent.type(inputs[0], "0");
    expect(inputs[0].value).toBe(""); // 0 -> empty, no stuck zero
    await userEvent.type(inputs[0], "99");
    expect(inputs[0].value).toBe("31"); // clamped to max day
  });

  it("clamps to the month's real length (February -> 28)", async () => {
    render(<DayRangeFilter from={null} to={null} maxDay={28} onApply={() => {}} onClear={() => {}} />);
    const inputs = screen.getAllByRole("textbox") as HTMLInputElement[];
    await userEvent.type(inputs[1], "31");
    expect(inputs[1].value).toBe("28"); // can't exceed Feb's 28 days
  });
});
