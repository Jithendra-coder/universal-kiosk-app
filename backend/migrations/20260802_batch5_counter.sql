create table if not exists counter_held_orders (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references businesses(id) on delete cascade,
  device_id uuid not null references devices(id) on delete cascade,
  order_reference text,
  payload jsonb not null,
  status text not null default 'held' check (status in ('held','resumed','cancelled','expired')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  expires_at timestamptz not null default (now() + interval '24 hours')
);
create index if not exists counter_held_orders_scope_idx on counter_held_orders(business_id,device_id,status,created_at desc);

create table if not exists counter_payment_claims (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references businesses(id) on delete cascade,
  payment_id uuid not null references payments(id) on delete cascade,
  order_id uuid not null references orders(id) on delete cascade,
  device_id uuid not null references devices(id) on delete cascade,
  status text not null default 'claimed' check (status in ('claimed','released','expired','completed')),
  claimed_at timestamptz not null default now(),
  expires_at timestamptz not null,
  released_at timestamptz,
  created_at timestamptz not null default now(),
  unique (payment_id, status) deferrable initially immediate
);
create index if not exists counter_payment_claims_scope_idx on counter_payment_claims(business_id,payment_id,status,expires_at);
