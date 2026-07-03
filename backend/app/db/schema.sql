-- backend/app/db/schema.sql
create table if not exists clients (
  id text primary key,
  name text not null,
  provider text not null,
  provider_config jsonb not null default '{}'::jsonb,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null,
  role text not null check (role in ('ADMIN','CLIENT')),
  client_id text references clients(id),
  active boolean not null default true,
  created_at timestamptz not null default now()
);

-- Manually-entered Orcado (budget). One row per client + year + DRE line +
-- area. `annual_amount` is the yearly budget; monthly = annual / 12. `area` is
-- 'institucional' (consolidated) or a cost-center name (Contencioso/Economico/
-- Arbitragem). `line_key` matches the canonical keys in app/closing/dre.py.
-- `monthly_amounts` is an optional 12-element jsonb array (Jan..Dez) for
-- workbook-granularity budgets where the Orçado varies month-to-month (Custo
-- equipe, Despesas, etc.). When null, monthly = annual_amount / 12 (even split).
create table if not exists budgets (
  client_id text not null references clients(id),
  ano int not null,
  area text not null default 'institucional',
  line_key text not null,
  annual_amount numeric not null default 0,
  monthly_amounts jsonb,
  updated_at timestamptz not null default now(),
  primary key (client_id, ano, area, line_key)
);

-- Manually-entered Realizado inputs that SISJURI cannot derive. Per-area
-- Recebimento is NO LONGER here — it is now derived from SISJURI (receipt view
-- split by CASO -> área jurídica, verified to the centavo vs the workbook).
-- What remains manual: per-area Comissão, Despesas Equipe, Despesa
-- Institucional. Grain is per competence month; `line_key` matches
-- app/closing/dre. A manual per-area Recebimento row still overrides the derived
-- value if one is entered (later-overrides-earlier).
create table if not exists manual_actuals (
  client_id text not null references clients(id),
  ano_mes text not null,
  area text not null,
  line_key text not null,
  valor numeric not null default 0,
  updated_at timestamptz not null default now(),
  primary key (client_id, ano_mes, area, line_key)
);

-- Cross-area recebimento reclassifications ('Resumo_Recebidas' overlay). The
-- per-area recebimento BASE is derived from SISJURI; finance then moves cash
-- between areas (a commission credited to the originating lawyer's area, a case
-- worked by one area but billed under another). Each row subtracts `valor` from
-- `origem` and adds it to `destino`, so the total is conserved and still sums to
-- the sacred SISJURI recebimento. Areas: Contencioso/Economico/Arbitragem.
create table if not exists area_transfers (
  id uuid primary key default gen_random_uuid(),
  client_id text not null references clients(id),
  ano_mes text not null,
  origem text not null,
  destino text not null,
  valor numeric not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists area_transfers_client_mes
  on area_transfers (client_id, ano_mes);

-- Raw SISJURI extraction snapshots (one JSON per client + competence month).
-- The on-server agent POSTs these to /api/ingest; the whole financial dataset
-- lives in `payload` as jsonb so it is durable, backed up, and multi-tenant
-- (keyed by client_id) — unlike the earlier per-VPS filesystem store.
create table if not exists sisjuri_snapshots (
  client_id text not null references clients(id),
  ano_mes text not null,
  payload jsonb not null,
  updated_at timestamptz not null default now(),
  primary key (client_id, ano_mes)
);
