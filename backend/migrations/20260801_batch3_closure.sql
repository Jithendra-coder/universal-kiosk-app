create table if not exists business_locations (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references businesses(id) on delete cascade,
  name text not null,
  created_at timestamptz not null default now(),
  unique (business_id, name)
);

create table if not exists kiosk_promotions (
  id uuid primary key default gen_random_uuid(), business_id uuid not null references businesses(id) on delete cascade,
  name text not null, description text, discount_type text not null default 'percentage', discount_value numeric(10,2) not null default 0,
  starts_at timestamptz, ends_at timestamptz, status text not null default 'draft', paused_at timestamptz,
  created_by uuid not null references app_users(id) on delete restrict, updated_by uuid references app_users(id) on delete set null,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists kiosk_promotion_targets (promotion_id uuid not null references kiosk_promotions(id) on delete cascade, target_type text not null, target_id uuid not null, primary key (promotion_id, target_type, target_id));
create table if not exists kiosk_promotion_locations (promotion_id uuid not null references kiosk_promotions(id) on delete cascade, location_id uuid not null references business_locations(id) on delete cascade, primary key (promotion_id, location_id));
create table if not exists kiosk_promotion_placements (promotion_id uuid not null references kiosk_promotions(id) on delete cascade, placement text not null, primary key (promotion_id, placement));

create table if not exists kiosk_qr_codes (
  id uuid primary key default gen_random_uuid(), business_id uuid not null references businesses(id) on delete cascade,
  name text not null, destination_type text not null, destination_id uuid, location_id uuid references business_locations(id) on delete set null,
  table_token text, active boolean not null default true, expires_at timestamptz, tracking_metadata jsonb not null default '{}'::jsonb,
  created_by uuid not null references app_users(id) on delete restrict, updated_by uuid references app_users(id) on delete set null,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);

create table if not exists kiosk_published_versions (
  id uuid primary key default gen_random_uuid(), business_id uuid not null references businesses(id) on delete cascade,
  version_number integer not null, config_signature text not null, snapshot jsonb not null, published_by uuid not null references app_users(id) on delete restrict,
  source_draft_id uuid, published_at timestamptz not null default now(), unique (business_id, version_number)
);
create table if not exists kiosk_restore_lineage (
  id uuid primary key default gen_random_uuid(), business_id uuid not null references businesses(id) on delete cascade,
  source_version_id uuid not null references kiosk_published_versions(id) on delete restrict, draft_id uuid not null,
  created_by uuid not null references app_users(id) on delete restrict, created_at timestamptz not null default now()
);
