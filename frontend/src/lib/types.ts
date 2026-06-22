// frontend/src/lib/types.ts
export type Role = "ADMIN" | "CLIENT";
export type Origin = "legaldesk" | "juritis" | "manual" | "formula" | "fixture";

export interface AuthUser {
  id: string;
  email: string;
  role: Role;
  client_id: string | null;
}

export interface ClientSummary {
  id: string;
  name: string;
  provider: string;
}

export interface Cell {
  value: number | null;
  origin: Origin;
}

export interface ClosingPayload {
  client: { id: string; name: string };
  period: { ano_mes: string; label: string; column_letter: string };
  day_range: { from: string; to: string; is_full_month: boolean };
  kpis: Record<string, number>;
  tab_order: string[];
  tabs: Record<string, unknown>;
  generated_at: string;
}
