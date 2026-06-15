create extension if not exists pgcrypto;

insert into users (user_id, full_name, email, password_hash, role, status)
values
  (
    '11111111-1111-4111-8111-111111111111',
    'RM Test Owner',
    'rm-owner-test@what2eat.com',
    crypt('123456', gen_salt('bf')),
    'OWNER',
    'ACTIVE'
  ),
  (
    '22222222-2222-4222-8222-222222222222',
    'RM Other Owner',
    'rm-other-owner-test@what2eat.com',
    crypt('123456', gen_salt('bf')),
    'OWNER',
    'ACTIVE'
  ),
  (
    '33333333-3333-4333-8333-333333333333',
    'RM Test Customer',
    'rm-customer-test@what2eat.com',
    crypt('123456', gen_salt('bf')),
    'CUSTOMER',
    'ACTIVE'
  )
on conflict (email) do update
set
  full_name = excluded.full_name,
  password_hash = excluded.password_hash,
  role = excluded.role,
  status = excluded.status;

insert into owner_profiles (owner_id, tax_id, business_license)
values
  ('11111111-1111-4111-8111-111111111111', 'RM-TAX-001', 'RM-LICENSE-001'),
  ('22222222-2222-4222-8222-222222222222', 'RM-TAX-002', 'RM-LICENSE-002')
on conflict (owner_id) do update
set
  tax_id = excluded.tax_id,
  business_license = excluded.business_license;

insert into customer_profiles (customer_id, preferred_price_range, loyalty_points, personalization_enabled)
values
  ('33333333-3333-4333-8333-333333333333', '50000 - 100000', 0, true)
on conflict (customer_id) do update
set
  preferred_price_range = excluded.preferred_price_range,
  loyalty_points = excluded.loyalty_points,
  personalization_enabled = excluded.personalization_enabled;

insert into restaurants (
  restaurant_id,
  owner_id,
  name,
  description,
  address,
  latitude,
  longitude,
  phone,
  opening_hours,
  price_range,
  rating_avg,
  approval_status,
  is_active
)
values
  (
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    '11111111-1111-4111-8111-111111111111',
    'RM Happy Thai Thu Duc',
    'Nha hang approved dung de test cap nhat, menu, booking va review.',
    '20 Doan Ket, Thu Duc, Ho Chi Minh',
    10.84723780,
    106.76853290,
    '0904192236',
    '{"mon":"08:00-22:00","tue":"08:00-22:00","wed":"08:00-22:00","thu":"08:00-22:00","fri":"08:00-22:00","sat":"08:00-22:00","sun":"08:00-22:00"}',
    '50000 - 60000',
    4.80,
    'APPROVED',
    true
  ),
  (
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    '11111111-1111-4111-8111-111111111111',
    'RM Pending Bistro',
    'Nha hang pending dung de test khong duoc cap nhat va khong duoc them menu.',
    '23 Hong Duc, Thu Duc, Ho Chi Minh',
    10.84381060,
    106.76428010,
    '0901125471',
    '{"mon":"08:00-22:00","tue":"08:00-22:00","wed":"08:00-22:00","thu":"08:00-22:00","fri":"08:00-22:00","sat":"08:00-22:00","sun":"08:00-22:00"}',
    '50000 - 70000',
    4.20,
    'PENDING',
    true
  ),
  (
    'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    '22222222-2222-4222-8222-222222222222',
    'RM Other Owner Restaurant',
    'Nha hang cua owner khac dung de test phan quyen.',
    '30 Nguyen Hue, Quan 1, Ho Chi Minh',
    10.77584390,
    106.70175550,
    '0902000002',
    '{"mon":"08:00-22:00","tue":"08:00-22:00","wed":"08:00-22:00","thu":"08:00-22:00","fri":"08:00-22:00","sat":"08:00-22:00","sun":"08:00-22:00"}',
    '70000 - 120000',
    4.50,
    'APPROVED',
    true
  )
on conflict (restaurant_id) do update
set
  owner_id = excluded.owner_id,
  name = excluded.name,
  description = excluded.description,
  address = excluded.address,
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  phone = excluded.phone,
  opening_hours = excluded.opening_hours,
  price_range = excluded.price_range,
  rating_avg = excluded.rating_avg,
  approval_status = excluded.approval_status,
  is_active = excluded.is_active;

insert into capacities (capacity_id, restaurant_id, day_of_week, start_time, end_time, max_capacity)
values
  ('a1111111-1111-4111-8111-111111111111', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 1, '08:00', '22:00', 60),
  ('a2222222-2222-4222-8222-222222222222', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', 1, '08:00', '22:00', 40),
  ('a3333333-3333-4333-8333-333333333333', 'cccccccc-cccc-4ccc-8ccc-cccccccccccc', 1, '08:00', '22:00', 50)
on conflict on constraint unique_capacity do update
set max_capacity = excluded.max_capacity;

insert into menu_items (
  item_id,
  restaurant_id,
  name,
  description,
  price,
  category,
  image_url,
  availability_status
)
values
  (
    'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    'Pad Thai Hai San',
    'Mon an co san dung de test thuc don cua owner.',
    169000,
    'Mon Thai',
    'https://happythai.vn/uploads/source/image-logo/pad-thai-hai-san.png',
    'AVAILABLE'
  ),
  (
    'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
    'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    'Mien Xao Cua',
    'Mon an cua owner khac dung de test phan quyen cap nhat mon.',
    239000,
    'Mon Thai',
    'https://happythai.vn/uploads/source/image-logo/mien-xao-cua.png',
    'AVAILABLE'
  )
on conflict (item_id) do update
set
  restaurant_id = excluded.restaurant_id,
  name = excluded.name,
  description = excluded.description,
  price = excluded.price,
  category = excluded.category,
  image_url = excluded.image_url,
  availability_status = excluded.availability_status;

insert into reservations (
  reservation_id,
  customer_id,
  restaurant_id,
  reservation_time,
  guest_count,
  notes,
  status,
  rejection_reason
)
values
  (
    'ffffffff-ffff-4fff-8fff-ffffffffffff',
    '33333333-3333-4333-8333-333333333333',
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    now() + interval '2 days',
    4,
    'Ban gan cua so',
    'PENDING',
    null
  )
on conflict (reservation_id) do update
set
  customer_id = excluded.customer_id,
  restaurant_id = excluded.restaurant_id,
  reservation_time = excluded.reservation_time,
  guest_count = excluded.guest_count,
  notes = excluded.notes,
  status = excluded.status,
  rejection_reason = excluded.rejection_reason;

insert into reviews (
  review_id,
  customer_id,
  restaurant_id,
  reservation_id,
  rating,
  comment,
  status,
  rejection_reason
)
values
  (
    '99999999-9999-4999-8999-999999999999',
    '33333333-3333-4333-8333-333333333333',
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    null,
    5,
    'Quan phu hop de test danh gia cua owner.',
    'APPROVED',
    null
  )
on conflict (review_id) do update
set
  customer_id = excluded.customer_id,
  restaurant_id = excluded.restaurant_id,
  reservation_id = excluded.reservation_id,
  rating = excluded.rating,
  comment = excluded.comment,
  status = excluded.status,
  rejection_reason = excluded.rejection_reason;
