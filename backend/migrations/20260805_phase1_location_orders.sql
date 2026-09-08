alter table orders add column if not exists location_id uuid references business_locations(id) on delete set null;
create index if not exists orders_business_location_placed_idx on orders(business_id, location_id, placed_at desc);
