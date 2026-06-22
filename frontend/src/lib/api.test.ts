// frontend/src/lib/api.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ApiError, apiFetch } from "./api";

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe("apiFetch", () => {
  it("attaches bearer token when present", async () => {
    localStorage.setItem("rumo_token", "abc");
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );
    await apiFetch("/api/clients");
    const headers = (spy.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer abc");
  });

  it("throws ApiError with status + detail on non-2xx", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Sem acesso a este cliente" }), { status: 403 }),
    );
    const err = await apiFetch("/api/clients/demo").catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({
      status: 403,
      detail: "Sem acesso a este cliente",
    });
  });
});
