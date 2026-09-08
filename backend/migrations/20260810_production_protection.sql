begin;

alter table auth_sessions add column if not exists reauthenticated_at timestamptz not null default now();

commit;
