// frontend/src/components/Badge.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { OriginBadge } from "./Badge";

describe("OriginBadge", () => {
  it("labels legaldesk as API", () => {
    render(<OriginBadge origin="legaldesk" />);
    expect(screen.getByText("API")).toBeInTheDocument();
  });
  it("labels manual as MANUAL", () => {
    render(<OriginBadge origin="manual" />);
    expect(screen.getByText("MANUAL")).toBeInTheDocument();
  });
  it("labels juritis as Juritis", () => {
    render(<OriginBadge origin="juritis" />);
    expect(screen.getByText("Juritis")).toBeInTheDocument();
  });
});
