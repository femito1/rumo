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
create table if not exists budgets (
  client_id text not null references clients(id),
  ano int not null,
  area text not null default 'institucional',
  line_key text not null,
  annual_amount numeric not null default 0,
  updated_at timestamptz not null default now(),
  primary key (client_id, ano, area, line_key)
);

-- Manually-entered Realizado inputs that SISJURI cannot derive. The prime case
-- is per-area Recebimento: the workbook assigns received cash to a practice
-- area (Contencioso/Economico/Arbitragem) via case-by-case human classification
-- and cross-area transfers recorded in 'Resumo_Recebidas', which has no DB
-- equivalent. Grain is per competence month. `line_key` matches app/closing/dre.
create table if not exists manual_actuals (
  client_id text not null references clients(id),
  ano_mes text not null,
  area text not null,
  line_key text not null,
  valor numeric not null default 0,
  updated_at timestamptz not null default now(),
  primary key (client_id, ano_mes, area, line_key)
);

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
