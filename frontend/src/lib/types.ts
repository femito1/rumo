// frontend/src/lib/types.ts
/** ADMIN = RUMO staff (all clients). CLIENT_ADMIN ("Gestor") = a client's own
 *  manager: same data as a CLIENT, plus the ability to provision users for its
 *  OWN client. CLIENT = read the deck only.
 *  ⚠ Gate RUMO-only UI on `=== "ADMIN"`, never on `!== "CLIENT"` — the latter is a
 *  deny-list that lets any new role through. */
export type Role = "ADMIN" | "CLIENT_ADMIN" | "CLIENT";
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
  /** Open (in-progress) month. Carried on the DECK, not just on `period`, because
   *  the print CSS hides everything outside `#presentation-root` — so the workspace
   *  banner never reached the exported PDF. A partial must never present as a closing. */
  is_partial?: boolean;
  status_label?: string;
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

/**
 * A known, already-diagnosed difference between our number and the client's
 * spreadsheet, written by hand in PT-BR (backend `app/closing/notes.py`). Not
 * runtime detection — nothing inspects a value; these are explanations we chose to
 * publish so the client reads the answer where the question comes up.
 */
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
  /** PT-BR explanations of the month's known discrepancies (may be empty). */
  generated_at: string;
}
