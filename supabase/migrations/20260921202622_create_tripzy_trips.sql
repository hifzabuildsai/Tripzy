create table if not exists public.trips (
  id uuid primary key,
  state jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.trips enable row level security;

comment on table public.trips is 'Durable Tripzy trip planning state.';
comment on column public.trips.state is 'Serialized TripState JSON document.';
