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
