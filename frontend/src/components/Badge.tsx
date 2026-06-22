// frontend/src/components/Badge.tsx
import type { Origin } from "../lib/types";

const LABELS: Record<Origin, string> = {
  legaldesk: "API",
  juritis: "Juritis",
  manual: "MANUAL",
  formula: "FÓRMULA",
  fixture: "DEMO",
};

export function OriginBadge({ origin }: { origin: Origin }) {
  return <span className={`badge badge-${origin}`}>{LABELS[origin]}</span>;
}
