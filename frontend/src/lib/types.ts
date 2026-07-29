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

/** A single line of a comparison table (Orçado vs Realizado + variação). */
export interface PresLine {
  key: string;
  label: string;
  orcado: number | null;
  realizado: number | null;
  delta: number | null;
  pct: number | null;
  status: "critico" | "atencao" | "ok" | null;
}

export interface PresAttainment {
  mes?: string;
  abbr: string;
  recebimento: number | null;
  meta: number | null;
  pct: number | null;
  gap: number | null;
}

export interface PresArea {
  key: string;
  label: string;
  mes: {
    receita: number | null;
    resultado_bruto: number | null;
    resultado_liquido: number | null;
    meta_receita: number | null;
  };
  ytd: {
    receita: number | null;
    resultado_liquido: number | null;
    meta_receita: number | null;
  };
  atingimento: PresAttainment[];
  dre: PresLine[];
}

/** A per-month + YTD matrix row (institucional detail / reserva). */
export interface PresMatrixRow {
  key: string;
  label: string;
  months: Record<string, number | null>;
  ytd: number | null;
}

export interface Presentation {
  titulo: string;
  periodo: string;
  periodo_mes: string;
  ano: number;
  meses_presentes: string[];
  headline: {
    faturamento: number | null;
    recebimento: number | null;
    /** Total despesa = custo equipe + despesas institucionais (4th card). */
    despesas: number | null;
    despesas_institucionais: number | null;
    custo_equipe: number | null;
    resultado_bruto: number | null;
    margem_bruta: number | null;
    resultado_liquido: number | null;
    margem_liquida: number | null;
    reserva_bonus: number | null;
  };
  institucional_detalhe: {
    meses: string[];
    month_indices: number[];
    linhas: PresMatrixRow[];
  };
  meta: {
    anual: number | null;
    receita_ytd: number | null;
    resultado_bruto_ytd: number | null;
    resultado_liquido_ytd: number | null;
    margem_liquida_ytd: number | null;
    atingimento: PresAttainment[];
  };
  analise_ytd: PresLine[];
  areas: PresArea[];
  reserva: {
    meses: string[];
    linhas: PresMatrixRow[];
  };
}

export interface ClosingPayload {
  client: { id: string; name: string };
  period: {
    ano_mes: string;
    label: string;
    column_letter: string;
    /** True for the OPEN current month, served as a month-to-date partial. */
    is_partial?: boolean;
    /** True only for a fully elapsed month — a real fechamento. */
    is_closing?: boolean;
    /** PT-BR label shown verbatim; distinguishes a partial from a closing. */
    status_label?: string;
  };
  day_range: { from: string; to: string; is_full_month: boolean };
  kpis: Record<string, number | null>;
  presentation?: Presentation;
  tab_order: string[];
  tabs: Record<string, unknown>;
  generated_at: string;
}
