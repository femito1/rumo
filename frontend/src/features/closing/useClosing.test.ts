// frontend/src/features/closing/useClosing.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useClosing } from "./useClosing";
import * as api from "../../lib/api";

describe("useClosing", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("does not fetch closing when month is empty (avoids 422)", async () => {
    const spy = vi.spyOn(api, "apiFetch").mockResolvedValue({} as never);
    renderHook(() => useClosing("mbc", "", null, null));
    await new Promise((r) => setTimeout(r, 50));
    expect(spy).not.toHaveBeenCalled();
  });

  it("fetches when month is valid", async () => {
    const spy = vi.spyOn(api, "apiFetch").mockResolvedValue({ client: { id: "mbc" } } as never);
    renderHook(() => useClosing("mbc", "2026-05", null, null));
    await waitFor(() => expect(spy).toHaveBeenCalledWith("/api/clients/mbc/closing?month=2026-05"));
  });
});
