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

export type ClosingMode = "mensal" | "acumulado";

export interface PresentationArea {
  key: string;
  label: string;
  receita: number | null;
  receita_orcado: number | null;
  resultado_bruto: number | null;
  resultado_liquido: number | null;
  reserva_bonus: number | null;
  atingimento: number | null;
}

export interface Presentation {
  titulo: string;
  periodo: string;
  headline: {
    faturamento: number | null;
    recebimento: number | null;
    resultado_bruto: number | null;
    margem_bruta: number | null;
    resultado_liquido: number | null;
    margem_liquida: number | null;
    reserva_bonus: number | null;
  };
  institucional: {
    recebimento: number | null;
    despesas: number | null;
    imposto: number | null;
    amortizacao: number | null;
  };
  areas: PresentationArea[];
  meta_anual: number | null;
  atingimento_mes: number | null;
  recebimento_mensal: { mes: string; recebimento: number | null }[];
}

export interface ClosingPayload {
  client: { id: string; name: string };
  period: { ano_mes: string; label: string; column_letter: string };
  day_range: { from: string; to: string; is_full_month: boolean };
  kpis: Record<string, number | null>;
  mode?: ClosingMode;
  presentation?: Presentation;
  tab_order: string[];
  tabs: Record<string, unknown>;
  generated_at: string;
}
