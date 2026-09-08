begin;

alter table businesses
add column if not exists kiosk_layout_id text,
add column if not exists welcome_screen jsonb;

update businesses
set kiosk_layout_id = case split_part(kiosk_theme, ':', 1)
  when 'left_category' then 'side-navigation'
  when 'category_gate' then 'category-first'
  else 'top-navigation'
end
where kiosk_layout_id is null;

update businesses
set welcome_screen = jsonb_build_object(
  'enabled', kiosk_start_screen_enabled,
  'heading', coalesce(nullif(kiosk_start_screen_settings->>'heading', ''), 'Welcome'),
  'supporting_text', coalesce(kiosk_start_screen_settings->>'supporting_text', ''),
  'instruction_text', coalesce(nullif(kiosk_start_screen_settings->>'instruction_text', ''), 'Tap to begin'),
  'start_button_text', coalesce(nullif(kiosk_start_screen_settings->>'start_button_text', ''), 'Start'),
  'text_position', kiosk_start_text_position,
  'touch_anywhere_to_start', kiosk_touch_to_start,
  'show_business_logo', coalesce((kiosk_start_screen_settings->>'show_business_logo')::boolean, true)
)
where welcome_screen is null;

alter table businesses
alter column kiosk_layout_id set default 'top-navigation',
alter column kiosk_layout_id set not null,
alter column welcome_screen set default '{
  "enabled": true,
  "heading": "Welcome",
  "supporting_text": "",
  "instruction_text": "Tap to begin",
  "start_button_text": "Start",
  "text_position": "middle",
  "touch_anywhere_to_start": false,
  "show_business_logo": true
}'::jsonb,
alter column welcome_screen set not null;

alter table businesses
drop constraint if exists businesses_kiosk_layout_id_check;

alter table businesses
add constraint businesses_kiosk_layout_id_check
check (kiosk_layout_id in ('side-navigation', 'top-navigation', 'category-first'));

create table if not exists kiosk_test_sessions (
  id uuid primary key default gen_random_uuid(),
  business_id uuid not null references businesses(id) on delete cascade,
  token_hash text not null unique,
  created_by uuid not null references app_users(id) on delete restrict,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  last_used_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists kiosk_test_sessions_business_created_idx
on kiosk_test_sessions(business_id, created_at desc);

create index if not exists kiosk_test_sessions_expires_at_idx
on kiosk_test_sessions(expires_at);

alter table orders
add column if not exists idempotency_key text;

create unique index if not exists orders_business_idempotency_uidx
on orders(business_id, idempotency_key)
where idempotency_key is not null;

commit;
