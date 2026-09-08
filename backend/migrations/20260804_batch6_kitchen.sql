alter table orders add column if not exists source text not null default 'kiosk';
create table if not exists kitchen_order_states (
  order_id uuid primary key references orders(id) on delete cascade,
  business_id uuid not null references businesses(id) on delete cascade,
  stage text not null check (stage in ('pending','preparing','ready')),
  is_held boolean not null default false, hold_reason text, held_at timestamptz,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists kitchen_item_states (
  order_item_id uuid primary key references order_items(id) on delete cascade,
  order_id uuid not null references orders(id) on delete cascade,
  business_id uuid not null references businesses(id) on delete cascade,
  completed_quantity integer not null default 0 check (completed_quantity >= 0), updated_at timestamptz not null default now()
);
create table if not exists kitchen_offline_events (
  event_id uuid primary key, business_id uuid not null references businesses(id) on delete cascade,
  device_id uuid not null references devices(id) on delete cascade, order_id uuid references orders(id) on delete cascade,
  action text not null, payload jsonb not null default '{}'::jsonb, status text not null default 'applied',
  created_at timestamptz not null default now()
);
create table if not exists kitchen_device_preferences (
  device_id uuid primary key references devices(id) on delete cascade,
  sound_enabled boolean not null default true, sound_volume integer not null default 70 check (sound_volume between 0 and 100), updated_at timestamptz not null default now()
);
create index if not exists kitchen_order_states_scope_idx on kitchen_order_states(business_id,stage,is_held);
create index if not exists kitchen_offline_events_scope_idx on kitchen_offline_events(business_id,device_id,created_at);
