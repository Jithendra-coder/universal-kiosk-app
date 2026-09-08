begin;

create table if not exists test_runtime_orders (
  id uuid primary key default gen_random_uuid(),
  test_session_id uuid not null references kiosk_test_sessions(id) on delete cascade,
  business_id uuid not null references businesses(id) on delete cascade,
  source text not null check (source in ('kiosk','counter')),
  order_type text not null check (order_type in ('dine_in','takeaway')),
  items jsonb not null default '[]'::jsonb,
  notes text,
  payment_status text not null default 'awaiting_payment' check (payment_status in ('awaiting_payment','paid')),
  kitchen_status text not null default 'pending_payment' check (kitchen_status in ('pending_payment','pending','preparing','ready','completed')),
  is_held boolean not null default false,
  held_at timestamptz,
  handed_over_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists test_runtime_orders_session_status_idx on test_runtime_orders(test_session_id, kitchen_status, created_at);

alter table test_runtime_orders
  add column if not exists location_id uuid,
  add column if not exists hold_reason text,
  add column if not exists held_by uuid,
  add column if not exists previous_kitchen_status text,
  add column if not exists handover_metadata jsonb not null default '{}'::jsonb,
  add column if not exists idempotency_key text,
  add column if not exists preparing_started_at timestamptz,
  add column if not exists ready_at timestamptz,
  add column if not exists completed_at timestamptz,
  add column if not exists rework_requested boolean not null default false,
  add column if not exists rework_reason text,
  add column if not exists rework_requested_at timestamptz,
  add column if not exists rework_metadata jsonb not null default '{}'::jsonb,
  add column if not exists table_label text,
  add column if not exists subtotal numeric(12,2) not null default 0,
  add column if not exists tax_amount numeric(12,2) not null default 0,
  add column if not exists total_amount numeric(12,2) not null default 0,
  add column if not exists payment_method text,
  add column if not exists paid_at timestamptz,
  add column if not exists handed_over_by uuid;

create unique index if not exists test_runtime_orders_idempotency_uidx
on test_runtime_orders(test_session_id, business_id, idempotency_key)
where idempotency_key is not null;

create table if not exists test_runtime_order_events (
  id uuid primary key default gen_random_uuid(),
  test_session_id uuid not null references kiosk_test_sessions(id) on delete cascade,
  business_id uuid not null references businesses(id) on delete cascade,
  order_id uuid not null references test_runtime_orders(id) on delete cascade,
  app_type text not null check (app_type in ('kiosk','counter','kitchen')),
  event_type text not null,
  from_status text,
  to_status text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists test_runtime_order_events_order_idx
on test_runtime_order_events(test_session_id, business_id, order_id, created_at);

create table if not exists test_runtime_availability_overrides (
  test_session_id uuid not null references kiosk_test_sessions(id) on delete cascade,
  product_id uuid not null references products(id) on delete cascade,
  is_available boolean not null,
  updated_at timestamptz not null default now(),
  primary key (test_session_id, product_id)
);

commit;
