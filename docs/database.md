# Database bootstrap and verification

The `supabase/migrations` directory is the repository-owned source of truth for
Tripzy's production database objects. Its two migrations match the migration
history and schema currently deployed to the production Supabase project:

- `public.trips` stores the serialized trip state and timestamps.
- Row Level Security is enabled with no policies. This intentionally denies
  direct `anon` and `authenticated` access.
- `set_trips_updated_at_on_update` refreshes `updated_at` before each update.

The backend uses the server-only Supabase service-role credential, which bypasses
RLS. Never expose that credential to the frontend or commit it to the repository.

## Local bootstrap

Docker is required by the Supabase CLI. From the repository root, start the
local stack and replay every migration:

```bash
npx --yes supabase@2.118.0 start
npx --yes supabase@2.118.0 db reset
```

Stop it when finished:

```bash
npx --yes supabase@2.118.0 stop
```

## RLS verification

Run the following as a database administrator against a freshly reset local
database. It creates a transaction-only probe row, verifies both Data API roles,
and rolls the row back. Both queries must return `false`:

```sql
begin;

insert into public.trips (id, state)
values (
  '00000000-0000-0000-0000-000000000018',
  '{"verification": true}'::jsonb
);

set local role anon;
select exists (
  select 1 from public.trips
  where id = '00000000-0000-0000-0000-000000000018'
) as anon_can_read_probe_trip;

reset role;
set local role authenticated;
select exists (
  select 1 from public.trips
  where id = '00000000-0000-0000-0000-000000000018'
) as authenticated_can_read_probe_trip;

rollback;
```

Do not run this probe against production.
