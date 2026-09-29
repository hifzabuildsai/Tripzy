create or replace function public.set_trips_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_trips_updated_at_on_update on public.trips;

create trigger set_trips_updated_at_on_update
before update on public.trips
for each row
execute function public.set_trips_updated_at();
